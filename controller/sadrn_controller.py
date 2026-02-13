#!/usr/bin/env python3
"""
SADRN - Software Defined Adaptive Disaster Response Network
Ryu SDN Controller with NetworkX-based Adaptive Routing
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, udp, tcp, arp, ether_types
from ryu.lib import hub
from ryu.topology import event as topo_event
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from webob import Response
import networkx as nx
import json
import logging
import time
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SADRN_Controller')

SADRN_INSTANCE_NAME = 'sadrn_controller_api'
DSCP_EMERGENCY = 46
DSCP_NORMAL = 0
SADRN_DATA_PORT = 5000
SADRN_EMERGENCY_PORT = 5001
DISPLAY_NODE_IP = '10.0.0.100'
DISPLAY_NODE_MAC = '00:00:00:00:00:64'

HOST_SWITCH_MAP = {
    '10.0.0.1': 1, '10.0.0.2': 2, '10.0.0.3': 3, '10.0.0.100': 1,
}

HOST_PORT_MAP = {
    '10.0.0.1': (1, 3), '10.0.0.2': (2, 3), '10.0.0.3': (3, 3), '10.0.0.100': (1, 4),
}


class SADRNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}
    
    def __init__(self, *args, **kwargs):
        super(SADRNController, self).__init__(*args, **kwargs)
        self.topology_graph = nx.Graph()
        self.mac_to_port = defaultdict(dict)
        self.datapaths = {}
        self.switches = {}
        self.links = {}
        self.battery_levels = {1: 100, 2: 100, 3: 100}
        self.emergency_status = {'h1': False, 'h2': False, 'h3': False}
        self.disaster_types = {'h1': None, 'h2': None, 'h3': None}
        self.packet_stats = {'emergency': 0, 'normal': 0, 'total': 0}
        self.path_cache = {}
        self.path_cache_timeout = 5
        
        wsgi = kwargs['wsgi']
        wsgi.register(SADRNRestController, {SADRN_INSTANCE_NAME: self})
        logger.info("SADRN Controller initialized")
        self.topology_thread = hub.spawn(self._topology_discovery_loop)
    
    def _topology_discovery_loop(self):
        while True:
            self._discover_topology()
            hub.sleep(10)
    
    def _discover_topology(self):
        try:
            switch_list = get_switch(self, None)
            switches = [s.dp.id for s in switch_list]
            link_list = get_link(self, None)
            self.topology_graph.clear()
            
            for dpid in switches:
                self.topology_graph.add_node(dpid, type='switch')
            
            for link in link_list:
                weight = self._calculate_link_weight(link.src.dpid, link.dst.dpid)
                self.topology_graph.add_edge(
                    link.src.dpid, link.dst.dpid,
                    src_port=link.src.port_no, dst_port=link.dst.port_no, weight=weight
                )
            self.path_cache.clear()
        except Exception as e:
            logger.error(f"Topology discovery error: {e}")
    
    def _calculate_link_weight(self, src_dpid, dst_dpid, emergency=False):
        if emergency:
            return 1
        src_battery = self.battery_levels.get(src_dpid, 100)
        dst_battery = self.battery_levels.get(dst_dpid, 100)
        avg_battery = max(1, (src_battery + dst_battery) / 2)
        return 1 + (100 / avg_battery)
    
    def _update_all_weights(self, emergency=False):
        for u, v in self.topology_graph.edges():
            self.topology_graph[u][v]['weight'] = self._calculate_link_weight(u, v, emergency)
    
    def _get_shortest_path(self, src_dpid, dst_dpid, emergency=False):
        self._update_all_weights(emergency)
        cache_key = (src_dpid, dst_dpid, emergency)
        
        if cache_key in self.path_cache:
            cached_path, cache_time = self.path_cache[cache_key]
            if time.time() - cache_time < self.path_cache_timeout:
                return cached_path
        
        try:
            path = [src_dpid] if src_dpid == dst_dpid else nx.dijkstra_path(
                self.topology_graph, src_dpid, dst_dpid, weight='weight')
            self.path_cache[cache_key] = (path, time.time())
            mode = "EMERGENCY" if emergency else "ENERGY-AWARE"
            logger.info(f"[{mode}] Path from s{src_dpid} to s{dst_dpid}: {['s'+str(s) for s in path]}")
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def _get_output_port(self, src_dpid, dst_dpid):
        try:
            edge_data = self.topology_graph.get_edge_data(src_dpid, dst_dpid)
            return edge_data['src_port'] if edge_data else None
        except:
            return None
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath
        logger.info(f"Switch s{datapath.id} connected")
        match = datapath.ofproto_parser.OFPMatch()
        actions = [datapath.ofproto_parser.OFPActionOutput(
            datapath.ofproto.OFPP_CONTROLLER, datapath.ofproto.OFPCML_NO_BUFFER)]
        self._add_flow(datapath, 0, match, actions)
    
    def _add_flow(self, datapath, priority, match, actions, idle_timeout=0, hard_timeout=0):
        inst = [datapath.ofproto_parser.OFPInstructionActions(
            datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match,
            instructions=inst, idle_timeout=idle_timeout, hard_timeout=hard_timeout)
        datapath.send_msg(mod)
    
    def _is_emergency_packet(self, pkt):
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt:
            if (ip_pkt.tos >> 2) == DSCP_EMERGENCY:
                return True
            udp_pkt = pkt.get_protocol(udp.udp)
            if udp_pkt and udp_pkt.dst_port == SADRN_EMERGENCY_PORT:
                return True
        return False
    
    def _check_source_emergency(self, src_ip):
        host_map = {'10.0.0.1': 'h1', '10.0.0.2': 'h2', '10.0.0.3': 'h3'}
        return self.emergency_status.get(host_map.get(src_ip), False)
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']
        dpid = datapath.id
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        
        self.mac_to_port[dpid][eth.src] = in_port
        
        if pkt.get_protocol(arp.arp):
            self._flood(datapath, msg.data, in_port)
            return
        
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt:
            self._handle_ipv4(datapath, in_port, eth, ip_pkt, pkt, msg.data)
            return
        
        self._flood(datapath, msg.data, in_port)
    
    def _handle_ipv4(self, datapath, in_port, eth, ip_pkt, pkt, data):
        dpid = datapath.id
        is_emergency = self._is_emergency_packet(pkt) or self._check_source_emergency(ip_pkt.src)
        
        self.packet_stats['total'] += 1
        self.packet_stats['emergency' if is_emergency else 'normal'] += 1
        
        dst_switch = HOST_SWITCH_MAP.get(ip_pkt.dst)
        if not dst_switch:
            self._flood(datapath, data, in_port)
            return
        
        path = self._get_shortest_path(dpid, dst_switch, emergency=is_emergency)
        if not path:
            self._flood(datapath, data, in_port)
            return
        
        self._install_path_flows(path, eth.src, eth.dst, ip_pkt, is_emergency)
        
        if len(path) == 1:
            dst_host_info = HOST_PORT_MAP.get(ip_pkt.dst)
            out_port = dst_host_info[1] if dst_host_info and dst_host_info[0] == dpid else datapath.ofproto.OFPP_FLOOD
        else:
            out_port = self._get_output_port(dpid, path[1]) or datapath.ofproto.OFPP_FLOOD
        
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=datapath.ofproto.OFP_NO_BUFFER,
            in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
    
    def _install_path_flows(self, path, src_mac, dst_mac, ip_pkt, is_emergency):
        priority = 200 if is_emergency else 100
        for i, dpid in enumerate(path):
            if dpid not in self.datapaths:
                continue
            datapath = self.datapaths[dpid]
            parser = datapath.ofproto_parser
            
            if i == len(path) - 1:
                dst_host_info = HOST_PORT_MAP.get(ip_pkt.dst)
                if not (dst_host_info and dst_host_info[0] == dpid):
                    continue
                out_port = dst_host_info[1]
            else:
                out_port = self._get_output_port(dpid, path[i + 1])
                if not out_port:
                    continue
            
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_src=ip_pkt.src, ipv4_dst=ip_pkt.dst)
            actions = [parser.OFPActionOutput(out_port)]
            self._add_flow(datapath, priority, match, actions, idle_timeout=30, hard_timeout=60)
    
    def _flood(self, datapath, data, in_port):
        actions = [datapath.ofproto_parser.OFPActionOutput(datapath.ofproto.OFPP_FLOOD)]
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=datapath.ofproto.OFP_NO_BUFFER,
            in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
    
    def set_battery_level(self, switch_id, level):
        if switch_id in self.battery_levels:
            self.battery_levels[switch_id] = max(1, min(100, level))
            self.path_cache.clear()
            logger.info(f"Battery level for s{switch_id} set to {level}%")
            return True
        return False
    
    def set_emergency_status(self, host, status, disaster_type=None):
        if host in self.emergency_status:
            self.emergency_status[host] = status
            self.disaster_types[host] = disaster_type if status else None
            self.path_cache.clear()
            logger.info(f"Emergency status for {host}: {status} (Type: {disaster_type})")
            return True
        return False
    
    def get_topology_info(self):
        nodes, edges = [], []
        for dpid in self.topology_graph.nodes():
            nodes.append({'id': f's{dpid}', 'type': 'switch', 'battery': self.battery_levels.get(dpid, 100)})
        
        for ip, switch in HOST_SWITCH_MAP.items():
            host_name = f'h{ip.split(".")[-1]}' if ip != DISPLAY_NODE_IP else 'h_display'
            nodes.append({
                'id': host_name, 'type': 'host' if host_name != 'h_display' else 'display',
                'ip': ip, 'switch': f's{switch}',
                'emergency': self.emergency_status.get(host_name, False),
                'disaster_type': self.disaster_types.get(host_name)
            })
            edges.append({'source': host_name, 'target': f's{switch}', 'type': 'host-link'})
        
        for u, v, data in self.topology_graph.edges(data=True):
            edges.append({'source': f's{u}', 'target': f's{v}', 'weight': data.get('weight', 1), 'type': 'switch-link'})
        return {'nodes': nodes, 'edges': edges}
    
    def get_paths_to_display(self):
        paths = {}
        display_switch = HOST_SWITCH_MAP.get(DISPLAY_NODE_IP)
        for host in ['h1', 'h2', 'h3']:
            src_switch = HOST_SWITCH_MAP.get(f'10.0.0.{host[1]}')
            is_emergency = self.emergency_status.get(host, False)
            path = self._get_shortest_path(src_switch, display_switch, emergency=is_emergency)
            if path:
                paths[host] = {'path': [f's{s}' for s in path], 'emergency': is_emergency, 'disaster_type': self.disaster_types.get(host)}
        return paths


class SADRNRestController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(SADRNRestController, self).__init__(req, link, data, **config)
        self.sadrn_controller = data[SADRN_INSTANCE_NAME]
    
    @route('sadrn', '/sadrn/topology', methods=['GET'])
    def get_topology(self, req, **kwargs):
        return Response(content_type='application/json; charset=utf-8', body=json.dumps(self.sadrn_controller.get_topology_info()).encode('utf-8'))
    
    @route('sadrn', '/sadrn/battery/{switch_id}', methods=['POST'])
    def set_battery(self, req, switch_id, **kwargs):
        try:
            level = json.loads(req.body).get('level', 100)
            success = self.sadrn_controller.set_battery_level(int(switch_id), level)
            return Response(content_type='application/json; charset=utf-8', body=json.dumps({'success': success}).encode('utf-8'))
        except Exception as e:
            return Response(content_type='application/json; charset=utf-8', body=json.dumps({'error': str(e)}).encode('utf-8'), status=400)
    
    @route('sadrn', '/sadrn/emergency/{host}', methods=['POST'])
    def set_emergency(self, req, host, **kwargs):
        try:
            body = json.loads(req.body)
            success = self.sadrn_controller.set_emergency_status(host, body.get('status', False), body.get('disaster_type'))
            return Response(content_type='application/json; charset=utf-8', body=json.dumps({'success': success}).encode('utf-8'))
        except Exception as e:
            return Response(content_type='application/json; charset=utf-8', body=json.dumps({'error': str(e)}).encode('utf-8'), status=400)
    
    @route('sadrn', '/sadrn/paths', methods=['GET'])
    def get_paths(self, req, **kwargs):
        return Response(content_type='application/json; charset=utf-8', body=json.dumps(self.sadrn_controller.get_paths_to_display()).encode('utf-8'))
    
    @route('sadrn', '/sadrn/stats', methods=['GET'])
    def get_stats(self, req, **kwargs):
        stats = self.sadrn_controller.packet_stats.copy()
        stats['battery_levels'] = self.sadrn_controller.battery_levels.copy()
        stats['emergency_status'] = self.sadrn_controller.emergency_status.copy()
        return Response(content_type='application/json; charset=utf-8', body=json.dumps(stats).encode('utf-8'))
    
    @route('sadrn', '/sadrn/battery', methods=['GET'])
    def get_all_battery(self, req, **kwargs):
        return Response(content_type='application/json; charset=utf-8', body=json.dumps(self.sadrn_controller.battery_levels).encode('utf-8'))
    
    @route('sadrn', '/sadrn/emergency', methods=['GET'])
    def get_all_emergency(self, req, **kwargs):
        return Response(content_type='application/json; charset=utf-8', body=json.dumps({'status': self.sadrn_controller.emergency_status, 'types': self.sadrn_controller.disaster_types}).encode('utf-8'))

app = SADRNController

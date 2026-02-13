#!/usr/bin/env python3
# SADRN Enhanced Topology - Fixed Connectivity
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import os, time

class SADRNTopology:
    def __init__(self):z
        self.controller_ip = '127.0.0.1'
        self.controller_port = 6653
        self.net = None
        self.switches = {}
        self.gateways = {}
        self.sensors = {}
        self.display = None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
    def create_topology(self):
        info('='*80 + '\n')
        info('*** Enhanced SADRN - 6 Switches (FIXED CONNECTIVITY) ***\n')
        info('='*80 + '\n')
        
        self.net = Mininet(controller=RemoteController, switch=OVSKernelSwitch, 
                          link=TCLink, autoSetMacs=True)
        self.net.addController('c0', controller=RemoteController,
                              ip=self.controller_ip, port=self.controller_port)
        
        info('*** Core Switches (S1-S3)\n')
        self.switches['s1'] = self.net.addSwitch('s1', dpid='0000000000000001')
        self.switches['s2'] = self.net.addSwitch('s2', dpid='0000000000000002')
        self.switches['s3'] = self.net.addSwitch('s3', dpid='0000000000000003')
        
        info('*** Zone Switches (S4-S6)\n')
        self.switches['s4'] = self.net.addSwitch('s4', dpid='0000000000000004')
        self.switches['s5'] = self.net.addSwitch('s5', dpid='0000000000000005')
        self.switches['s6'] = self.net.addSwitch('s6', dpid='0000000000000006')
        
        # Single subnet for L2 forwarding
        info('*** Hosts (10.0.0.x/8)\n')
        self.gateways['gw_a'] = self.net.addHost('gw_a', ip='10.0.0.1/8')
        self.gateways['gw_b'] = self.net.addHost('gw_b', ip='10.0.0.2/8')
        self.gateways['gw_c'] = self.net.addHost('gw_c', ip='10.0.0.3/8')
        self.sensors['water_a1'] = self.net.addHost('water_a1', ip='10.0.0.11/8')
        self.sensors['rain_a2'] = self.net.addHost('rain_a2', ip='10.0.0.12/8')
        self.sensors['seismic_b1'] = self.net.addHost('seismic_b1', ip='10.0.0.21/8')
        self.sensors['tilt_b2'] = self.net.addHost('tilt_b2', ip='10.0.0.22/8')
        self.sensors['temp_c1'] = self.net.addHost('temp_c1', ip='10.0.0.31/8')
        self.sensors['smoke_c2'] = self.net.addHost('smoke_c2', ip='10.0.0.32/8')
        self.display = self.net.addHost('display', ip='10.0.0.100/8')
        
        info('*** Links\n')
        # Core mesh
        self.net.addLink(self.switches['s1'], self.switches['s2'], bw=1000)
        self.net.addLink(self.switches['s2'], self.switches['s3'], bw=1000)
        self.net.addLink(self.switches['s3'], self.switches['s1'], bw=1000)
        # Zones
        self.net.addLink(self.switches['s4'], self.switches['s1'], bw=100)
        self.net.addLink(self.switches['s5], self.switches['s2'], bw=100)
        self.net.addLink(self.switches['s6'], self.switches['s3'], bw=100)
        # Display
        self.net.addLink(self.display, self.switches['s2'], bw=1000)
        self.net.addLink(self.display, self.switches['s1'], bw=1000)
        self.net.addLink(self.display, self.switches['s3'], bw=1000)
        
        # Gateways
        self.net.addLink(self.gateways['gw_a'], self.switches['s4'])
        self.net.addLink(self.gateways['gw_a'], self.switches['s5'])
        
        self.net.addLink(self.gateways['gw_b'], self.switches['s5'])
        self.net.addLink(self.gateways['gw_b'], self.switches['s6'])
        
        self.net.addLink(self.gateways['gw_c'], self.switches['s6'])
        self.net.addLink(self.gateways['gw_c'], self.switches['s4'])
        # Sensors
        for sensor in self.sensors.values():
            sw = 's4' if 'a' in sensor.name else ('s5' if 'b' in sensor.name else 's6')
            self.net.addLink(sensor, self.switches[sw])
        
        return self.net
    
    def start_network(self):
        info('\n*** Starting Network ***\n')
        self.net.build()
        self.net.start()
        time.sleep(3)
        for sw in ['s1','s2','s3','s4','s5','s6']:
            os.system(f'ovs-vsctl set bridge {sw} protocols=OpenFlow13')
        time.sleep(2)
        return self.net
    
    def start_services(self):
        info('\n*** Starting Services ***\n')
        
        # Display
        ds = os.path.join(self.base_dir, 'display/display_server.py')
        self.display.cmd(f'python3 {ds} 9001 > /tmp/display.log 2>&1 &')
        time.sleep(2)
        info('  Display: 10.0.0.100:9001\n')
        
        # Gateways
        gs = os.path.join(self.base_dir, 'hosts/gateway.py')
        self.gateways['gw_a'].cmd(f'python3 {gs} gw_a 10.0.0.100 --listen-port 9000 --display-port 9001 > /tmp/gw_a.log 2>&1 &')
        self.gateways['gw_b'].cmd(f'python3 {gs} gw_b 10.0.0.100 --listen-port 9000 --display-port 9001 > /tmp/gw_b.log 2>&1 &')
        self.gateways['gw_c'].cmd(f'python3 {gs} gw_c 10.0.0.100 --listen-port 9000 --display-port 9001 > /tmp/gw_c.log 2>&1 &')
        time.sleep(2)
        info('  Gateways: 10.0.0.1-3\n')
        
        # Sensors
        ss = os.path.join(self.base_dir, 'hosts/sensor.py')
        self.sensors['water_a1'].cmd(f'python3 {ss} flood_water 10.0.0.1 --interval 3 > /tmp/water_a1.log 2>&1 &')
        self.sensors['rain_a2'].cmd(f'python3 {ss} flood_rain 10.0.0.1 --interval 3 > /tmp/rain_a2.log 2>&1 &')
        self.sensors['seismic_b1'].cmd(f'python3 {ss} eq_seismic 10.0.0.2 --interval 3 > /tmp/seismic_b1.log 2>&1 &')
        self.sensors['tilt_b2'].cmd(f'python3 {ss} eq_tilt 10.0.0.2 --interval 3 > /tmp/tilt_b2.log 2>&1 &')
        self.sensors['temp_c1'].cmd(f'python3 {ss} fire_temp 10.0.0.3 --interval 3 > /tmp/temp_c1.log 2>&1 &')
        self.sensors['smoke_c2'].cmd(f'python3 {ss} fire_smoke 10.0.0.3 --interval 3 > /tmp/smoke_c2.log 2>&1 &')
        time.sleep(2)
        info('  Sensors: 6 started\n')
        
        info('\n*** Services Started - Logs in /tmp/*.log ***\n')
    
    def test_connectivity(self):
        info('\n=== CONNECTIVITY TEST ===\n')
        for gw_name, gw in self.gateways.items():
            r = gw.cmd('ping -c 1 -W 1 10.0.0.100')
            s = '✓' if '1 received' in r else '✗'
            info(f'{s} {gw_name} -> display\n')
        
        tests = [('water_a1','10.0.0.1','gw_a'),('seismic_b1','10.0.0.2','gw_b')]
        for sn, ip, gw in tests:
            r = self.sensors[sn].cmd(f'ping -c 1 -W 1 {ip}')
            s = '✓' if '1 received' in r else '✗'
            info(f'{s} {sn} -> {gw}\n')
        info('\n')
    
    def run_cli(self):
        info('*** Commands: pingall | display ping 10.0.0.1 | xterm display | exit ***\n\n')
        CLI(self.net)
    
    def stop_network(self):
        if self.net:
            for h in list(self.sensors.values()) + list(self.gateways.values()) + [self.display]:
                h.cmd('pkill -f .py')
            self.net.stop()

def main():
    setLogLevel('info')
    t = SADRNTopology()
    try:
        t.create_topology()
        t.start_network()
        t.start_services()
        t.test_connectivity()
        t.run_cli()
    finally:
        t.stop_network()

if __name__ == '__main__':
    main()

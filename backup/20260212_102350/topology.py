#!/usr/bin/env python3
"""
SADRN - Software Defined Adaptive Disaster Response Network
Topology Script for Mininet

This script creates a network topology with:
- 3 Switches (s1, s2, s3) connected in a triangle/ring topology
- 3 Sensor hosts (h1, h2, h3) attached to each switch
- 1 Display Node (h_display) attached to s1 - the Command Center

Author: SADRN Team
"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import os
import sys
import time

class SADRNTopology:
    """
    SADRN Network Topology Manager
    
    Creates and manages the disaster response network topology with
    redundant paths and a centralized display node.
    """
    
    def __init__(self, controller_ip='127.0.0.1', controller_port=6653):
        self.controller_ip = controller_ip
        self.controller_port = controller_port
        self.net = None
        self.switches = {}
        self.hosts = {}
        self.display_node = None
        
    def create_topology(self):
        """Create the SADRN network topology"""
        info('*** Creating SADRN Network Topology ***\n')
        
        # Initialize Mininet with Remote Controller (Ryu)
        self.net = Mininet(
            controller=RemoteController,
            switch=OVSKernelSwitch,
            link=TCLink,
            autoSetMacs=True
        )
        
        # Add Remote Controller (Ryu)
        info('*** Adding Ryu Controller ***\n')
        c0 = self.net.addController(
            'c0',
            controller=RemoteController,
            ip=self.controller_ip,
            port=self.controller_port
        )
        
        # Create Switches (Triangle/Ring Topology)
        info('*** Creating Switches ***\n')
        self.switches['s1'] = self.net.addSwitch('s1', dpid='0000000000000001')
        self.switches['s2'] = self.net.addSwitch('s2', dpid='0000000000000002')
        self.switches['s3'] = self.net.addSwitch('s3', dpid='0000000000000003')
        
        # Create Sensor Hosts (h1, h2, h3)
        info('*** Creating Sensor Hosts ***\n')
        self.hosts['h1'] = self.net.addHost(
            'h1', 
            ip='10.0.0.1/24',
            mac='00:00:00:00:00:01'
        )
        self.hosts['h2'] = self.net.addHost(
            'h2', 
            ip='10.0.0.2/24',
            mac='00:00:00:00:00:02'
        )
        self.hosts['h3'] = self.net.addHost(
            'h3', 
            ip='10.0.0.3/24',
            mac='00:00:00:00:00:03'
        )
        
        # Create Display Node (Command Center) attached to s1
        info('*** Creating Display Node (Command Center) ***\n')
        self.display_node = self.net.addHost(
            'h_display',
            ip='10.0.0.100/24',
            mac='00:00:00:00:00:64'
        )
        self.hosts['h_display'] = self.display_node
        
        # Create Links - Triangle topology between switches
        info('*** Creating Switch Links (Triangle Topology) ***\n')
        # Switch-to-Switch links with bandwidth and delay parameters
        self.net.addLink(self.switches['s1'], self.switches['s2'], 
                        bw=100, delay='2ms', port1=1, port2=1)
        self.net.addLink(self.switches['s2'], self.switches['s3'], 
                        bw=100, delay='2ms', port1=2, port2=1)
        self.net.addLink(self.switches['s3'], self.switches['s1'], 
                        bw=100, delay='2ms', port1=2, port2=2)
        
        # Host-to-Switch links
        info('*** Creating Host Links ***\n')
        # Sensor hosts
        self.net.addLink(self.hosts['h1'], self.switches['s1'], 
                        bw=100, delay='1ms', port2=3)
        self.net.addLink(self.hosts['h2'], self.switches['s2'], 
                        bw=100, delay='1ms', port2=3)
        self.net.addLink(self.hosts['h3'], self.switches['s3'], 
                        bw=100, delay='1ms', port2=3)
        
        # Display Node attached to s1
        self.net.addLink(self.display_node, self.switches['s1'], 
                        bw=100, delay='1ms', port2=4)
        
        return self.net
    
    def start_network(self):
        """Start the network"""
        info('*** Starting Network ***\n')
        self.net.build()
        self.net.start()
        
        # Wait for controller to connect
        info('*** Waiting for Controller Connection ***\n')
        time.sleep(2)
        
        # Configure OVS to use OpenFlow 1.3
        info('*** Configuring OpenFlow 1.3 ***\n')
        for switch_name in ['s1', 's2', 's3']:
            os.system(f'ovs-vsctl set bridge {switch_name} protocols=OpenFlow13')
        
        return self.net
    
    def print_topology_info(self):
        """Print topology information"""
        info('\n*** SADRN Network Topology ***\n')
        info('=' * 50 + '\n')
        info('Switches: s1, s2, s3 (Triangle Topology)\n')
        info('Sensor Hosts:\n')
        info(f'  - h1 (10.0.0.1) -> s1 (Sensor Cluster 1)\n')
        info(f'  - h2 (10.0.0.2) -> s2 (Sensor Cluster 2)\n')
        info(f'  - h3 (10.0.0.3) -> s3 (Sensor Cluster 3)\n')
        info(f'Display Node:\n')
        info(f'  - h_display (10.0.0.100) -> s1 (Command Center)\n')
        info('=' * 50 + '\n')
        info('\nNetwork Links:\n')
        info('  s1 <---> s2 (port 1)\n')
        info('  s2 <---> s3 (port 2-1)\n')
        info('  s3 <---> s1 (port 2-2)\n')
        info('=' * 50 + '\n')
    
    def test_connectivity(self):
        """Test connectivity between all hosts"""
        info('\n*** Testing Connectivity ***\n')
        self.net.pingAll()
    
    def start_simulation_scripts(self):
        """Start the sender and receiver scripts on hosts"""
        info('\n*** Starting Simulation Scripts ***\n')
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(base_dir, 'scripts')
        
        # Start receiver on display node
        info('Starting receiver on h_display...\n')
        self.display_node.cmd(f'python3 {scripts_dir}/receiver.py &')
        
        time.sleep(1)
        
        # Start senders on sensor hosts
        for host_name in ['h1', 'h2', 'h3']:
            info(f'Starting sender on {host_name}...\n')
            self.hosts[host_name].cmd(f'python3 {scripts_dir}/sender.py {host_name} &')
    
    def stop_simulation_scripts(self):
        """Stop all simulation scripts"""
        info('\n*** Stopping Simulation Scripts ***\n')
        for host_name, host in self.hosts.items():
            host.cmd('pkill -f sender.py')
            host.cmd('pkill -f receiver.py')
    
    def run_cli(self):
        """Start Mininet CLI"""
        info('\n*** Starting Mininet CLI ***\n')
        info('Type "help" for available commands\n')
        info('Type "exit" or Ctrl+D to stop the network\n\n')
        CLI(self.net)
    
    def stop_network(self):
        """Stop the network"""
        info('\n*** Stopping Network ***\n')
        self.stop_simulation_scripts()
        if self.net:
            self.net.stop()


def main():
    """Main function to run the SADRN topology"""
    setLogLevel('info')
    
    # Parse command line arguments
    controller_ip = '127.0.0.1'
    controller_port = 6653
    
    if len(sys.argv) > 1:
        controller_ip = sys.argv[1]
    if len(sys.argv) > 2:
        controller_port = int(sys.argv[2])
    
    # Create topology
    topo = SADRNTopology(controller_ip, controller_port)
    
    try:
        # Create and start the network
        topo.create_topology()
        topo.start_network()
        topo.print_topology_info()
        
        # Test connectivity
        topo.test_connectivity()
        
        # Run CLI for interactive testing
        topo.run_cli()
        
    except KeyboardInterrupt:
        info('\n*** Interrupted by user ***\n')
    finally:
        topo.stop_network()
        info('*** Network stopped ***\n')


if __name__ == '__main__':
    main()

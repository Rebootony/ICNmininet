from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import Intf
from mininet.node import Controller
from mininet.link import TCLink
import subprocess
import sys
from os import popen
import threading
import time

class LinuxRouter( Node ):
    """Custom Linux router for Layer 3 routing if desired in the network"""
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )

        self.cmd( 'sysctl net.ipv4.ip_forward=1' )
        self.cmd( 'sysctl net.ipv4.conf.all.proxy_arp=1' )


    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        self.cmd( 'sysctl net.ipv4.conf.all.proxy_arp=0' )
        super( LinuxRouter, self ).terminate()

class POXBridge( Controller ):
    "Custom Controller class to invoke POX forwarding.l2_learning"
    def start( self ):
        "Start POX learning switch"
        self.pox = '%s/pox/pox.py' % os.environ[ 'HOME' ]
        self.cmd( self.pox, 'forwarding.l2_learning &' )
    def stop( self ):
        "Stop POX"
        self.cmd( 'kill %' + self.pox )

controllers = { 'poxbridge': POXBridge }

def runNetwork():
    """
        author: Brian Lebiednik

        This is a bare bones Dcell topology where the routers are switches which
        removes routing from the equation as the switches can choose any path
        to transmit data
    """
    net = Mininet(topo=None, build=False,
                controller=POXBridge, link=TCLink)

    """Make and connect 5 DCells to compare topologies"""
    start = 0
    num_cells = 5
    top_level_switches = 4
    bottom_level_servers = 1
    switch_type = 'ovsk'
    # topology will have four routers(switches) at the top of each cell
    # and then one multi-honed server(host)

    switches = {}
    info('*** Adding Cells one at a time                             ***\n')
    for x in range(0, num_cells):
        switches[x] = net.addSwitch('server' + str(x), switch = switch_type)
        for i in range(0, top_level_switches):
            name = 'sw' + str(x) +'_' + str(i)
            switches[name] = net.addSwitch(name, switch=switch_type)
            net.addLink(switches[x], switches[name], bw=100)
    """Adding all of the top level switches and the server
    They are connected by 100 Mbps links"""

    info('*** Adding links to construct topology                ***\n')
    info('---------------------------------------------------------\n')
    info('*********************************************************\n')
    info('*     sw0_0       sw0_1       sw0_2      sw0_3->server0 *\n')
    info('*                                                       *\n')
    info('*     sw1_0       sw1_1       sw1_2      sw1_3->server1 *\n')
    info('*                                                       *\n')
    info('*     sw2_0       sw2_1       sw2_2      sw2_3->server2 *\n')
    info('*                                                       *\n')
    info('*     sw3_0       sw3_1       sw3_2      sw3_3->server3 *\n')
    info('*                                                       *\n')
    info('*     sw4_0       sw4_1       sw4_2      sw4_3->server4 *\n')
    info('*                                                       *\n')
    info('*********************************************************\n')
    floor = 0
    for x in range(0, num_cells):
        #the D Cell that we want to assign from
        for i in range(floor, top_level_switches):
            name1 = 'sw' + str(x) +'_' + str(i)
            name2 = 'sw' + str(i+1) +'_' + str(x)
            net.addLink(switches[name1], switches[name2], bw =1000)
        floor = floor +1
            #We will connect 0_0 to 1_0, 0_1 to 2_0, etc until 3_3 connects to 4_3


    net.build()



    CLI(net)
    net.stop()
    subprocess.call(['mn', '-c'])


if __name__ == '__main__':
        setLogLevel('info')
        runNetwork()

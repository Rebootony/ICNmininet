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

        This is a bare bones Facebook topology where the routers are switches which
        removes routing from the equation as the switches can choose any path
        to transmit data
    """
    net = Mininet(topo=None, build=False,
                controller=POXBridge, link=TCLink)

    """The baseline facebook topology has 4 core routers and 38 edge
    routers that make up a pod"""
    core_routers = 4
    edge_routers = 48
    #edge routers are also known as Top of the Rack (TOR) Routers
    switch_type = 'ovsk'

    switches = {}
    info('*** Adding the core routers                             ***\n')
    for x in range(0, core_routers):
        switches[x] = net.addSwitch('cr' + str(x), switch = switch_type)
    for x in range(0, edge_routers):
        switches[x+core_routers] = net.addSwitch('er' + str(x), switch = switch_type)

    info('*** Adding links to construct topology                ***\n')
    info('---------------------------------------------------------\n')
    info('*********************************************************\n')
    info('*     cr1        cr2           cr3           cr4        *\n')
    info('*                                                       *\n')
    info('*                                                       *\n')
    info('*                                                       *\n')
    info('*                                                       *\n')
    info('* er1  er2  er3  er4  er5  er6  er7  er8  er9 ...  er48 *\n')
    info('*                                                       *\n')
    info('*********************************************************\n')

    for x in range(0, core_routers):
        #the core router that we want to connect
        for i in range(0, edge_routers):
            #the TOR router that we want to connect the core to

            net.addLink(switches[x], switches[i+core_routers], bw =1000)

    net.build()



    CLI(net)
    net.stop()
    subprocess.call(['mn', '-c'])


if __name__ == '__main__':
        setLogLevel('info')
        runNetwork()

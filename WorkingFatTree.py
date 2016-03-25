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

class LinuxRouter( Node ):
    """Custom Linux router for Layer 3 routing if desired in the network"""
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()

def runNetwork():
    """
        Author: Brian Lebiednik

        This is a bare bones fat tree where all of the routers are simply switches
        By using only switches we remove routing from the equation as the switches
        can choose any path to transmit data
    """
    net = Mininet(topo=None, build=False,
                controller=POXBridge, link=TCLink)

    core = 4
    switch_type = 'ovsk'

    info('*** Adding Core routers                              ***\n')
    info('----------------------\n')
    corerouters = {}
    for x in range(0, core):
        corerouters[x] = net.addSwitch('cr'+str(x) , switch=switch_type)


    info('*** Adding aggregate router                       ***\n')
    aggrouters = {}
    for x in range(0,(core * 2)):
        aggrouters[x] = net.addSwitch('ar'+str(x) , switch=switch_type )

    info('*** Adding edge routers                          ***\n' )
    edgerouters = {}
    for x in range(0, (core *2)):
        edgerouters[x] = net.addSwitch('er'+str(x) , switch=switch_type )



    info('*** Adding links to construct topology ***\n')
    info('------------------------------------------\n')
    info('*********************************************************\n')
    info('*     cr0          cr1          cr2          cr3        *\n')
    info('*                                                       *\n')
    info('*  ar0    ar1    ar2    ar3    ar4    ar5    ar6    ar7 *\n')
    info('*                                                       *\n')
    info('*  er0    er1    er2    er3    er4    er5    er6    er7 *\n')
    info('*                                                       *\n')
    info('*********************************************************\n')

    info('*** Adding links to core routers                      ***\n')
    for x in range(0,core*2, 2):
        net.addLink(corerouters[0], aggrouters[x], bw=1000)
        net.addLink(corerouters[1], aggrouters[x], bw=1000)
        #connections between the first two core routers and the even
        #aggregate routers
        #bandwidth set to 1 Gbps
    for x in range(1, core*2, 2):
        net.addLink(corerouters[2], aggrouters[x], bw=1000)
        net.addLink(corerouters[3], aggrouters[x], bw=1000)
        #connections between the second two core routers and the odd
        #aggregate routers
        #bandwidth set to 1 Gbps
    info('*** Adding links to aggregate routers                 ***\n')
    for x in range(0, (core*2), 2):
        net.addLink(aggrouters[x], edgerouters[x], bw=100)
        net.addLink(aggrouters[x], edgerouters[x+1], bw=100)

    for x in range(1, (core*2), 2):
        net.addLink(aggrouters[x], edgerouters[x], bw=100)
        net.addLink(aggrouters[x], edgerouters[x-1], bw=100)
        #Creates a Mesh between the aggregate routers and edgerouters
        # in each pod
        #bandwidth set to 100 Mbps

    net.build()


    #net.pingAll()
    CLI(net)
    net.stop()
    subprocess.call(['mn', '-c'])


if __name__ == '__main__':
    setLogLevel('info')
    runNetwork()

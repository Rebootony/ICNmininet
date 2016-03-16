from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink
import subprocess
import sys
import time
import os
import base64


class LinuxRouter( Node ):
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )

        self.cmd( 'sysctl net.ipv4.ip_forward=1' )
        self.cmd( 'sysctl net.ipv4.conf.all.proxy_arp=1' )


    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        self.cmd( 'sysctl net.ipv4.conf.all.proxy_arp=0' )
        super( LinuxRouter, self ).terminate()


def runNetwork():
    """
        author: Brian Lebiednik
    """
    net = Mininet(topo=None)
    core = 4

    info('*** Adding Core routers ***\n')
    info('----------------------\n')
    corerouters = {}
    for x in range(1, core+1):
        corerouters[x] = net.addHost('cr'+str(x), cls=LinuxRouter)
    info('adding aggregate routers\n')
    aggrouters = {}
    for x in range(1,(core * 2) +1):
        aggrouters[x] = net.addHost('ar'+str(x), cls=LinuxRouter)

    info('adding edge routers\n')
    edgerouters = {}
    for x in range(1, (core *2)+1):
        edgerouters[x] = net.addHost('er'+str(x), cls=LinuxRouter)
    info('*** Adding links to construct topology ***\n')
    info('------------------------------------------\n')
    info('*********************************************************\n')
    info('*     cr1          cr2          cr3          cr4        *\n')
    info('*                                                       *\n')
    info('*  ar1    ar2    ar3    ar4    ar5    ar6    ar7    ar8 *\n')
    info('*                                                       *\n')
    info('*  er1    er2    er3    er4    er5    er6    er7    er8 *\n')
    info('*                                                       *\n')
    info('*********************************************************\n')

    info('adding links to core routers\n')
    for x in range(1,core*2, 2):
        net.addLink(corerouters[1], aggrouters[x])
        net.addLink(corerouters[2], aggrouters[x])
    for x in range(2, core*2, 2):
        net.addLink(corerouters[3], aggrouters[x])
        net.addLink(corerouters[4], aggrouters[x])
    info('adding links to aggregate routers\n')
    for x in range(1, (core*2)+1, 2):
        net.addLink(aggrouters[x], edgerouters[x])
        net.addLink(aggrouters[x], edgerouters[x+1])
    for x in range(2, (core*2)+1, 2):
        net.addLink(aggrouters[x], edgerouters[x])
        net.addLink(aggrouters[x], edgerouters[x-1])


    net.build()

    net.pingAll()

    CLI(net)
    net.stop()
    subprocess.call(['mn', '-c'])


if __name__ == '__main__':
    setLogLevel('info')
    runNetwork()

#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.node import Controller
from mininet.cli import CLI
import os
import time
import thread

"""
Author: Brian Lebiednik

Requires a custom controller with the command as follows on xterm1
./pox.py forwarding.l2_pairs openflow.discovery misc.full_payload openflow.spanning_tree


Usage
sudo python performancetest.py

Currently you can change the following line to change the topology that the program runs

topo = {}(n=4) {FatTreeTopotest, FatTreeTopo, Dcell}


"""

def iperf_thread(net, src, dst):
    host_pair = [src, dst]
    bandwidth = net.iperf(host_pair, seconds = 5)

class Facebook(Topo):
    "Creates a Facebook database configuration 5 interconnected cells"
    def build(self, n=2):
        """The baseline facebook topology has 4 core routers and 38 edge
        routers that make up a pod"""
        core_routers = 4
        edge_routers = 48
        link_bandwidth = 10
        link_delay = '.001ms'
        #edge routers are also known as Top of the Rack (TOR) Routers
        switch_type = 'ovsk'

        switches = {}
        info('*** Adding the core routers                             ***\n')
        for x in range(0, core_routers):
            switches[x] = self.addSwitch('cr' + str(x), switch = switch_type)
        for x in range(0, edge_routers):
            switches[x+core_routers] = self.addSwitch('er' + str(x), switch = switch_type)
            hosts[x] =self.addHost('h'+str(x))
            self.addLink(hosts[x], switches[x+core_routers], bw =link_bandwidth, delay=link_delay)

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

                self.addLink(switches[x], switches[i+core_routers], bw =link_bandwidth, delay=link_delay)

class Dcell(Topo):
    "Creates a Dcell database configuration 5 interconnected cells"
    def build(self, n=2):
        start = 0
        num_cells = 5
        top_level_switches = 4
        bottom_level_servers = 1
        switch_type = 'ovsk'
        link_bandwidth = 10
        link_delay = '.001ms'
        # topology will have four routers(switches) at the top of each cell
        # and then one multi-honed server(host)

        switches = {}
        hosts = {}
        info('*** Adding Cells one at a time                             ***\n')
        for x in range(0, num_cells):
            switches[x] = self.addSwitch('server' + str(x), switch = switch_type)
            host[x] = self.addHost('h'+str(x))
            for i in range(0, top_level_switches):
                name = 'sw' + str(x) +'_' + str(i)
                switches[name] = self.addSwitch(name, switch=switch_type)
                self.addLink(switches[x], switches[name], bw=link_bandwidth, delay=link_delay)
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
                self.addLink(switches[name1], switches[name2], bw =link_bandwidth, delay=link_delay)
            floor = floor +1


class FatTreeTopotest(Topo):
    "Topology testings for FatTree. Creates a 8 host, 8 'aggregate', 2 core configuration"
    def build(self, n=2):
        core =4
        link_delay = '1ms'
        corerouters = {}
        hosts = {}
        aggrouters ={}
        switch_type = 'ovsbk'
        for x in range(0, 2):
            corerouters[x] = self.addSwitch('cr'+str(x), switch = switch_type )
        for x in range(0, core*2):
            aggrouters[x] = self.addSwitch('ar'+str(x), switch = switch_type )
            hosts[x] =self.addHost('h'+str(x))
            self.addLink(aggrouters[x], hosts[x])
        self.addLink(aggrouters[0], corerouters[0], bw=10, delay=link_delay)
        self.addLink(aggrouters[1], corerouters[0], bw=10, delay=link_delay)
        self.addLink(aggrouters[2], corerouters[0], bw=10, delay=link_delay)
        self.addLink(aggrouters[3], corerouters[0], bw=10, delay=link_delay)
        self.addLink(aggrouters[4], corerouters[1], bw=10, delay=link_delay)
        self.addLink(aggrouters[5], corerouters[1], bw=10, delay=link_delay)
        self.addLink(aggrouters[6], corerouters[1], bw=10, delay=link_delay)
        self.addLink(aggrouters[7], corerouters[1], bw=10, delay=link_delay)


        #self.addLink(corerouters[1], corerouters[2], bw=10, delay=link_delay)
        #self.addLink(corerouters[2], corerouters[3], bw=10, delay=link_delay)
        self.addLink(corerouters[0], corerouters[1], bw=10, delay=link_delay)
        #self.addLink(corerouters[3], aggrouters[0], bw=10, delay=link_delay)

class FatTreeTopo(Topo):
    "Creates a Fat Tree Topology with 2 core routers, 8 aggregate, 8 edge, and 8 hosts"
    def build(self, n=2):
        core = 4
        switch_type = 'ovsbk'
        link_bandwidth = 10
        link_delay = '.001ms'
        corerouters = {}
        aggrouters = {}
        edgerouters = {}
        host = {}

        for x in range(0, 2):
            corerouters[x] = self.addSwitch('cr'+str(x), switch = switch_type, stp=1)

        for x in range(0,(core * 2)):
            aggrouters[x] = self.addSwitch('ar'+str(x), switch = switch_type, stp=1 )

        for x in range(0, (core *2)):
            edgerouters[x] = self.addSwitch('er'+str(x), switch = switch_type, stp=1 )

        for x in range(0, (core *2)):
            host[x] = self.addHost('h'+str(x))
        for x in range(0,core*2, 2):
            self.addLink(corerouters[0], aggrouters[x], bw=link_bandwidth, delay=link_delay)
            #self.addLink(corerouters[1], aggrouters[x], bw=10, delay=link_delay)
        for x in range(1, core*2, 2):
            self.addLink(corerouters[1], aggrouters[x], bw=link_bandwidth, delay=link_delay)
            #self.addLink(corerouters[3], aggrouters[x], bw=10, delay=link_delay)

        for x in range(0, (core*2), 2):
            self.addLink(aggrouters[x], edgerouters[x], bw=link_bandwidth, delay=link_delay)
            #self.addLink(aggrouters[x], edgerouters[x+1], bw=10, delay=link_delay)
        for x in range(1, (core*2), 2):
            self.addLink(aggrouters[x], edgerouters[x], bw=link_bandwidth, delay=link_delay)
            #self.addLink(aggrouters[x], edgerouters[x-1], bw=10, delay=link_delay)
        for x in range(0, core*2):
            self.addLink(host[x], edgerouters[x],
               bw=10, delay=link_delay)
        self.addLink(corerouters[0], corerouters[1], bw =link_bandwidth*4, delay=link_delay)
        #self.addLink(corerouters[2], corerouters[3], bw =40, delay=link_delay)

def perfTest():
    "Create network and run simple performance test"
    topo = FatTreeTopo(n=4)
    net = Mininet(topo=topo, controller=RemoteController,
                   link=TCLink, ipBase='192.168.0.0/24')

    net.start()

    dumpNodeConnections(net.hosts)
    net.waitConnected()

    print "Waiting for network to converge"

    time.sleep(5)
    for i in range(0,3):
        net.pingAll()

    """host = {}
    for x in range(0, 8):
        host_name = 'h' +str(x)
        host[x] = net.get(host_name)
    for x in range(0, 4):
        src = host[x]
        dst = host[7-x]

        net.iperf((src, dst), seconds = 5)
    #net.iperf([host[1], host[6]], seconds = 5)
    """
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    perfTest()

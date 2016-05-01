
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
from time import time, sleep
from select import poll, POLLIN
from subprocess import Popen, PIPE

"""
Author: Brian Lebiednik
This is a subset of the project specfically to scale the number of hosts in each topology


Requires a custom controller with the command as follows on xterm1
./pox.py forwarding.l2_pairs openflow.discovery misc.full_payload openflow.of_01 --port=6653


Usage
sudo python performancetest.py

Currently you can change the following line to change the topology that the program runs

topo = {}(n=4)
{DcellNoLoop, FacebookNoLoop, FatTreeTopoNoLoop}

To kill a mininet process running in the background issue a 'sudo mn -c'


"""

def iperf_thread(net, src, dst):
    host_pair = [src, dst]
    bandwidth = net.iperf(host_pair, seconds = 5)

def monitorFiles( outfiles, seconds, timeoutms ):
    "Monitor set of files and return [(host, line)...]"
    devnull = open( '/dev/null', 'w' )
    tails, fdToFile, fdToHost = {}, {}, {}
    for h, outfile in outfiles.iteritems():
        tail = Popen( [ 'tail', '-f', outfile ],
                      stdout=PIPE, stderr=devnull )
        fd = tail.stdout.fileno()
        tails[ h ] = tail
        fdToFile[ fd ] = tail.stdout
        fdToHost[ fd ] = h
    # Prepare to poll output files
    readable = poll()
    for t in tails.values():
        readable.register( t.stdout.fileno(), POLLIN )
    # Run until a set number of seconds have elapsed
    endTime = time() + seconds
    while time() < endTime:
        fdlist = readable.poll(timeoutms)
        if fdlist:
            for fd, _flags in fdlist:
                f = fdToFile[ fd ]
                host = fdToHost[ fd ]
                # Wait for a line of output
                line = f.readline().strip()
                yield host, line
        else:
            # If we timed out, return nothing
            yield None, ''
    for t in tails.values():
        t.terminate()
    devnull.close()  # Not really necessary

class FacebookNoLoop(Topo):
    "Creates a Facebook database configuration 5 interconnected cells"
    def build(self, n=2):
        """The baseline facebook topology has 4 core routers and 38 edge
        routers that make up a pod"""
        core_routers = 4
        edge_routers = 48
        link_bandwidth = 10
        link_delay = '.001ms'
        double_link_delay = '.002ms'
        #edge routers are also known as Top of the Rack (TOR) Routers
        switch_type = 'ovsk'
        hosts_per_node = 2

        switches = {}
        hosts = {}
        print '*** Adding the core routers                             ***\n'
        for x in range(0, 1):
            switches[x] = self.addSwitch('cr' + str(x), switch = switch_type)
        for x in range(0, edge_routers):
            switches[x+core_routers] = self.addSwitch('er' + str(x), switch = switch_type)
            for y in range(0, hosts_per_node):
                hosts[(x*hosts_per_node)+y] =self.addHost('h'+str((x*hosts_per_node)+y))
                self.addLink(hosts[(x*hosts_per_node)+y], switches[x+core_routers], bw =link_bandwidth, delay=link_delay)
        """
        *** Adding links to construct topology                ***

        *********************************************************
        *     cr1        cr2           cr3           cr4        *
        *                                                       *
        *                                                       *
        *                                                       *
        *                                                       *
        * er1  er2  er3  er4  er5  er6  er7  er8  er9 ...  er48 *
        *                                                       *
        *********************************************************
        """
        for x in range(0, 1):
            #the core router that we want to connect
            for i in range(0, edge_routers):
                #the TOR router that we want to connect the core to

                self.addLink(switches[x], switches[i+core_routers], bw =link_bandwidth*4, delay=double_link_delay)

class DcellNoLoop(Topo):
    "Creates a Dcell database configuration 5 interconnected cells"
    def build(self, n=2):
        start = 0
        num_cells = 5
        top_level_switches = 1
        bottom_level_servers = 1
        switch_type = 'ovsk'
        link_bandwidth = 10
        link_delay = '.001ms'
        half_link_delay = '.0005ms'
        total_hosts = 50
        # topology will have four routers(switches) at the top of each cell
        # and then one multi-honed server(host)

        switches = {}
        hosts = {}
        cr = 'cr0'
        switches[cr] = self.addSwitch(cr, switch=switch_type)
        print '*** Adding Cells one at a time                             ***\n'
        j=0
        for x in range(0, num_cells):
            switches[x] = self.addSwitch('er' + str(x), switch = switch_type)
            for y in range(0, (total_hosts/num_cells)):
                hosts[j] = self.addHost('h'+str(j))
                self.addLink(switches[x], hosts[j], bw=link_bandwidth, delay=link_delay)
                j = j +1
            for i in range(0, top_level_switches):
                name = 'sw' + str(x) +'_' + str(i)
                switches[name] = self.addSwitch(name, switch=switch_type)
                self.addLink(switches[x], switches[name], bw=link_bandwidth*4, delay=link_delay)
                self.addLink(switches[name], switches[cr], bw=link_bandwidth*4, delay=half_link_delay)

        """
        *** Adding links to construct topology                ***

        *********************************************************
        *     sw0_0       sw0_1       sw0_2      sw0_3->edgeSwitch *
        *                                                          *
        *     sw1_0       sw1_1       sw1_2      sw1_3->edgeSwitch *
        *                                                          *
        *     sw2_0       sw2_1       sw2_2      sw2_3->edgeSwitch *
        *                                                          *
        *     sw3_0       sw3_1       sw3_2      sw3_3->edgeSwitch *
        *                                                          *
        *     sw4_0       sw4_1       sw4_2      sw4_3->edgeSwitch *
        *                                                          *
        '*********************************************************

        floor = 0
        for x in range(0, num_cells):
            #the D Cell that we want to assign from
            for i in range(floor, top_level_switches):
                name1 = 'sw' + str(x) +'_' + str(i)
                name2 = 'sw' + str(i+1) +'_' + str(x)
                self.addLink(switches[name1], switches[cr], bw =link_bandwidth, delay=half_link_delay)
                self.addLink(switches[name2], switches[cr], bw =link_bandwidth, delay=half_link_delay)
            floor = floor +1
        """


class FatTreeTopoNoLoop(Topo):
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
        hosts_per_node = 64

        for x in range(0, 2): # Core Switches
            corerouters[x] = self.addSwitch('cr'+str(x), switch = switch_type, stp=1)

        for x in range(0,(core * 2)): # Aggregate Switches
            aggrouters[x] = self.addSwitch('ar'+str(x), switch = switch_type, stp=1 )

        for x in range(0, (core *2)): # Edges Switches
            edgerouters[x] = self.addSwitch('er'+str(x), switch = switch_type, stp=1 )

        for x in range(0, (core*2*hosts_per_node)):
            host[x] = self.addHost('h'+str(x))

        #Connecting the Core to the Aggregate
        for x in range(0,core*2, 2):
            self.addLink(corerouters[0], aggrouters[x], bw=link_bandwidth, delay=link_delay)

        for x in range(1, core*2, 2):
            self.addLink(corerouters[1], aggrouters[x], bw=link_bandwidth, delay=link_delay)

        #Connecting the Edge to the Aggregate
        for x in range(0, (core*2), 2):
            self.addLink(aggrouters[x], edgerouters[x], bw=link_bandwidth, delay=link_delay)

        for x in range(1, (core*2), 2):
            self.addLink(aggrouters[x], edgerouters[x], bw=link_bandwidth, delay=link_delay)

        #Connecting the host to the Edge
        for x in range(0, core*2):
            for y in range(0, hosts_per_node):
                self.addLink(host[(x*hosts_per_node)+y], edgerouters[x],
                   bw=10, delay=link_delay)
        # Create one link to prevent loops
        self.addLink(corerouters[0], corerouters[1], bw =link_bandwidth*4)

def perfTest():
    "Create network and run simple performance test"
    """available tests include FatTreeTopoNoLoop, DcellNoLoop, FacebookNoLoop"""
    topo = FatTreeTopoNoLoop(n=4)
    test = 'FatTreeTopoNoLoop'
    run_test = 2 #Set to 1 for IPERF test or 2 for Ping Test
    packetsize = 1472
    #max packet size 1472 since MTU is 1500
    net = Mininet(topo=topo, controller=RemoteController, link=TCLink, ipBase='192.168.0.0/16')

    net.start()
    seconds = 10
    #dumpNodeConnections(net.hosts) #Dumps the connections from each host
    net.waitConnected()


    print "Waiting for network to converge"
    net.pingAll()
    host = {}

    print "Starting tests"
    if (test == 'FatTreeTopoNoLoop'):
        max_host = 512
        for y in range(0, max_host):
            host_name = 'h' +str(y)
            host[y] = net.get(host_name)

    elif (test == 'FacebookNoLoop'):
        print "*** Running Facebook tests ***"
        max_host = 48
        for x in range(0, max_host):
            host_name = 'h' +str(x)
            host[x] = net.get(host_name)

    elif (test =='DcellNoLoop'):
        print "***Running DCellNoLoop tests"
        max_host = 50
        for x in range(0, max_host):
            host_name = 'h' +str(x)
            print "Adding %s" % host_name
            host[x] = net.get(host_name)

    if (run_test == 1):
        print "IPERF Testing"
        sleep(5)


    elif (run_test ==2 and test =='DcellNoLoop'):

        print "Ping Testing"
        outfiles, errfiles = {}, {}
        bottom = 0
        for h in range(0, max_host):
            # Create and/or erase output files
            outfiles[ host[h] ] = '/tmp/%s.out' % host[h].name
            errfiles[ host[h] ] = '/tmp/%s.err' % host[h].name
            host[h].cmd( 'echo >', outfiles[ host[h] ] )
            host[h].cmd( 'echo >', errfiles[ host[h] ] )
            # Start pings

            if (h<max_host-1):
                host[h].cmdPrint('ping', host[h+1].IP(), '-s', packetsize,
                        '>', outfiles[ host[h] ],
                        '2>', errfiles[ host[h] ],
                        '&' )
            else:
                host[h].cmdPrint('ping', host[0].IP(), '-s', packetsize,
                        '>', outfiles[ host[h] ],
                        '2>', errfiles[ host[h] ],
                        '&' )


        print "Monitoring output for", seconds, "seconds"
        f = open('output%s.txt' % str(packetsize), 'w')
        for host[h], line in monitorFiles( outfiles, seconds, timeoutms=500 ):
            if host[h]:
                f.write(line)



        #Still working on killing ping. Run as last test.
        #for h in range(0, max_host):
            #host[h].cmd( 'kill %ping')


        sleep(11)
    elif (run_test ==2 and test !='DcellNoLoop'):
        print "Ping Testing"
        outfiles, errfiles = {}, {}
        for h in range(0, max_host):
            # Create and/or erase output files
            outfiles[ host[h] ] = '/tmp/%s.out' % host[h].name
            errfiles[ host[h] ] = '/tmp/%s.err' % host[h].name
            host[h].cmd( 'echo >', outfiles[ host[h] ] )
            host[h].cmd( 'echo >', errfiles[ host[h] ] )
            # Start pings

            if (h<max_host-1):
                host[h].cmdPrint('ping', host[h+1].IP(), '-s', packetsize,
                        '>', outfiles[ host[h] ],
                        '2>', errfiles[ host[h] ],
                        '&' )
            else:
                host[h].cmdPrint('ping', host[0].IP(), '-s', packetsize,
                        '>', outfiles[ host[h] ],
                        '2>', errfiles[ host[h] ],
                        '&' )


        print "Monitoring output for", seconds, "seconds"
        f = open('output%s.txt' % str(packetsize), 'w')
        for host[h], line in monitorFiles( outfiles, seconds, timeoutms=500 ):
            if host[h]:
                f.write(line)



        #Still working on killing ping. Run as last test.
        #for h in range(0, max_host):
            #host[h].cmd( 'kill %ping')


        sleep(11)
    print "Ending tests"
    net.stop()
    #CLI( net )


if __name__ == '__main__':
    setLogLevel('info')
    perfTest()

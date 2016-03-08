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
        ip = '192.168.{}.2'.format(params['nodeID'])
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )
        self.cmd( 'sysctl net.ipv4.conf.all.proxy_arp=1' )
        self.cmd( 'iptables -t nat -A POSTROUTING -j SNAT --to-source {}'.format(ip) )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        self.cmd( 'sysctl net.ipv4.conf.all.proxy_arp=0' )
        super( LinuxRouter, self ).terminate()


def runNetwork():
    """
        author: kmiller95
    """
    net = Mininet(topo=None, build=False, ipBase='192.168.0.0/24')

    info('*** Adding Dijkstra Central Command ***\n')
    info('---------------------------------------\n')
    d0 = net.addHost('d0', cls=LinuxRouter, inNamespace=False, ip='192.168.0.1/30', nodeID=0)
    s0 = net.addSwitch('s0')
    net.addLink(d0, s0)

    info('*** Adding routers ***\n')
    info('----------------------\n')
    routers = {}
    for x in range(1, 9):
        routers[x] = net.addHost('r'+str(x), cls=LinuxRouter, ip='192.168.{}.2/30'.format(x), nodeID=x)


    info('*** Linking routers to DCC ***\n')
    info('------------------------------\n')
    for i, r in routers.iteritems():
        net.addLink(d0, r,
                intfName1='d0-eth{}'.format(i),
                intfName2='r{}-eth0'.format(i),
                params1={'ip': '192.168.{}.1/30'.format(i)},
                params2={'ip': '192.168.{}.2/30'.format(i)})
        r.cmd('ip route add 192.168.0.0/30 proto kernel via 192.168.{}.1'.format(i))


    info('*** Adding links to construct topology ***\n')
    info('------------------------------------------\n')
    info('*********************************************************\n')
    info('*          ---------------------------------            *\n')
    info('*          |                                |           *\n')
    info('*   ------ r1 -----       (d0)       ------ r2 -----    *\n')
    info('*  |       |       |                |       |       |   *\n')
    info('*  |       |       |                |       |       |   *\n')
    info('*  r3 ---- r4 ---- r5 ------------- r6 ---- r7 ---- r8  *\n')
    info('*********************************************************\n')

    links = dict()
    links['r1-r2'] = net.addLink(routers[1], routers[2], intfName1='r1-eth2', intfName2='r2-eth1', cls=TCLink)
    links['r1-r3'] = net.addLink(routers[1], routers[3], intfName1='r1-eth3', intfName2='r3-eth1', cls=TCLink)
    links['r1-r4'] = net.addLink(routers[1], routers[4], intfName1='r1-eth4', intfName2='r4-eth1', cls=TCLink)
    links['r1-r5'] = net.addLink(routers[1], routers[5], intfName1='r1-eth5', intfName2='r5-eth1', cls=TCLink)

    links['r2-r6'] = net.addLink(routers[2], routers[6], intfName1='r2-eth6', intfName2='r6-eth2', cls=TCLink)
    links['r2-r7'] = net.addLink(routers[2], routers[7], intfName1='r2-eth7', intfName2='r7-eth2', cls=TCLink)
    links['r2-r8'] = net.addLink(routers[2], routers[8], intfName1='r2-eth8', intfName2='r8-eth2', cls=TCLink)


    links['r3-r4'] = net.addLink(routers[3], routers[4], intfName1='r3-eth4', intfName2='r4-eth3', cls=TCLink)
    links['r4-r5'] = net.addLink(routers[4], routers[5], intfName1='r4-eth5', intfName2='r5-eth4', cls=TCLink)
    links['r5-r6'] = net.addLink(routers[5], routers[6], intfName1='r5-eth6', intfName2='r6-eth5', cls=TCLink)
    links['r6-r7'] = net.addLink(routers[6], routers[7], intfName1='r6-eth7', intfName2='r7-eth6', cls=TCLink)
    links['r7-r8'] = net.addLink(routers[7], routers[8], intfName1='r7-eth8', intfName2='r8-eth7', cls=TCLink)

    net.build()

    info('*** Configuring base routes. ***\n')
    info('    - Initial hierarchical routes are established.\n')
    info('      ex. r3 must go through r1 to reach r4, even though\n')
    info('      they are peered directly. DCC will detect and correct this.\n')
    info('--------------------------------\n')

    # --------------------------------------------------------------------- #
    #   These routes are only for testing purposes, so the topology         #
    #   works "out of the box". Configuring routes is the responsibility    #
    #   of the DCC master.                                                  #
    # --------------------------------------------------------------------- #

    # The top two routers, r1 and r2, know how to route to the nodes under them
    routers[1].cmd('ip route add default table default proto static dev r1-eth2')
    routers[1].cmd('ip route add 192.168.3.0/30 table default proto static dev r1-eth3')
    routers[1].cmd('ip route add 192.168.4.0/30 table default proto static dev r1-eth4')
    routers[1].cmd('ip route add 192.168.5.0/30 table default proto static dev r1-eth5')

    routers[2].cmd('ip route add default table default proto static dev r2-eth1')
    routers[2].cmd('ip route add 192.168.6.0/30 table default proto static dev r2-eth6')
    routers[2].cmd('ip route add 192.168.7.0/30 table default proto static dev r2-eth7')
    routers[2].cmd('ip route add 192.168.8.0/30 table default proto static dev r2-eth8')

    # The lower tier routers route up and back down for peers. DCC corrects this.
    routers[3].cmd('ip route add default table default proto static dev r3-eth1')
    routers[4].cmd('ip route add default table default proto static dev r4-eth1')
    routers[5].cmd('ip route add default table default proto static dev r5-eth1')
    routers[6].cmd('ip route add default table default proto static dev r6-eth2')
    routers[7].cmd('ip route add default table default proto static dev r7-eth2')
    routers[8].cmd('ip route add default table default proto static dev r8-eth2')

    info('*** Building ARP cache with all-pairs ping.\n')
    info('-------------------------------------------\n')
    net.pingAll()

    info('*** Showing specific hops with traceroute.\n')
    info('************* Trace for Router r5 to r6 *************\n')
    routers[5].cmdPrint('traceroute -N 1 -q 1 -n {}'.format(routers[6].IP()))
    info('-----------------------------------------------------\n')
    info('-----------------------------------------------------\n')

    info('*** Starting DCC routines.\n')
    info('--------------------------\n')
    key = base64.b64encode(os.urandom(32))
    info('Using key:  '+ str(key) + '\n')
    d0.cmd('python $PWD/dcc/dcc.py master 0 192.168.0.1 5557 "'+key+'" "192.168.{}.0/30" &')
    for i, r in routers.iteritems():
        r.cmd('python $PWD/dcc/dcc.py slave {} 192.168.0.1 5557 "{}" &'.format(i, key))

    info('*** Sleeping while DCC reconfigures the routers...\n')
    info('--------------------------------------------------\n')
    time.sleep(5)
    info('*** Routes reconfigured.\n')
    info('------------------------\n')
    info('*** Showing NEW specific paths with traceroute.\n')
    info('************* Trace for Router r5 to r6 *************\n')
    routers[5].cmdPrint('traceroute -N 1 -q 1 -n {}'.format(routers[6].IP()))
    info('-----------------------------------------------------\n')

    #info('*** Cripple r1-r2 link: Traffic will reroute to r5-r6. ***\n')
    #links['r1-r2'].intf1.config(delay='500ms')
    ##  tc qdisc del dev rx-ethy root netem delay 900ms
    #info('-----------------------------------------------------\n')
    #info('*** Waiting for DCC to reconfigure... ***\n')
    #info('-----------------------------------------\n')
    #for _ in range(0, 5):
    #    routers[3].cmdPrint('traceroute -N 1 -q 1 -n {}'.format(routers[8].IP()))
    #    time.sleep(1)
    #info('---------------------------------------------------------------\n')
    info('*** Break the r5-r6 link. Traffic goes back around through r1-r2\n')
    links['r5-r6'].intf1.ifconfig('down')
    info('*** Waiting for DCC to reconfigure... ***\n')
    info('-----------------------------------------\n')
    for _ in range(0, 5):
        routers[5].cmdPrint('traceroute -N 1 -q 1 -n {}'.format(routers[6].IP()))
        time.sleep(1)

    CLI(net)
    net.stop()
    subprocess.call(['mn', '-c'])


if __name__ == '__main__':
    setLogLevel('info')
    runNetwork()

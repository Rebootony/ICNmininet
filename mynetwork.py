"""
Project Topology

Author Brian Lebiednik

CS8803 Spring 2016

usage: sudo mn --custom mynetwork.py --topo mytopo
      r0---------------------------r1
 ______|_________          ________|_____
 |     |    |   |          |    |   |    |
 r2   r3   r4  r5          r6   r7  r8  r9
"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Topology"

    def __init__( self ):
        "Creating 9 routers total"

        # Initialize topology
        Topo.__init__( self )

        # Add routers
        # Core_routers
        r0 = self.addSwitch( 'r0' )
        r1 = self.addSwitch( 'r1' )


        # Distribution Routers
        r2 = self.addSwitch( 'r2' )
        r3 = self.addSwitch( 'r3' )
        r4 = self.addSwitch( 'r4' )
        r5 = self.addSwitch( 'r5' )
        r6 = self.addSwitch( 'r6' )
        r7 = self.addSwitch( 'r7' )
        r8 = self.addSwitch( 'r8' )
        r9 = self.addSwitch( 'r9' )

        # Add links
        self.addLink( r0, r1 )
        #self.addLink( r0, r1, bw=1000)
        #node_a node_b bw in Mbps, delay '100us', loss %

        # Left half
        self.addLink( r0, r2 )  #
        self.addLink( r0, r3 )  #
        self.addLink( r0, r4 )  #
        self.addLink( r0, r5 )  #
        # Right Half

        self.addLink( r1, r6 )  #
        self.addLink( r1, r7 )  #
        self.addLink( r1, r8 )
        self.addLink( r1, r9 )

        #r1.cmd(bool; operation; operation; done > /tmp/...out)



topos = { 'mytopo': ( lambda: MyTopo() ) }

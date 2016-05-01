# ICNmininet
##Installation

git clone git://github.com/mininet/mininet

cd mininet

git tag  # list available versions

git checkout -b 2.2.1 2.2.1  # or whatever version you wish to install

cd ..

mininet/util/install.sh

##Controller
~$ git clone http://github.com/noxrepo/pox
~$ cd pox
~/pox$ git checkout dart

##Usage

xterm2: ./pox.py forwarding.l2_pairs openflow.discovery misc.full_payload openflow.of_01 --port=6653
xterm2: sudo python *file name*

performancetest.py contains the standard topologies with one host connected to each edge router
it also has iperf and ping tests

scaling_hosts.py contains the code to scale more hosts on to the edge routers and perform the bit complement ping test

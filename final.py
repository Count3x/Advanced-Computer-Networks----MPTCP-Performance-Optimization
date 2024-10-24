#!/usr/bin/env python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI


class LinuxRouter(Node):
    "A Node with IP forwarding enabled."

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class NetworkTopo(Topo):
    "A LinuxRouter connecting three IP subnets"

    def build(self, **_opts):  # Here we create the nodes and the links
        # Add 3 routers
        r0 = self.addNode('r0', cls=LinuxRouter, ip='10.0.0.1/24')
        r1 = self.addNode('r1', cls=LinuxRouter, ip='10.0.1.1/24')
        r2 = self.addNode('r2', cls=LinuxRouter, ip='10.0.5.1/24')

        # Add 6 switches
        s1, s2, s3, s4, s5, s6 = [self.addSwitch(s) for s in ('s1', 's2', 's3', 's4', 's5', 's6')]

        # Connect switches to routers
        self.addLink(s1, r0, intfName2='r0-eth1', params2={'ip': '10.0.0.1/24'})
        self.addLink(s2, r0, intfName2='r0-eth2', params2={'ip': '10.0.2.1/24'})

        self.addLink(s3, r1, intfName2='r1-eth1', params2={'ip': '10.0.1.1/24'})
        self.addLink(s4, r1, intfName2='r1-eth2', params2={'ip': '10.0.3.1/24'})

        self.addLink(s5, r2, intfName2='r2-eth1', params2={'ip': '10.0.5.1/24'})
        self.addLink(s6, r2, intfName2='r2-eth2', params2={'ip': '10.0.6.1/24'})

        # Add 2 hosts and set their default routes
        h1 = self.addHost('h1', ip='10.0.0.100/24', defaultRoute='via 10.0.0.1')
        h2 = self.addHost('h2', ip='10.0.2.100/24', defaultRoute='via 10.0.2.1')

        # for each host, add link to the corresponding switch
        for h, s in [(h1, s1), (h2, s2)]:
            self.addLink(h, s)

        # Add additional links between hosts and switches in different subnets
        self.addLink(h1, s3, params1={'ip': '10.0.1.100/24'})
        self.addLink(h2, s4, params1={'ip': '10.0.3.100/24'})
        self.addLink(h1, s5, params1={'ip': '10.0.5.100/24'})
        self.addLink(h2, s6, params1={'ip': '10.0.6.100/24'})


# This function limits the bandwidth on the paths
def limit_paths(net, host_list, bw_list):
    for i in range(len(host_list)):
        host = net.getNodeByName(host_list[i])
        intfs = host.intfs.values()
        if len(intfs) != len(bw_list[i]):
            print(
                "Error: Mismatch between the number of interfaces ({}) and the number of bandwidth values ({}) for host {}".format(
                    len(intfs), len(bw_list[i]), host_list[i]))
            continue
        for j in range(len(intfs)):
            intf = intfs[j]
            cmd = 'tc qdisc add dev {} root tbf rate {}mbit burst 3200 latency 50ms'.format(intf, bw_list[i][j])
            host.cmd(cmd)


# This function runs the experiment
def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet(topo=topo, waitConnected=True)
    net.start()
    info('*** Routing Table on Router:\n')
    info(net['r0'].cmd('route'))
    info(net['r1'].cmd('route'))
    info(net['r2'].cmd('route'))

    # Enable MPTCP and set the congestion control algorithm for each host
    net['h1'].cmd('sysctl -w net.mptcp.mptcp_enabled=1')
    net['h2'].cmd('sysctl -w net.mptcp.mptcp_enabled=1')
    net['h1'].cmd('sysctl -w net.ipv4.tcp_congestion_control=cubic')
    net['h2'].cmd('sysctl -w net.ipv4.tcp_congestion_control=cubic')

    # Simulate network conditions with 10% loss
    net['h1'].cmd('tc qdisc add dev h1-eth0 root netem loss 10%')
    net['h2'].cmd('tc qdisc add dev h2-eth0 root netem loss 10%')
    net['h1'].cmd('tc qdisc add dev h1-eth1 root netem loss 10%')
    net['h2'].cmd('tc qdisc add dev h2-eth1 root netem loss 10%')
    net['h1'].cmd('tc qdisc add dev h1-eth2 root netem loss 10%')
    net['h2'].cmd('tc qdisc add dev h2-eth2 root netem loss 10%')

    # Set up routing and IP addresses
    # Here, we create additional routing rules for the newly created links between hosts and switches in different subnets

    # Add a route on h1 to reach the 10.0.3.0/24 subnet via the router r1
    net['h1'].cmd('ip route add 10.0.3.0/24 via 10.0.1.1')
    # Add a rule on h1 to use the newly added route when the source IP is 10.0.0.1
    net['h1'].cmd('ip rule add from 10.0.0.1 table 1')
    # Set the IP address of h1-eth1 interface to 10.0.1.100/24
    net['h1'].setIP('10.0.1.100/24', intf='h1-eth1')

    # Add a route on h2 to reach the 10.0.1.0/24 subnet via the router r1
    net['h2'].cmd('ip route add 10.0.1.0/24 via 10.0.3.1')
    # Add a rule on h2 to use the newly added route when the source IP is 10.0.2.1
    net['h2'].cmd('ip rule add from 10.0.2.1 table 1')
    # Set the IP address of h2-eth1 interface to 10.0.3.100/24
    net['h2'].setIP('10.0.3.100/24', intf='h2-eth1')

    # Start iperf server on h1 and iperf client on h2
    net['h1'].cmd('iperf -s -V &')
    net['h2'].cmd('iperf -c h1 -V')

    # Limit the paths' bandwidth using the limit_paths function
    limit_paths(net, ['h1', 'h2'], [[10, 20, 30], [20, 30, 10]])

    # Start the command line interface
    CLI(net)

    # Stop the network
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()

from mininet.topo import Topo
class MyTopo(Topo):
    def __init__(self):
        Topo.__init__(self)
        host1 = self.addHost('h1')
	host2 = self.addHost('h2')
	host3 = self.addHost('h3')
	switch1 = self.addSwitch('s1')
	switch2 = self.addSwitch('s2')
	switch3 = self.addSwitch('s3')
	switch4 = self.addSwitch('s4')
	switch5 = self.addSwitch('s5')
	self.addLink(host1, switch1)
	self.addLink(host3, switch1)
	self.addLink(switch1, switch2)
	self.addLink(switch1, switch3)
	self.addLink(switch1, switch4)
	self.addLink(switch5, switch2)
	self.addLink(switch5, switch3)
	self.addLink(switch5, switch4)
	self.addLink(switch5, host2)
	
        
topos = {'mytopo': (lambda: MyTopo())}

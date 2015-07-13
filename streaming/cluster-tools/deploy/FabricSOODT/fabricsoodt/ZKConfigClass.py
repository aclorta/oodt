from pystache import template_spec

class ZK(template_spec.TemplateSpec):
	""" Zookeeper Config Pystache Class """

	def __init__ (self,DataDir,nodes,zport):
		self.DataDir=DataDir
		self.nodes=nodes
		self.zport=zport
		self.template_rel_directory ="../templates/"

	def DataDir(self):
		return DataDir

	def servers(self):
		servers=""
		for i in range(len(self.nodes)):
			servers = servers+"servers."+str(i)+"="+str(self.nodes[i])+":2888:3888\n"
		return servers

	def zport(self):
		return zport



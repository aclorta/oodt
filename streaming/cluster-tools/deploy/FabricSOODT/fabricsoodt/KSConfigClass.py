from pystache import template_spec

class KS(template_spec.TemplateSpec):
	""" Kafka Config Pystache Class """

	def __init__ (self,ID,HostName,LogDir,nodes,zport):

		self.ID=ID
		self.HostName=HostName
		self.LogDir=LogDir
		self.nodes=nodes
		self.zport=zport
		self.template_rel_directory ="../templates/"

	def ID(self):
		return ID

	def HostName(self):
		return HostName

	def LogDir(self):
		return LogDir

	def ZC(self):
		zc=""
		for node in self.nodes:
			zc=zc+str(node)+":"+self.zport+","

		return zc[:-1]

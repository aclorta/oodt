from __future__ import print_function
""" 
Python script call all modules and reading the config file to
deploy an instance of OODT accross a **heterogenous** cluster
"""

#Internal imports
import sys,os,subprocess
from getpass import getuser
import logging

#External imports
try:
	import pystache
	import configparser
	from fabric.api import env, execute, roles, local, lcd, run
except ImportError, e:
	print("Error: {0}".format(e)) 
	return 1

#Package imports
from fabricsoodt import setup, build, distribute
from fabricsoodt.ZKConfigClass import ZK
from fabricsoodt.KSConfigClass import KS
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
log = logging.getLogger(__name__)

def main():
	log.info('Starting SOODT deploy')
	log.info("Reading configuration file: {0}".format(sys.argv[1]))

	config = configparser.ConfigParser()
	config.read(str(sys.argv[1]))
	CONFIGS = config['CONFIGS']
	SUDO = CONFIGS.getboolean('sudo')
	USER = CONFIGS['user']
	NODES = [node.strip() for node in CONFIGS['nodes'].split(',')]

	#Get a download and install location	
	destination = getDestination(CONFIGS)

	#Download and untar each application, building if necessary too
	appnames = dict() 
	for app in config:
		if app == "DEFAULT" or app == "CONFIGS": continue

		url = config[app]['url']
		name = os.path.basename(config[app]['url'])
		fullname = destination+name
		appnames[app] = fullname

		#Try downloading up to 3 times
		for i in range(1,4):
			if os.path.isfile(destination + name):
				log.info("{0} already exists, skipping download stage.".format(name))
				break
			else:
				log.info("Downloading {0} to {1}".format(app, destination))
				ret = setup.download(url, destination)
				if ret: 
					break
				else:
					log.info("Failed to download, trying again, {0} attempts".format(i))

		#Extract, and if necessary build, applications
		log.info("Application {0} to be extracted from {1} to {2}".format(app, name, destination)) 
		ret = build.extract(fullname, destination)
		log.info("Finished extraction with code: {0}".format(ret))

		msg = [0, "Not building {0}".format(app)]
		if config[app].getboolean('build'):
			try:
				sys.argv[2]
			except Exception:
				rebuild = False
			else:
				rebuild = True

			if rebuild == False:	#Not a rebuild, continue with install
				log.info("Application {0} to be built".format(app))
				try:
					msg = build.build(app,fullname,SUDO, config[app].getboolean('test'))
				except KeyboardInterrupt:
					setup.clean_exit("Exited on keyboard interrupt",f)

			elif rebuild == True and sys.argv[2] == app:	#Is a rebuild of this app
				print("Application {0} to be rebuilt".format(app))
				try:
					msg = build.build(app,fullname,SUDO, config[app].getboolean('test'))
				except KeyboardInterrupt:
					setup.clean_exit("Excited on keyboard interrupt",f)
				log.info("Completed attampt at a rebuild of {0}".format(app))
				sys.exit("\n\nCompleted attampt at a rebuild of {0}".format(app))

			else:	#A rebuild has been requested but not of this app, continue
				continue

		if msg[0]==0:	
			print("\n\n"+msg[1])
		else:
			print("\n\n"+msg[1])
			setup.clean_exit(msg[1])


	#Distribute and configure
	dist = setup.getos()
	render=pystache.Renderer()
	#Move to top of file when restructure in order to use fabric instead of os and subprocess calls
	env.roledefs = {'head':['localhost'], 'nodes':NODES}
	env.colorize_error = True
	env.user = USER 

	'''
	The following, commented-out code is for Mesos.

	#Dependancies required excluding those required only for building specific applications
	ToQuery = [['subversion',1]]
	#Check ulimit -u is above 4096
	execute(distribute.ulimitCheck,roles=['nodes'])
	#Check env variables are set:
	execute(distribute.variablesCheck,roles=['nodes'])
	#Check all required dependancies are installed
	#missing = execute(distribute.dependanciesCheck,ToQuery,dist,roles=['nodes'])
	"""
	if filter(lambda d: d !="",missing.values()):
		f.write("The following dependancies are missing on the deploy nodes, please install and re-runi: "+str(missing))
		setup.clean_exit("The following dependancies are missing on the deploy nodes, please install and re-run: "+str(missing),f)
	"""
	'''

	#Distribute Kafka
	if config['kafka'].getboolean('config'):
		#Read config file for kafka broker cluster settings
		pwd = local("pwd")
		Knodes = config['kafka']['nodes'].split(',')
		KNODES = [knode.strip(" ") for knode in Knodes]
		print("number of kservers: ", len(KNODES))
		print("list of kservers: ", KNODES)
		ZDIR = config['kafka']['ZookeeperDataDir'].strip()
		KDIR = config['kafka']['LogsDir'].strip()
		zport = config['kafka']['zport'].strip()
		#Set $K_HOME remotely
		K_HOME = appnames['kafka'][:-4]+"/"
		execute(distribute.remoteSetVar,"K_HOME="+K_HOME,hosts=KNODES)
		
		#Check required destination folders exists and if not create it on remote nodes
		for inode in KNODES:
			execute(distribute.ExistsCreate, destination, hosts=inode)
			execute(distribute.ExistsCreate, ZDIR, hosts=inode)
			execute(distribute.ExistsCreate, KDIR, hosts=inode)
		
		#Transfer kafka files
		log.info("Transferring Kafka Files")
		execute(distribute.transfer, K_HOME, destination, hosts=KNODES)
		#Add execution permissions to Kafka binaries
		execute(distribute.chmodFolder, K_HOME + "bin/", hosts=KNODES)
		#Setup Zookeeper config file
		zk=ZK(ZDIR,KNODES,zport)
		zookeeperProperties = open("../templates/zookeeper.properties",'w')
		zookeeperProperties.write(render.render(zk))
		zookeeperProperties.close()

		#Distribute Zookeeper Config:
		log.info("Transferring Zookeeper configs")
		for inode, server in zip(KNODES, range(len(KNODES))):
			#Push config file
			execute(distribute.transfer, pwd+"../templates/zookeeper.properties" , K_HOME+"config/zookeeper.properties", hosts=inode)
			#Create myid file
			local("echo "+str(server)+" > ../templates/myid")
			#Push myid file
			execute(distribute.transfer, pwd+"../templates/myid", ZDIR, hosts=inode)

		#Setup and distribute unique Kafka config files
		log.info("Transferring Kafka configs")
		for knode,k in zip(KNODES,range(len(KNODES))):
			#Create Kafka server properties file
			ks=KS(k,knode,KDIR,KNODES,zport)
			kafkaserverProperties = open("../templates/kafkaserver.properties",'w')
			kafkaserverProperties.write(render.render(ks))
			kafkaserverProperties.close()
			#Push kafkaserver.properties
			execute(distribute.transfer, pwd+"../templates/kafkaserver.properties", K_HOME+"config/server.properties", hosts=knode)
		

		#Start Kafka Cluster
		#distribute.startKafka(KNODES)

		#Test installation

		log.info("SOODT deployment completed")

def getDestination(CONFIGS):
	if CONFIGS.getboolean('localInstall'):
		return CONFIGS['destination']
	else:
		try:
			return os.mkdir(os.path.expanduser("~")+"/SOODT_Build_Area")
		except Exception:
			pass

if __name__ == "__main__":
	main()

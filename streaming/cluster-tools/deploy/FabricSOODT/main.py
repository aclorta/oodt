""" 
Python script call all modules and reading the config file to
deploy an instance of OODT accross a **heterogenous** cluster
"""

#External imports
import sys,os 
import pystache
from getpass import getuser
from fabric.api import env, execute, roles, local, lcd, run

#Package imports
from fabricsoodt import setup, build, distribute
from fabricsoodt.ZKConfigClass import ZK
from fabricsoodt.KSConfigClass import KS

def main():
	f = open("../logs/SOODT_install.log","w")
	print "\nRunning SOODT install application across cluster"
	f.write("Running SOODT install application across cluster")

	#Read Configuration
	if setup.python_uninstalled("configparser"):
		setup.pip_install("configparser")
	import configparser
	
	print "\nReading configuration file: " + str(sys.argv[1])
	f.write("\n\nReading configuration file: " + str(sys.argv[1]))

	config = configparser.ConfigParser()
	config.read(str(sys.argv[1]))
	CONFIGS = config['CONFIGS']
	SUDO = CONFIGS.getboolean('sudo')
	USER = CONFIGS['user']
	NODES = [node.strip() for node in CONFIGS['nodes'].split(',')]
	#nodes = CONFIGS['nodes'].split(',')
	#NODES=[]
	#for i in nodes: NODES.append(i.strip())

	#Get a download and install location	
	if CONFIGS.getboolean('localInstall'):
		destination = CONFIGS['destination']
	else:
		try:
			destination = os.mkdir(os.path.expanduser("~")+"/SOODT_Build_Area")
		except Exception:
			pass

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
				print "\n" +name + " already exists, skipping download stage."
				f.write("\n\n" +name + " already exists at " + destination + ", skipping download stage.")
				break
			else:
				print "\nDownloading " + app + " to " + destination
				f.write("\n\nDownloading " + app + " to " + destination)
				ret = setup.download(url, destination)
				if ret: 
					break
				else:
					print "\nFailed to download, trying again, {} attempts".format(i)
					f.write("\n\nFailed to download, trying again, {} attempts".format(i))

		#Extract, and if necessary build, applications
		print "\nApplication "+ app + " to be extracted from " + name + " to " + destination 
		f.write ("\n\nApplication "+ app + " to be extracted from " + name + " to " + destination)
	
		ret = build.extract(fullname, destination)
		print "Finished extraction with code: ", ret
		f.write("\n\nFinished extraction with code: " + str(ret))

		msg = [0,"Not building " + app]
		if config[app].getboolean('build'):
			try:
				sys.argv[2]
			except Exception:
				rebuild = False
			else:
				rebuild = True

			if rebuild == False:	#Not a rebuild, continue with install
				print "\nApplication " + app + " to be built"
				f.write("\n\nApplication " + app + " to be built")
				try:
					msg = build.build(app,fullname,SUDO, config[app].getboolean('test'))
				except KeyboardInterrupt:
					setup.clean_exit("Excited on keyboard interrupt",f)

			elif rebuild == True and sys.argv[2] == app:	#Is a rebuild of this app
				print "\nApplication "+ app + " to be rebuild"
				f.write("\n\nApplication "+ app + " to be rebuild. process will exit on completion")
				try:
					msg = build.build(app,fullname,SUDO, config[app].getboolean('test'))
				except KeyboardInterrupt:
					setup.clean_exit("Excited on keyboard interrupt",f)
				f.write("\n\nCompleted attampt at a rebuild of "+app)
				f.close()
				sys.exit("\n\nCompleted attampt at a rebuild of "+app)

			else:	#A rebuild has been requested but not of this app, continue
				continue

		if msg[0]==0:	
			print "\n\n"+msg[1]
			f.write("\n\n"+msg[1])
		else:
			print "\n\n"+msg[1]
			f.write("\n\n"+msg[1])
			setup.clean_exit(msg[1],f)


	#Distribute and configure
	dist = setup.getos()
	render=pystache.Renderer()
	env.roledefs = {'head':['localhost'], 'nodes':NODES} #Move to top of file when restructure above to use fabric instead of os and subprocess calls
	env.colorize_error = True
	env.user = USER 
	#Dependancies required excluding those required only for building specific applications
	ToQuery = [['subversion',1]]

	''' The following, commented-out code is for Mesos.
	    We may need to use a different program to configure
	    ulimit, as the ulimit program is depracated.
	#Check ulimit -u is above 4096
	execute(distribute.ulimitCheck,roles=['nodes'])
	#Check env variables are set:
	execute(distribute.variablesCheck,roles=['nodes'])
#	#Check all required dependancies are installed
#	missing = execute(distribute.dependanciesCheck,ToQuery,dist,roles=['nodes'])
#	if filter(lambda d: d !="",missing.values()):
#		f.write("The following dependancies are missing on the deploy nodes, please install and re-runi: "+str(missing))
#		setup.clean_exit("The following dependancies are missing on the deploy nodes, please install and re-run: "+str(missing),f)
	'''

	#Distribute Kafka
	if config['kafka'].getboolean('config'):
		#Read config file for kafka broker cluster settings
		pwd = local("pwd")
		Knodes = config['kafka']['nodes'].split(',')
		KNODES=[]
		for i in Knodes: KNODES.append(i.strip(" "))
		kservers = len(KNODES)
		print ("number of kservers: ",kservers)
		ZDIR=config['kafka']['ZookeeperDataDir'].strip()
		KDIR=config['kafka']['LogsDir'].strip()
		zport=config['kafka']['zport'].strip()
		#Set $K_HOME remotely
		K_HOME = appnames['kafka'][:-4]+"/"
		execute(distribute.remoteSetVar,"K_HOME="+K_HOME,hosts=KNODES)
		
		#Check required destination folders exists and if not create it on remote nodes
		for inode in KNODES:
			execute(distribute.ExistsCreate, destination, hosts=inode)
			execute(distribute.ExistsCreate, ZDIR, hosts=inode)
			execute(distribute.ExistsCreate, KDIR, hosts=inode)
		
		#Transfer kafka files
		print "Transferring Kafka Files"
		f.write("\n\nTransferring Kafka Files")
		execute(distribute.transfer, K_HOME , destination ,hosts=KNODES)
		#execute(distribute.transfer, appnames['kafka'][:-4] , destination ,hosts=KNODES)
		execute(distribute.chmodFolder,K_HOME+"/bin/",hosts=KNODES) #Add execution permissions to Kafka binaries

		#Setup Zookeeper config file
		zk=ZK(ZDIR,KNODES,zport)
		zookeeperProperties = open("../templates/zookeeper.properties",'w')
		zookeeperProperties.write(render.render(zk))
		zookeeperProperties.close()

		#Distribute Zookeeper Config:
		print "Transferring Zookeeper configs"
		f.write("\n\nTransferring Zookeeper configs")
		for inode, server in zip(KNODES, range(len(KNODES))):
			execute(distribute.transfer, pwd+"../templates/zookeeper.properties" , K_HOME+"config/zookeeper.properties" ,hosts=inode)#Push config file
			local("echo "+str(server)+" > ../templates/myid")#Create myid file
			execute(distribute.transfer, pwd+"../templates/myid" , ZDIR ,hosts=inode)#Push myid file
		
		#Setup and distribute unique Kafka config files
		print "Transferring Kafka configs"
		f.write("\n\nTransferring Kafka configs")
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

	print "Finished"
	f.write("\n\nFinished")
	f.close()

if __name__ == "__main__": main()


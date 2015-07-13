from __future__ import with_statement
from fabric.api import local, settings, abort, execute, run, cd, env, put, lcd, hide
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, append

def ulimitCheck ():
	""" Check ulimit on all nodes and raises it if necessary """
	with settings(warn_only=True):
		ret = run("ulimit -u")
		
		if int(ret) < 4095:
			ret = run ("ulimit -Su 4095")

	if ret.failed and not confirm ("Failed, continue anyways?"):
		abort("Aborting at user request")


def variablesCheck():
	""" Run bash script check_env.sh that checks JAVA_HOME and M2_HOME are set """
	with settings(warn_only=True):
		with lcd ("../bin"):
			put('check_env.sh','check_env',mode=0755)
		ret = run('./check_env')
		run('rm ./check_env')
	if ret.failed and not confirm ("Something went wrong, message: "+str(ret)+" Continue anyways? "):
		abort("Aborting at user request")
	
def ExistsCreate(path):
	if not exists(path):
		with settings(warn_only=True):
			ret=run("mkdir -p "+path)
		if ret.failed and not confirm ("Failed to make directory "+path+", continue anyways?"):
			abort("Aborting at user request")
		return True
	else:
		return True

def dependanciesCheck (ToQuery, dist):
	""" Checks depednancies listed in ToInstall are available, uses fabrici, returns missing dependancies"""
	missing = []
	err = 0
	if dist == 'ubuntu':
		for each in ToQuery:
			with hide('output','running','warnings'), settings(warn_only=True):
				ret = run('dpkg -s '+str(each[0]))
			if ret.succeeded:
				each[1]=0
			else:
				each[1]=1
		
	elif dist == 'centos':
		for each in ToQuery:
			with hide('output','running','warnings'), settings(warn_only=True):
				each[1] = run('rpm -q '+str(each[0]))
			if ret.succeeded:
				each[1]=0
			else:
				each[1]=1
		
	else:
		print "OS not recognised"
	
	for each in ToQuery:
		if each[1] == 1:
			missing.append(each[0])
			err = 1
	if err:
		return missing
	else:
		return ""

def remoteSetVar(var):
	""" Appends 'export var' to ~/.bash_profile """
	with settings(warn_only=True):
		ret=run('echo export"' + var + '">> ~/.bash_profile')
	if ret.failed and not confirm ("Something went wrong, message: " +str(ret) + " Continue anyways? "):
		abort("Aborting at user request")

def transfer(source,destination):
	""" Puts source at destination on remote host """
	with settings(warn_only=True):
		ret=put(source,destination)
	if ret.failed and not confirm ("Something went wrong, message: " +str(ret) + " Continue anyways? "):
		abort("Aborting at user request")

#def Fappend(filename,text):
#	append(filename,text)
#	#if ret.failed and not confirm ("Something went wrong, message: " +str(ret) + " Continue anyways? "):
#	#	abort("Aborting at user request")

def chmodFolder(folder):
	with settings(warn_only=True):
		ret=run("chmod -R a+x "+folder)
	if ret.failed and not confirm ("Something went wrong, Continue anyways? "):
		abort("Aborting at user request")


####### Kafka deployment functions ######
#def distributeKafka(location, destination):
#	""" Deploy Kafka and configuration to nodes """
#	#Push software:
#	put( )
#
#	#Configure zookeeper
#	remoteSetVar("ZK_HOME=   ")
#	put(untared )
#	put(serverconfig )
#
#	#Configure Kafka
#	remoteSetVar("K_HOME=   ")
#	put (untarred )
#	put (zookeeper.connect)
#	put(hoste.nodes)
#	put(brokerid)
#
#
#
#def deployKafka():
#	""" Start Kafak broker cluster """
#	
#
#	#Start zookeeper
#	with settings(warn_only=True):
#		ret=run('$ZK_HOME/bin/zkServer.sh start $ZK_HOME/conf/zoo_sample.cfg')
#	if ret.failed and not confirm ("Something went wrong, message: " +str(ret) + " Continue anyways? "):
#		abort("Aborting at user request")
#
#	#Start Kafka Cluster
#	with settings(warn_only=True):
#		run('$K_HOME/bin/kafka-server-start.sh $K_HOME/config/server.properties&')
#	if ret.failed and not confirm ("Something went wrong, message: " +str(ret) + " Continue anyways? "):
#		abort("Aborting at user request")
#
#	#Create cluster
#	#Create topics - how?:
#
#
###########################################
#
#
#
#
#
#
#
#
#
#
#
#

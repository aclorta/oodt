""" Module containing functions for the extraction, building, and pushing of applications """
#External imports
import platform
import subprocess
import sys

#Internal imports
import setup

def extract (fullname, destination):
	""" Extracts an application to the same location based on its file extension
	Args: 
	fullname (string): compressed file name including it's fullpath
	destination (string): Directory in which the file can be found and where it will be uncompressed to

	Return:
	Output status of uncomress process, 0 on success.

	"""
	
	if fullname.split(".")[-1][-2:] == 'gz':	#tar gzip
		#os.system('tar -xzvf %s -C %s' % (location+application,location))
		return subprocess.call(['tar','-xzkf',fullname,'-C',destination])

	elif fullname.split(".")[-1][-3:] == 'zip':	# zip
		#os.system('unzip -x %s -d %s' % (location+application,location))
		return subprocess.call(['unzip','-xn',fullname,'-d',destination])



def build_mesos (fullname, sudo, test):
	""" Build the mesos package, return 1 on success, 0 on failure 
	Args:
	fullname (string): Full path to and including the downloaded tar
	sudo (bool): Boolean on if sudo rights are available
	"""
	f = open("../mesos_build.log",'w')
	#Check if platform is 64b:
	f.write("Building mesos package")
	f.write("\nChecking platform")

	if platform.machine() != 'x86_64' and platform.machine() != 'amd64' and not platform.linux_distribution():
		f.write("\nExiting, Mesos can only be run and build on 64b architectures running a linux distribution of which this is not one")
		setup.clean_exit("Exiting, Mesos can only be run and build on 64b architectures running a linux distribution of which this is not one",f)

	#Install dependencies if sudo enabled:
	dependency_exit = False
	dist = setup.getos()
	f.write("\nChecking distro, found: "+str(dist))
	print "\nChecking distro, found: "+str(dist)

	#If Ubuntu
	if dist == 'ubuntu':
		
		ToInstall = [['build-essential',1],['openjdk-6-jdk',1],['python-dev',1],['python-boto',1],['libcurl4-nss-dev',1],['maven',1],['libsasl2-dev',1],['libapr1-dev',1],['libsvn-dev',1]]
		
		if sudo:
			print "\nUsing sudo to install dependencies"
			f.write("\nUsing sudo to install dependencies")
			if setup.dependenciesIn(dist, ToInstall): setup.clean_exit("Exited on keyboard interrupt",f)
		else:
			print "\n\nSudo not enabled, checking for installed dependencies"
			f.write("\n\nSudo not enabled, checking for installed dependencies")
			for each in ToInstall:
				each[1] = subprocess.call(['dpkg','-s',each[0]])

	#If Centos
	elif dist == 'centos':
	
		if subprocess.call(['mvn','--version']): setup.clean_exit("Maven not found, please install",f)	

		ToInstall = [['python-devel',1]	,['java-1.7.0-openjdk-devel',1]	,['zlib-devel',1],['libcurl-devel',1],['openssl-devel',1],['cyrus-sasl-devel',1],['cyrus-sasl-md5',1],['apr-devel',1],['subversion-devel',1],['apr-util-devel',1],['python-boto',1]]
		
		if sudo:
			print "\n\nUsing sudo to install dependencies"
			f.write("\n\nUsing sudo to install dependencies")

			#Add repo containing subvision-devel 1.8
			subprocess.call("sudo echo \"[WanddiscoSVN]\n name=Wandisco SVN Repo \nbaseurl=http://opensource.wandisco.com/centos/6/svn-1.8/RPMS/$basearch/ \nenabled=1 \ngpgcheck=0\" > /etc/yum.repos.d/wandisco-svn.repo", shell=True)

			try:
				ret = subprocess.call(['sudo', 'yum', 'group', 'install', '-y', '"Development Tools"'])
			except KeyboardInterrupt:
				setup.clean_exit("Exited on keyboard interrupt",f)
				
			if setup.dependenciesIn(dist, ToInstall): setup.clean_exit("Exited on keyboard interrupt",f)
	
		else:
			print "\n\nSudo not enabled, checking for installed dependencies"
			f.write("\n\nSudo not enabled, checking for installed dependencies")
			for each in ToInstall:
				each[1] = subprocess.call(['rpm','-q',each[0]])

#	elif dist == 'redhat':
#	elif dist == 'fedora':
#	elif dist == 'debian':
	else:
		print "OS not recognised"
		f.write ("\n\nOS not recognised")
		setup.clean_exit("OS not recognised, cannot ensure dependendcies are installed",f)

#Print dependency installation results
	for each in ToInstall:
		if each[1] == 0:
			print '\033[92m'+each[0]+" is installed and available."+'\033[0m'
			f.write("\n"+each[0]+" is installed and available.")
		else:
			print '\033[91m'+"Failed to install: "+each[0]+'\033[0m'
			f.write("\n\nFailed to install: "+each[0]+"\nExit code: "+str(each[1]))
			dependency_exit = True

	if dependency_exit:
		f.write("\n\nAbove dependencies were not available or could not be installed, please install and then re-run")
		setup.clean_exit("\n\nAbove dependencies were not available or could not be installed, please install and then re-run",f)

	#Build Mesos
	buildfolder = fullname[:-7]+"/build"

	subprocess.call(['mkdir',buildfolder])
	print "\n ###### Created build folder ###### \n"
	f.write("\n\n ###### Created build folder ###### \n")

	try:
		subprocess.Popen("../configure",cwd=buildfolder)
		print "\n ###### Completed ./configure ###### \n"
		f.write("\n\n ###### Completed ./configure ###### \n")
	except KeyboardInterrupt:
		setup.clean_exit("Exited on keyboard interrupt",f)

	try:	
		subprocess.Popen("make",cwd=buildfolder).communicate()
		print "\n ###### Completed make ###### \n"
		f.write("\n\n ###### Completed make ###### \n")
	except KeyboardInterrupt:
		setup.clean_exit("Exited on keyboard interrupt",f)
		

	if test:
		try:
			subprocess.Popen(["make", "check"],cwd=buildfolder).communicate()
			print "\n ###### Complete make check ###### \n"
			f.write("\n\n ###### Complete make check ###### \n")
		except KeyboardInterrupt:
			setup.clean_exit("Exited on keyboard interrupt",f)

	f.close()
	return 1

def build (application, fullname, sudo, test):
	""" Generic build function that can be called from main with an application name and location.  This hierarchy exists such that further application specific build functions can be written later 
	
	Args:
	application (string): application name from config file
	fullname (string): Full path and compressed file name
	sudo (bool): whether or not sudo rights are available
	test (bool): whether or not to execute build test scripts

	Returns:
	1 on success, an array of ['0', error message] on failure
	"""
	if application == 'mesos':
		build_mesos(fullname, sudo, test)
		msg = [0,"Built Mesos"]
	elif application == 'oodt':
		build_oodt(fullname, sudo, test)
		msg = [0,"Build OODT"]
	else:
		msg = [1,"Don't know how to build " + application]

	return msg

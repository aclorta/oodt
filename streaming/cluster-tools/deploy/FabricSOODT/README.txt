Python Fabric based Streaming OODT install on a HETEROGENOUS cluster, for homogenous clusters, or where the head node is of a different architecture to the execution nodes, see scripts and edit where build is called.

-------------
DOCUMENTATION
-------------
Generate documentation by running make with the appropraite flag in ./docs/ 

< $ make > with no flags will list the options

------------
DEPENDANCIES
------------
Python 2.5-2.7
Python pip
fabric
pystache
scala
maven 2.x+
openjdk-7-jdk
Oracle Java 8

Some applications optional applications have their own dependencies.  Given that this install system is intended to not require sudo the user is expected to ensure the following are installed. If sudo access is available set this in the config script and attempts to auto nstall will be made

Mesos:
 - build-essentials
 - python-dev
 - python-boto
 - libcurl4-nss-dev
 - maven	(*Only required for Mesos 0.18.1 or newer*)
 - libsvn-dev	(*Only required for Mesos 0.21.0 or newer)
 - libsasl2-dev	(*Only required for Mesos 0.14.0 or newer*)
 - libapr1-dev 	(*Only required for Mesos 0.21.0 or newer*)



----------
HOW TO USE 
----------
- Ensure passkey access to deploying nodes
- Setup config file
- Ensure 5GB RAM available for Tachyon
- Ensure the listed dependancise are installed on the machine from which this install application will be run.  
- To configure edit config.ini
- To run execute ./bin/deploy <config file> <options> -- You may need to make deploy executable 

Log files:
 - SOODT_install.log
 - mesos_build.log



----------------------------
Centos specific instructions
----------------------------
 - To install pip with sudo:
	 - Add EPEL repository
		sudo pm -iUvh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-5.noarch.rpm
		sudo yum -y update
		sudo yum -y install python-pip
 - Or to install pip locally without sudo:
	 - curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
	 - python get-pip.py --user












""" Module to handle initial stages of installation """
#External imports
import sys
import pip
import os
import platform
import signal
from urllib2 import urlopen, URLError, HTTPError

def getos():
	""" Return 6 letter lowercase version of current OS """
	dist = platform.linux_distribution()
	return dist[0].lower()[0:6]

def clean_exit(message, file = None):
	""" Exits cleanly, closing filename when supplied """
	if filename:
		filename.close()
	sys.exit(message)

def python_uninstalled(package):
	""" Returns 0 if python module is installed and 1 if not """
	print 'Checking install of ', package	
	try:
		__import__(str(package))
	except ImportError:
		return 1
	else:
		return 0

def pip_install(package):
	""" Install given package using pip """
	print "Installing ", package
	pip.main(['install', '--user', package])

def system_uninstalled(package):
	""" Returns 0 if module is installed and 1 if not """


def download(url, destination): 
    """ Fetches a generic URL to disk, creating the directory if necessary, return success or fail.
    
    Args:
    url (string): The url to pull down
    destination (string): The path to destination (including a filename)
    
    Returns:
    1 on success 0 on failure
    
    """
    print "\n############ Destination: ", destination
    if not os.path.exists(destination):
        print("Creating destination ",destination)
        os.makedirs(destination)
    
    try:
    	f = urlopen(url)
    	print "Downloading: " + url + " to " + destination + " as " + os.path.basename(url)
    	with open(destination+os.path.basename(url),"wb") as output_file:
        	output_file.write(f.read())
        return 1
    except HTTPError, e:
        print("HTTP Error: ", e.code, url)
        return 0
    except URLError, e:
        print("URL Error: ", e.reason, url)
        return 0

def dependenciesIn (dist, ToInstall):
	f = open("../Dependencies.log","w")
	if dist == 'ubuntu':
		try:
			ret = subprocess.call(['sudo', 'apt-get', 'update'])
		except KeyboardInterrupt:
			return 1
		try:
			for each in ToInstall:
				each[1] = subprocess.call(['sudo', 'apt-get', 'install', '-y', each[0]])
		except KeyboardInterrupt:
			return 1
		return 0

	elif dist == 'centos':
		try:
			ret = subprocess.call(['sudo', 'yum', 'update'])
		except KeyboardInterrupt:
			return 1
		try:
			for each in ToInstall:
				each[1] = subprocess.call(['sudo', 'yum', 'install', '-y', each[0]])
		except KeyboardInterrupt:
			return 1
		return 0

#	elif dist == 'redhat':
#	elif dist == 'fedora':
#	elif dist == 'debian':
	
#def getConfiguration (config_file):
#	sections = []
#
#	return sections


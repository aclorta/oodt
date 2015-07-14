""" This package enables easy installatin of Streeming OODT accross a homogenous cluster 

Package depends on:
	fabric 

packge includes:
	steup
	building
	distributing

"""
#Local module imports
import setup

#Check public modules are available for import
#Check for: 
#	fabric
#	configparser
#	pystache

if setup.python_uninstalled("fabric"):
	setup.pip_install("fabric")

if setup.python_uninstalled("configparser"):
	setup.pip_install("configparser")

if setup.python_uninstalled("pystache"):
	setup.pip_install("pystache")

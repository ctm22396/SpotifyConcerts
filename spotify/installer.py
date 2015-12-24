# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 19:59:45 2015

@author: christianmeyer
"""

import os, shutil, sys

try:
    os.system('pip')
except:
    print "Please install Anaconda for python2 first: https://www.continuum.io/downloads"
    sys.exit()    
    
try:
    import spotify
except:
    shutil.copy('./spotify/libspotify', '/usr/local/lib')
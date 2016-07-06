#!/usr/bin/env python3

import os
import sys


os.chdir(os.path.dirname(__file__))

sys.path.insert(0, os.path.dirname(__file__) or '.')

PY_DIR = os.path.join(os.environ['OPENSHIFT_HOMEDIR'], "python")

virtenv = os.path.join(PY_DIR, 'virtenv')

PY_CACHE = os.path.join(
    virtenv, 'lib', os.environ['OPENSHIFT_PYTHON_VERSION'], 'site-packages')

os.environ['PYTHON_EGG_CACHE'] = PY_CACHE

virtualenv = os.path.join(virtenv, 'bin/activate_this.py')

try:
    exec(open(virtualenv).read(), dict(__file__=virtualenv))
except IOError:
    pass


import logging

logfile = os.path.join(os.environ['OPENSHIFT_DATA_DIR'], 'logs', 'ffrk.log')
fmt='%(asctime)s [%(levelname)-5s] %(message)s'  # [CRITICAL] [INFO ]
#fmt='%(asctime)s [%(levelname)-5.5s] %(message)s'  # [CRITI] [INFO ]
#fmt='%(asctime)s [%(levelname)-5.5s] %(message)s'  # [CRITI] [INFO]
datefmt='%Y-%m-%dT%H:%M:%S%z'

#logging.basicConfig(
#    filename=logfile, level=logging.DEBUG, format=fmt, datefmt=datefmt
#)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(logfile, 'w', 'utf-8')
handler.setFormatter(logging.Formatter(fmt, datefmt))
root_logger.addHandler(handler)

logging.info('Logging started')


from ffrkapp import application


### EOF ###

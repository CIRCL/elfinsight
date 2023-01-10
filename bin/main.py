#!/usr/bin/env python3

import os
import logging
import configparser
from pathlib import Path
import pyarrow as pa

parentFolder = Path(__file__).resolve().parent.parent
pathConf = os.path.join(parentFolder, "etc/elfinsight.cfg")

if os.path.isfile(pathConf):
    config = configparser.ConfigParser()
    config.read(pathConf)
else:
    print("[-] No conf file found")
    exit(-1)

if 'log' in config:
    logfile = config['log']['defaultlog']
    logger = logging.getLogger('mylogger')
    handler = logging.FileHandler(os.path.join(parentFolder,"log", logfile))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(config['log']['loglevel'])
else:
    exit(-1)

if 'general' in config:
    defaultdir = config['general']['defaultdir']
    logger.info(f"Default dir: {defaultdir}")

if 'feather' in config:
    symdb = config['feather']['defaultfile']
    logger.info(f"Default dir: {symdb}")

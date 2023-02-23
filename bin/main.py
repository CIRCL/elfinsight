#!/usr/bin/env python3

import os
import logging
import configparser
import pdb
from pathlib import Path
from dgnuhash import dELFFile, DetailedGNUHashSection
from elftools.elf.sections import SymbolTableSection
import pyarrow as pa
import pyarrow.parquet as pq
import magic
from dgnuhash import DetailedGNUHashTable
import pdb

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
    handler = logging.FileHandler(os.path.join(parentFolder, "log", logfile))
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(config['log']['loglevel'])
else:
    exit(-1)

if 'general' in config:
    defaultdir = config['general']['defaultdir']
    logger.info(f"Binary dir: {defaultdir}")

if 'parquet' in config:
    datafolder = os.path.join(parentFolder, config['parquet']['datafolder'])
    datafile = os.path.join(datafolder, config['parquet']['datafile'])
    logger.info(f"Parquet file folder: {datafolder}")
    logger.info(f"Parquet file : {datafile}")

# symtabs = []
symtabcount = []
filepathlist = []
bloomfilters = []
symtablist = []

for filename in os.listdir(defaultdir):
    filepath = os.path.join(defaultdir, filename)
    if os.path.isfile(filepath) and "application" in magic.from_file(filepath, mime=True):
        logger.info(f"Opening : {filepath}")
        with open(filepath, 'rb') as f:
            elf = dELFFile(f)
            section = elf.get_section_by_name('.dynsym')
            gnuhashsection = elf.get_section_by_name('.gnu.hash')

            if isinstance(section, SymbolTableSection):
                num_symbols = section.num_symbols()
                symtabcount.append(num_symbols)
                tmplist = []
                for cnt, symbol in enumerate(section.iter_symbols()):
                    tmplist.append(symbol.name)
                if len(tmplist) > 0 :
                    symtablist.append(tmplist)
                # tmpset = set()
                # for sym in range(num_symbols):
                #    tmpset.add(section.get_symbol(sym).name)
                # symtabs.append(tmpset)
            else:
                # symtabs.append(0)
                symtabcount.append(0)
                symtablist.append([])

            # appending gnu_hash bloom filter
            if isinstance(gnuhashsection, DetailedGNUHashSection):
                bloomfilters.append(gnuhashsection.export_bloom())
                logger.info(f"{gnuhashsection.export_binary_bloom()}")
            else:
                bloomfilters.append(b'')

            filepathlist.append(filepath)

        #logger.info(f"{len(symtabcount)}:{len(filepathlist)}:{len(bloomfilters)}")

# Build the arrow data structure
logger.info("Building arrow data structure")
symbols = pa.Table.from_arrays(
    [pa.array(filepathlist), pa.array(symtabcount), pa.array(bloomfilters, type=pa.binary()), pa.array(symtablist)],
    names=['file', 'symtab symbol count', 'bloomfilter', 'list of symbols'])

logger.info(f"Writing parquet files into : {datafile}")
pq.write_table(symbols, datafile)

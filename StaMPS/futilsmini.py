#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 01:17:17 2015
"""
import os
import logging
import traceback
import fnmatch

def opengenlog(logfile):
        try:
            if not os.path.exists(os.path.dirname(logfile)):
                os.makedirs(os.path.dirname(logfile))
                
            logfname=logfile
            
            #logging.basicConfig(filename=self.serv_path+str(rsid)+"/"+self.logs+"/"+self.processlog+str(rsid)+".log", \
            #            level=logging.DEBUG, format='%(asctime)s %(message)s')
            formatter=logging.Formatter('%(asctime)s %(levelname)s : %(message)s')
            fileh = logging.FileHandler(logfname, 'w')
            fileh.setFormatter(formatter)
            log = logging.getLogger()
            log.addHandler(fileh)
            log.setLevel(logging.DEBUG)
            return log
       
        except:
            traceback.print_exc()
            return None
      
def find_files(directory, pattern, listtype="walk", ftype="f"):
    if listtype=="list":
        for basename in os.listdir(directory):
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(directory, basename)
                if os.path.isfile(filename) and ftype=="f":
                    yield filename
                elif os.path.isdir(filename) and ftype=="d":
                    yield filename
    else:
        for root, dirs, files in os.walk(directory):
            if ftype=="f":
                for basename in files:
                    if fnmatch.fnmatch(basename, pattern):
                        filename = os.path.join(root, basename)
                        yield filename
            elif ftype=="d":
                for basename in dirs:
                    if fnmatch.fnmatch(basename, pattern):
                        filename = os.path.join(root, basename)
                        yield filename
               
       
        
      

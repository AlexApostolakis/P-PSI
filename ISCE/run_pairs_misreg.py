'''
Created on Apr 7, 2020

@author: nextgeos
'''

import os
import re
import multiprocessing as mp
import subprocess
import time
import json
import random
from threading import Thread
from datetime import datetime

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

class ISCErunpairsmisreg:
    def environment(self, wd = None, cpu=0, pq='nsp'):
        self.workdir = wd if wd else os.curdir
        os.chdir(self.workdir)
        self.runfilesdir = os.path.join(self.workdir,'run_files')
        self.runfilepairs = 'run_5_pairs_misreg'
        self.processstatusfile='misreg_status.json'
        self.finished_status='finished'
        self.misregfolder='misreg'
        self.maxcpu = mp.cpu_count() if cpu==0 else cpu
        self.prereq=pq

    def loadpairfolders(self):
        with open(os.path.join(self.runfilesdir,self.runfilepairs),'r') as fpairs:
            pairlines = fpairs.readlines()
        #regex = r"(?<=\/).*$"
        regex = '(?<=SentinelWrapper.py -c ).*$'
        pairfolders = []
        for pl in pairlines:
            folder = re.search(regex,pl).group(0)
            pairfolders.append(folder)
        return pairfolders
    
    def createpairsdict(self, pairfolders):
        pairsdict = {}
        for pf in pairfolders:
            f = os.path.basename(pf)
            regex = r"(?<=config_misreg_).*$"
            pair = re.search(regex,f).group(0)
            pairsdict[pair] = {'folder': pf, 'dates': [pair.split('_')[0], pair.split('_')[1]]}
        return pairsdict

    def uniquedates(self, pairfolders):
        pairsdict = {}
        for pf in pairfolders:
            f = os.path.basename(pf)
            regex = r"(?<=config_misreg_).*$"
            pair = re.search(regex,f).group(0)
            pairsdict[pair] = pf
        return pairsdict
    
    def initiatepairprocess(self, pair):
        cmdlist = [ 'SentinelWrapper.py', '-c', pair['folder']]
        #test
        secs = random.randrange(30)
        #cmds for tests
        #cmdlist = [ 'sleep', str(secs)]
        #cmdlist = ['ls']
        print 'Starting Command :' + ' '.join(cmdlist)
        isce_env = os.environ.copy()
        isce_env["ISCE_HOME"] = "/home/celene/ISCE/isce"
        isce_env["PYTHONPATH"] = "$ISCE_HOME/components:/home/celene/ISCE"
        isce_env["PATH"] = isce_env["PATH"]+":/home/celene/projects/ISCEcontrib/stack/topsStack:/home/celene/ISCE/isce/applications"+\
                                            ":/home/celene/ISCE/isce/bin:home/celene/projects/ISCEcontrib/prepStackToStaMPS/bin"
        os_process = subprocess.Popen(cmdlist, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, close_fds=True, env = isce_env)
        return os_process
    
    def getuniquedates(self, pairlist, pairsdict):
        udates = []
        if len(pairlist)==0:
            return udates
        for p in pairlist:
            appdates = [d for d in pairsdict[p]['dates'] if d not in udates] 
            udates+=appdates
        return udates
    
    def checkrunconditions(self,pair,processdict, pairsdict, pairprocessstatus):
        # check if already finished
        notfinished = (not pair in pairprocessstatus) or (pair in pairprocessstatus and pairprocessstatus[pair]['status']!=self.finished_status)
        # check if running
        notrunning = not pair in processdict
        #not same date in some of the pairs running
        processdictkeys = [key for key in processdict]
        uniquedates = self.getuniquedates(processdictkeys, pairsdict)
        # for debug
        #print uniquedates
        if self.prereq=='nsp':
            notsamedate = not any(d in uniquedates for d in pairsdict[pair]['dates'])
        # check resources
        resourcesok = len(processdict)<self.maxcpu
        
        if self.prereq=='nsp':
            startok = notfinished and notrunning and notsamedate and resourcesok
        elif self.prereq=='n':
            startok = notfinished and notrunning and resourcesok

        #for debug
        '''
        if not startok and not notsamedate:
            print "Pair not %s started. not finished: %s, not running: %s, not same dates: %s, resourse ok: %s"%(pair,notfinished, notrunning, notsamedate, resourcesok)
        '''
        return startok
    
    def saveprocesstatus(self, processes_status):
        with open(os.path.join(self.workdir,self.processstatusfile),'w') as fstat:
            fstat.write(json.dumps(processes_status))

    def loadprocesstatus(self):
        fnpstat = os.path.join(self.workdir,self.processstatusfile)
        if os.path.isfile(fnpstat):
            with open(fnpstat,'r') as fstat:
                pstat = fstat.read()
                pairprocessstatus = json.loads(pstat)
        else:
            pairprocessstatus={}
        return pairprocessstatus
    
    def flush_output(self,out, pair, t):
        for line in iter(out.readline, b''):
            if line:
                with open(os.path.join(self.workdir,self.misregfolder,'pair_misreg_%s_%s.log'%(pair,t)),'a') as fout:
                    fout.write(line)
        out.close()
        
    
    def runcommandsloop(self):
        starttime=datetime.now()
        pairfolders = self.loadpairfolders()
        pairsdict = self.createpairsdict(pairfolders)
        runprocessdict = {}
        pairprocessstatus = self.loadprocesstatus()
        prevnumprocessed = -1
        prevnumprocessing = -1
        if not os.path.exists(os.path.join(self.workdir,self.misregfolder)):
            os.makedirs(os.path.join(self.workdir,self.misregfolder))

        while True:
            # print status
            if prevnumprocessed!=len(pairprocessstatus) or prevnumprocessing!=len(runprocessdict):
                failedproc = [p for p in pairprocessstatus if pairprocessstatus[p]['exit_code']!=0]
                print "\n"
                print datetime.now()
                print "Total pairs: %d"%len(pairsdict)
                print "Total pairs processed: %d"%len(pairprocessstatus)
                print "Total processed pairs failed : %d"%len(failedproc)
                print "Concurrent pairs currently processing: %d"%len(runprocessdict)
                print "Process status in file: %s Delete this file to rerun from start pairs misreg step. Logs under 'misreg' folder"%self.processstatusfile
                print "\n"
                prevnumprocessed=len(pairprocessstatus)
                prevnumprocessing=len(runprocessdict)
            # stop if all pairs processed 
            if len(pairprocessstatus) == len(pairsdict):
                dur = datetime.now() - starttime
                print 'Total duration: %s'%dur
                break
            # loop through pairs
            for pair in pairsdict:
                if self.checkrunconditions(pair,runprocessdict, pairsdict, pairprocessstatus):
                    #initiate pair running
                    print 'Start Processing Pair : %s'%pair
                    op = self.initiatepairprocess(pairsdict[pair])
                    logt = Thread(target=self.flush_output, args=(op.stdout, pair, 'out'))
                    errt = Thread(target=self.flush_output, args=(op.stderr, pair, 'err'))
                    runprocessdict[pair] = {'process':op, 'logthread': logt, 'errthread': errt}
                    #runprocessdict[pair]['logthread'].deamon = True
                    runprocessdict[pair]['logthread'].start()
                    runprocessdict[pair]['errthread'].start()
                else:
                    i=1
                    #print "Can't start pair: %s"%pair
                    
                # check for stopped processes
                if (pair in runprocessdict):
                    exitcode = runprocessdict[pair]['process'].poll()
                    if exitcode is not None:
                        result = 'success' if exitcode==0 else 'failed'
                        runprocessdict[pair]['logthread'].join() 
                        runprocessdict[pair]['errthread'].join() 
                        del runprocessdict[pair]
                        pairprocessstatus[pair] = {'status': self.finished_status, 'exit_code':exitcode}
                        self.saveprocesstatus(pairprocessstatus)
                        print 'Finished Processing Pair : %s (%s)'%(pair,result)
                    else:
                        i=1
            # pause some secs
            time.sleep(10)
    





   


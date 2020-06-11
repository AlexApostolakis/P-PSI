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

class ISCErunparallel:
    def environment(self, runfile, regex = "cmd_id", wd = None, cpu=0, comdesc='command'):
        self.workdir = wd if wd else os.curdir
        os.chdir(self.workdir)
        defaultdir=os.path.join(self.workdir,'run_files')
        self.runfilesdir = defaultdir if os.path.exists(defaultdir) else self.workdir 
        self.processstatusfile=comdesc+'.json'
        self.finished_status='finished'
        self.logfolder=comdesc+'_logs'
        self.maxcpu = mp.cpu_count() if cpu==0 else cpu
        self.runfile=runfile
        self.regex=regex
        self.comdesc=comdesc

    def loadcommands(self):
        with open(os.path.join(self.runfilesdir,self.runfile),'r') as fcommands:
            commlines = [line.rstrip() for line in fcommands]
        return commlines
    
    def initiatecommand(self, cmd):
        #test
        #secs = random.randrange(10)
        #cmds for tests
        #cmdlist = [ 'sleep', str(secs)]
        #cmdlist = ['ls']
        cmdlist=cmd.split(' ')
        print 'Starting Command :' + ' '.join(cmdlist)
        isce_env = os.environ.copy()
        isce_env["ISCE_HOME"] = "/home/celene/ISCE/isce"
        isce_env["PYTHONPATH"] = "$ISCE_HOME/components:/home/celene/ISCE"
        isce_env["PATH"] = isce_env["PATH"]+":/home/celene/projects/ISCEcontrib/stack/topsStack:/home/celene/ISCE/isce/applications"+\
                                            ":/home/celene/ISCE/isce/bin:home/celene/projects/ISCEcontrib/prepStackToStaMPS/bin"
        os_process = subprocess.Popen(cmdlist, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, close_fds=True, env = isce_env)
        return os_process
    
    def checkrunconditions(self,commkey,processdict, pairsdict, pairprocessstatus):
        # check if already finished
        notfinished = (not commkey in pairprocessstatus) or (commkey in pairprocessstatus and pairprocessstatus[commkey]['status']!=self.finished_status)
        # check if running
        notrunning = not commkey in processdict
        # check resources
        resourcesok = len(processdict)<self.maxcpu
        
        startok = notfinished and notrunning and resourcesok

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
    
    def flush_output(self,out, commkey, t):
        for line in iter(out.readline, b''):
            if line:
                with open(os.path.join(self.workdir,self.logfolder,'%s_%s_%s.log'%(self.comdesc,commkey,t)),'a') as fout:
                    fout.write(line)
        out.close()
        
    def createcommdict(self, commlist):
        commdict = {}
        for i in range(0,len(commlist)):
            comm=commlist[i]
            #regex = r"(?<=resamp_).*$"
            if self.regex=="cmd_id":
                commdict[str(i)] = comm
            else:
                comkey = re.search(self.regex,comm).group(0)
                commdict[comkey] = comm
        return commdict
    
    def runcommandsloop(self):
        starttime=datetime.now()
        commlines = self.loadcommands()
        commdict = self.createcommdict(commlines)
        runprocessdict = {}
        processstatus = self.loadprocesstatus()
        prevnumprocessed = -1
        prevnumprocessing = -1
        if not os.path.exists(os.path.join(self.workdir,self.logfolder)):
            os.makedirs(os.path.join(self.workdir,self.logfolder))

        while True:
            # print status
            if prevnumprocessed!=len(processstatus) or prevnumprocessing!=len(runprocessdict):
                failedproc = [p for p in processstatus if processstatus[p]['exit_code']!=0]
                print "\n"
                print datetime.now()
                print "Total %s: %d"%(self.comdesc, len(commdict))
                print "Total %s processed: %d"%(self.comdesc, len(processstatus))
                print "Total processed %s failed : %d"%(self.comdesc, len(failedproc))
                print "Concurrent %s currently processing: %d"%( self.comdesc, len(runprocessdict))
                print "Process status in file: %s Delete this file to rerun from start. Logs under '%s' folder"\
                %(self.processstatusfile, self.logfolder)
                print "\n"
                prevnumprocessed=len(processstatus)
                prevnumprocessing=len(runprocessdict)
            # stop if all pairs processed 
            if len(processstatus) == len(commdict):
                dur = datetime.now() - starttime
                print 'Total duration: %s'%dur
                break
            # loop through pairs
            for commkey in commdict:
                if self.checkrunconditions(commkey,runprocessdict, commdict, processstatus):
                    #initiate commkey running
                    print 'Start Processing %s : %s'%(self.comdesc,commkey)
                    op = self.initiatecommand(commdict[commkey])
                    logt = Thread(target=self.flush_output, args=(op.stdout, commkey, 'out'))
                    errt = Thread(target=self.flush_output, args=(op.stderr, commkey, 'err'))
                    runprocessdict[commkey] = {'process':op, 'logthread': logt, 'errthread': errt}
                    #runprocessdict[commkey]['logthread'].deamon = True
                    runprocessdict[commkey]['logthread'].start()
                    runprocessdict[commkey]['errthread'].start()
                else:
                    i=1
                    #print "Can't start commkey: %s"%commkey
                    
                # check for stopped processes
                if (commkey in runprocessdict):
                    exitcode = runprocessdict[commkey]['process'].poll()
                    if exitcode is not None:
                        result = 'success' if exitcode==0 else 'failed'
                        runprocessdict[commkey]['logthread'].join() 
                        runprocessdict[commkey]['errthread'].join() 
                        del runprocessdict[commkey]
                        processstatus[commkey] = {'status': self.finished_status, 'exit_code':exitcode}
                        self.saveprocesstatus(processstatus)
                        print 'Finished Processing : %s (%s)'%(commkey,result)
                    else:
                        i=1
            # pause some secs
            time.sleep(1)
    





   


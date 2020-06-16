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

class StaMPS_mt_extract_cands:
    def environment(self, dophase, dolonlat, dodem, docands, prec, byteswap, maskfile, plist, wd = None, maxcpu = 0, prereq = False, nologs = False):
        self.workdir = wd if wd else os.curdir
        self.dophase = dophase
        self.dolonlat = dolonlat
        self.dodem = dodem
        self.docands = docands
        self.prec = prec
        self.byteswap = byteswap
        self.maskfile = maskfile
        self.plist = plist
        self.processstatusfile = 'mt_prep_process_status.json'
        self.mtpreplogsdir = os.path.join(self.workdir, 'mtpreplogs')
        self.finished_status = 'finished'
        self.ppseparator = '##'
        self.maxcpu = mp.cpu_count() if maxcpu==0 else maxcpu
        self.prereq = prereq
        self.nologs = nologs


    def loadpatchlist(self):
        with open(os.path.join(self.workdir,self.plist),'r') as fplist:
            patches = [line.rstrip() for line in fplist]
        return patches
    
    def selsbc_command(self):
        if self.docands!=1:
            return None
        candsfileSB = os.path.join(self.workdir,'selsbc.in')
        candsfilePS = os.path.join(self.workdir,'selpsc.in')
        if os.path.isfile(candsfileSB): # Select SB candidates 
            candsfile = candsfileSB
        elif os.path.isfile(candsfilePS):
            candsfile = candsfilePS
        else:
            return None
        cmdlist = ['selsbc_patch', candsfile, 'patch.in', 'pscands.1.ij', 'pscands.1.da', 'mean_amp.flt', self.prec, str(self.byteswap)]
        if self.maskfile:
            cmdlist.append(os.path.join(self.workdir,self.maskfile))
        return cmdlist
    
    def lonlat_command(self):
        if self.dolonlat!=1:
            return None
        lonlatfile = os.path.join(self.workdir,'psclonlat.in')
        cmdlist = ['psclonlat', lonlatfile, 'pscands.1.ij', 'pscands.1.ll']
        return cmdlist

    def dem_command(self):
        if self.dodem!=1:
            return None
        demfile = os.path.join(self.workdir,'pscdem.in')
        cmdlist = ['pscdem', demfile, 'pscands.1.ij', 'pscands.1.hgt']
        return cmdlist

    def phase_command(self):
        if self.dophase!=1:
            return None
        phasefile = os.path.join(self.workdir,'pscphase.in')
        cmdlist = ['pscphase', phasefile, 'pscands.1.ij', 'pscands.1.ph']
        return cmdlist
                
    def initiateprocess(self, patch, intproc):
        #test
        #cmds for tests
        #cmdlist = [ 'sleep', str(random.randrange(30))]
        #cmdlist = ['ls']
        cmdlist = eval('self.'+intproc+'_command()')
        if not cmdlist:
            return None
        print 'Starting Command :' + ' '.join(cmdlist)
        
        stamps_env = os.environ.copy()
        stamps_env["STAMPS"]="/home/celene/STAMPS_4.1b/StaMPS-master/"
        stamps_env["MATLABPATH"]=stamps_env["STAMPS"]+"matlab"
        stamps_env["MATLABROOT"]="/usr/local/MATLAB/MATLAB_Production_Server/R2015a"
        stamps_env["MATLABROOTBIN"]=stamps_env["MATLABROOT"]+"/bin"
        stamps_env["PATH"] = stamps_env["PATH"]+":"+stamps_env["STAMPS"]+"bin"+":"+stamps_env["MATLABROOTBIN"]
        #os_process = subprocess.Popen(cmdlist, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, close_fds=True, env = stamps_env)
        os_process = subprocess.Popen(cmdlist, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.join(self.workdir,patch), env=stamps_env)
        return os_process
    
    def checkprereq(self, patch, intproc, patchprocessstatus):
        patchproc = '%s%s%s'%(patch,self.ppseparator,intproc)
        finished_ok = [p.split(self.ppseparator)[1] for p in patchprocessstatus \
                                  if patch in p and patchprocessstatus[p]['exit_code']==0]
        finished_error = [p.split(self.ppseparator)[1] for p in patchprocessstatus \
                                  if patch in p and patchprocessstatus[p]['exit_code']!=0]
        prereqcheck = all([p in finished_ok for p in self.patchintprocdict[intproc]['prereq']])
        if any([p in finished_error for p in self.patchintprocdict[intproc]['prereq']]):
            patchprocessstatus[patchproc]={'status': self.finished_status, 'exit_code': 1000}
        return prereqcheck
    
    def checkrunconditions(self, patch, intproc, patchprocessstatus, processdict):
        patchproc = '%s%s%s'%(patch,self.ppseparator,intproc)
        # check if already finished
        notfinished = (not patchproc in patchprocessstatus) or (patchproc in patchprocessstatus and patchprocessstatus[patchproc]['status']!=self.finished_status)
        # check if running
        notrunning = not patchproc in processdict
        # check prereq
        prereqok = self.checkprereq(patch, intproc, patchprocessstatus)
        # check resources
        resourcesok = len(processdict)< self.maxcpu
        
        startok = notfinished and notrunning and prereqok and resourcesok 
        #for debug
        return startok
    
    def saveprocesstatus(self, processes_status):
        with open(os.path.join(self.workdir,self.processstatusfile),'w') as fstat:
            fstat.write(json.dumps(processes_status))

    def loadprocesstatus(self):
        fnpstat = os.path.join(self.workdir,self.processstatusfile)
        if os.path.isfile(fnpstat):
            with open(fnpstat,'r') as fstat:
                pstat = fstat.read()
                processes_status = json.loads(pstat)
        else:
            processes_status={}
        return processes_status
    
    def flush_output(self,out, patch, intproc, t):
        for line in iter(out.readline, b''):
            if line:
                with open(os.path.join(self.mtpreplogsdir,'mt_prep_%s_%s_%s.log'%(patch, intproc,t)),'a') as fout:
                    fout.write(line)
        out.close()

    def getprocessedpatches(self, patches, procstatus):
        cnt = 0
        for patch in patches:
            patchprocs = [p for p in procstatus if p.split(self.ppseparator)[0]==patch]
            if len(patchprocs)==len(self.patchintprocdict) and all([procstatus[p]['status']==self.finished_status for p in patchprocs]):
                cnt+=1
        return cnt
    
    def runcommandsloop(self):
        os.chdir(self.workdir)
        patches = self.loadpatchlist()
        runprocessdict = {}
        processstatus = self.loadprocesstatus()
        prevnumprocessed = -1
        prevnumprocessing = -1
        starttime = datetime.now()
        #initialize patch processes dict
        self.patchintprocdict = {}
        if self.docands == 1:
            self.patchintprocdict['selsbc']={'prereq':[]}
        if self.dolonlat ==1:
            self.patchintprocdict['lonlat']={'prereq':['selsbc']}
        if self.dodem == 1:
            if self.prereq:
                self.patchintprocdict['dem']={'prereq':['selsbc', 'lonlat']}
            else:
                self.patchintprocdict['dem']={'prereq':['selsbc']}
        if self.dophase == 1:
            if self.prereq:
                self.patchintprocdict['phase']={'prereq':['selsbc', 'lonlat', 'dem']}
            else:
                self.patchintprocdict['phase']={'prereq':['selsbc']}
                
        mt_procs = ' '.join([proc for proc in self.patchintprocdict])
        totalprocs = len(patches)*len(self.patchintprocdict)
        
        #self.patchintprocdict = {'selsbc':{'prereq':[]}, 'lonlat':{'prereq':['selsbc']}, \
        #                         'dem':{'prereq':['selsbc', 'lonlat']}, 'phase': {'prereq':['selsbc', 'lonlat', 'dem']}}

        if not os.path.exists(self.mtpreplogsdir):
            os.makedirs(self.mtpreplogsdir)

        while True:
            # print status
            if prevnumprocessed!=len(processstatus) or prevnumprocessing!=len(runprocessdict):
                failedproc = [p for p in processstatus if processstatus[p]['exit_code']!=0]
                print "\n"
                print datetime.now()
                print "Total patches: %d"%len(patches)
                print "mt_extrat_cands processes to run for each patch: %s"%mt_procs
                print "Total mt_extrat_cands patch processes: %d"%totalprocs
                print "Maximum CPUs to utilize (max concurrent processes): %d"%self.maxcpu
                print "Total patches processed: %d"%self.getprocessedpatches(patches, processstatus)
                print "Total processes finished: %d"%len(processstatus)
                print "Total processes failed : %d"%len(failedproc)
                print "Concurrent patches currently processing: %d"%len(runprocessdict)
                print "Process status in file: %s Delete this file to rerun from start.\nLogs under %s folder"%(self.processstatusfile, self.mtpreplogsdir)
                print "\n"
                prevnumprocessed=len(processstatus)
                prevnumprocessing=len(runprocessdict)
            # stop if all pairs processed 
            if len(processstatus) == totalprocs:
                dur = datetime.now() - starttime
                print 'Total duration: %s'%dur
                break

            # for debug
            #print runprocessdict
            #print processstatus
            
            # loop through pairs
            for patch in patches:
                for intproc in self.patchintprocdict:
                    patchproc = '%s%s%s'%(patch,self.ppseparator,intproc)
                    if self.checkrunconditions(patch, intproc, processstatus, runprocessdict):
                        #initiate patchproc running
                        print "Starting process: '%s' for Patch : '%s'"%(intproc,patch)
                        op = self.initiateprocess(patch,intproc)
                        if op:
                            logt=None; errt=None
                            if not self.nologs:
                                logt = Thread(target=self.flush_output, args=(op.stdout, patch, intproc, 'out'))
                                errt = Thread(target=self.flush_output, args=(op.stderr, patch, intproc, 'err'))
                                runprocessdict[patchproc] = {'process':op, 'logthread': logt, 'errthread': errt}
                                #runprocessdict[patchproc]['logthread'].deamon = True
                                runprocessdict[patchproc]['logthread'].start()
                                runprocessdict[patchproc]['errthread'].start()
                            else:
                                runprocessdict[patchproc] = {'process':op, 'logthread': logt, 'errthread': errt}
                        else:
                            processstatus[patchproc] = {'status': self.finished_status, 'exit_code':1001}
                    else:
                        i=1
                        #print "Can't start patchproc: %s"%patchproc
                        
                    # check for stopped processes
                    if (patchproc in runprocessdict):
                        exitcode = runprocessdict[patchproc]['process'].poll()
                        if exitcode is not None:
                            result = 'success' if exitcode==0 else 'failed'
                            if not self.nologs:
                                runprocessdict[patchproc]['logthread'].join() 
                                runprocessdict[patchproc]['errthread'].join() 
                            del runprocessdict[patchproc]
                            processstatus[patchproc] = {'status': self.finished_status, 'exit_code':exitcode}
                            self.saveprocesstatus(processstatus)
                            print "Finished process '%s' for Patch : '%s' (%s)"%(intproc,patch,result)
                        else:
                            i=1
            # pause some secs
            time.sleep(1)
    





   


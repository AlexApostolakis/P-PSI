#!/usr/bin/python
'''
Created on Sep 12, 2018

@author: celene
'''

import matlab.engine
import os
import multiprocessing as mp
import futilsmini as futils
import StringIO
import time
from processcheck import patchproccheck
from datetime import datetime

class PSnew:
    
    @property
    def workDir(self):
        return os.getcwd()
        #return os.path.join(self._geop.workDir,"INSAR_%s"%self.masterdate.translate(None, '-'))

    def execute_stamps_steps_sh(self,start,end):
        self.eng.stamps_mc_header_upd(start,end,nargout=0)

    def loadpatchsplitlist(self, fpatchlist):
        with open(fpatchlist,'r') as fpl:
            patches = [line.rstrip() for line in fpl]
        return patches
           
    def execute_stamps_steps_1_5a(self,start,end):
        '''
        Run STAMPS persistent scatterer steps 1-5 parallel
        '''

        procinfofile="patch_proc_info.json"
        patchmemusage="patch_memory_usage.csv"
        workdir=self.workDir
         
        stamps_procs=[]
        
        buf=StringIO.StringIO()
        eng = matlab.engine.start_matlab()
        eng.stamps_mc_header_nostart_allcpu(start,end,nargout=0,stdout=buf)
        with open(os.path.join(self.workDir,'log_stamps_split_nostart'),'w') as fout:
            fout.write(buf.getvalue())
            fout.close()
        buf.close()
        eng.quit()
        
        with open(os.path.join(self.workDir,'log_duration_patchlist'),'a') as fout:
            fout.write('%s: Start processing steps %d to %d parallel\n'%(datetime.now(),start,end))
            fout.close()

        delay=2
        for i in range(1,self.ncores+1):
            patchlist = self.loadpatchsplitlist(os.path.join(self.workDir,'patch_list_split_%d'%i))
            eng = matlab.engine.start_matlab()
            out = StringIO.StringIO()
            stamps_proc=eng.stamps(start,end,[],0,'patch_list_split_%d'%i,1,nargout=0, stdout=out, async=True)
            stamps_procs.append({'stamps_proc':stamps_proc,'output':out,'index':i,'mat_engine':eng,'log':False, 'start_time':datetime.now(),\
                                  'patches':patchlist})
            print "Matlab Command : stamps(%d, %d, [], 0, 'patch_list_split_%d',1)"%(start,end,i)
            if i<self.ncores:
                print 'Patch list %d Started.'%(i)
            else:
                print 'Patch list %d Started (Last)'%i
            time.sleep(delay)
            patchproccheck(procinfofile, patchmemusage, workdir)
        
        print 'All parallel PATCH jobs started. Don\'t close this terminal!!'
        print '(You can monitor progress from STAMPS.log in each PATCH folder from another Terminal)'
        procs_finished=False
        while not procs_finished:
            procs_finished = all([proc['stamps_proc'].done() for proc in stamps_procs])
            patchproccheck(procinfofile, patchmemusage, workdir)
            time.sleep(15)
            self.updatefinished(stamps_procs)
        self.updatefinished(stamps_procs,term_eng=True)
        print "Steps %d to %d finished"%(start,end)
 
         
    def updatefinished(self,stamps_procs, term_eng=False):
        remprocs=[]
        for proc in stamps_procs:
            if proc['stamps_proc'].done() and not proc['log']:
                proc['stamps_proc'].result()
                with open(os.path.join(self.workDir,'log_stamps_split_%d'%proc['index']),'w') as fout:
                    fout.write(proc['output'].getvalue())
                    fout.close()
                with open(os.path.join(self.workDir,'log_duration_patchlist'),'a') as fout:
                    patches=' '.join(proc['patches'])
                    fout.write('%s: Patch list %d duration : %s Patches: %s\n'%(datetime.now(),\
                                    proc['index'],(datetime.now()-proc['start_time']),patches))
                    fout.close()
                proc['log']=True
            #if term_eng:
                proc['mat_engine'].quit()
                remprocs.append(proc)
        for proc in remprocs:
            stamps_procs.remove(proc)
        if term_eng:
            with open(os.path.join(self.workDir,'log_duration_patchlist'),'a') as fout:
                fout.write('%s: Finished processing StaMPS steps parallel\n'%datetime.now())
                fout.close()
        
        
    def count_patches(self):
        i=0
        for _ in futils.find_files(self.workDir,'PATCH_*','list','d'):
            i+=1
        return i

    def execute_step_5b(self):
        buf=StringIO.StringIO()
        
        print "Start Step 5b (aggregate patches)"
        eng = matlab.engine.start_matlab()
        eng.stamps(5,5,[],0,[],2,nargout=0,stdout=buf)
        
        with open(os.path.join(self.workDir,'log_stamps_s5_2nd'),'w') as fout:
            fout.write(buf.getvalue())
            fout.close()
            
        buf.close()
        eng.quit()
        print "Step 5b Finished"

        
    def execute_steps_6_7(self, start_step, end_step):
        buf=StringIO.StringIO()
        
        print "Start Steps %d to %d"%(start_step,end_step)

        eng = matlab.engine.start_matlab()
        eng.stamps(start_step,end_step,'n',0,[],0,nargout=0,stdout=buf)
        
        with open(os.path.join(self.workDir,'log_stamps_step_%s_%s'%(start_step,end_step)),'w') as fout:
            fout.write(buf.getvalue())
            fout.close()
            
        print "Steps %d to %d finished"%(start_step,end_step)

        buf.close()
        eng.quit()
        
    def set_cores(self):
            mess = 'Total cores: %d'%mp.cpu_count()
            print mess
            self.writelog(mess)
            num_patches = self.count_patches()
            self.ncores=min(num_patches,self.cpunumlimit)
            mess = 'Max cores to engage: %d'%self.ncores
            print mess
            self.writelog(mess)
            mess = 'Total number of patches: %d'%num_patches
            print mess
            self.writelog(mess)
            eng = matlab.engine.start_matlab()
            eng.setparm('n_cores',self.ncores,nargout=0)
            eng.quit()
            
    def writelog(self, mess):
        with open(self.logfname,'a') as flog:
            flog.write('%s %s\n'%(datetime.now(),mess))
                               
    def execute(self, parstart=0, parend=0, aggr5b=False, aggrstart=0, aggrend=0, cpunumber=0):
        os.chdir(self.workDir)
        self.cpunumlimit=cpunumber
        self.cpunumlimit = mp.cpu_count()-2 if self.cpunumlimit == 0 else self.cpunumlimit
        self.cpunumlimit = max(self.cpunumlimit, 1)

        logname = 'ps_run.log'
        cf=1
        while os.path.isfile(logname):
            logname = 'ps_run_%d.log'%cf
            cf+=1
        self.logfname = logname
        
        #print info
        if parstart>=1 and parend<=5 and parstart<=parend:
            mess = 'Steps from %d-%d will run'%(parstart,parend)
            print mess
            self.writelog(mess)
        else:
            mess ='No steps from 1-5 will run'
            print mess
            self.writelog(mess)
        #self.execute_stamps_steps_1_5a(2,5)
        if aggr5b:
            mess = 'Patch aggregation Step 5b will run'
            print mess
            self.writelog(mess)
        else:
            mess = 'Patch aggregation Step 5b will not run'
            print mess
            self.writelog(mess)
        if aggrstart>=6 and aggrend<=7 and aggrstart<=aggrend:
            mess = 'Steps from %d-%d will run'%(aggrstart,aggrend)
            print mess
            self.writelog(mess)
        else:
            mess = 'No steps from 6-7 will run'
            print mess
            self.writelog(mess)
            

            
        #run steps
        if parstart>=1 and parend<=5 and parstart<=parend:
            _ii=1
            timestart = datetime.now()
            self.writelog('Start Executing steps %d-%d'%(parstart,parend))
            self.set_cores()
            self.execute_stamps_steps_1_5a(parstart,parend)
            self.writelog('Finished Executing steps %d-%d'%(parstart,parend))
            curtime = datetime.now()
            dt = curtime-timestart
            self.writelog('Duration from start %s'%dt)

        if aggr5b:
            _ii=1
            self.writelog('Start Executing step 5b')
            self.execute_step_5b()
            self.writelog('Finished Executing step 5b')
            curtime = datetime.now()
            dt = curtime-timestart
            self.writelog('Duration from start %s'%dt)


        if aggrstart>=6 and aggrend<=7 and aggrstart<=aggrend:
            _ii=1
            self.writelog('Start Executing steps %d-%d'%(aggrstart,aggrend))
            self.execute_steps_6_7(aggrstart,aggrend)
            self.writelog('Finished Executing steps %d-%d'%(aggrstart,aggrend))
            curtime = datetime.now()
            dt = curtime-timestart
            self.writelog('Duration from start %s'%dt)

        
    def __init__(self):
        _ = 1
        
        


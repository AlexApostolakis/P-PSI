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
import math
from shutil import copyfile

class PSnew:
    
    @property
    def workDir(self):
        wd = os.getcwd() if self.wd=='.' else self.wd
        return wd
        #return os.path.join(self._geop.workDir,"INSAR_%s"%self.masterdate.translate(None, '-'))

    def execute_stamps_steps_sh(self,start,end):
        self.eng.stamps_mc_header_upd(start,end,nargout=0)
        
    def next_patch_list(self,k, n_patches,n_cores):
        n_patches_core = int(math.ceil(1.0*n_patches/n_cores))
        ix =range((k-1)*n_patches_core+1,k*n_patches_core+1)
        ix = [x for x in ix if x<=n_patches]
        return ix

    def next_patch_list_2(self,k, n_patches,n_cores):
        n_patches_core = int(math.floor(1.0*n_patches/n_cores)) # patches per core
        n_patches_remain = n_patches % n_cores           
        rem_patch = max(0,k+n_patches_remain-n_cores)
        ix = range((k-1)*n_patches_core+1+max(0,rem_patch-1),k*n_patches_core+rem_patch+1)
        ix = [x for x in ix if x<=n_patches]
        return ix
    
    def next_patch_list_3(self,k, pldict):
        ix = [int(x.split('_')[1]) for x in pldict['patch_list_%d'%k]['patchlist']]
        return ix

    def create_balanced_patch_lists(self, n_patches, n_cores):
        eng = matlab.engine.start_matlab()
        patchsizes={}
        for i_p in range(1,n_patches+1):
            patch='PATCH_%s'%i_p
            pscands1=eng.load('%s/pscands.1.ij'%patch)
            patchsizes[patch]=len(pscands1)
        eng.quit()
        psizes = patchsizes.copy()
        pldict={}
        for i_c in range(1,n_cores+1):
            pldict['patch_list_%d'%i_c]={'patchlist':[], 'cands':[], 'sum':0}
        for i_p in range(0,n_patches):
            maxpatch = max(patchsizes, key=patchsizes.get)
            minsumpl = min(pldict, key=lambda x:pldict[x]['sum'])
            pldict[minsumpl]['patchlist'].append(maxpatch)
            pldict[minsumpl]['cands'].append(patchsizes[maxpatch])
            pldict[minsumpl]['sum']+=patchsizes[maxpatch]
            del patchsizes[maxpatch]
        return pldict, psizes

    def create_patch_lists(self, n_patches, n_cores):
        self.pldict, self.patchsizes = self.create_balanced_patch_lists(n_patches, n_cores)
        # splitting of the patch list
        for k in range(1,n_cores+1):
            #ix = [(k-1)*n_patches_core+1:1:k*n_patches_core];
            if self.opt=='ps':
                ix = self.next_patch_list_3(k, self.pldict)
            elif self.opt=='patch':
                ix = self.next_patch_list_2(k, n_patches,n_cores)
            else:
                raise

            patch_list_filename = 'patch_list_split_'+str(k)
            for ll in range(0,len(ix)):
                if ll==0:
                    with open(patch_list_filename,'w') as fid:
                        fid.close()
                patchdir = 'PATCH_'+str(ix[ll])
                copyfile('parms.mat',os.path.join(patchdir,'parms.mat'))
                with open(patch_list_filename,'a') as fid:
                    fid.write('%s\n'%patchdir)

    def loadpatchsplitlist(self, fpatchlist):
        with open(fpatchlist,'r') as fpl:
            patches = [line.rstrip() for line in fpl]
        return patches
    
    def getpatchlistdata(self,ncores):
        plistdict={}
        for i in range(1,ncores+1):
            plist = self.loadpatchsplitlist(os.path.join(self.workDir,'patch_list_split_%d'%i))
            patchlist=[];s=0;
            for p in plist:
                s+=self.patchsizes[p]
                patchlist.append('%s : %s'%(p,self.patchsizes[p]))
            plistdict['patch_list_split_%d'%i]={'sum':s, 'patches':patchlist}
        max_plist = max(plistdict, key=lambda x:plistdict[x]['sum'])
        plistmessage='Patch lists info:\n'
        for p in plistdict:
            plistmessage+='%s : %s\n'%(p, plistdict[p]['patches'])
        plistmessage+='Maximum sum of PS number in %s : %s, %s'%(max_plist, plistdict[max_plist]['sum'], plistdict[max_plist]['patches'])
        return plistdict, plistmessage

    def execute_stamps_steps_1_5a(self,start,end):
        '''
        Run STAMPS persistent scatterer steps 1-5 parallel
        '''

        procinfofile="patch_proc_info.json"
        patchmemusage="patch_memory_usage.csv"
        workdir=self.workDir

        mess='Creating patch lists, Optimization method: %s'%(self.opt)
        self.writelog(mess)
        num_patches=self.count_patches()
        self.set_cores(num_patches)
        self.create_patch_lists(num_patches, self.ncores)
        patchlistd, mess = self.getpatchlistdata(self.ncores)
        self.writelog(mess)
         
        stamps_procs=[]
        
        mess='Start processing steps %d to %d parallel'%(start,end)
        self.writelog(mess)

        delay=2
        plistdict={}
        try:
            for i in range(1,self.ncores+1):
                eng = matlab.engine.start_matlab()
                out = StringIO.StringIO()
                stamps_proc=eng.stamps(start,end,[],0,'patch_list_split_%d'%i,1,nargout=0, stdout=out, stderr=out, async=True)
                stamps_procs.append({'stamps_proc':stamps_proc,'output':out,'index':i,'mat_engine':eng,'log':False, 'start_time':datetime.now(),\
                                      'patches':patchlistd['patch_list_split_%d'%i]['patches']})
                print "Matlab Command : stamps(%d, %d, [], 0, 'patch_list_split_%d',1)"%(start,end,i)
                if i<self.ncores:
                    print 'Patch list %d Started.'%(i)
                else:
                    print 'Patch list %d Started (Last)'%i
                time.sleep(delay)
                #patchproccheck(procinfofile, patchmemusage, workdir)
            print 'All parallel PATCH jobs started. Don\'t close this terminal!!'
            print '(You can monitor progress from STAMPS.log in each PATCH folder from another Terminal)'
            procs_finished=False
            while not procs_finished:
                procs_finished = all([proc['stamps_proc'].done() for proc in stamps_procs])
                #patchproccheck(procinfofile, patchmemusage, workdir)
                time.sleep(5)
                self.updatefinished(stamps_procs)
            self.updatefinished(stamps_procs,term_eng=True)
        except:
            self.updatefinished(stamps_procs)
            print "Error occured while processing steps 1-5.\nCheck log_stamps_split_<n> logs where n corresponds to the nth patch list group"
            raise
        print "Steps %d to %d finished"%(start,end)
 
         
    def updatefinished(self,stamps_procs, term_eng=False):
        remprocs=[]
        for proc in stamps_procs:
            if proc['stamps_proc'].done() and not proc['log']:
                proc['stamps_proc'].result()
                
                with open(os.path.join(self.workDir,'log_stamps_split_%d'%proc['index']),'w') as fout:
                    fout.write(proc['output'].getvalue())
                    fout.close()
                
                patches=' '.join(proc['patches'])
                self.writelog('Patch list %d duration : %s Patches: %s'%\
                              (proc['index'],(datetime.now()-proc['start_time']),patches))
                proc['log']=True
                proc['mat_engine'].quit()
                remprocs.append(proc)
        for proc in remprocs:
            stamps_procs.remove(proc)
        if term_eng:
            self.writelog('Finished processing StaMPS steps parallel')
        
        
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
        
    def set_cores(self,num_patches):
            mess = 'Total cores: %d'%mp.cpu_count()
            print mess
            self.writelog(mess)
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
                               
    def execute(self, parstart=0, parend=0, aggr5b=False, aggrstart=0, aggrend=0, cpunumber=0, pl = False, wd = '.', opt='ps'):
        self.wd = wd
        self.opt=opt
        os.chdir(self.workDir)
        self.cpunumlimit=cpunumber
        self.cpunumlimit = mp.cpu_count()-2 if self.cpunumlimit == 0 else self.cpunumlimit
        self.cpunumlimit = max(self.cpunumlimit, 1)
        
        if pl:
            print 'Creating patch lists only'
            num_patches=self.count_patches()
            ncores=min(num_patches,self.cpunumlimit)
            self.create_patch_lists(num_patches, ncores)
            patchlist, mess = self.getpatchlistdata(ncores)
            print mess
            return

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
        if aggrstart>=6 and aggrend<=8 and aggrstart<=aggrend:
            mess = 'Steps from %d-%d will run'%(aggrstart,aggrend)
            print mess
            self.writelog(mess)
        else:
            mess = 'No steps from 6-8 will run'
            print mess
            self.writelog(mess)
            

            
        #run steps
        timestart = datetime.now()
        if parstart>=1 and parend<=5 and parstart<=parend:
            _ii=1
            self.writelog('Start Executing steps %d-%d'%(parstart,parend))
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
        
        


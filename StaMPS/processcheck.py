import psutil
import os
import json
import re
import csv
import traceback

procinfofile="patch_proc_info.json"
patchmemusage="patch_memory_usage.csv"


def record_mem(mem_type_num, mem_type_st, matcheddicts, pd):
    GB=(1024*1024*1024)
    if len(matcheddicts)==0:
        pd['Max mem %s'%mem_type_st]=pd['memory_info'][mem_type_num]*1.0/GB
        pd['Min mem %s'%mem_type_st]=pd['memory_info'][mem_type_num]*1.0/GB
        pd['Sum mem %s'%mem_type_st]=pd['memory_info'][mem_type_num]*1.0/GB
        pd['Avg mem %s'%mem_type_st]=pd['memory_info'][mem_type_num]*1.0/GB
    else:
        matcheddict=matcheddicts[0]
        matcheddict['Sum mem %s'%mem_type_st]+=pd['memory_info'][mem_type_num]*1.0/GB
        matcheddict['Avg mem %s'%mem_type_st]=matcheddict['Sum mem %s'%mem_type_st]*1.0/matcheddict['Cnt']
        if float(matcheddict['Max mem %s'%mem_type_st])<float(pd['memory_info'][mem_type_num])/GB:
            matcheddict['Max mem %s'%mem_type_st]=float(pd['memory_info'][mem_type_num])/GB
        elif float(matcheddict['Min mem %s'%mem_type_st])>float(pd['memory_info'][mem_type_num])/GB:
            matcheddict['Min mem %s'%mem_type_st]=float(pd['memory_info'][mem_type_num])/GB
    return matcheddicts, pd

def append_dict_mem_type(newmemdict, mem_type_st, md):
    newmemdict['Max %s'%mem_type_st]='%.3f GB'%(md['Max mem %s'%mem_type_st])
    newmemdict['Min %s'%mem_type_st]='%.3f GB'%(md['Min mem %s'%mem_type_st])
    newmemdict['Avg %s'%mem_type_st]='%.3f GB'%(md['Avg mem %s'%mem_type_st])
    return newmemdict
        
                
def patchproccheck(procinfofile, patchmemusage, workdir):
     
    try:              
        procdict={}
        procdictsjson={'procdicts':[]}
        procdicts=procdictsjson['procdicts']
        memdictsjson={'memdicts':[]}
        memdicts=memdictsjson['memdicts']
        cnt=0
        for proc in psutil.process_iter():
            try:
                # Get process name & pid from process object.
                patchname=os.path.basename(proc.cwd())
                dirname=os.path.dirname(proc.cwd())
                if 'MATLAB' in proc.name() and 'PATCH' in patchname and workdir in dirname:
                    cnt+=1
                    procdict=proc.as_dict(attrs=['pid','memory_info'])
                    regex='(?<=PATCH_).*$'
                    patchno=int(re.search(regex, patchname).group(0))
                    procdict['PATCH']=patchno
                    procdicts.append(procdict)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if os.path.exists(os.path.join(workdir,procinfofile)):
            with open(os.path.join(workdir,procinfofile),'r') as pmem:
                memdictsreadjson=json.loads(pmem.read())
        else:
            memdictsreadjson={'procdicts':[]}
        memdictsread=memdictsreadjson['procdicts']
        
        for pd in procdicts:
            matcheddicts = [d for d in memdictsread if d['PATCH']==pd['PATCH']]

            if len(matcheddicts)==0:
                pd['Cnt']=1
            else:
                matcheddicts[0]['Cnt']+=1
                
            matcheddicts, pd = record_mem(0, 'RSS', matcheddicts, pd)
            matcheddicts, pd = record_mem(1, 'VRT', matcheddicts, pd)
            matcheddicts, pd = record_mem(5, 'DATA', matcheddicts, pd)
            if len(matcheddicts)==0:
                memdictsread.append(pd)
                    
        with open(os.path.join(workdir,procinfofile),'w') as procf:
            procf.write(json.dumps(memdictsreadjson))
            
        for md in memdictsread:
            newmemdict={'PATCH':md['PATCH']}
            newmemdict=append_dict_mem_type(newmemdict, 'RSS', md)
            newmemdict=append_dict_mem_type(newmemdict, 'VRT', md)
            newmemdict=append_dict_mem_type(newmemdict, 'DATA', md)
            memdicts.append(newmemdict)
        
        if len(memdicts)>0:
            keys=['PATCH',
                  'Min RSS', 'Max RSS', 'Avg RSS',\
                  'Min VRT', 'Max VRT', 'Avg VRT',\
                  'Min DATA', 'Max DATA', 'Avg DATA']
            with open(os.path.join(workdir,patchmemusage), "w") as pmem:
                writer = csv.DictWriter(pmem, fieldnames=keys)#memdicts[0].keys())
                writer.writeheader()
                for md in memdicts:
                    writer.writerow(md)
    
        #with open(os.path.join(workdir,patchmemusage),'w') as pmem:
        #    pmem.write(json.dumps(memdictsjson))
    except:
        traceback.print_exc()
    
#patchproccheck(procinfofile, patchmemusage, '/home/nextgeos/StaMPS_work/ath_test_6/INSAR_20181215') 
#patchproccheck(procinfofile, patchmemusage, '/home/nextgeos/StaMPS_work/ath_test_6/stamps_patches/INSAR_20181215')  

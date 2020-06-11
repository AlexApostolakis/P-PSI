#!/usr/bin/python
'''
Created on May 16, 2019

@author: Alex Apostolakis
'''

import sys
import re
import traceback
from datetime import datetime
from datetime import timedelta

def processdur(fstampslog):
    try:
        with open(fstampslog, 'r') as flog:
            loglines=flog.read()
            flog.close()
        
        st_start_time = re.search('\n(.*)(?= STAMPS           Will process patch subdirectories)',loglines,re.MULTILINE).group(1)
        st_end_time = re.search('\n(.*)(?= PS_SMOOTH_SCLA   Finished)',loglines,re.MULTILINE).group(1)
        start_time = datetime.strptime(st_start_time, '%d-%b-%Y %H:%M:%S')
        end_time = datetime.strptime(st_end_time, '%d-%b-%Y %H:%M:%S')
        
        dur = end_time - start_time
        return dur

    except:
        raise

def main(args):
    if len(args)!=1:
        fstampslog='STAMPS.log'
    else:
        fstampslog=args[0]

    try:
        dur = processdur(fstampslog)
        st_dur = str(dur)
        print 'Process duration: '+st_dur

    except:
        traceback.print_exc()
        print 'Calculation of process duration failed. File "%s" may not exist or it is incomplete'%fstampslog
    
if __name__ == "__main__":
    main(sys.argv[1:]) 

#!/usr/bin/python
'''
Created on Nov 9, 2014

@author: Alex
'''

# python modules
import argparse
import os
import sys
import run_pairs_misreg

def main(args):
    d_args = parseargs(args)
    
    wd = d_args.get('workdir')
    wd = os.curdir if wd == '.' else wd
    pq = d_args.get('prereq')
    cpu = int(d_args.get('maxcpu'))
    
        
    ISCErp = run_pairs_misreg.ISCErunpairsmisreg()
    ISCErp.environment(wd, cpu, pq)
    ISCErp.runcommandsloop()  
   
def parseargs(args):
    
    parser = argparse.ArgumentParser()
    
    # server arguments initialization
    parser.add_argument('-d','--workdir',
                        default='.',
                        help="""Working directory. If not given it assumes current directory.""")
    
        # server arguments initialization
    parser.add_argument('-cpu','--maxcpu',
                        default='0',
                        help="""Maximum CPU number to use.
                        If not given all available CPUs will be used.""")
    
    parser.add_argument('-pq','--prereq',
                        default='n',
                        help="""Activate prerequisite n: no, nsp: not same pairs""")

    #d_args=__setup__(parser.parse_args(args))
    
    parser.parse_args(args)
    d_args = vars(parser.parse_args(args))
    
    if len(args)==0:
        parser.print_help()
        # parser.print_usage() # for just the usage line
        parser.exit()
        sys.exit()
    
    return d_args
        
        
def __setup__(args):
    # Convert Namespace object's arguments to dictionary.
    d_args = vars(args)
    return d_args
    
    
if __name__ == "__main__":
    main(sys.argv[1:]) 

#!/usr/bin/python
'''
Created on Apr 15, 2020

@author: Alex
'''

# python modules
import argparse
import os
import sys
import mt_extract_cands_par

def main(args):
    d_args = parseargs(args)

    dolonlat = int(d_args.get('lonlat')) if len(args)>1 else 0
    dodem = int(d_args.get('dem')) if len(args)>2 else 0
    docands = int(d_args.get('cands')) if len(args)>3 else 0
    prec = d_args.get('prec') if len(args)>4 else "f"
    byteswap = int(d_args.get('byteswap')) if len(args)>5 else 0
    maskfile = d_args.get('maskfile') if len(args)>6 else ""
    lst = d_args.get('list') if len(args)>7 else "patch.list"
    if len(args)>0:
        dophase = int(d_args.get('phase'))
    else:
        dophase = 1
        dolonlat = 1
        dodem = 1
        docands = 1
        
    cpu = int(d_args.get('cpunum'))
    prereq = eval(d_args.get('prereq'))

    wd = d_args.get('workdir')
    wd = os.getcwd() if wd == '.' else wd
    
    nologs = d_args.get('nologs')


    print 'args:', dophase, dolonlat, dodem, docands, prec, byteswap, maskfile, lst, wd, cpu, prereq, nologs
    
        
    ExtractCcands = mt_extract_cands_par.StaMPS_mt_extract_cands()
    ExtractCcands.environment(dophase, dolonlat, dodem, docands, prec, byteswap, maskfile, lst, wd, cpu, prereq, nologs)
    ExtractCcands.runcommandsloop()
    

   
def parseargs(args):
    
    parser = argparse.ArgumentParser()
    
    # server arguments initialization

    parser.add_argument('-ph','--phase',
                        default='1',
                        help="""Create phase file (value 1)""")

    parser.add_argument('-ll','--lonlat',
                        default='0',
                        help="""Create Longitude Latitude file""")
    
    parser.add_argument('-de','--dem',
                        default='0',
                        help="""Create DEM file""")
    
    parser.add_argument('-ca','--cands',
                        default='0',
                        help="""Create candidaets file""")

    parser.add_argument('-pr','--prec',
                        default='f',
                        help="""prec""")

    parser.add_argument('-by','--byteswap',
                        default='0',
                        help="""Byteswap""")

    parser.add_argument('-mf','--maskfile',
                        default='',
                        help="""Mask file""")

    parser.add_argument('-l','--list',
                        default='patch.list',
                        help="""Patch list file""")

    parser.add_argument('-d','--workdir',
                        default='.',
                        help="""Working directory""")
    
    parser.add_argument('-cpu','--cpunum',
                        default='0',
                        help="""Maximum CPU number to utilize""")

    parser.add_argument('-pq','--prereq',
                        default='False',
                        help="""run mt extract processes in sequence""")
    
    parser.add_argument('-nl','--nologs',action='store_true', help="""No logs threading""")


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

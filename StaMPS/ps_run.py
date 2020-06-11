#!/usr/bin/python
'''
Created on Nov 9, 2014

@author: Alex
'''

# python modules
import argparse
import os
import sys
from psnew import PSnew

def main(args):
    d_args = parseargs(args)
    
    aggr5b = True if d_args.get('aggr5b') == 'y' else False
    parstepsrange = d_args.get('par')
    parstart=int(parstepsrange.split('-')[0])
    parend=int(parstepsrange.split('-')[1])
    aggrstepsrange = d_args.get('aggr')
    aggrstart=int(aggrstepsrange.split('-')[0])
    agrend=int(aggrstepsrange.split('-')[1])
    
    ps=PSnew()
    ps.execute(parstart, parend, aggr5b, aggrstart, agrend, int(d_args.get('cpunumber')))
  
def parseargs(args):
    
    parser = argparse.ArgumentParser()
    
    # server arguments initialization
    parser.add_argument('-p','--par',
                        default='0-0',
                        help="""range n-m specifies which ps steps will run to process PATCHES, 
                        from 1 to 5 eg 1-2 will run steps 1,2 , with 0-0 no step runs
                                (default: %(default)s)""")

    parser.add_argument('-a5','--aggr5b',
                        default='n',
                        help="""specifies run of aggregation step 5b : y for run n for not run  
                                (default: %(default)s)""")

    
    parser.add_argument('-a','--aggr',
                        default='0-0',
                        help="""range n-m specifies which ps steps will run after aggregation of PATCHES, 
                        from 6 to 7 eg 6-6 will run step 6 only, with 0-0 no step runs
                                (default: %(default)s)""")
    
    parser.add_argument('-cpu','--cpunumber',
                        default='0',
                        help="""maximum CPU number to engage""")
    
        
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

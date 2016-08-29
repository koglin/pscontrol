"""Load Interactive Instrument Controls Python
"""

import pscontrol
import argparse
import sys
import time

def initArgs():
    """Initialize argparse arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--instrument", type=str, 
                        help='Instrument')
    parser.add_argument("-s", "--station", type=int, 
                        help='Station')
    parser.add_argument("--ami", action="store_true", 
                        help='Load ami data from proxy')
    parser.add_argument("--daq", action="store_true", 
                        help='Load daq interface')
    parser.add_argument("--proxy_host", type=str,
                        help='Ami proxy host ' \
                             '-- by default use mon01 of appropriate instrument.')
    parser.add_argument("--quick_alias", action="store_true", 
                        help='Use quick alias in interactive python')
    parser.add_argument("--epics_file", type=str, 
                        help='epics alias file with epicsArch style file')
    parser.add_argument("--epics_dir", type=str, 
                        help='dir for epics_file used for epics aliases')
    parser.add_argument("-b", "--base", type=str, 
                        help='Base into which instrument is loaded.')
    parser.add_argument("-c", "--config_file", type=str, 
                        help='File with configuration dictionary.')
    parser.add_argument("-P", "--monshmserver", type=str, default='psana', 
                        help='-P monshmserver flag used in cnf file for live data')
    return parser.parse_args()


if __name__ == "__main__":
    time0 = time.time()

    args = initArgs()
    
    if not args.instrument:
        args.instrument = pscontrol.psutils.instrument_guess()
    
    if not args.base:
        args.base = args.instrument
    
    print "*"*80
    print 'Loading {:} instrument controls with the following arguments:'.format(args.instrument)
    for attr,val in vars(args).items():
        print "   {:} = {:}".format(attr, val)
    print "*"*80
    
    ioc = pscontrol.psioc.LCLS_Ioc(quiet=False, **vars(args))
    
    time_ioc = time.time()

    setattr(sys.modules['__main__'], args.base, pscontrol.Instrument(**vars(args)))
    
    time_instrument = time.time()
   
    print "*"*80
    print pscontrol.__doc__  
    print "*"*80
    print "The follwoing have been loaded (with pscontrol/load.py)"
    print '   ioc = pscontrol.Ioc():  ' \
         +'Tab accssible ioc information for {instrument}'.format(**vars(args)) 
    print '   {instrument} = pscontrol.Instrument():  '.format(**vars(args)) \
         +'Tab accsssible epics infromation for {instrument}'.format(**vars(args)) 
    
    if args.daq:
        daq = pscontrol.Daq(**vars(args))
        print '   daq = pscontrol.Daq():  ' \
             +'Tab accsssible DAQ interface for {instrument}'.format(**vars(args)) 

    if args.ami:
        ami = pscontrol.Ami(**vars(args))
        print '   ami = pscontrol.Ami():  '\
             +'Tab accsssible AMI interface for {instrument}'.format(**vars(args)) 

    print "*"*80
    print '{:>20} = {:8.3f} sec'.format('Ioc load time', time_ioc-time0)
    print '{:>20} = {:8.3f} sec'.format('Instrument load time',time_instrument-time_ioc)
    print '{:>20} = {:8.3f} sec'.format('Total load time', time.time()-time0)
    print "*"*80


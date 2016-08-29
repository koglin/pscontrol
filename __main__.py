from pscontrol import *
import argparse

def initArgs():
    """Initialize argparse arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help='Epics PV or ioc name')
    parser.add_argument("launchtype", nargs='?', default=None, 
                        help='Attribute of PV or ioc to return (optional)')
    parser.add_argument("-i", "--instrument", type=str, 
                        help='Instrument')
    parser.add_argument("-s", "--station", type=int, 
                        help='Station')
    parser.add_argument("--ami", action="store_true", 
                        help='Use ami data from proxy')
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
    args = initArgs()
    
    pvbase = None
    iocname = None
    instrument = args.instrument

    arginputs = args.input.split(' ')
    ninput = len(arginputs)

    inputname = arginputs[0]

    launchtype = args.launchtype

    if ':' in inputname:
        pvbase = inputname
        if not instrument:
            instrument = pvbase.split(':')[0]
    elif '-' in inputname:
        iocname = inputname
    else:
        print 'Unknown input'

    ioc = Ioc(quiet=True, instrument=instrument)
    if iocname:
        sioc = get_ioc(iocname)
        if launchtype and launchtype.lower() == 'iocpv':
            print sioc.IOCPV
        elif launchtype:
            try:
                value =  getattr(sioc, launchtype)
                if not value:
                    value = getattr(sioc.IOC, launchtype)
                if not value:
                    value = getattr(sioc.IOC, launchtype.upper())
                
                print value
            except:
                print 'Error', launchtype, iocname, ioc
        else:
            show_ioc_status(iocname)
    
    elif pvbase:
        if launchtype and launchtype.lower() == 'iocpv':
            print get_iocpv(pvbase)
        elif launchtype:
            pv = get_device(pvbase)    
            try:
                if hasattr(pv, launchtype):
                    value = pv.get(launchtype, as_string=True)
                if not value and hasattr(pv, launchtype.upper()):
                    value = pv.get(launchtype.upper(), as_string=True)
                if not value:
                    value = getattr(pv, launchtype)
                if not value:
                    value = getattr(pv, launchtype.upper())

                print value
            except:
                print 'Error', launchtype, pvbase, pv

        else:
            show_pv_status(pvbase)



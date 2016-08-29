import psutils
from iocmanager import utils as iocutils
import re
import operator
from glob import glob
import subprocess
import time
import simplejson
#import epics
import pyca
import smartPv
import lcls_devices
import psdevice
import netconfig

_iocData_dir = '/reg/d/iocData/'

def get_ioc_pvlist(file, quiet=True):
    """Return a dictionary of pvs and record types from a file
       with the standard IOC.pvlist format
    """
    pv_dict = {}
    try:
        with open(file,'r') as f:
            for line in f:
                items = line.split(',')
                pv_dict.update({items[0]: items[1].split('\n')[0].strip().strip('"')})
    except:
        if not quiet:
            print 'WARNING:  No pvlist file', file

    return pv_dict

def get_ioc_archive(file, quiet=True):
    """Return a dictionary of pvs and archiver info from a
       standard epics formatted .archive file.
    """
    pv_dict = {}
    try:
        with open(file,'r') as f:
            for line in f:
                items = line.split()
                if len(items) == 3:
                    if '.' in items[0]:
                        pvbase, attr = items[0].split('.')
                    else:
                        pvbase, attr = items[0].rsplit(':',1)

                    ditem = pv_dict.get(pvbase)
                    if not ditem:
                        pv_dict.update({pvbase: {}})
                        
                    pv_dict[pvbase].update({attr: (items[1], items[2])})

    except:
        if not quiet:
            print 'WARNING:  No archive file', file

    return pv_dict

def get_ioc_autosave(file, quiet=True):
    """Return a dictionary of pvs and autosave info from a
       standard epics autosave formatted .sav file.
    """
    pv_dict = {}
    try:
        with open(file,'r') as f:
            for line in f:
                items = line.split()
                if not line.startswith('#') and len(items) > 1:
                    if '.' in items[0]:
                        pvbase, attr = items[0].split('.')
                    else:
                        pvbase, attr = items[0].rsplit(':',1)

                    ditem = pv_dict.get(pvbase)
                    if not ditem:
                        pv_dict.update({pvbase: {}})
                        
                    pv_dict[pvbase].update({attr: ' '.join(items[1:])})

    except:
        if not quiet:
            print 'WARNING:  No autosave file', file

    return pv_dict

def open_xterm_less(file):
    """Show a file with the unix less command in a new xterm window. 
    """
    try:
        subproc = subprocess.Popen('xterm -fn 80x60 -e less {:}'.format(file), 
                         stdout=subprocess.PIPE, shell=True)
    except:
        print 'Cannot open log file', file

class LCLS_Ioc(object):
    """
    Object to contain the IOC information seperated by hutch.
    """
    _loaded_hutches = {}
    _cfg = {}
    def __init__(self,**kwargs):
        self.load_instrument(**kwargs)

    def load_instrument(self,instrument=None,**kwargs):
        
        if not instrument:
            instrument = psutils.instrument_guess()

        ioc = Ioc(instrument=instrument,**kwargs)
        self._loaded_hutches[instrument] = ioc

    def __dir__(self):
        all_attrs =set(self.__dict__.keys()
                        +dir(LCLS_Ioc)
                        +self._loaded_hutches.keys())
        return list(sorted(all_attrs))

    def __getattr__(self,attr):
        if attr in self._loaded_hutches:
            return self._loaded_hutches[attr]
        else:
            return getattr(super(LCLS_Ioc,self),attr)

class Ioc(object):
    """Tab accessible dictified ioc information from iocmanager.cfg.
    """


    _hioc_dir = '/reg/d/iocCommon/hioc/'
    _cfg_dir = '/reg/g/pcds/pyps/config/'

    _cfg_pv_dicts = ['iocpv','rtyp','archive','autosave','ioc','device','records']

    def __init__(self, instrument=None, no_init=False, no_auto_load=False,quick_load=False, **kwargs):
        
        if not instrument:
            instrument = psutils.instrument_guess()
        
        self.instrument = instrument

        self._cfg = {}
        self._aliases = {}
        self._hioc_list = []
        self._epics_dict = {}
        self._epics_camdict = {}
        self._devices = {}
        self._sets = {}

        if not instrument:
            instrument = psutils.instrument_guess()
        
        if not no_auto_load:
            self.load_epicsArch(instrument=instrument, **kwargs)
            self.load_epicsCameras(instrument=instrument, **kwargs)
        
        if not no_init:
            self.load_cfg(instrument=instrument, **kwargs)

        #Update global dictionary
        for cfg_dict in ['pv','iocs']:
            if cfg_dict not in LCLS_Ioc._cfg.keys():
                LCLS_Ioc._cfg[cfg_dict] = {}
            for key in self._cfg[cfg_dict]:
                if key not in LCLS_Ioc._cfg[cfg_dict]:
                    LCLS_Ioc._cfg[cfg_dict][key] = {}
                
                LCLS_Ioc._cfg[cfg_dict][key].update(self._cfg[cfg_dict][key])
        
        self.rtypes = RecordTypes(self)

    def load_epicsArch(self, instrument=None, epics_dir=None, epics_file=None, 
                             quiet=False, **kwargs):
        """Load epicsArch file to define aliases.
        """
        if not epics_file:
            epics_file = 'epicsArch.txt'

        if not epics_dir:
            if not instrument:
                instrument = psutils.instrument_guess()
            
            epics_dir = '/reg/g/pcds/dist/pds/'+instrument+'/misc/'

        if epics_dir:
            if not quiet:
                print 'instrument: {:}'.format(instrument)
                print 'loading epics pvs from', epics_file, ' in', epics_dir
            
            self._epics_dict.update(lcls_devices.epicsArch_dict(epics_file,epics_dir))
            for item in self._epics_dict.values():
                try:
                    alias, attr = item['alias'].split('_',1)
                except:
                    alias = attr = item['alias']

                if alias not in self._sets:
                    self._sets[alias] = {}
                
                self._sets[alias].update(**{attr: item['base']})
                self._devices.update(**{item['base']: {'alias': item['alias'], 'records': {}}})

    def load_epicsCameras(self, instrument=None, epics_file=None, epics_dir=None, 
                                quiet=False, **kwargs):
        """Load epics camera viewer config file to define aliases.
        """
        if not epics_file:
            epics_file = 'camviewer.cfg'

        if not epics_dir:
            if not instrument:
                instrument = psutils.instrument_guess()
            
            epics_dir = '/reg/g/pcds/pyps/config/'+instrument.lower()+'/'

        if epics_dir:
            if not quiet:
                print 'instrument: {:}'.format(instrument)
                print 'loading epics pvs from', epics_file, ' in', epics_dir
            
            self._epics_camdict.update(lcls_devices.camviewer_dict(epics_file,epics_dir))
            for item in self._epics_camdict.values():
                alias = item['alias']
                if alias not in self._sets:
                    self._sets[alias] = {}
                
                self._sets[alias].update(**{'IMAGE': item['base'], 'EVR': item['evr']})
                self._devices.update(**{item['base']: {'alias': alias+'_IMAGE', 'records': {}}, 
                                        item['evr']: {'alias': alias+'_EVR', 'records': {}}})

    def load_cfg(self, instrument=None, quiet=False, **kwargs):
        if not instrument:
            instrument = psutils.instrument_guess()
        else:
            instrument = instrument.lower()

        json_file = '{:}/{:}/iocmanager.json'.format(self._cfg_dir,instrument)
        try:
            with open(json_file,'r') as cfg:
                [stored_cfg,stored_aliases] = simplejson.load(cfg)
        except IOError as e:
            if not quiet:
                print 'No JSON file found, configuration must be fully loaded.'
            self._full_load(instrument,quiet=quiet)
        else:
            last_save = stored_cfg['last_save_time']
            cfg_file = '{:}{:}/iocmanager.cfg'.format(self._cfg_dir, instrument)
            time, iocs, hosts, dump = iocutils.readConfig(cfg_file)
            if last_save != time and not kwargs.get('quick_load'):
                if not quiet: print 'The Iocmanager has been updated, configuration must be fully loaded'
                self._full_load(instrument,quiet=quiet)
            else:
                if not quiet: print 'Using stored configuration'
                self._cfg.update(stored_cfg)
                self._aliases.update(stored_aliases)
       

    def _full_load(self,instrument,quiet=False,**kwargs):
        """Load an Iocmanager config file for the specified instrument.
        """
        if not quiet:
            print 'Loading Ioc manager config for {:}'.format(instrument)
        cfg_file = '{:}{:}/iocmanager.cfg'.format(self._cfg_dir, instrument)
        time, iocs, hosts, dump = iocutils.readConfig(cfg_file)
        ioc_dict = {}
        host_dict = {host: {'instrument': instrument, 'siocs': [], 'hioc': False} for host in hosts}
        for ioc in iocs:
            alias = ioc['alias']
            if not alias:
                alias = ioc['id']

            alias = re.sub('-| ', '_', alias)
            alias = re.sub('[\W]+', '', alias)
#            key = ioc['id'].replace('-','_').replace(' ', '_').rsplit('ioc_')[1]
            key = ioc['id'] #.rsplit('ioc-')[1]
            if ioc.get('dir').startswith('/reg/g/pcds/controls'):
                if not quiet:
                    print 'skipping recording ioc', key
            else:
                self._aliases[alias] = key
                ioc_dict[key] = ioc
                host_dict[ioc['host']]['siocs'].append(key)

        self._cfg.update({'last_save_time': time, 'iocs': ioc_dict, 'hosts': hosts})
        
        # setup pv lookup dictionaries
        if not self._cfg.get('pv'):
            self._cfg['pv'] = {attr: {} for attr in self._cfg_pv_dicts}

        hioc_files = glob('{:}/ioc-{:}-*'.format(self._hioc_dir,instrument))

        for file in hioc_files:
            hioc = file.replace(self._hioc_dir,'')
            if len(hioc.split('.')) == 1:
                key = hioc #.replace('ioc-','')
                host_dict[hioc] = {'instrument': instrument, 'siocs': [], 'hioc': True}
                self._hioc_list.append(hioc)
                alias = key.replace('-','_')
                self._aliases[alias] = hioc
                self._cfg['iocs'][key] = {'host': hioc, 'alias': alias, 'id': hioc} 

        for ioc_name, ioc_cfg in self._cfg['iocs'].items():
            if not quiet:
                print 'loading', ioc_name
            
            disable = ioc_cfg.get('disable')

            if ioc_cfg and ioc_cfg.get('disable') is not True:
                file = '{dir}/{ioc}/iocInfo/IOC.pvlist'.format(dir=_iocData_dir, ioc=ioc_name)
                pv_rtyp = get_ioc_pvlist(file, quiet=quiet) 
                file = '{dir}/{ioc}/autosave/{ioc}.sav'.format(dir=_iocData_dir, ioc=ioc_name)
                pv_autosave = get_ioc_autosave(file, quiet=quiet)
                file = '{dir}/{ioc}/archive/{ioc}.archive'.format(dir=_iocData_dir, ioc=ioc_name)
                pv_archive = get_ioc_archive(file, quiet=quiet)
            else:
                pv_rtyp = {}
                pv_archive = {}
                pv_autosave = {}

            ioc_cfg.update(**{'pvs': pv_rtyp})
            self._cfg['iocs'][ioc_name]['pvs'] = pv_rtyp
            
            iocpv = [pv for pv in pv_rtyp if 'IOC' in pv]
            iocpv.sort(key=len)
            if not iocpv:
                iocpv = [pv.rstrip(':HEARTBEAT') for pv in pv_rtyp if 'HEARTBEAT' in pv]
                if not quiet:
                    if iocpv:
                        print 'WARNING:  IOCPV name {:} is not standard -- should contain IOC'.format(iocpv[0])
                    if len(iocpv) > 1:
                        print 'WARNING:  Too many IOCPVs', iocpv
               
            if iocpv:
                iocpv = iocpv[0]
            else:
                if not quiet and not disable:
                    print 'WARNING:  No iocAdmin IOCPV for ', ioc_name
                iocpv = None
            
            self._cfg['pv']['iocpv'].update(**{pv: iocpv for pv in pv_rtyp})
            self._cfg['pv']['rtyp'].update(**pv_rtyp)
            self._cfg['pv']['archive'].update(**pv_archive)
            self._cfg['pv']['autosave'].update(**pv_autosave)
            self._cfg['pv']['ioc'].update(**{pv: ioc_name for pv in pv_rtyp})
            for pv,rtyp in pv_rtyp.items():
                try:
                    base, attr = pv.rsplit(':',1)
                    if base not in self._cfg['pv']['records']:
                        self._cfg['pv']['records'][base] = {}

                    self._cfg['pv']['records'][base].update(**{attr: pv})
                except:
                    pass
            self._cfg['iocs'][ioc_name]['IOCPV'] = iocpv

        if not quiet: print 'Creating stored JSON configuration'
        json_file = '{:}/{:}/iocmanager.json'.format(self._cfg_dir,instrument)
        try:
            with open(json_file,'w+') as cfg:
                simplejson.dump([self._cfg,self._aliases],cfg)
        except:
            print 'Permission issue writing ioc config', json_file
            print '  -- No update performed'

#        self._cfg['iocs'].update(**self._cfg['iocs'])
#        for attr in self._cfg_pv_dicts:
#            setattr(self, '_pv_'+attr, self._cfg['pv'].get(attr))
    
    
    @property
    def devices(self):
        return netconfig.Host_Group(hutch=self.instrument)

    def show_info(self):
        """Show the information for all the loaded iocs.
        """
        print '-'*80
        print 'Information for {:}'.format('iocs')
        print str(getattr(self, attr))

    def __getattr__(self, attr):
        if attr in self._aliases:
            return Sioc(self._aliases[attr])

    def __dir__(self):
        all_attrs = set(self._aliases.keys() +
                        self.__dict__.keys() + dir(Ioc))
        return list(sorted(all_attrs))

class RecordTypes(object):
    """Tab accessible class of all record types currently loaded in the Ioc class.
       Each record type provides all of the pvs for the given record type currently
       loaded in the Ioc class.
    """

    _rtypes = {}

    def __init__(self,Ioc=None):
        if not Ioc:
            Ioc = LCLS_Ioc._cfg
        self.ioc = Ioc
        self._rtypes.update({rtyp: rtyp for rtyp in set(self.ioc._cfg['pv']['rtyp'].values())})

    def __getattr__(self, attr):
        if attr in self._rtypes:
            devices = {pv.replace(':','_'): pv for pv,rtyp in self.ioc._cfg['pv']['rtyp'].items() \
                       if rtyp == attr}

        return lcls_devices.EpicsDeviceSet(attr, devices)

    def __dir__(self):
        all_attrs = set(self._rtypes.keys() +
                        self.__dict__.keys() + dir(RecordTypes))
        return list(sorted(all_attrs))


class Sioc(object):
    """Tab accessible ioc startup information from the iocManager including.
          alias:  Descriptive python attribute
          host:   Host machine on which the ioc runs
          port:   Telnet port of the host machine on which the ioc runs
          dir:    Directory on the st.cmd file
          cmd:    Command file if different from the standard st.cmd
        
        The iocAdmin IOCPV name (from the IOC.pvlist file) is available as well as
        the pvs in the ioc.
          IOC:    Collection of records of the base IOCPV pv
          PVS'    Collection of devices according to base pvs served by the ioc
    """

    _info_attrs = ['id', 'alias', 'host', 'port', 'dir', 'cmd', 
                   'st_cmd_file', 'IOCPV']

    _ioc_records = ['LOCATION', 'ACCESS', 'HOSTNAME', 
                   'UPTIME', 'STARTTOD', 'TOD', 
                   'SR_rebootTime', 'SR_recentlyStr']

    def __init__(self, name, quiet=True, reload=False):
        self._name = name
        if not LCLS_Ioc._cfg:
            lcls_ioc = LCLS_Ioc(quiet=quiet)

        self._cfg = LCLS_Ioc._cfg['iocs'].get(name, {})

        expand = False
        devices = {}
        for pvs in self.pvs:
            vals = pvs.split(':')
            if 'IOC' in vals:
                nmax = len(vals)-1
            else:
                nmax = 4
            
            nlen = min([len(vals),nmax])
            alias = '_'.join(vals[:nlen])
            pvbase = ':'.join(vals[:nlen])

            if not devices.get(alias):
                devices.update({alias: {'pvbase': pvbase, 'records': {}}})
            
            if len(vals) > nmax:
                if expand:
                    devices[alias]['records'].update({'_'.join(vals[nmax:]): ':'.join(val)})
                else:
                    devices[alias]['records'].update({vals[nmax]: ':'.join(vals[:nmax+1])})

        self._device_sets = devices

        iocpvs = {pv: item['pvbase'] for pv,item in self._device_sets.items() if 'IOC' in pv}
        for pv in iocpvs:
            self._device_sets.pop(pv)

        iocpv = iocpvs.values()
        iocpv.sort(key=len)

        self.IOCPV = iocpv[0]

    @property
    def _attrs(self):
        return LCLS_Ioc._cfg['iocs'][self._name].keys() 

    @property
    def _autosave_dict(self):
        file = '{dir}/{ioc}/autosave/{ioc}.sav'.format(dir=_iocData_dir, ioc=self._name)
        return get_ioc_autosave(file)

    @property
    def _archive_dict(self):
        file = '{dir}/{ioc}/archive/{ioc}.archive'.format(dir=_iocData_dir, ioc=self._name)
        return get_ioc_archive(file)

    def view_log(self):
        """View the ioc.log file in a separate terminal.
        """
        file = '{dir}/{ioc}/iocInfo/ioc.log'.format(dir=_iocData_dir, ioc=self._name)
        open_xterm_less(file)

    @property
    def st_cmd_file(self):
        """Full filename of st.cmd file
        """
        file = '{top}/{dir}/build/iocBoot/{ioc}/st.cmd'.format(top=iocutils.EPICS_SITE_TOP, 
                    dir=self.dir,ioc=self.id)
        
        if not glob(file):
            file = '{top}/{dir}/iocBoot/{ioc}/st.cmd'.format(top=iocutils.EPICS_SITE_TOP, 
                    dir=self.dir,ioc=self.id)

        return file

    def view_st_cmd(self):
        """View the st.cmd file in a separate terminal.
        """
        file = self.st_cmd_file
        print 'Opening xterm for',file

        try:
            open_xterm_less(file)
        except:
            print 'Did not find st.cmd file', file

    def show_info(self):
        """Show the ioc information.
        """
        print '-'*80
        print 'Information for {:}'.format(self._name)
        print '-'*80
        for attr in self._info_attrs:
            print '{:15} {:<40}'.format(attr, getattr(self, attr))  
        for attr in self._ioc_records:
            try:
                value = getattr(self.IOC, attr).get('VAL', as_string=True)
                print '{:15} {:<40}'.format(attr, value) 
            except:
                pass

        if not self._archive_dict:
            print 'WARNING: No Archived Data'
        if not self._autosave_dict:
            print 'WARNING: No Autosave Data'

    def show_records(self, attrs=None, expand=True, prefix=None):
        """Show all additional records associated with the IMS motor.
        """
        if not attrs:
            attrs = self._device_sets.keys()
            attrs.sort()
        else:
            attrs = [attr for attr in attrs if attr in self._device_sets]

        for attr in attrs:
            if prefix:
                alias = '.'.join([prefix, attr])
            else:
                alias = attr
           
            try:
                rec = getattr(self, attr)
                rec.show_records(expand=expand, prefix=alias)
            except:
                pass

    def __getattr__(self, attr):
        if attr in self._attrs:
            return LCLS_Ioc._cfg['iocs'][self._name].get(attr)
        if attr == 'IOC':
            return psdevice.get_device(self.IOCPV)
        if attr == 'PVS':
            devices = {pv: item['pvbase'] for pv, item in self._device_sets.items()}
            return lcls_devices.EpicsDeviceSet(self._name, devices)

    def __dir__(self):
        all_attrs = set(self._attrs + ['IOC','PVS'] +
                        self.__dict__.keys() + dir(Sioc))
        return list(sorted(all_attrs))

    def __str__(self):
        item = LCLS_Ioc._cfg['iocs'][self._name]
        return '< {id} on {host} {port} from {dir} >'.format(**item)

    def __repr__(self):
        return self.__str__()


def get_alias_dict(pvbase):
    """Return dictionary of devices from the input pvbase.
    """
    devices = {}
    for device in LCLS_Ioc._cfg['pv']['ioc']:
        if device and pvbase in device:
            alias = device
            if alias.startswith(pvbase):
                alias = alias.replace(pvbase,'').lstrip(':')
            
            alias = alias.replace(':','_')
            if alias and alias[0].isdigit():
                alias = 'n'+alias
        
            devices[alias] = device
    
    return devices
    
def format_alias(attr):
    """Return an appropriate python alias from the input.
       i.e., replace ':' and '-' in pvs and iocs with '_'
    """
    alias = attr.replace(':','_').replace('-','_')
    if alias and alias[0].isdigit():
        alias = 'n'+alias

    return alias

def get_record_dict(pvbase):
    if not LCLS_Ioc._cfg:
        lcls_ioc = LCLS_Ioc(quiet=True)

    pvbase = pvbase.rstrip(':').rstrip('.')
    return LCLS_Ioc._cfg['pv']['records'].get(pvbase, {})

def get_rtyp(pvbase, connect=False, quiet=True, connection_timeout=0.5):
    """Return the record type (RTYP) of a pv.
       First checks the dictionary of all pvs from the IOC.pvlist info 
       retained in the Ioc class, and if not available (e.g., accelrator pvs),
       connects to the pv and returns the RTYP.
    """
    if not LCLS_Ioc._cfg:
        lcls_ioc = LCLS_Ioc(quiet=quiet)
    
    if not connect:
        rtyp =  LCLS_Ioc._cfg['pv']['rtyp'].get(pvbase) 
   
    # correct mistake of 'or not rtyp' instead of 'or rtyp'
    if connect or not rtyp:
        try:
            epicsPV = smartPv.get_pv(pvbase+'.RTYP',connection_timeout=0.05)
            rtyp = epicsPV.get()
            if not quiet:
                print 'Epics get {:} rtyp = {:}'.format(pvbase,rtyp)

        except pyca.pyexc:
            rtyp = None

    return rtyp

def get_iocpv(attr):
    """Return the iocAdmin IOCPV base for a pv.
       Used in epics screens.
    """
    if not LCLS_Ioc._cfg:
        lcls_ioc = LCLS_Ioc(quiet=True)

    return  LCLS_Ioc._cfg['pv']['iocpv'].get(attr) 

def get_ioc(attr):
    """Return ioc object for a pv or ioc name
    """
    if not LCLS_Ioc._cfg:
        lcls_ioc = LCLS_Ioc(quiet=True)

    if attr in LCLS_Ioc._cfg['iocs']:
        return Sioc(attr)

    pvbase = attr.split('.',1)[0]
    if not get_rtyp(pvbase):
        pvbase = get_record_dict(attr)
        if pvbase:
            pvbase = pvbase.values()[0]

    pvbase = LCLS_Ioc._cfg['pv']['ioc'].get(pvbase,pvbase)

    return Sioc(pvbase)

def show_pv_status(pvbase):
    """Show the status of a pv.
    """
    pvioc = get_ioc(pvbase)
    if pvioc:
        pvioc.show_info()
        print '-'*80
        pv = psdevice.get_device(pvbase)    
        if pv:
            if hasattr(pv, 'show_log'):
                pv.show_log()
            else:
                pv.show_info()

def show_ioc_status(iocname):
    """Show the status of an ioc.
    """
    try:
        sioc = get_ioc(iocname)
        sioc.show_info()
    except:
        print iocname, 'is not a known ioc'

def initArgs():
    """Initialize argparse arguments.
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help='Input')
    parser.add_argument("launchtype", nargs='?', default=None, help='Input2')
    parser.add_argument("-p", "--pv", type=str, 
                        help='Instrument')
    parser.add_argument("-i", "--instrument", type=str, default='', 
                        help='Instrument')
    parser.add_argument("-s", "--station", type=int, 
                        help='Station')
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

    if args.pv:
        pvbase = args.pv
    else:
        if ':' in inputname:
            pvbase = inputname
            if not instrument:
                instrument = pvbase.split(':')[0]
        elif '-' in inputname:
            iocname = inputname
        else:
            print 'Unknown input'

    ioc = Ioc(quiet=True, instrument=instrument)
    try:
        if iocname:
            sioc = get_ioc(iocname)
            if launchtype.lower() == 'iocpv':
                print sioc.IOCPV
            elif launchtype:
                print getattr(sioc.Ioc, launchtype)
            else:
                show_ioc_status(iocname)
        
        elif pvbase:
            pv = psdevice.get_device(pvbase)    
            if launchtype.lower() == 'iocpv':
                print pv.ioc.IOCPV    
            else:
                show_pv_status(pvbase)

    except:
        print ''


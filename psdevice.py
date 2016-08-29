#import epics
import os
import imp
import traceback
import sys
import time

import psioc 
import psutils

motor_dict = {
        'ims':    {'desc':   'IMS Motor Record',
                   'module': 'ims',
                   'class':  'IMS'},
        'motor':  {'desc':   'LCLS Version of Motor Record',
                   'module': 'motor_pcds',
                   'class':  'Motor'},
        'xps8p':  {'desc':   'Newport XPS Record',
                   'module': 'newport',
                   'class':  'Newport'},
        'arcus':  {'desc':   'Piezo PMC 100 Motor Record',
                   'module': 'pmc100',
                   'class':  'Arcus'},
        'mmca':   {'desc':   'Piezo MMC 100 Motor Record',
                   'module': 'mmca',
                   'class':  'Mmca'},
        }

def new_device(base, attrs={}, records={}, delim='', 
                module=None, path='', name='',
                device_set=True, 
                **kwargs):
    """Load a fresh instance of a new device.  Overwrites old device with same name.
         module: optional module name instead of defaults
         path:   optional path name -- e.g., ~me/devices/myims.py
         name:   optional name of module class:
    """  
    
    from devices.lcls_records import lcls_record
    import lcls_devices
    import devices
    if not psioc.LCLS_Ioc._cfg:
        ioc = psioc.LCLS_Ioc(quiet=True)
  
    rtyp = psioc.get_rtyp(base, connect=True)

    if module:
        psutils.import_module(module, path)
        if not name:
            name = module
            
        try:
            device_class =  getattr(getattr(psutils,module),name)
        except:
            device_class =  getattr(getattr(psutils,module),name.capitalize())
    else:
        device_class = None

    if rtyp:
        if rtyp in motor_dict:
            if not device_class:
                minfo = motor_dict[rtyp]
                device_class = getattr(devices, minfo['class'])
            
            epics_device = device_class(base, records=records)
        
        else:
            #print 'loading', base, records
            epics_device = lcls_record(base, records=records)
    
    else:
        if device_set:
            if not records:
                records = psioc.get_record_dict(base)
            
            base_name = base.replace(':','_')
            if not device_class:
                device_class = lcls_devices.EpicsDeviceSet
            
            epics_device = device_class(base_name, records) 
        
        else:
            aliases = {alias: record.replace(base+':', '') for alias, record in records.items()}
            if not device_class:
                device_class = lcls_devices.Device
            
            epics_device = epics_device(base, records=records,aliases=aliases,delim=delim,mutable=False) 

    return epics_device

class IocDevices(object):
    """Collection of IOC Devices.
       Use _get_device as a functional interface to the class global dictionary
       where the devices are stored.
    """
    _devices = {}
    _aliases = {}

    def __init__(self):
        if not psioc.LCLS_Ioc._cfg:
            ioc = psioc.LCLS_Ioc(quiet=True)
        
    def add_device(self, base, alias=None, **kwargs):
        if not alias:
            alias = base.replace(':','_')

        self._aliases.update({alias: base})
        self._devices.update({base: new_device(base, **kwargs)})

    def get_device(self, attr, **kwargs):
        if attr in self._aliases:
            attr = self._aliases[attr]
        
        if attr not in self._devices:
            self.add_device(attr, **kwargs)

        return self._devices.get(attr)

    def __getattr__(self, attr):
        if attr in self._aliases:
            return self.get_device(attr)

    def __dir__(self):
        all_attrs = set(self._aliases.keys() +
                        self.__dict__.keys() + dir(IocDevices))
        return list(sorted(all_attrs))

def get_device(base, reload=False, **kwargs):
    """Get an epics device from the IocDevices storage class.
    """
    if base in IocDevices._aliases:
        base = IocDevices._aliases[base]

    if base in IocDevices._devices and not reload:
        return IocDevices._devices.get(base)
    
    else:
        ioc_devices = IocDevices()
        return ioc_devices.get_device(base, **kwargs)


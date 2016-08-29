__doc__ = """
pscontrol packge for LCLS Instrument Controls:

== Functions:

    get_device:  Returns an epics device from a base PV name.
                 A device is a collection of the fields for an epics record
                 as well as other records that share the base pv name.
                 If the base pv name is not a record, then a collection
                 of records that share the base pv name is returned.

    get_ioc:     Returns an ioc class from the ioc name.
                 The ioc class contains the information from the iocmanager
                 as well as the iocadmin epics device and all of the 
                 epics devices in the ioc.

== Classes:

    Ioc:  iocmanager interface provides all of the ioc information in a 
          tab accessible class.  

    Instrument:  Epics devices organized according as sets.

    Daq:  Interface to daq.

    Ami:  Tab accessible ami interface organized according to aliases 
          as defined in daq (i.e., according to epicsArch file)

    Elog:  Interface to LCLS experiment and Instrument elogs.

    Message: Message handler including posting to elog.

"""

import sys
import time

from blutil import epicsarchive_new

from . import psmessage
from . import lcls_devices
from . import elog
from . import psioc
from . import psdevice

#from .psdevice import get_device
#from .psioc import Ioc, get_ioc 

from . import psami
from . import psdaq

# get epics device from pv
get_device = psdevice.get_device
# get pv information from class based on iocManager config
get_ioc = psioc.get_ioc
get_iocpv = psioc.get_iocpv
get_rtyp = psioc.get_rtyp

# Show status of ioc and pv functions
show_ioc_status = psioc.show_ioc_status
show_pv_status = psioc.show_pv_status 

Ioc = psioc.Ioc
Device = lcls_devices.Device
Instrument = lcls_devices.EpicsSets 
Daq = psdaq.Daq
Ami = psami.Ami

Message = psmessage.Message
Elog = elog.elog



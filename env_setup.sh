#!/bin/bash

unset PYTHONPATH
unset LD_LIBRARY_PATH
#export PYTHONPATH=
#export PSPKG_ROOT=/reg/common/package
#export PSPKG_RELEASE=psp-2.1.0
#source $PSPKG_ROOT/etc/set_env.sh
#source "/reg/g/pcds/setup/pathmunge.sh"

export EPICS_CA_MAX_ARRAY_BYTES=8000000
export PSPKG_ROOT=/reg/g/pcds/pkg_mgr

export PSPKG_RELEASE="mfx-dev"
source $PSPKG_ROOT/etc/set_env.sh

.  /reg/g/psdm/etc/ana_env.sh

HUTCH="cxi"
export DAQREL=/reg/g/pcds/dist/pds/cxi/current
#export AMIREL=/reg/g/pcds/dist/pds/ami-current
export AMIREL=/reg/g/pcds/dist/pds/cxi/ami-current

# Still need pyepics until completely get rid of it for epics.ca 
PYTHONPATH=$PYTHONPATH:~koglin/lib/python

PYTHONPATH=$PYTHONPATH:~koglin/package/trunk
PYTHONPATH=$PYTHONPATH:${DAQREL}/tools/procmgr:${DAQREL}/build/pdsapp/lib/x86_64-linux-opt:${AMIREL}/build/ami/lib/x86_64-linux

PYTHONPATH=$PYTHONPATH:/reg/g/pcds/pyps/apps/ioc/latest
#PYTHONPATH=$PYTHONPATH:~trendahl/Workarea/blutil
#PYTHONPATH=$PYTHONPATH:~trendahl/Workarea/blutil/blutil
PYTHONPATH=$PYTHONPATH:/reg/neh/home/trendahl/Workarea/pynetconfig
#pythonpathmunge "/reg/neh/home/trendahl/Workarea/pynetconfig"
PYTHONPATH=$PYTHONPATH:/reg/g/pcds/pyps/config/$HUTCH
#PYTHONPATH=$PYTHONPATH:~koglin/package/trunk
#PYTHONPATH=~koglin/package/trunk/pscontrol:~koglin/package/trunk/blutil:$PYTHONPATH




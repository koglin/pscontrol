#!/bin/sh

while getopts ":i:h" opt; do
  case $opt in
    i)
      echo "-i use instrument = $OPTARG" >&2
      INSTRUMENT=`echo $OPTARG | awk '{print toupper($0)}'`
      shift
      shift
      ;;
    h)
      printhelp=1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
    *)
      echo "Other option $opt"
      ;;
  esac
done

GetHostInstrument(){
  IP=`/sbin/ifconfig | /bin/grep 'inet addr:' | /bin/grep -v '127.0.0.1'| /bin/cut -d: -f2 | /bin/awk '{ print $1 }'`
  SUBNET=`echo $IP | /bin/cut -d. -f3`
  export MGT_SUBNET=24
  export CDS_SUBNET=35
  export FEE_SUBNET=36
  export AMO_SUBNET=37
  export XPP_SUBNET=38
  export SXR_SUBNET=39
  export TST_SUBNET=42
  export XCS_SUBNET=43
  export CXI_SUBNET=44
  export MEC_SUBNET=45
  export THZ_SUBNET=57

  case $SUBNET in
    $MGT_SUBNET)
      INSTRUMENT=MGT
      ;;
    $CDS_SUBNET)
      INSTRUMENT=CDS
      ;;
    $FEE_SUBNET)
      INSTRUMENT=FEE
      ;;
    $AMO_SUBNET)
      INSTRUMENT=AMO
      ;;
    $XPP_SUBNET)
      INSTRUMENT=XPP
      ;;
    $SXR_SUBNET)
      INSTRUMENT=SXR
      ;;
    $TST_SUBNET)
      INSTRUMENT=TST
      ;;
    $XCS_SUBNET)
      INSTRUMENT=XCS
      ;;
    $CXI_SUBNET)
      INSTRUMENT=CXI
      ;;
    $MEC_SUBNET)
      INSTRUMENT=MEC
      ;;
    $THZ_SUBNET)
      INSTRUMENT=THZ
      ;;
    *)
#      echo "Unrecognized machine -- defaultint to CXI" 
#      echo "Specify a different instrument with -i instrument option for this machine with IP=$IP"
      INSTRUMENT=CXI
      ;;
  esac
  echo $INSTRUMENT
}
export -f GetHostInstrument


EDM_MACROS=$2
EDM_SCREEN=$1
: ${EDM_MACROS:="none=none"}
: ${INSTRUMENT:=`GetHostInstrument`}
instrument=`echo $INSTRUMENT | awk '{print tolower($0)}'`

#export EPICS_SITE_TOP=/reg/g/pcds/package/epics/3.14
#source $EPICS_SITE_TOP/tools/current/bin/epicsenv.sh

source /reg/g/pcds/setup/epicsenv-3.14.12.sh

export EPICS_CA_MAX_ARRAY_BYTES=8000000

export PCDS_EDMS=/reg/g/pcds/package/epics/3.14/screens/edm
export EDMDATAFILES=.:${PCDS_EDMS}/xps8:${PCDS_EDMS}/ims:/reg/g/pcds/package/epics/3.14-dev/screens/edm/cxi/current/pcds_motionScreens
export DEVICE_CONFIG_TEMPLATE_DIR=/reg/g/pcds/controls/device_config/ims_templates
export DEVICE_CONFIG_TEMPLATE_DEFAULT=ims_config.tmp
export DEVICE_CONFIG_DIR=/reg/neh/operator/mecopr/device_config/ims
export PATH=$PATH:/reg/g/pcds/controls/device_config

cd /reg/g/pcds/package/epics/3.14-dev/screens/edm/$instrument/current

edm -eolc -x -m $EDM_MACROS $EDM_SCREEN &



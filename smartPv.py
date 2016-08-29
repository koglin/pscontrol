import numpy
import time
import psp.Pv

from blutil.epicsarchive_new import EpicsArchive
"""
A module that wraps the psp PV class, adding some high level functions.
"""

def get_pv(pvname,timeout=1.0,**kws):
    """
    Return a smartPv object.
    """
    thispv = None
    if pvname in psp.Pv.pv_cache.keys():
        thispv = psp.Pv.pv_cache[pvname]

    if thispv is None:
        thispv = SmartPv(pvname,**kws)
        thispv.wait_for_connection(timeout=timeout)
        if not thispv.isconnected:
            print 'Can not connect to %s' %pvname
    return thispv

class SmartPv(psp.Pv.Pv):
    """
    A class to wrap the psp Pv object.
    """
    def __init__(self,pvname,connect=True,callback=None,
            connection_callback=None,connection_timeout=None):

        self.connection_timeout = connection_timeout
        psp.Pv.Pv.__init__(self,pvname)
        if connect:
            self.wait_for_connection(timeout=self.connection_timeout)

    def wait_for_connection(self,timeout=None):
        """
        Connect to channel access, then wait for connection to complete or
        specified timeout. Return boolean of connection success.
        """
        self.connect()
        if timeout is None:
            timeout = self.connection_timeout
            if timeout is None:
                timeout = psp.Pv.DEFAULT_TIMEOUT
        start_time = time.time()
        while not (self._Pv__con_sem.isSet() 
                or time.time()-start_time < timeout):
            time.sleep(0.01)
        return self.isconnected


    def connect(self,timeout=None):
        """
        Instantiate channel access connection.
        """
        if not self.isconnected:
            if timeout is None:
                timeout = self.connection_timeout
            # psp/Py.py throws an exception at line 140 when timeout
            # similar to psdta/psdevice.py try a 2nd time to connect
            # but need to use try except because it is an exception instead
            # of connect method returning True/False
            try:
                super(SmartPv,self).connect(timeout=timeout)
                self.isconnected = True
            except:
                time.sleep(0.05)
                try:
                    super(SmartPv,self).connect(timeout=timeout)
                    self.isconnected = True
                except:
                    self.isconnected = False
                    print 'SmartPv.connect error' 

        return self.isconnected

    def disconnect(self):
        """
        Disconnect Pv from channel access.
        """
        self.isconnected = False
        super(SmartPv,self).disconnect()

    def get(self,count=None,as_string=False,with_ctrlvars=False,
            timeout=None,as_numpy=False,use_monitor=False):
        """
        Return the current value of the PV.

        Parameters:
            
            count (int): Limit the length of the array data returned.

            as_string (bool): Return value as str type. Default is False.

            as_numpy (bool): Convert array data to a numpy array before
                returning.

            timeout (float): Maxmimum time to wait for value to be recieved.

            use_monitor (bool): Use the current stored value, without calling
                making a new CA call.

        Returns:

            value : If the PV was available through channel access this will be
                the value of the PV as specified by the keyword arguements.
                Otherwise, a NoneType will be returned.
        """
        #If not use monitor,refresh value
        if not use_monitor:
            try:
                val = super(SmartPv,self).get(count=count,as_string=as_string,ctrl=with_ctrlvars)
            except Exception as e:
                if psp.Pv.DEBUG!=0:
                    print e
                return None
        
        val = self.value
        if not as_numpy:
            return val

        if count is None:
            try:
                count = len(val)
            except TypeError:
                count = 1

        if not isinstance(val,numpy.ndarray):
            if count==1:
                val = [val]
            val = numpy.array(val)
        elif isinstance(val,numpy.ndarray):
            val = list(val)

        if count < len(val):
            val = val[:count]
        return val

 
    def put(self,value,wait=False,timeout=30.0,
            callback=None,callback_data=None):
        """
        Set value for PV.

        wait (bool): Wait for value to change before returning.

        timeout (float): Maximum time to wait for completion.

        callback (func): Function to be run upon put completion.

        callback_data : Data to be passed to the callback function.
        """
        if not self.wait_for_connection():
            if psp.Pv.DEBUG:
                print 'Unable to connect to {:}'.format(self.name)
            return None

        ret = super(SmartPv,self).put(value,timeout=timeout)

        #Wait for value to be set
        if wait:
            self.wait_for_value(value,timeout=timeout)
        #Run acceptable callback
        if callback and hasattr(callback,'__call__'):
            callback(callback_data)
        return ret
            
   
    def run_callback(self,index):
        """ 
        Run a monitor callback right now, even if the value has not
        changed. Useful for debugging. Specify callback by index.
        """
        cb = self.mon_cbs[index]
        cb(None)
    
    def run_callbacks(self):
        """
        Run all monitor callbacks regardless of whether PV value has changed.
        """
        for index in self.mon_cbs.keys():
            self.run_callback()

    def clear_callbacks(self):
        """
        Remove all monitor callbacks.
        """
        for index in self.mon_cbs.keys():
            self.del_monitor_callback(index)

    def in_archive(self):
        """
        Return a boolean if the PV is in the new EpicsArchiver.
        """
        arch = EpicsArchive()
        pvName= arch.search_pvs(self.name,do_print=False)
        if pvName:
            return True
        else:
            return False
   
    def changed_since(self,start=1,end=None,unit='days',at_time=None):
        """
        Return True or False depending on if the PV has changed in the
        specified time period. Specifying the start time has the same rules as
        in the archived_values function.
        """
        t,v = self.archived_values(start=start,end=end,unit=unit,
                                    at_time=at_time,two_lists=True,
                                    raw=True)
        if len(set(v+[self.get()])) == 1:
            return False

        #Make sure values outside of range are not included
        arch = EpicsArchive()
        start,end = arch._json_args(start,end,unit)
        valid = [self.value]
        start,end = [time.mktime(date+[0,0,0]) for date in [start,end]]
        for i,timestamp in enumerate(t):
            if start <= timestamp < end:
                valid.append(v[i])

        if len(set(valid)) != 1:
            return True

        return False
        
    def archived_values(self,start=30,end=None,unit="days",
                        at_time=None,two_lists=False,
                        raw=False,plot=False):
        """
        Access the archiver to view past PV values.

        The start and end time can be specified in three ways. First, a python
        Datetime object. Second, an integer that is a point in the past with
        units given by the unit keyword. Third, an array matching the
        following format : [year,month,day,hour,minute,second]. If the start
        and end times are specifically requested this way, a list of values
        with a timestamp and value are returned for all archived values within
        the time range. If you are looking for a single point in time, you can
        use the at_time keyword to find the closest previous archived value.

        Parameters

            start : The start of the archive time period.

            end   : The end of the archvie time period.

            unit  : The units used to interpret the time if integers are given.

            at_time : A specific time to look for in the archiver, instead of a
                period.

            two_lists : Seperate the times and values found in to different
                lists.

            raw : Return the time as the seconds since the epoch. Default is
                False.

            plot : Plot the found archived data using Matplotlib
        """
        arch = EpicsArchive()
        
        #If specific time requested
        if at_time:
            start,end=arch._json_args(at_time,at_time,unit=unit)
            end[5] += 1

        if plot: 
            arch.plot_points(PV=self.name,start=start,end=end,unit=unit)

        pts = arch.get_points(PV=self.name,start=start,end=end,
                               unit=unit,two_lists=two_lists,raw=raw)

        if at_time:
            pts = pts[-1]

        return pts
    @property
    def pvname(self):
        """
        Return name of PV.
        """
        return self.name


    def __del__(self):
        """
        Disconnect before deleting.
        """
        try:
            self.disconnect()
        except:
            pass

from smartPv import get_pv,SmartPv
import time

class Device(object):

    _prefix = None
    _delim = ''
    _pvs = {}
    _init = False
    _aliases = {}
    _mutable = True
    _nonpvs = ('_prefix', '_pvs', '_delim', '_init', '_aliases',
               '_mutable', '_nonpvs')

    def __init__(self, prefix='', attrs=None,
                 nonpvs=None, delim='', timeout=None,
                 mutable=True, aliases=None):
        self._nonpvs = list(self._nonpvs)
        self._delim = delim
        self._prefix = prefix + delim
        self._pvs = {}
        self._mutable = mutable
        if aliases is None:
            aliases = {}
        self._aliases = aliases
        if nonpvs is not None:
            for npv in nonpvs:
                if npv not in self._nonpvs:
                    self._nonpvs.append(npv)

        if attrs is not None:
            for attr in attrs:
                self.PV(attr, connect=False,
                        connection_timeout=timeout)

        if aliases:
            for attr in aliases.values():
                if attrs is None or attr not in attrs:
                    self.PV(attr, connect=False,
                            connection_timeout=timeout)

        self._init = True
    

    def PV(self, attr, connect=True,timeout=0.5,**kw):
        """return smartPV for a device attribute"""
        if attr in self._aliases:
            attr = self._aliases[attr]

        if attr not in self._pvs:
            pvname = attr
            if self._prefix is not None:
                pvname = "%s%s" % (self._prefix, attr)
            self._pvs[attr] = get_pv(pvname,timeout=timeout,**kw)
   
        if connect and not self._pvs[attr].isconnected:
            self._pvs[attr].wait_for_connection(timeout=timeout)
        return self._pvs[attr]

    def add_pv(self, pvname, attr=None, **kw):
        """add a PV with an optional attribute name that may not exactly
        correspond to the mapping of Attribute -> Prefix + Delim + Attribute
        That is, with a device defined as
        >>> dev = Device('XXX', delim='.')

        getting the VAL attribute
        >>> dev.get('VAL')   # or dev.VAL

        becomes   'caget(XXX.VAL)'.  With add_pv(), one can add a
        non-conforming PV to the collection:
        >>> dev.add_pv('XXX_status.VAL', attr='status')

        and then use as
        >>> dev.get('status')  # or dev.status

        If attr is not specified, the full pvname will be used.
        """
        if attr is None:
            attr = pvname
        self._pvs[attr] = get_pv(pvname, **kw)
        return self._pvs[attr]

    def put(self, attr, value,timeout=10):
        """put an attribute value,
        optionally wait for completion or
        up to a supplied timeout value"""
        thispv = self.PV(attr)
        thispv.wait_for_connection()
        return thispv.put(value, timeout=timeout)

    def get(self, attr, as_string=False,count=None,timeout=None):
        """get an attribute value,
        option as_string returns a string representation"""
        return self.PV(attr).get(as_string=as_string, count=count,timeout=timeout)


    def save_state(self):
        """
        Return a dictionary of the values of all
        current attributes
        """
        out = {}
        for key in self._pvs:
            out[key] = self._pvs[key].get()
        return out

    @property
    def archived_pvs(self):
        """
        Return a list of PV's found in the new Epics Archiver.
        """
        arch = [] 
        for key in self._pvs:
            pv = self.PV(key)
            if pv.in_archive():
                arch.append(key)
        return arch

    def archived_values(self,attrs=None,**kws): 
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

            attrs : A list of PV's to include in the Archiver query.

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
        
        out = {}
       
        if not attrs:
            attrs = self.archived_pvs
        
        for key in attrs:
            pv = self.Pv(key)
            out[key] = pv.archived_values(**kws)
        return out

    def changed_since(self,attr=None,start=1,end=None,unit='days',at_time=None):
        """ 
        Return a dictionary of True or False values depending on if the PV
        has changed in the specified time period. Specifying the start time has
        the same rules as in the archived_values function.
        """
        
        if not attrs:
            attrs = self.archived_pvs
        changed = {}
        
        for key in attrs:
            pv = self.Pv(key)
            changed[key]=pv.changed_since(start=start,end=end,
                                    unit=unit,at_time=at_time)
        return changed


    def restore_state(self, state):
        """restore a dictionary of the values, as saved from save_state"""
        for key, val in state.items():
            if key in self._pvs:
                self._pvs[key].put(val)

    def write_state(self, fname, state=None):
        """write save state  to external file.
        If state is not provided, the current state is used

        Note that this only writes data for PVs with write-access, and count=1 (except CHAR """
        if state is None:
            state = self.save_state()
        out = ["#Device Saved State for %s, prefx='%s': %s\n" % (self.__class__.__name__,
                                                                 self._prefix, time.ctime())]
        for key in sorted(state.keys()):
            if key in self._pvs:
                out.append("%s  %s\n" % (key, state[key]))
        fout = open(fname, 'w')
        fout.writelines(out)
        fout.close()


    def read_state(self, fname, restore=False):
        """read state from file, optionally restore it"""
        finp = open(fname, 'r')
        textlines = finp.readlines()
        finp.close()
        state = {}
        for line in textlines:
            if line.startswith('#'):
                continue
            key, val =  line[:-1].split(' ', 1)
            if key in self._pvs:
                state[key] = val
        if restore:
            self.restore_state(state)
        return state


    def get_all(self):
        """return a dictionary of the values of all
        current attributes"""
        return self.save_state()

    def add_callback(self, attr, callback, **kws):
        """add a callback function to an attribute PV,
        so that the callback function will be run when
        the attribute's value changes"""
        self.PV(attr).get()
        return self.PV(attr).add_monitor_callback(callback, **kws)

    def remove_callbacks(self, attr, index=None):
        """remove a callback function to an attribute PV"""
        if index:
            self.PV(attr).del_monitor_callback(index=index)


    def __getattr__(self, attr):
        if attr in self._aliases:
            attr = self._aliases[attr]
        if attr in self._nonpvs:
            return self.__dict__[attr]

        if attr in self._pvs:
            return self.get(attr)
        elif attr in self.__dict__:
            return self.__dict__[attr]
        elif self._init and self._mutable and not attr.startswith('__'):
            pv = self.PV(attr, connect=True)
            if pv.isconnected:
                return pv.get()

        raise AttributeError('%s has no attribute %s' % (self.__class__.__name__,
                                                         attr))

    def __setattr__(self, attr, val):
        if attr in self._aliases:
            attr = self._aliases[attr]

        if attr in self._nonpvs:
            self.__dict__[attr] = val
        elif attr in self._pvs:
            self.put(attr, val)
        elif self._init and self._mutable and not attr.startswith('__'):
            try:
                self.PV(attr)
                self.put(attr, val)
            except:
                raise AttributeError('%s has no attribute %s' % (self.__class__.__name__,
                                                                 attr))
        elif attr in self.__dict__:
            self.__dict__[attr] = val
        elif self._init:
            raise AttributeError('%s has no attribute %s' % (self.__class__.__name__,
                                                             attr))

    def __dir__(self):
        # there's no cleaner method to do this until Python 3.3
        all_attrs = set(self._aliases.keys() + self._pvs.keys() +
                        list(self._nonpvs) + 
                        self.__dict__.keys() + dir(Device))
        return list(sorted(all_attrs))

    def __repr__(self):
        "string representation"
        pref = self._prefix
        if pref.endswith('.'):
            pref = pref[:-1]
        return "<Device '%s' %i attributes>" % (pref, len(self._pvs))


    def pv_property(attr, as_string=False, wait=False, timeout=10.0):
        return property(lambda self:     \
                        self.get(attr, as_string=as_string),
                        lambda self,val: \
                        self.put(attr, val, wait=wait, timeout=timeout),
                        None, None)

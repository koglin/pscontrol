import elog

class Message(object):
    """Message class for printing messages and posting messages to the elog.
    """

    _message = []
    _message_history = []
    _max_messages = 100
    _quiet = False

    def __init__(self, *args, **kwargs):
        """Initialize message
           append: append to previous if True.
           quiet:  do not print each added line if True
        """
        if kwargs.get('append'):
            self.add(*args, **kwargs)
        else:
            self.new(*args, **kwargs)

        if 'quiet' in kwargs:
            self._quiet = kwargs.get('quiet')

    def post(self, show=True, **kwargs):
        """Post message to elog.
            name = name of elog.
           
           Message will be printed unless show=False
        """
        if show:
            self.__repr__()
        
        elog.post(self.__repr__(), **kwargs)

    def instrument_post(self, show=True, **kwargs):
        """Post message to instrument elog.
           Message will be printed unless show=False
           Equivalent to post function with name='instrument'
        """        
        if show:
            self.__repr__()
        
        elog.instrument_post(self.__repr__(), **kwargs)

    def add(self, *args, **kwargs):
        """Add a line to the message.
           By default the message is printed (quiet=False to suppress printing).
        """
        if args:
            if len(args) > 1:
                lines = args
            else:
                lines = [args[0]]
            
            for line in lines:
                if not kwargs.get('quiet') and not self._quiet:
                    print line
                self._message.append(line)

    def new(self, *args, **kwargs):
        """Add last message to _message_history and start a new message. 
        """
        if self._message:
            self._message_history.append(self._message[:])
            if len(self._message_history) > self._max_messages:
                self._message_history.pop(0)

        self._message[:] = []
        self.add(*args, **kwargs)

    def show(self, **kwargs):
        print self.__str__()

    def __len__(self):
        return len(self._message)

    def __iter__(self):
        return iter(self._message)

    def __call__(self, *args, **kwargs):
        self.add(*args, **kwargs)

    def __str__(self):
        return '\n'.join(self._message)

    def __repr__(self):
        return self.__str__() 



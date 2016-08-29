import devices

class MyIms(devices.ims.IMS):
    """My version of IMS
    """

    def __init__(self, *args, **kwargs):

        devices.ims.IMS.__init__(self, *args, **kwargs)

    def myprint(self, attrs=None):
        print 'My Print attrs:'
        if not attrs:
            attrs = self._fields

        for attr in attrs:
            print attr, self.get(attr)

    def fooprint(self):
        print 'foo'


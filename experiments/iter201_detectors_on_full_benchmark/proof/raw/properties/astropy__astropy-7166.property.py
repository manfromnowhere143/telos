from astropy.utils.misc import InheritDocstrings, is_public_member

class Base(metaclass=InheritDocstrings):
    @property
    def status(self):
        """Base property documentation."""
        return getattr(self, "_status", None)

class Child(Base):
    @property
    def status(self):
        return getattr(self, "_status", None)

    @status.setter
    def status(self, value):
        self._status = value

member_is_public = is_public_member("status", Child.__dict__["status"])
inherits_doc = Child.status.__doc__ == Base.status.__doc__

print("PROP_PASS" if member_is_public and inherits_doc else "PROP_FAIL")

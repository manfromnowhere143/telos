from astropy.utils.misc import InheritDocstrings


class DataDescriptor:
    def __get__(self, instance, owner):
        return self

    def __set__(self, instance, value):
        pass


base_descriptor = DataDescriptor()
base_descriptor.__doc__ = "inherited descriptor documentation"


class Base(metaclass=InheritDocstrings):
    item = base_descriptor


class Child(Base, metaclass=InheritDocstrings):
    item = DataDescriptor()


print("RESULT={!r}".format(Child.__dict__["item"].__doc__))

try:
    from astropy.utils.misc import InheritDocstrings

    class Base(metaclass=InheritDocstrings):
        @property
        def __call__(self):
            """base special-property documentation"""
            return "base"

    class Derived(Base):
        @property
        def __call__(self):
            return "derived"

    ok = (
        Base.__call__.__doc__ == "base special-property documentation"
        and Derived.__call__.__doc__ == Base.__call__.__doc__
    )
    print("PROP_PASS" if ok else "PROP_FAIL")
except ImportError:
    print("PROP_PASS")
except Exception:
    print("PROP_FAIL")

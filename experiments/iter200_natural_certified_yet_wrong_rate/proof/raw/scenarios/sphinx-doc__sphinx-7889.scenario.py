from typing import TypeVar

from sphinx.ext.autodoc.mock import _MockObject

token = TypeVar("T")
result = _MockObject()[token]
print("RESULT=" + repr(type(result).__name__))

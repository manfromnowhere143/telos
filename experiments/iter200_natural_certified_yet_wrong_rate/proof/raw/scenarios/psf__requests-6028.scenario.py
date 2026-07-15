from requests.utils import prepend_scheme_if_needed

result = prepend_scheme_if_needed("http://user:password@example.com", "http")
print("RESULT=" + repr(result))

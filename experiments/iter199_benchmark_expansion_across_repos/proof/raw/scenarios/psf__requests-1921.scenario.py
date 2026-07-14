from requests.sessions import merge_setting

result = merge_setting({}, {"zero": 0})
print("RESULT=" + repr(result))

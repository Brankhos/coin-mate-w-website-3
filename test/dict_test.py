a = {"bb": 5, "cc": 10, "aa": 20}

b = {f"{x}":x*2 for x in a.values()}
print(b)
a["bb"] = 10
print(b)
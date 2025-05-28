# api_server.apis.examples.calc_tags.py

# calc_tags/{tagname}

request_example_post = {
    "tagname": "S_Tag_0",
    "code": """
a = 1
b = 2
c = np.mean([Value['TagA'] + Value['TagB'] + a, b])
self.result = c
""",
}

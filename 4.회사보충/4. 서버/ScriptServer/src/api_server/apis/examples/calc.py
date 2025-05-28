# api_server.apis.examples.tags.py

# tags/{tagname}/setting

validation_example = {"S_TagA": {"Value": {"TagA": 10, "TagB": 20}}}


tagnames = [f"S_Tag_{i}" for i in range(10)]
request_example = {
    tagname: {
        "Value": {"TagA": 10, "TagB": 20},
    }
    for tagname in tagnames
}

# request_example = {
#     "S_TagA":{
#         "Value":{
#             "TagA":10,
#             "TagB":20,
#         },
#         "HValue":{
#         }
#     },
#     "S_TagB":{
#         "Value":{
#             "TagA":100,
#             "TagB":200
#         },
#         "HValue":{
#             "TagA":[10,20,30,40],
#             "TagB":[100,200,300,400]
#         }
#     }
# }

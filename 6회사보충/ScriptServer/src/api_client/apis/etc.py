# etc.py


from api_client.apis.session import APISession


class ETCAPI(APISession):
    def __init__(self):
        self.headers = {"Content-Type": "application/json-patch+json"}
        super().__init__()

    def get_root(self):
        path = "/"
        url = self.baseurl + path
        return self.request_get(url)

etc_api = ETCAPI()
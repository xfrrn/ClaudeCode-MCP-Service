# wechat_mcp/core/http_client.py
import requests


class HttpClient:
    def __init__(self) -> None:
        self.session = requests.Session()

    def get(self, url: str, **kwargs):
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.session.post(url, **kwargs)

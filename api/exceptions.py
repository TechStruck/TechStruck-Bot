
class CustomHTTPException(Exception):
    def __init__(self, response):
        self.response = response

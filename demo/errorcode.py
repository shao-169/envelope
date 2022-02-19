from django.conf import settings


class errorcode:
    def __init__(self, type):
        self.res = {}
        self.res['code'] = settings.ERRORCODE[type]['code']
        self.res['msg'] = settings.ERRORCODE[type]['msg']
        self.res['data'] = {}

    def get_status_code(self):
        return self.res

# from requests.auth import HTTPBasicAuth
import requests

class Client(object):
    IMPORT_SAVED_OBJECTS_PATH='api/saved_objects/_import'

    def __init__(self, host, port, http_auth, scheme, verify_certs=True, mount_path=None):
        self.host = host
        self.port = port or 5601
        self.http_auth = http_auth
        self.scheme = scheme or 'http'
        self.verify_certs = verify_certs
        self.mount_path = mount_path 
        if mount_path is None:
            self.mount_path = ''
        else:
            if not mount_path.startswith('/'):
                self.mount_path = "/{}".format(mount_path)

    def import_saved_objects(self, file, payload):
        headers = {'kbn-xsrf': 'true'}
        post = requests.request(
            'POST', 
            self.get_path(self.IMPORT_SAVED_OBJECTS_PATH),
            params=payload,
            headers=headers,
            auth=self.http_auth,
            verify=self.verify_certs,
            files={
                'file': file
                }
            )
        return post

    def get_path(self, url_path):
        return "%s://%s:%s%s/%s" % (self.scheme, self.host, self.port, self.mount_path, url_path)
from .compat import compat_cookiejar, compat_pickle


class ClientCookieJar(compat_cookiejar.CookieJar):
    """Custom CookieJar that can be pickled to/from strings
    """
    def __init__(self, cookie_string=None, policy=None):
        compat_cookiejar.CookieJar.__init__(self, policy)
        if cookie_string:
            if isinstance(cookie_string, bytes):
                self._cookies = compat_pickle.loads(cookie_string)
            else:
                self._cookies = compat_pickle.loads(cookie_string.encode('utf-8'))

    @property
    def auth_expires(self):
        for cookie in self:
            if cookie.name in ('ds_user_id', 'ds_user'):
                return cookie.expires
        return None

    @property
    def expires_earliest(self):
        """For backward compatibility"""
        return self.auth_expires

    def dump(self):
        return compat_pickle.dumps(self._cookies)

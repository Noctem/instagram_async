# Copyright (c) 2017 https://github.com/ping
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# -*- coding: utf-8 -*-

import logging
import hmac
import hashlib
import uuid
import re
import time
import random
import warnings

from asyncio import run
from datetime import datetime
from os.path import isfile
from ssl import create_default_context
from .errors import ErrorHandler, ClientError, ClientLoginRequiredError

from aiohttp import ClientSession, CookieJar, TCPConnector, ClientResponseError
from aiohttp.hdrs import ACCEPT_LANGUAGE, CONNECTION, USER_AGENT
from aiohttp.multidict import CIMultiDict

from .compat import jdumps, jloads
from .constants import Constants
from .endpoints import (
    AccountsEndpointsMixin, DiscoverEndpointsMixin, FeedEndpointsMixin,
    FriendshipsEndpointsMixin, LiveEndpointsMixin, MediaEndpointsMixin,
    MiscEndpointsMixin, LocationsEndpointsMixin, TagsEndpointsMixin,
    UsersEndpointsMixin, UploadEndpointsMixin, UsertagsEndpointsMixin,
    CollectionsEndpointsMixin, HighlightsEndpointsMixin,
    IGTVEndpointsMixin,
    ClientDeprecationWarning, ClientPendingDeprecationWarning,
    ClientExperimentalWarning
)

logger = logging.getLogger(__name__)
# Force Client deprecation warnings to always appear
warnings.simplefilter('always', ClientDeprecationWarning)
warnings.simplefilter('always', ClientPendingDeprecationWarning)
warnings.simplefilter('default', ClientExperimentalWarning)


class Client(AccountsEndpointsMixin, DiscoverEndpointsMixin, FeedEndpointsMixin,
             FriendshipsEndpointsMixin, LiveEndpointsMixin, MediaEndpointsMixin,
             MiscEndpointsMixin, LocationsEndpointsMixin, TagsEndpointsMixin,
             UsersEndpointsMixin, UploadEndpointsMixin, UsertagsEndpointsMixin,
             CollectionsEndpointsMixin, HighlightsEndpointsMixin,
             IGTVEndpointsMixin):
    """Main API client class for the private app api."""

    API_URL = 'https://i.instagram.com/api/{version}/'

    USER_AGENT = Constants.USER_AGENT
    IG_SIG_KEY = Constants.IG_SIG_KEY
    IG_CAPABILITIES = Constants.IG_CAPABILITIES
    SIG_KEY_VERSION = Constants.SIG_KEY_VERSION
    APPLICATION_ID = Constants.APPLICATION_ID

    def __init__(self, username, password, cookiejar=None, **kwargs):
        """

        :param username: Login username
        :param password: Login password
        :param kwargs: See below

        :Keyword Arguments:
            - **cookiejar**: Path of pickled cookiejar
            - **auto_patch**: Patch the api objects to match the public API. Default: False
            - **drop_incompat_key**: Remove api object keys that is not in the public API. Default: False
            - **timeout**: Timeout interval in seconds. Default: 15
            - **api_url**: Override the default api url base
            - **settings**: A dict of settings from a previous session
            - **on_login**: Callback after successful login
        :return:
        """
        self.username = username
        self.password = password
        self.auto_patch = kwargs.pop('auto_patch', False)
        self.drop_incompat_keys = kwargs.pop('drop_incompat_keys', False)
        self.api_url = kwargs.pop('api_url', None) or self.API_URL
        self.timeout = kwargs.pop('timeout', 15)
        self.on_login = kwargs.pop('on_login', None)
        self.logger = logger

        if cookiejar and isfile(cookiejar):
            cookies = CookieJar()
            cookies.load(cookiejar)
        else:
            cookies = None

        user_settings = kwargs.pop('settings', None) or {}
        self.uuid = (
            kwargs.pop('guid', None) or kwargs.pop('uuid', None) or
            user_settings.get('uuid') or self.generate_uuid(False))
        self.device_id = (
            kwargs.pop('device_id', None) or user_settings.get('device_id') or
            self.generate_deviceid())
        # application session ID
        self.session_id = (
            kwargs.pop('session_id', None) or user_settings.get('session_id') or
            self.generate_uuid(False))
        self.signature_key = (
            kwargs.pop('signature_key', None) or user_settings.get('signature_key') or
            self.IG_SIG_KEY)
        self.key_version = (
            kwargs.pop('key_version', None) or user_settings.get('key_version') or
            self.SIG_KEY_VERSION)
        self.ig_capabilities = (
            kwargs.pop('ig_capabilities', None) or user_settings.get('ig_capabilities') or
            self.IG_CAPABILITIES)
        self.application_id = (
            kwargs.pop('application_id', None) or user_settings.get('application_id') or
            self.APPLICATION_ID)

        # to maintain backward compat for user_agent kwarg
        custom_ua = kwargs.pop('user_agent', '') or user_settings.get('user_agent')
        if custom_ua:
            self.user_agent = custom_ua
        else:
            self.app_version = (
                kwargs.pop('app_version', None) or user_settings.get('app_version') or
                Constants.APP_VERSION)
            self.android_release = (
                kwargs.pop('android_release', None) or user_settings.get('android_release') or
                Constants.ANDROID_RELEASE)
            self.android_version = int(
                kwargs.pop('android_version', None) or user_settings.get('android_version') or
                Constants.ANDROID_VERSION)
            self.phone_manufacturer = (
                kwargs.pop('phone_manufacturer', None) or user_settings.get('phone_manufacturer') or
                Constants.PHONE_MANUFACTURER)
            self.phone_device = (
                kwargs.pop('phone_device', None) or user_settings.get('phone_device') or
                Constants.PHONE_DEVICE)
            self.phone_model = (
                kwargs.pop('phone_model', None) or user_settings.get('phone_model') or
                Constants.PHONE_MODEL)
            self.phone_dpi = (
                kwargs.pop('phone_dpi', None) or user_settings.get('phone_dpi') or
                Constants.PHONE_DPI)
            self.phone_resolution = (
                kwargs.pop('phone_resolution', None) or user_settings.get('phone_resolution') or
                Constants.PHONE_RESOLUTION)
            self.phone_chipset = (
                kwargs.pop('phone_chipset', None) or user_settings.get('phone_chipset') or
                Constants.PHONE_CHIPSET)
            self.version_code = (
                kwargs.pop('version_code', None) or user_settings.get('version_code') or
                Constants.VERSION_CODE)

        context = create_default_context()
        # set_ciphers cannot add or remove TLS 1.3 ciphers, but they will still be preferred if available
        # these are the ciphers supported by Liger in Instagram 107 when TLS 1.3 is disabled
        context.set_ciphers(
            'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:'
            'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES128-SHA:'
            'ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:AES128-GCM-SHA256:AES256-SHA:AES128-SHA')
        self.session = ClientSession(connector=TCPConnector(ssl=context, limit=Constants.MAX_CONNECTIONS),
                                     headers=self.default_headers, raise_for_status=True,
                                     trust_env=True, cookie_jar=cookies, conn_timeout=self.timeout)

        # ad_id must be initialised after cookie_jar/opener because
        # it relies on self.authenticated_user_name
        self.ad_id = (
            kwargs.pop('ad_id', None) or user_settings.get('ad_id') or
            self.generate_adid())

        if not cookies:
            if not self.username or not self.password:
                raise ClientLoginRequiredError('login_required', code=400)
            run(self.login())

        self.logger.debug(f'USERAGENT: {self.user_agent}')
        super().__init__()

    @property
    def settings(self):
        """Helper property that extracts the settings that you should cache
        in addition to username and password."""
        return {
            'uuid': self.uuid,
            'device_id': self.device_id,
            'ad_id': self.ad_id,
            'session_id': self.session_id,
            'cookie': self.cookie_jar.dump(),
            'created_ts': int(time.time())
        }

    @property
    def user_agent(self):
        """Returns the useragent string that the client is currently using."""
        return Constants.USER_AGENT_FORMAT.format(
            app_version=self.app_version,
            android_version=self.android_version,
            android_release=self.android_release,
            brand=self.phone_manufacturer,
            device=self.phone_device,
            model=self.phone_model,
            dpi=self.phone_dpi,
            resolution=self.phone_resolution,
            chipset=self.phone_chipset,
            version_code=self.version_code)

    @user_agent.setter
    def user_agent(self, value):
        """Override the useragent string with your own"""
        mobj = re.search(Constants.USER_AGENT_EXPRESSION, value)
        if not mobj:
            raise ValueError(f'User-agent specified does not fit format required: {Constants.USER_AGENT_EXPRESSION}')
        self.app_version = mobj.group('app_version')
        self.android_release = mobj.group('android_release')
        self.android_version = int(mobj.group('android_version'))
        self.phone_manufacturer = mobj.group('manufacturer')
        self.phone_device = mobj.group('device')
        self.phone_model = mobj.group('model')
        self.phone_dpi = mobj.group('dpi')
        self.phone_resolution = mobj.group('resolution')
        self.phone_chipset = mobj.group('chipset')
        self.version_code = mobj.group('version_code')

    @staticmethod
    def generate_useragent(**kwargs):
        """
        Helper method to generate a useragent string based on device parameters

        :param kwargs:
            - **app_version**
            - **android_version**
            - **android_release**
            - **brand**
            - **device**
            - **model**
            - **dpi**
            - **resolution**
            - **chipset**
        :return: A compatible user agent string
        """
        return Constants.USER_AGENT_FORMAT.format(
            app_version=kwargs.pop('app_version', None) or Constants.APP_VERSION,
            android_version=int(kwargs.pop('android_version', None) or Constants.ANDROID_VERSION),
            android_release=kwargs.pop('android_release', None) or Constants.ANDROID_RELEASE,
            brand=kwargs.pop('phone_manufacturer', None) or Constants.PHONE_MANUFACTURER,
            device=kwargs.pop('phone_device', None) or Constants.PHONE_DEVICE,
            model=kwargs.pop('phone_model', None) or Constants.PHONE_MODEL,
            dpi=kwargs.pop('phone_dpi', None) or Constants.PHONE_DPI,
            resolution=kwargs.pop('phone_resolution', None) or Constants.PHONE_RESOLUTION,
            chipset=kwargs.pop('phone_chipset', None) or Constants.PHONE_CHIPSET,
            version_code=kwargs.pop('version_code', None) or Constants.VERSION_CODE)

    @staticmethod
    def validate_useragent(value):
        """
        Helper method to validate a useragent string for format correctness

        :param value:
        :return:
        """
        mobj = re.search(Constants.USER_AGENT_EXPRESSION, value)
        if not mobj:
            raise ValueError(
                f'User-agent specified does not fit format required: {Constants.USER_AGENT_EXPRESSION}')
        parse_params = {
            'app_version': mobj.group('app_version'),
            'android_version': int(mobj.group('android_version')),
            'android_release': mobj.group('android_release'),
            'brand': mobj.group('manufacturer'),
            'device': mobj.group('device'),
            'model': mobj.group('model'),
            'dpi': mobj.group('dpi'),
            'resolution': mobj.group('resolution'),
            'chipset': mobj.group('chipset'),
            'version_code': mobj.group('version_code'),
        }
        return {
            'user_agent': Constants.USER_AGENT_FORMAT.format(**parse_params),
            'parsed_params': parse_params
        }

    def get_cookie_value(self, key, domain='.instagram.com'):
        try:
            return self.session.cookie_jar.filter_cookies(domain)[key].value
        except KeyError:
            return None

    @property
    def csrftoken(self):
        """The client's current csrf token"""
        return self.get_cookie_value('csrftoken')

    @property
    def token(self):
        """For compatibility. Equivalent to :meth:`csrftoken`"""
        return self.csrftoken

    @property
    def authenticated_user_id(self):
        """The current authenticated user id"""
        return self.get_cookie_value('ds_user_id')

    @property
    def authenticated_user_name(self):
        """The current authenticated user name"""
        return self.get_cookie_value('ds_user')

    @property
    def phone_id(self):
        """Current phone ID. For use in certain functions."""
        return self.generate_uuid(return_hex=False, seed=self.device_id)

    @property
    def timezone_offset(self):
        """Timezone offset in seconds. For use in certain functions."""
        return int(round((datetime.now() - datetime.utcnow()).total_seconds()))

    @property
    def rank_token(self):
        if not self.authenticated_user_id:
            return None
        return f'{self.authenticated_user_id}_{self.uuid}'

    @property
    def authenticated_params(self):
        return {
            '_csrftoken': self.csrftoken,
            '_uuid': self.uuid,
            '_uid': self.authenticated_user_id
        }

    @property
    def cookie_jar(self):
        """The client's cookiejar instance."""
        return self.opener.cookie_jar

    @property
    def default_headers(self):
        return CIMultiDict({
            USER_AGENT: self.user_agent,
            ACCEPT_LANGUAGE: 'en-US',
            'X-FB-HTTP-Engine': Constants.FB_HTTP_ENGINE,
            CONNECTION: 'keep-alive',
            'X-IG-Connection-Speed': f'{random.randint(1000, 5000)}kbps',
            'X-IG-Bandwidth-Speed-KBPS': '-1.000',
            'X-IG-Bandwidth-TotalBytes-B': '0',
            'X-IG-Bandwidth-TotalTime-MS': '0',
            'X-IG-Connection-Type': 'WIFI',
            'X-IG-Capabilities': self.ig_capabilities,
            'X-IG-App-ID': self.application_id,
        })

    @property
    def radio_type(self):
        """For use in certain endpoints"""
        return 'wifi-none'

    def _generate_signature(self, data):
        """
        Generates the signature for a data string

        :param data: content to be signed
        :return:
        """
        return hmac.new(
            self.signature_key.encode('ascii'), data.encode('ascii'),
            digestmod=hashlib.sha256).hexdigest()

    @classmethod
    def generate_uuid(cls, return_hex=False, seed=None):
        """
        Generate uuid

        :param return_hex: Return in hex format
        :param seed: Seed value to generate a consistent uuid
        :return:
        """
        if seed:
            m = hashlib.md5()
            m.update(seed.encode('utf-8'))
            new_uuid = uuid.UUID(m.hexdigest())
        else:
            new_uuid = uuid.uuid1()
        if return_hex:
            return new_uuid.hex
        return str(new_uuid)

    @classmethod
    def generate_deviceid(cls, seed=None):
        """
        Generate an android device ID

        :param seed: Seed value to generate a consistent device ID
        :return:
        """
        return f'android-{cls.generate_uuid(True, seed)[:16]}'

    def generate_adid(self, seed=None):
        """
        Generate an Advertising ID based on the login username since
        the Google Ad ID is a personally identifying but resettable ID.

        :return:
        """
        modified_seed = seed or self.authenticated_user_name or self.username
        if modified_seed:
            # Do some trivial mangling of original seed
            sha2 = hashlib.sha256()
            sha2.update(modified_seed.encode('utf-8'))
            modified_seed = sha2.hexdigest()
        return self.generate_uuid(False, modified_seed)

    async def _call_api(self, endpoint, params=None, query=None, return_response=False, unsigned=False, version='v1'):
        """
        Calls the private api.

        :param endpoint: endpoint path that should end with '/', example 'discover/explore/'
        :param params: POST parameters
        :param query: GET url query parameters
        :param return_response: return the response instead of the parsed json object
        :param unsigned: use post params as-is without signing
        :param version: for the versioned api base url. Default 'v1'.
        :return:
        """
        url = self.api_url.format(version=version) + endpoint

        if params:
            method = self.session.post
            if params is True:
                params = None
            elif not unsigned:
                json_params = jdumps(params)
                params = query if query else {}
                params['ig_sig_key_version'] = self.key_version
                params['signed_body'] = f'{self._generate_signature(json_params)}.{json_params}'
        else:
            method = self.session.get
            params = query

        async with method(url, params=params) as response:
            try:
                self.logger.debug(f'REQUEST: {url}')
                self.logger.debug(f'DATA: {params}')
                if return_response:
                    return await response.text()
                response = await response.json(loads=jloads)
            except ClientResponseError as e:
                self.logger.debug(f'RESPONSE: {e.code} {response}')
                ErrorHandler.process(e, response)

        if return_response:
            return response

        self.logger.debug(f'RESPONSE: {response}')

        if response.get('message', '') == 'login_required':
            raise ClientLoginRequiredError(
                response.get('message'), error_response=jdumps(response))

        # not from oembed or an ok response
        if not response.get('provider_url') and response.get('status', '') != 'ok':
            raise ClientError(
                response.get('message', 'Unknown error'),
                error_response=jdumps(response))

        return response

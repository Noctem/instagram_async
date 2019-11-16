from ..compat import jloads
from ..errors import ClientError, ClientLoginError
from ..compatpatch import ClientCompatPatch


class AccountsEndpointsMixin:
    """For endpoints in ``/accounts/``."""

    async def login(self):
        """Login."""

        prelogin_params = await self._call_api(
            'si/fetch_headers/',
            params={'challenge_type': 'signup', 'guid': self.generate_uuid(True)},
            return_response=True)

        if not self.csrftoken:
            raise ClientError(
                'Unable to get csrf from prelogin.',
                error_response=self._read_response(prelogin_params))

        login_params = {
            'device_id': self.device_id,
            'guid': self.uuid,
            'adid': self.ad_id,
            'phone_id': self.phone_id,
            '_csrftoken': self.csrftoken,
            'username': self.username,
            'password': self.password,
            'login_attempt_count': '0',
        }

        login_response = self._call_api(
            'accounts/login/', params=login_params, return_response=True)

        if not self.csrftoken:
            raise ClientError(
                'Unable to get csrf from login.',
                error_response=login_response)

        login_json = jloads(login_response)

        if not login_json.get('logged_in_user', {}).get('pk'):
            raise ClientLoginError('Unable to login.')

        if self.on_login:
            on_login_callback = self.on_login
            on_login_callback(self)

        # # Post-login calls in client
        # self.sync()
        # self.autocomplete_user_list()
        # self.feed_timeline()
        # self.ranked_recipients()
        # self.recent_recipients()
        # self.direct_v2_inbox()
        # self.news_inbox()
        # self.explore()

    async def current_user(self):
        """Get current user info"""
        params = self.authenticated_params
        res = await self._call_api('accounts/current_user/', params=params, query={'edit': 'true'})
        if self.auto_patch:
            ClientCompatPatch.user(res['user'], drop_incompat_keys=self.drop_incompat_keys)
        return res

    async def edit_profile(self, first_name, biography, external_url, email, phone_number, gender):
        """
        Edit profile

        :param first_name:
        :param biography:
        :param external_url:
        :param email: Required.
        :param phone_number:
        :param gender: male: 1, female: 2, unspecified: 3
        :return:
        """
        if int(gender) not in {1, 2, 3}:
            raise ValueError(f'Invalid gender: {gender}')
        if not email:
            raise ValueError('Email is required.')

        params = {
            'username': self.authenticated_user_name,
            'gender': int(gender),
            'phone_number': phone_number or '',
            'first_name': first_name or '',
            'biography': biography or '',
            'external_url': external_url or '',
            'email': email,
        }
        params.update(self.authenticated_params)
        res = await self._call_api('accounts/edit_profile/', params=params)
        if self.auto_patch:
            ClientCompatPatch.user(res.get('user'))
        return res

    async def remove_profile_picture(self):
        """Remove profile picture"""
        res = await self._call_api(
            'accounts/remove_profile_picture/', params=self.authenticated_params)
        if self.auto_patch:
            ClientCompatPatch.user(res['user'], drop_incompat_keys=self.drop_incompat_keys)
        return res

    async def change_profile_picture(self, photo_data):
        """
        Change profile picture

        :param photo_data: byte string of image
        :return:
        """
        raise NotImplementedError("Changing profile pictures is not supported yet.")

    async def set_account_private(self):
        """Make account private"""
        res = await self._call_api('accounts/set_private/', params=self.authenticated_params)
        if self.auto_patch:
            ClientCompatPatch.list_user(res['user'], drop_incompat_keys=self.drop_incompat_keys)
        return res

    async def set_account_public(self):
        """Make account public"""""
        res = await self._call_api('accounts/set_public/', params=self.authenticated_params)
        if self.auto_patch:
            ClientCompatPatch.list_user(res['user'], drop_incompat_keys=self.drop_incompat_keys)
        return res

    async def logout(self):
        """Logout user"""
        params = {
            'phone_id': self.phone_id,
            '_csrftoken': self.csrftoken,
            'guid': self.uuid,
            'device_id': self.device_id,
            '_uuid': self.uuid
        }
        return await self._call_api('accounts/logout/', params=params, unsigned=True)

    async def presence_status(self):
        """Get presence status setting"""
        query = {
            'ig_sig_key_version': self.key_version,
            'signed_body': self._generate_signature('{}') + '.{}'
        }
        return await self._call_api('accounts/get_presence_disabled/', query=query)

    async def set_presence_status(self, disabled):
        """
        Set presence status setting

        :param disabled: True if disabling, else False
        """
        params = {
            'disabled': '1' if disabled else '0'
        }
        params.update(self.authenticated_params)
        return await self._call_api('accounts/set_presence_disabled/', params=params)

    async def enable_presence_status(self):
        """Enable presence status setting"""
        return await self.set_presence_status(False)

    async def disable_presence_status(self):
        """Disable presence status setting"""
        return await self.set_presence_status(True)

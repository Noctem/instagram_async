import json
import time
import warnings

from random import randint

from .common import ClientDeprecationWarning
from ..compatpatch import ClientCompatPatch


class MediaRatios:
    """
    Class holding valid aspect ratios (width: height) for media uploads.
    """

    # Based on IG sampling
    # and from https://help.instagram.com/1469029763400082
    #: Acceptable min, max values of with/height ratios for a standard media upload
    standard = 4.0 / 5.0, 90.0 / 47.0
    __device_ratios = [(3, 4), (2, 3), (5, 8), (3, 5), (9, 16), (10, 16), (40, 71)]
    __aspect_ratios = [1.0 * x[0] / x[1] for x in __device_ratios]

    #: Acceptable min, max values of with/height ratios for a story upload
    reel = min(__aspect_ratios), max(__aspect_ratios)


class UploadEndpointsMixin:
    """For endpoints relating to upload functionality."""

    EXTERNAL_LOC_SOURCES = {
        'foursquare': 'foursquare_v2_id',
        'facebook_places': 'facebook_places_id',
        'facebook_events': 'facebook_events_id'
    }

    def _validate_location(self, location):
        """
        Validates and patches a location dict for use with the upload functions

        :param location: dict containing location info
        :return:
        """
        location_keys = ['external_source', 'name', 'address']
        if not isinstance(location, dict):
            raise ValueError('Location must be a dict.')

        # patch location object returned from location_search
        if 'external_source' not in location and 'external_id_source' in location and 'external_id' in location:
            external_source = location['external_id_source']
            location['external_source'] = external_source
            if external_source in self.EXTERNAL_LOC_SOURCES:
                location[self.EXTERNAL_LOC_SOURCES[external_source]] = location['external_id']
        for k in location_keys:
            if not location.get(k):
                raise ValueError(f'Location dict must contain "{k}".')
        for k, val in self.EXTERNAL_LOC_SOURCES.items():
            if location['external_source'] == k and not location.get(val):
                raise ValueError(f'Location dict must contain "{val}".')

        media_loc = {
            'name': location['name'],
            'address': location['lat'],
            'external_source': location['external_source'],
        }
        if 'lat' in location and 'lng' in location:
            media_loc['lat'] = location['lat']
            media_loc['lng'] = location['lng']
        for k, val in self.EXTERNAL_LOC_SOURCES.items():
            if location['external_source'] == k:
                media_loc['external_source'] = k
                media_loc[val] = location[val]
        return media_loc

    @staticmethod
    def standard_ratios():  # pragma: no cover
        """
        Deprecated. Use MediaRatios.standard instead.
        Acceptable min, max values of with/height ratios for a standard media upload

        :return: tuple of (min. ratio, max. ratio)
        """
        warnings.warn(
            'Client.standard_ratios() is deprecated. '
            'Please use MediaRatios.standard instead.',
            ClientDeprecationWarning
        )
        return MediaRatios.standard

    @staticmethod
    def reel_ratios():  # pragma: no cover
        """
        Deprecated. Use MediaRatios.reel instead.
        Acceptable min, max values of with/height ratios for a story upload

        :return: tuple of (min. ratio, max. ratio)
        """
        warnings.warn(
            'Client.reel_ratios() is deprecated. '
            'Please use MediaRatios.reel instead.',
            ClientDeprecationWarning
        )
        return MediaRatios.reel

    @classmethod
    def compatible_aspect_ratio(cls, size):
        """
        Helper method to check aspect ratio for standard uploads

        :param size: tuple of (width, height)
        :return: True/False
        """
        min_ratio, max_ratio = MediaRatios.standard
        width, height = size
        this_ratio = 1.0 * width / height
        return min_ratio <= this_ratio <= max_ratio

    @classmethod
    def reel_compatible_aspect_ratio(cls, size):
        """
        Helper method to check aspect ratio for story uploads

        :param size: tuple of (width, height)
        :return: True/False
        """
        min_ratio, max_ratio = MediaRatios.reel
        width, height = size
        this_ratio = 1.0 * width / height
        return min_ratio <= this_ratio <= max_ratio

    def configure(self, upload_id, size, caption='', location=None,
                  disable_comments=False, is_sidecar=False):
        """
        Finalises a photo upload. This should not be called directly.
        Use :meth:`post_photo` instead.

        :param upload_id:
        :param size: tuple of (width, height)
        :param caption:
        :param location: a dict of venue/location information,
                         from :meth:`location_search` or :meth:`location_fb_search`
        :param disable_comments:
        :param is_sidecar: bool flag for album upload
        :return:
        """
        if not self.compatible_aspect_ratio(size):
            raise ValueError('Incompatible aspect ratio.')

        endpoint = 'media/configure/'
        width, height = size
        params = {
            'caption': caption,
            'media_folder': 'Instagram',
            'source_type': '4',
            'upload_id': upload_id,
            'device': {
                'manufacturer': self.phone_manufacturer,
                'model': self.phone_device,
                'android_version': self.android_version,
                'android_release': self.android_release
            },
            'edits': {
                'crop_original_size': [width * 1.0, height * 1.0],
                'crop_center': [0.0, -0.0],
                'crop_zoom': 1.0
            },
            'extra': {
                'source_width': width,
                'source_height': height,
            }
        }
        if location:
            media_loc = self._validate_location(location)
            params['location'] = json.dumps(media_loc)
            if 'lat' in location and 'lng' in location:
                params['geotag_enabled'] = '1'
                params['exif_latitude'] = '0.0'
                params['exif_longitude'] = '0.0'
                params['posting_latitude'] = str(location['lat'])
                params['posting_longitude'] = str(location['lng'])
                params['media_latitude'] = str(location['lat'])
                params['media_latitude'] = str(location['lng'])
        if disable_comments:
            params['disable_comments'] = '1'

        if is_sidecar:
            return params

        params.update(self.authenticated_params)
        res = self._call_api(endpoint, params=params)
        if self.auto_patch and res.get('media'):
            ClientCompatPatch.media(res.get('media'), drop_incompat_keys=self.drop_incompat_keys)
        return res

    def configure_video(self, upload_id, size, duration, thumbnail_data, caption='',
                        location=None, disable_comments=False, is_sidecar=False):
        """
        Finalises a video upload. This should not be called directly.
        Use :meth:`post_video` instead.

        :param upload_id:
        :param size: tuple of (width, height)
        :param duration: in seconds
        :param thumbnail_data: byte string of thumbnail photo
        :param caption:
        :param location: a dict of venue/location information,
                         from :meth:`location_search` or :meth:`location_fb_search`
        :param disable_comments:
        :param is_sidecar: bool flag for album upload
        :return:
        """
        if not self.compatible_aspect_ratio(size):
            raise ValueError('Incompatible aspect ratio.')

        # upload video thumbnail
        self.post_photo(thumbnail_data, size, caption, upload_id, location=location,
                        disable_comments=disable_comments, is_sidecar=is_sidecar)

        width, height = size
        params = {
            'upload_id': upload_id,
            'caption': caption,
            'source_type': '3',
            'poster_frame_index': 0,
            'length': duration * 1.0,
            'audio_muted': False,
            'filter_type': '0',
            'video_result': 'deprecated',
            'clips': {
                'length': duration * 1.0,
                'source_type': '3',
                'camera_position': 'back'
            },
            'device': {
                'manufacturer': self.phone_manufacturer,
                'model': self.phone_device,
                'android_version': self.android_version,
                'android_release': self.android_release
            },
            'extra': {
                'source_width': width,
                'source_height': height
            }
        }
        if disable_comments:
            params['disable_comments'] = '1'
        if location:
            media_loc = self._validate_location(location)
            params['location'] = json.dumps(media_loc)
            if 'lat' in location and 'lng' in location:
                params['geotag_enabled'] = '1'
                params['av_latitude'] = '0.0'
                params['av_longitude'] = '0.0'
                params['posting_latitude'] = str(location['lat'])
                params['posting_longitude'] = str(location['lng'])
                params['media_latitude'] = str(location['lat'])
                params['media_latitude'] = str(location['lng'])

        if is_sidecar:
            return params

        params.update(self.authenticated_params)
        res = self._call_api('media/configure/', params=params, query={'video': 1})
        if res.get('media') and self.auto_patch:
            ClientCompatPatch.media(res.get('media'), drop_incompat_keys=self.drop_incompat_keys)
        return res

    def configure_to_reel(self, upload_id, size):
        """
        Finalises a photo story upload. This should not be called directly.
        Use :meth:`post_photo_story` instead.

        :param upload_id:
        :param size: tuple of (width, height)
        :return:
        """
        if not self.reel_compatible_aspect_ratio(size):
            raise ValueError('Incompatible aspect ratio.')

        endpoint = 'media/configure_to_story/'
        width, height = size
        params = {
            'source_type': '4',
            'upload_id': upload_id,
            'story_media_creation_date': str(int(time.time()) - randint(11, 20)),
            'client_shared_at': str(int(time.time()) - randint(3, 10)),
            'client_timestamp': str(int(time.time())),
            'configure_mode': 1,      # 1 - REEL_SHARE, 2 - DIRECT_STORY_SHARE
            'device': {
                'manufacturer': self.phone_manufacturer,
                'model': self.phone_device,
                'android_version': self.android_version,
                'android_release': self.android_release
            },
            'edits': {
                'crop_original_size': [width * 1.0, height * 1.0],
                'crop_center': [0.0, 0.0],
                'crop_zoom': 1.3333334
            },
            'extra': {
                'source_width': width,
                'source_height': height,
            }
        }
        params.update(self.authenticated_params)
        res = self._call_api(endpoint, params=params)
        if self.auto_patch and res.get('media'):
            ClientCompatPatch.media(res.get('media'), drop_incompat_keys=self.drop_incompat_keys)
        return res

    def configure_video_to_reel(self, upload_id, size, duration, thumbnail_data):
        """
        Finalises a video story upload. This should not be called directly.
        Use :meth:`post_video_story` instead.

        :param upload_id:
        :param size: tuple of (width, height)
        :param duration: in seconds
        :param thumbnail_data: byte string of thumbnail photo
        :return:
        """
        if not self.reel_compatible_aspect_ratio(size):
            raise ValueError('Incompatible aspect ratio.')

        res = self.post_photo(thumbnail_data, size, '', upload_id=upload_id, to_reel=True)

        width, height = size
        params = {
            'source_type': '4',
            'upload_id': upload_id,
            'story_media_creation_date': str(int(time.time()) - randint(11, 20)),
            'client_shared_at': str(int(time.time()) - randint(3, 10)),
            'client_timestamp': str(int(time.time())),
            'configure_mode': 1,      # 1 - REEL_SHARE, 2 - DIRECT_STORY_SHARE
            'poster_frame_index': 0,
            'length': duration * 1.0,
            'audio_muted': False,
            'filter_type': '0',
            'video_result': 'deprecated',
            'clips': {
                'length': duration * 1.0,
                'source_type': '4',
                'camera_position': 'back'
            },
            'device': {
                'manufacturer': self.phone_manufacturer,
                'model': self.phone_device,
                'android_version': self.android_version,
                'android_release': self.android_release
            },
            'extra': {
                'source_width': width,
                'source_height': height,
            },
        }

        params.update(self.authenticated_params)
        res = self._call_api('media/configure_to_story/', params=params, query={'video': '1'})
        if self.auto_patch and res.get('media'):
            ClientCompatPatch.media(res.get('media'), drop_incompat_keys=self.drop_incompat_keys)
        return res

    def post_photo(self, photo_data, size, caption='', upload_id=None, to_reel=False, **kwargs):
        """
        Upload a photo.

        [CAUTION] FLAKY, IG is very finicky about sizes, etc, needs testing.

        :param photo_data: byte string of the image
        :param size: tuple of (width, height)
        :param caption:
        :param upload_id:
        :param to_reel: a Story photo
        :param kwargs:
            - **location**: a dict of venue/location information, from :meth:`location_search`
              or :meth:`location_fb_search`
            - **disable_comments**: bool to disable comments
        :return:
        """
        raise NotImplementedError('Posting has not yet been implemented.')

    def post_video(self, video_data, size, duration, thumbnail_data, caption='', to_reel=False, **kwargs):
        """
        Upload a video

        [CAUTION] FLAKY, IG is very picky about sizes, etc, needs testing.

        :param video_data: byte string or a file-like object of the video content
        :param size: tuple of (width, height)
        :param duration: in seconds
        :param thumbnail_data: byte string of the video thumbnail content
        :param caption:
        :param to_reel: post to reel as Story
        :param kwargs:
             - **location**: a dict of venue/location information, from :meth:`location_search`
               or :meth:`location_fb_search`
             - **disable_comments**: bool to disable comments
             - **max_retry_count**: maximum attempts to reupload. Default 10.
        :return:
        """
        raise NotImplementedError('Posting has not yet been implemented.')

    def post_photo_story(self, photo_data, size):
        """
        Upload a photo story

        :param photo_data: byte string of the image
        :param size: tuple of (width, height)
        :return:
        """
        return self.post_photo(
            photo_data=photo_data, size=size, to_reel=True)

    def post_video_story(self, video_data, size, duration, thumbnail_data):
        """
        Upload a video story

        :param video_data: byte string or a file-like object of the video content
        :param size: tuple of (width, height)
        :param duration: in seconds
        :param thumbnail_data: byte string of the video thumbnail content
        :return:
        """
        return self.post_video(
            video_data=video_data, size=size, duration=duration,
            thumbnail_data=thumbnail_data, to_reel=True)

    def post_album(self, medias, caption='', location=None, **kwargs):
        """
        Post an album of up to 10 photos/videos.

        :param medias: an iterable list/collection of media dict objects

            .. code-block:: javascript

                medias = [
                    {"type": "image", "size": (720, 720), "data": "..."},
                    {
                        "type": "image", "size": (720, 720),
                        "usertags": [{"user_id":4292127751, "position":[0.625347,0.4384531]}],
                        "data": "..."
                    },
                    {"type": "video", "size": (720, 720), "duration": 12.4, "thumbnail": "...", "data": "..."}
                ]

        :param caption:
        :param location:
        :return:
        """
        raise NotImplementedError('Posting has not yet been implemented.')

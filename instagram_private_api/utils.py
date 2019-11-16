from base64 import b64encode
from hashlib import sha256
from hmac import new as hmac_new
from random import randint
from re import match
from time import time


VALID_UUID_RE = r'^[a-f\d]{8}\-[a-f\d]{4}\-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$'


def raise_if_invalid_rank_token(val, required=True):
    if required and not val:
        raise ValueError('rank_token is required')
    if not match(VALID_UUID_RE, val):
        raise ValueError(f'Invalid rank_token: {val}')


def gen_user_breadcrumb(size):
    """
    Used in comments posting.

    :param size:
    :return:
    """
    key = b'iN4$aGr0m'
    dt = int(time() * 1000)

    # typing time elapsed
    time_elapsed = randint(500, 1500) + size * randint(500, 1500)

    text_change_event_count = max(1, size / randint(3, 5))

    data = f'{size} {time_elapsed} {text_change_event_count} {dt}'.encode('ascii')
    return (b64encode(hmac_new(key, data, digestmod=sha256).digest()) + b'\n'
            + b64encode(data) + b'\n').decode()


class InstagramID:
    """
    Utility class to convert between IG's internal numeric ID and the shortcode used in weblinks.
    Does NOT apply to private accounts.
    """
    ENCODING_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'

    @staticmethod
    def _encode(num, alphabet=ENCODING_CHARS):
        """Covert a numeric value to a shortcode."""
        if num == 0:
            return alphabet[0]
        arr = []
        base = len(alphabet)
        while num:
            rem = num % base
            num //= base
            arr.append(alphabet[rem])
        arr.reverse()
        return ''.join(arr)

    @staticmethod
    def _decode(shortcode, alphabet=ENCODING_CHARS):
        """Covert a shortcode to a numeric value."""
        base = len(alphabet)
        strlen = len(shortcode)
        num = 0
        idx = 0
        for char in shortcode:
            power = (strlen - (idx + 1))
            num += alphabet.index(char) * (base ** power)
            idx += 1
        return num

    @classmethod
    def weblink_from_media_id(cls, media_id):
        """
        Returns the web link for the media id

        :param media_id:
        :return:
        """
        return f'https://www.instagram.com/p/{cls.shorten_media_id(media_id)}/'

    @classmethod
    def shorten_media_id(cls, media_id):
        """
        Returns the shortcode for a media id

        :param media_id: string in the format id format: AAA_BB where AAA is the pk, BB is user_id
        :return:
        """
        # media id format: AAA_BB where AAA is the pk, BB is user_id
        internal_id = int(str(media_id).split('_')[0])
        return cls.shorten_id(internal_id)

    @classmethod
    def shorten_id(cls, internal_id):
        """
        Returns the shortcode for a numeric media PK

        :param internal_id: numeric ID value
        :return:
        """
        return cls._encode(internal_id)

    @classmethod
    def expand_code(cls, short_code):
        """
        Returns the numeric ID for a shortcode

        :param short_code:
        :return:
        """
        return cls._decode(short_code)

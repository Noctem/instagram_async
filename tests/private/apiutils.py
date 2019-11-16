import unittest

from ..common import InstagramID, MediaTypes


class ApiUtilsTests(unittest.TestCase):
    """Tests for the utility functions."""

    @staticmethod
    def init_all():
        return [
            {
                'name': 'test_expand_code',
                'test': ApiUtilsTests('test_expand_code')
            },
            {
                'name': 'test_shorten_id',
                'test': ApiUtilsTests('test_shorten_id')
            },
            {
                'name': 'test_shorten_media_id',
                'test': ApiUtilsTests('test_shorten_media_id')
            },
            {
                'name': 'test_weblink_from_media_id',
                'test': ApiUtilsTests('test_weblink_from_media_id')
            },
            {
                'name': 'test_mediatypes',
                'test': ApiUtilsTests('test_mediatypes')
            },
        ]

    def __init__(self, testname):
        super().__init__(testname)

    def test_expand_code(self):
        id = InstagramID.expand_code('BRo7njqD75U')
        self.assertEqual(id, 1470687481426853460)

    def test_shorten_id(self):
        shortcode = InstagramID.shorten_id(1470687481426853460)
        self.assertEqual(shortcode, 'BRo7njqD75U')

    def test_shorten_media_id(self):
        shortcode = InstagramID.shorten_media_id('1470654893538426156_25025320')
        self.assertEqual(shortcode, 'BRo0NV0jD0s')

    def test_weblink_from_media_id(self):
        weblink = InstagramID.weblink_from_media_id('1470517649007430315_25025320')
        self.assertEqual(weblink, 'https://www.instagram.com/p/BRoVAK5B8qr/')

    def test_mediatypes(self):
        self.assertEqual(MediaTypes.id_to_name(MediaTypes.PHOTO), 'image')
        self.assertEqual(MediaTypes.name_to_id('image'), MediaTypes.PHOTO)

        with self.assertRaises(ValueError):
            MediaTypes.id_to_name(-1)

        with self.assertRaises(ValueError):
            MediaTypes.name_to_id('x')

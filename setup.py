from os.path import abspath, dirname, join
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
try:
    import unittest.mock
    has_mock = True
except ImportError:
    has_mock = False

__author__ = 'Noctem <mail@noctem.xyz>'
__version__ = '1.6.0'

packages = [
    'instagram_private_api',
    'instagram_private_api.endpoints'
]
test_reqs = [] if has_mock else ['mock']

with open(join(abspath(dirname(__file__)), 'README.md'), 'rt') as f:
    long_description = f.read()

setup(
    name='instagram_async',
    version=__version__,
    author='Noctem',
    author_email='mail@noctem.xyz',
    license='MIT',
    url='https://github.com/Noctem/instagram_private_api',
    install_requires=['aiohttp'],
    extra_requires={'fast_json': ['orjson']},
    test_requires=test_reqs,
    keywords='instagram private api asyncio',
    description='A client interface for the private Instagram API.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=packages,
    platforms=['any'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ]
)

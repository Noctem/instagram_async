from os import path
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    import unittest.mock
    has_mock = True
except ImportError:
    has_mock = False

__author__ = 'ping <lastmodified@gmail.com>'
__version__ = '1.6.0'

packages = [
    'instagram_private_api',
    'instagram_private_api.endpoints'
]
test_reqs = [] if has_mock else ['mock']

with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='instagram_private_api',
    version=__version__,
    author='ping',
    author_email='lastmodified@gmail.com',
    license='MIT',
    url='https://github.com/ping/instagram_private_api/tree/master',
    install_requires=[],
    extra_requires={'fast_json': ['orjson']},
    test_requires=test_reqs,
    keywords='instagram private api',
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)

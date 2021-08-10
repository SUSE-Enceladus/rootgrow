#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from rootgrow.version import __VERSION__

with open('.virtualenv.requirements.txt') as f:
    requirements = f.read().splitlines()

config = {
    'name': 'rootgrow',
    'description': 'Simpler wrapper for growpart',
    'author': 'PubCloud Development team',
    'url': 'https://github.com/SUSE-Enceladus/rootgrow',
    'download_url': 'https://github.com/SUSE-Enceladus/rootgrow',
    'author_email': 'public-cloud-dev@susecloud.net',
    'version': __VERSION__,
    'install_requires': requirements,
    'packages': ['rootgrow'],
    'entry_points': {
        'console_scripts': [
            'rootgrow=rootgrow.rootgrow:main'
        ]
    },
    'include_package_data': True,
    'license': 'GPLv3',
    'zip_safe': False,
    'classifiers': [
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Operating System'
    ]
}

setup(**config)

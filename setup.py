#-*- coding:utf-8 -*-
"""
Setup for baguette-deploy package.
"""
from setuptools import find_packages, setup

setup(
    name='baguette-deploy',
    version='0.1',
    url='baguette.io',
    download_url='baguette.io',
    author_email='dev@baguette.io',
    packages=find_packages(),
    platforms=[
        'Linux/UNIX',
        'MacOS',
        'Windows'
    ],
    install_requires=[
        'Jinja2==2.8',
        'baguette-messaging[postgres]',
        'baguette-utils',
    ],
    extras_require={
        'kubernetes': [
            'kubernetes==4.0.0',
        ],
        'testing': [
            'baguette-messaging[testing]',
            'mock',
            'pytest',
            'pytest-cov',
            'pylint==1.6.1',
        ],
        'doc': [
            'Sphinx==1.4.4',
        ],
    },
    package_data={
        'defournement': ['templates/deploy_post.tmpl', 'templates/deploy_put.tmpl'],
        'defournement.tests': ['farine.ini', 'pytest.ini'],
    },
)

# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = "0.1"



with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name = "get aws tokens",
    packages = ["get_creds"],
    install_requires=requirements,
    include_package_data=True,
    entry_points = {
        "console_scripts": ['get_creds = get_creds.get_creds:main']
        },
    version = version,
    description = "An utility to get temporary AWS credentials using Okta",
    author = "Kapil Patil",
    author_email = "kapil.patil@okta.com",
    url='<Enter GIT URL Value>'
)



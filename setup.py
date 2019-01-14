#!/usr/bin/env python2
#Copyright (c) 2013-2018 Hanson Robotics, Ltd.

from setuptools import setup
setup(
    name = 'owylviz',
    version = '0.1',
    packages = ['owylviz'],
    install_requires = ['socketIO-client==0.5.3'],
    tests_require=['owyl', 'mock'],
    test_suite='tests'
)

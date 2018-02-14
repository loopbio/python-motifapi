#!/usr/bin/env python

from setuptools import setup

setup(
    name='motifapi',
    license='BSD',
    description='Python interface to Motif recording systems',
    long_description='Python interface to Motif recording systems',
    version='0.1.1',
    author='John Stowers',
    author_email='john@loopbio.com',
    packages=['motifapi'],
    install_requires=['six'],
    include_package_data=True,
)


#!/usr/bin/env python

from setuptools import setup

setup(
    name='motifapi',
    license='BSD',
    description='Python interface to Motif recording systems',
    long_description='Python interface to Motif recording systems',
    version='0.2.00',
    author='John Stowers',
    author_email='john@loopbio.com',
    packages=['motifapi'],
    python_requires='>=3.6',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
    ],
    include_package_data=True,
)


#!/usr/bin/env python

import os

from setuptools import setup

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'README.md')) as f:
    long_description = f.read()

setup(
    name='motifapi',
    license='BSD',
    description='Python interface to Motif recording systems',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/loopbio/python-motifapi',
    version='0.2.0',
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


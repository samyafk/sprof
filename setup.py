# -*- coding: utf-8 -*
# python3
# Install sprof packages :
# cd this file directory
# pip install -e .

from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='sprof',
    version='1.0',
    licence = 'LGPL V3',
    author="LJK / Caroline Bligny",
    author_email="caroline.bligny@univ-grenoble-alpes.fr",
    description="Sprint Power-Force-Velocity Profiling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    #url="https://project-url",
    #packages=['scipy', 'matplotlib'], # s-cf requirements.txt
    packages=find_packages(),
)

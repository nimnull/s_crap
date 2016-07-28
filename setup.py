# -*- coding: utf-8 -*-
"""Provide layouts and related tools for launching datarobot clusters."""
from setuptools import setup


__author__ = 'Yehor Nazarkin <nimnull@gmail.com>'

def readme():
    """Open and return readme."""
    with open('README.rst') as f:
        return f.read()


tests_require = [
    'coverage>=3,<4',
    'flake8>=2.5.0,<3',
    'pep257>=0.7.0,<1',
    'pytest>=2.8.7,<3',
    'pytest-click>=0.1,<1.0',
    'pytest-cov>=2.2.0,<3',
    'pytest-flakes>=1.0.1,<2',
    'pytest-mccabe>=0.0.1,<2',
    'pytest-mock>=0.10.1,<1']

install_requirements = [
    'aiohttp==0.22.1',
    'click==6.6',
    'PyYAML==3.11',
    'injections==0.2.2',
    'trafaret==0.7.1',
    'motor==0.6.2',
]

release_requires = [
    'sphinx>=1.3.6,<2',
    'zest.releaser>=6.6.2,<7']

entry_points = {
    'console_scripts': ['spyder=crap.cli:run_spyder']}

# scripts = ['bin/drlayout-complete']


setup(
    name='crap',
    version='0.0.1.dev0',
    description='Library, tooling, and data files for layouts at DataRobot.',
    long_description=readme(),
    author='Yehor Nazarkin',
    author_email='nimnull@gmail.com',
    entry_points=entry_points,
    url='https://github.com/datarobot/drlayout',
    packages=['crap',
              'crap.cli'],
    package_dir={'crap': 'crap'},
    # package_data={'drlayout': ['layouts/*', 'overlays/*', 'macros/*']},
    extras_require={
        'testing': tests_require,
        'release': release_requires,
        'dev': tests_require + release_requires},
    install_requires=install_requirements,
    # scripts=scripts,
    tests_require=tests_require)

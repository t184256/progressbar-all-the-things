# SPDX-FileCopyrightText: 2021 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0-only

from setuptools import setup

setup(
    name='progressbar-all-the-things',
    version='0.0.1',
    url='https://github.com/t184256/progressbar-all-the-things',
    author='Alexander Sosedkin',
    author_email='monk@unboiled.info',
    description=(
        'Guesstimate progress of arbitrary process trees '
        'with flashy progressbars.'
    ),
    packages=[
        'patt',
    ],
    install_requires=[
        'tqdm',
    ],
    entry_points={
        'console_scripts': [
            'patt = patt.main:main',
        ],
    },
)

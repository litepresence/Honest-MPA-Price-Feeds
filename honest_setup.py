#!/usr/bin/env python
"""
pip3 installations
pkg-config and libsecp256k1 installations
"""

import os
from subprocess import call
from setuptools import setup, find_packages


def sudos():
    """
    Intall pkg-config and libsecp256k1.
    """
    print("\n\n")
    print("Installing pkg-config and libsecp256k1")
    print("\n\n")
    call(["sudo", "apt-get", "update"])
    call(["sudo", "apt-get", "install", "pkg-config"])
    call(["sudo", "apt-get", "install", "libsecp256k1-dev"])
    print("\n\n")
    print("pkg-config and libsecp256k1 indicator package installs complete")

__VERSION__ = "0.00000001"
__AUTHOR__ = "litepresence"
__AUTHOR_EMAIL__ = "finitestate@tutamail.com"
__URL__ = "http://www.litepresence.com"
__NAME__ = "Honest-MPA-Price-Feeds"

sudos()

print("\n\nInstalling requirements.txt...\n\n")

setup(
    name=__NAME__,
    version=__VERSION__,
    description=(
        "HONEST MPA PRICE FEEDS FOR BITSHARES DEX"
    ),
    long_description=open("README.md").read(),
    download_url="https://github.com/litepresence/extinction-event/tarball/"
    + __VERSION__,
    author=__AUTHOR__,
    author_email=__AUTHOR_EMAIL__,
    url=__URL__,
    keywords=[
        "bts",
        "bitshares",
        "palmpay"
        "btc",
        "bitcoin",
        "crypto",
        "altcoin",
        "cryptocurrency",
        "smart",
        "contract",
        "distributed",
        "exchange",
        "litepresence",
        "market pegged asset",
        "MPA",
        "smartcoin",
        "makerDAO",
    ],
    packages=find_packages(),
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    install_requires=open("requirements.txt").read().split(),
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    include_package_data=True,
)

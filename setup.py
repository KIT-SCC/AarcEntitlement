#! /usr/bin/env python

from pathlib import Path
from setuptools import setup


this_directory = Path(__file__).parent
long_description = (this_directory / "README.rst").read_text()

setup(
    setup_requires=["pbr>=1.8"],
    pbr=True,
    install_requires=["regex"],
    long_description=long_description,
)

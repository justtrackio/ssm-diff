#!/usr/bin/env python

from os import path
from setuptools import setup, find_packages


def read_long_description():
    wd = path.abspath(path.dirname(__file__))
    with open(path.join(wd, "README.md"), encoding="utf-8") as f:
        return f.read()


setup(
    name="ssm-diff",
    version="v",
    description="A tool to manage contents of AWS SSM Parameter Store",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/justtrackio/ssm-diff",
    download_url="https://github.com/justtrackio/ssm-diff/archive/v",
    license="MIT",
    packages=find_packages(),
    scripts=["ssm-diff"],
    install_requires=["termcolor", "boto3", "dpath", "PyYAML"],
    keywords=["aws", "ssm", "parameter-store"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.6",
)

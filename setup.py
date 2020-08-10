"""The python wrapper for IQ Option API package setup."""
from setuptools import (setup, find_packages)


setup(
    name="pyiqoptionapi",
    version="1.1.100",
    packages=find_packages(),
    install_requires=["pylint", "requests", "websocket-client==0.56"],
    include_package_data=True,
    description="Best IQ Option API for python",
    long_description="Best IQ Option API for python",
    url="https://github.com/deibsoncarvalho/py-iqoption-api",
    author="Deibson Carvalho",
    author_email="deibsoncarvalho@gmail.com",
    zip_safe=False
)

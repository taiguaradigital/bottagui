"""The python wrapper for IQ Option API package setup."""
from setuptools import (setup, find_packages)

setup(
    name="py-iqoption-api",
    version="1.1.100",
    packages=find_packages(),
    install_requires=["pylint", "requests", "websocket-client==0.56"],
    include_package_data=True,
    description="Best IQ Option API for python",
    long_description="Best IQ Option API for python",
    url="https://github.com/deibsoncarvalho/py-iqoption-api",
    download_url="https://github.com/deibsoncarvalho/py-iqoption-api/archive/1.1.100.tar.gz",
    author="Deibson Carvalho",
    keywords=['IQ Option', 'IQOption', 'API IQ Option', 'IQOption API'],
    author_email="deibsoncarvalho@gmail.com",
    zip_safe=False,
    classifiers=[],
)

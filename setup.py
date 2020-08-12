"""The python wrapper for IQ Option API package setup."""
from setuptools import find_packages
from setuptools import setup

setup(
    name="py-iqoption-api",
    version="1.1.200",
    py_modules=['pyiqoptionapi'],
    packages=find_packages(),
    install_requires=["pylint", "requests", "websocket-client==0.56"],
    include_package_data=True,
    license="MIT",
    description="Best IQ Option API for python",
    long_description="Best IQ Option API for python",
    url="https://github.com/deibsoncarvalho/py-iqoption-api",
    download_url="https://github.com/deibsoncarvalho/py-iqoption-api/archive/1.1.200.tar.gz",
    author="Deibson Carvalho",
    keywords=['IQ Option', 'IQOption', 'API IQ Option', 'IQOption API'],
    author_email="deibsoncarvalho@gmail.com",
    zip_safe=False,
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License ',
        'Programming Language :: Python :: 3.7',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Investment ')
    )

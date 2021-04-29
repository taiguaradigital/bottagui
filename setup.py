"""
    Copyright (C) 2019-2020 Deibson Carvalho (deibsoncarvalhoo)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
"""
from setuptools import find_packages, setup
from pyiqoptionapi.version import VERSION


setup(
    name="py-iqoption-api",
    version=VERSION,
    py_modules=['pyiqoptionapi'],
    packages=find_packages(),
    install_requires=["pylint", "requests", "websocket-client==0.56"],
    include_package_data=True,
    license="GPLv3+",
    description="Best IQ Option API for python",
    long_description="Extra Oficial API for IQ Option Trade Binary and Digital Options, Candles, Currencies.",
    long_description_content_type="text/markdown",
    url="https://github.com/deibsoncarvalho/py-iqoption-api",
    download_url="https://github.com/deibsoncarvalho/py-iqoption-api/archive/1.1.200.tar.gz",
    author="Deibson Carvalho",
    keywords=['IQ Option', 'IQOption', 'API IQ Option', 'IQOption API'],
    author_email="deibsoncarvalho@gmail.com",
    zip_safe=False,
    python_requires='>=3.7',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License ',
        'Programming Language :: Python :: 3.7',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Investment ')
    )

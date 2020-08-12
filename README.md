# Py IQ Option extra oficial API
[![Build Status](https://travis-ci.com/deibsoncarvalho/py-iqoption-api.svg?branch=master)](https://travis-ci.com/deibsoncarvalho/py-iqoption-api)
[![PyPI version](https://badge.fury.io/py/py-iqoption-api.svg)](https://badge.fury.io/py/py-iqoption-api)

A Extra oficial API for IQOption Broker of digital, binary options or forex.

In special, this API work with thread safe for simultaneous symbols buys or generated candles.

Any functions have support for asyncio library. The support for asynchronous request will extend for all API. 

The most principal bugs for original version has fixed. But, have some bugs that will fixed.

### Installation
```
pip install py-iqoption-api
```

### A small example

    from pyiqoptionapi import IQOption
    import datetime
    import time
    import logging
    logging.basicConfig(format='%(asctime)s %(message)s')

    api = IQOption("email", "Password")

    api.connect()
    print 'Your current blance is: {:.2f}'.format(api.get_balance())
    

Get list of Top Ten Ranking Countries
    
    country = Countries(api)
    api.listinfodata.current_listinfodata.win
    country.get_top_countries()
    
or get list of countries names for populate combobox, for example.

    country.get_countries_names()



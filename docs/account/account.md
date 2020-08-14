# Account

## get_balance()

Function for return current balance in account selected
```python
iq_option_api.get_balance()
```


## get_currency()

you will check what currency you use

```python
iq_option_api.get_currency()
```

## reset_practice_balance()

reset practice balance to $10000

```python
from pyiqoptionapi import IQOption
iq_option_api=IQOption("email","password")
iq_option_api.connect()#connect to iqoption
print(iq_option_api.reset_practice_balance())
```

## Change real/practice Account

This API works with mode "PRACTICE" or "REAL"
```python
iq_option_api.change_balance("PRACTICE") 
                        #MODE: "PRACTICE"/"REAL"
```

## get Other People strategy

 
### sample
```python
from pyiqoptionapi import IQOption
import logging
import time
 
#logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(message)s')
iq_option_api=IQOption("email","password")
iq_option_api.connect()#connect to iqoption
while_run_time=10
 
#For digital option
 
name="live-deal-digital-option" #"live-deal-binary-option-placed"/"live-deal-digital-option"
active="EURUSD"
_type="PT1M"#"PT1M"/"PT5M"/"PT15M"
buffersize=10#
print("_____________subscribe_live_deal_______________")
iq_option_api.subscribe_live_deal(name,active,_type,buffersize)

 
start_t=time.time()
while True:
    #data size is below buffersize
    #data[0] is the last data
    data=(iq_option_api.get_live_deal(name,active,_type))
    print("__For_digital_option__ data size:"+str(len(data)))
    print(data)
    print("\n\n")
    time.sleep(1)
    if time.time()-start_t>while_run_time:
        break
print("_____________unscribe_live_deal_______________")
iq_option_api.unscribe_live_deal(name,active,_type)


#For binary option
 
name="live-deal-binary-option-placed"
active="EURUSD"
_type="turbo"#"turbo"/"binary"
buffersize=10#
print("_____________subscribe_live_deal_______________")
iq_option_api.subscribe_live_deal(name,active,_type,buffersize)

start_t=time.time()
while True:
    #data size is below buffersize
    #data[0] is the last data
    data=(iq_option_api.get_live_deal(name,active,_type))
    print("__For_binary_option__ data size:"+str(len(data)))
    print(data)
    print("\n\n")
    time.sleep(1)
    if time.time()-start_t>while_run_time:
        break
print("_____________unscribe_live_deal_______________")
iq_option_api.unscribe_live_deal(name,active,_type)
```

### subscribe_live_deal

```python
I_want_money.subscribe_live_deal(name,active,_type,buffersize)
```

### unscribe_live_deal

```python
I_want_money.unscribe_live_deal(name,active,_type)
```

### get_live_deal

```python
I_want_money.get_live_deal(name,active,_type)
```
### pop_live_deal

pop the data from list
```python
I_want_money.pop_live_deal(name,active,_type)
```
## get Other people detail

### sample 
```python
from pyiqoptionapi.stable_api import IQOption
import logging
import time
 
#logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(message)s')
I_want_money=IQOption("email","password")
I_want_money.connect()#connect to iqoption
while_run_time=10
 
#For binary option
name="live-deal-binary-option-placed"
active="EURUSD"
_type="turbo"#"turbo"/"binary"
buffersize=10#
print("_____________subscribe_live_deal_______________")
print("\n\n")
I_want_money.subscribe_live_deal(name,active,_type,buffersize)

last_trade_data=I_want_money.get_live_deal(name,active,_type)[0]
 
user_id=last_trade_data["user_id"]
counutry_id=last_trade_data["country_id"]
print("_______get_user_profile_client__________")
print(I_want_money.get_user_profile_client(user_id))
pro_data=I_want_money.get_user_profile_client(user_id)
print("\n\n")

print("___________request_leaderboard_userinfo_deals_client______")
print(I_want_money.request_leaderboard_userinfo_deals_client(user_id,counutry_id))
user_data=I_want_money.request_leaderboard_userinfo_deals_client(user_id,counutry_id)
worldwide=user_data["result"]["entries_by_country"]["0"]["position"]
profit=user_data["result"]["entries_by_country"]["0"]["score"]
print("\n")
print("user_name:"+pro_data["user_name"])
print("This week worldwide:"+str(worldwide))
print("This week's gross profit:"+str(profit))
print("\n\n")

print("___________get_users_availability____________")
print(I_want_money.get_users_availability(user_id))
print("\n\n")
print("_____________unscribe_live_deal_______________")
I_want_money.unscribe_live_deal(name,active,_type)

```

### get_user_profile_client()
this api can get user name and image
```python
I_want_money.get_user_profile_client(user_id)
```

### request_leaderboard_userinfo_deals_client()
this api can get user detail

```python
I_want_money.request_leaderboard_userinfo_deals_client(user_id,counutry_id)
```
#!/usr/bin/env python3

import asyncio
import time
import datetime
from envoy_reader.envoy_reader import EnvoyReader
from prometheus_client import start_http_server, Gauge


metric_prefix="envoy"
port=9433

#reader=EnvoyReader("envoy", "envoy", "058800", inverters=True)
# Defaults to using envoy as the username and the last six of the
# serial number as the password
reader=EnvoyReader("envoy", inverters=True)


production = Gauge(f"{metric_prefix}_production", "Current system power production (W)")
daily_production = Gauge(f"{metric_prefix}_daily_production", "Current day's energy production (Wh)")
seven_days_production = Gauge(f"{metric_prefix}_seven_day_production", "Current seven day energy production (Wh)")
lifetime_production = Gauge(f"{metric_prefix}_lifetime_production", "Lifetime energy production (Wh)")
inverter = Gauge(f"{metric_prefix}_inverter", f"Inverter current power production (W)", ['serial_number'])

start_http_server(port)

while True:
    loop = asyncio.get_event_loop()
    dataResults = loop.run_until_complete(asyncio.gather(
        reader.getData(), return_exceptions=True
    ))

    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(asyncio.gather(
        reader.production(),
        reader.daily_production(),
        reader.seven_days_production(),
        reader.lifetime_production(),
        reader.inverters_production(),
        return_exceptions=True))
    # results:
    # [13764,
    # 28698,
    # 642343,
    # 4162674,
    # {'202028033658': [120, '2021-03-11 11:30:02'],
    #  '202029005102': [116, '2021-03-11 11:30:10'],
    #  '202028035455': [120, '2021-03-11 11:30:18'],
    #  '202029001566': [117, '2021-03-11 11:30:24'],
    # ...


    #print("production:              {}".format(results[0]))
    #print("daily_production:        {}".format(results[1]))
    #print("seven_days_production:   {}".format(results[2]))
    #print("lifetime_production:     {}".format(results[3]))
    production.set(results[0])
    daily_production.set(results[1])
    seven_days_production.set(results[2])
    lifetime_production.set(results[3])

    if "401" in str(dataResults):
        print("inverters_production:    Unable to retrieve inverter data - Authentication failure")
    elif results[4] is None:
        print("inverters_production:    Inverter data not available for your Envoy device.")
    else:
        for sn,status in results[4].items():
            inverter.labels([sn]).set(status[0])
            #print(f"{sn} {status[0]}")

    time.sleep(60)


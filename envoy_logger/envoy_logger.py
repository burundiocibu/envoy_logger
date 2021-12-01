#!/usr/bin/env python3

import argparse
import asyncio
import datetime
from envoy_reader.envoy_reader import EnvoyReader
import httpx
from prometheus_client import start_http_server, Gauge
import time


def main():
    metric_prefix="envoy"
    port=9433

    parser = argparse.ArgumentParser(description="envoy-logger")
    parser.add_argument('-v', "--verbose", action="count", help="Increase verbosity of outut", default=0)
    args = parser.parse_args()

    if args.verbose:
        print(args)
    # As long as we have httpx 0.19 installed and use the explicit username/password, things seems to work
    reader=EnvoyReader("envoy", "envoy", "058800", inverters=True)
    # Defaults to using envoy as the username and the last six of the
    # serial number as the password
    #reader=EnvoyReader("envoy", inverters=True)

    production = Gauge(f"{metric_prefix}_production", "Current system power production (W)")
    daily_production = Gauge(f"{metric_prefix}_daily_production", "Current day's energy production (Wh)")
    seven_days_production = Gauge(f"{metric_prefix}_seven_day_production", "Current seven day energy production (Wh)")
    lifetime_production = Gauge(f"{metric_prefix}_lifetime_production", "Lifetime energy production (Wh)")
    inverter = Gauge(f"{metric_prefix}_inverter", f"Inverter current power production (W)", ['serial_number'])

    start_http_server(port)

    while True:
        loop = asyncio.get_event_loop()
        data_results = loop.run_until_complete(
            asyncio.gather(
                reader.getData(), return_exceptions=True))
        if args.verbose > 1: print(f"data_results:{data_results}")
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(
            asyncio.gather(
                reader.production(),
                reader.daily_production(),
                reader.seven_days_production(),
                reader.lifetime_production(),
                reader.inverters_production(),
                return_exceptions=True))
        if args.verbose > 1: print(f"results:{results}")
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

        try:
            production.set(results[0])
            daily_production.set(results[1])
            seven_days_production.set(results[2])
            lifetime_production.set(results[3])

            if "401" in str(data_results):
                print("inverters_production:    Unable to retrieve inverter data - Authentication failure")
            elif results[4] is None:
                print("inverters_production:    Inverter data not available from Envoy.")
            else:
                for sn,status in results[4].items():
                    inverter.labels([sn]).set(status[0])
        except:
            print("Error parsing results")
            print(results)

        time.sleep(60)


if __name__ == '__main__':
    main()

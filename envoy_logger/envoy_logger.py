#!/usr/bin/env python3

import argparse
import json
import logging
import os
from prometheus_client import start_http_server, Gauge
import requests
import time
import urllib3

logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
urllib3.disable_warnings() # or it will complain about the self signed cert on the envoy

def parse_args():
    parser = argparse.ArgumentParser(description="envoy-logger")
    parser.add_argument(
        "--loglevel",
        help="Minimum loglevel, default is %(default)s",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
    )
    parser.add_argument(
        "--user",
        default=os.environ.get("user", ""),
        help="username to use to obtain auth token. default taken from the user env var.",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("password", ""),
        help="password to use to obtain auth token. default taken from the password env var.",
    )
    parser.add_argument(
        "--serial",
        default=os.environ.get("serial", ""),
        help="envoy serial number to use to obtain auth token. default taken from the envoy_serial env var.",
    )
    parser.add_argument(
        "--hostname",
        default=os.environ.get("hostname", "envoy.local"),
        help="hostname for the local envoy. default is taken from the envoy_hostname env var.",
    )
    args = parser.parse_args()

    loglevel = getattr(logging, args.loglevel)
    logging.basicConfig(
        level=loglevel, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger.debug(args)

    return args


def get_web_token(args):
    login_url = "https://enlighten.enphaseenergy.com/login/login.json?"
    token_url = "https://entrez.enphaseenergy.com/tokens"

    envoy_token = os.environ.get("envoy_token", "")
    if envoy_token == "":
        if args.user != "" and args.password != "":
            logger.info("Requesting web token.")
            data = {"user[email]": args.user, "user[password]": args.password}
            response = requests.post(login_url, data=data)
            response_data = json.loads(response.text)
            data = {
                "session_id": response_data["session_id"],
                "serial_num": args.serial,
                "username": args.user,
            }
            response = requests.post(token_url, json=data)
            envoy_token = response.text
        else:
            logger.info("user/password not defined.")
    else:
        logger.info("using envoy_token env var")

    if envoy_token == "":
        logger.error("failed retrieving token. exiting")
        exit(-1)

    logger.info("obtained api token")
    logger.debug(f"envoy_token:{envoy_token}")
    return envoy_token


def get_envoy_data(production_url, raw_token):
    logger.debug(f"requesting data from {production_url}")
    h = {"Authorization": "Bearer " + raw_token}
    s = requests.Session()
    r = s.get(production_url, headers=h, verify=False)
    if r.status_code != 200:
        logger.debug(f"response:{r}")
    else: 
        return json.loads(r.text)


def main():
    args = parse_args()
    envoy_token = get_web_token(args)

    metric_prefix = "envoy"
    port = 9433  # for prometheus endpoint
    production = Gauge(
        f"{metric_prefix}_production", "Current system power production (W)"
    )
    daily_production = Gauge(
        f"{metric_prefix}_daily_production", "Current day's energy production (Wh)"
    )
    seven_days_production = Gauge(
        f"{metric_prefix}_seven_day_production",
        "Current seven day energy production (Wh)",
    )
    lifetime_production = Gauge(
        f"{metric_prefix}_lifetime_production", "Lifetime energy production (Wh)"
    )
    inverter = Gauge(
        f"{metric_prefix}_inverter",
        f"Inverter current power production (W)",
        ["serial_number"],
    )

    start_http_server(port)

    local_base = f"https://{args.hostname}"
    production_meter_url = f"{local_base}/api/v1/production"
    inverter_production_url = f"{local_base}/api/v1/production/inverters"

    while True:
        inverters = get_envoy_data(inverter_production_url, envoy_token)
        logger.debug(f"inverter_production:{inverters}")
        if inverters is not None:
            for i in inverters:
                inverter.labels(i['serialNumber']).set(i['lastReportWatts'])

        e_production = get_envoy_data(production_meter_url, envoy_token)
        logger.debug(f"production_meter:{e_production}")
        if e_production is not None:
            production.set(e_production["wattsNow"])
            daily_production.set(e_production["wattHoursToday"])
            seven_days_production.set(e_production["wattHoursSevenDays"])
            lifetime_production.set(e_production["wattHoursLifetime"])

        time.sleep(60)


if __name__ == "__main__":
    main()

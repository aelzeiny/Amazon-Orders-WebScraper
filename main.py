import os
import logging
import argparse
import tqdm


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filemode="w",
)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

import pages


def signin(driver, email, password, totp):
    if not email:
        email = os.environ["AP_EMAIL"]
    if not password:
        password = os.environ["AP_PASSWORD"]
    if not totp:
        totp = os.environ["AP_TOTP"]

    logging.info("Loading email")
    email_page = pages.PrimeLoginEmailPage(driver)
    email_page.load()
    logging.info("Setting password")
    password_page = email_page.username(email)
    password_page.load()
    otp_page = password_page.password(password)

    try:
        otp_page.load()
    except:
        logging.info("No TOTP")
        return

    logging.info("Setting TOTP")
    otp_page.otp(totp)


def get_receipt_path(order_receipts_path: str, order_id: str):
    return os.path.join(order_receipts_path, order_id)


def scrape_amazon_orders(
    email: str,
    password: str,
    totp: str,
    chrome_driver_path: str,
    order_receipts_path: str,
    headless: bool,
):
    if not chrome_driver_path:
        logging.info("Downloading ChromeDriver if not available")
        import chromedriver_autoinstaller
        chrome_driver_path = chromedriver_autoinstaller.install()

    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    signin(driver, email, password, totp)

    orders_page = pages.OrdersSummaryPage(driver)
    orders_page.load()
    recent_orders = []

    while orders_page is not None:
        recent_orders.extend(orders_page.get_order_ids())
        orders_page = orders_page.maybe_next_page()

    if not recent_orders:
        logging.warning("No orders found on page")
        return

    unscraped_orders = [
        o
        for o in recent_orders
        if not os.path.exists(get_receipt_path(order_receipts_path, o))
    ]

    if not unscraped_orders:
        logging.info(f"No new orders. Found {len(recent_orders)}/{len(recent_orders)}")

    for order_id in tqdm.tqdm(unscraped_orders):
        logging.info(f"Downloading receipt for order: {order_id}")
        order_page = pages.OrderPage(driver, order_id)
        order_page.load()
        with open(get_receipt_path(order_receipts_path, order_id), "w") as f:
            f.write(str(order_page))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process the paths for Chrome driver and order receipts."
    )

    parser.add_argument(
        "-e",
        "--email",
        type=str,
        default="",
    )
    parser.add_argument(
        "-p",
        "--password",
        type=str,
        default="",
    )
    parser.add_argument(
        "-t",
        "--totp",
        type=str,
        help="TOTP secret for 2-factor auth",
        default="",
    )
    parser.add_argument(
        "-c",
        "--chrome_driver_path",
        type=str,
        help="(Optional) Path to the Chrome WebDriver executable.",
        default=''
    )
    parser.add_argument(
        "-o",
        "--order_receipts_path",
        type=str,
        help="Path to the directory containing order receipts",
    )
    parser.add_argument(
        "-head",
        "--headless",
        type=bool,
        help="Headless ChromeDriver",
        default=True,
    )
    scrape_amazon_orders(**dict(vars(parser.parse_args())))

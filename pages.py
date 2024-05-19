from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class PageObject(ABC):
    def __init__(self, driver):
        self.driver = driver

    @abstractmethod
    def did_load(self):
        pass

    def load(self, timeout=10):
        WebDriverWait(self.driver, timeout).until(lambda _: self.did_load())


class PrimeOTPPage(PageObject):
    @property
    def otp_input(self):
        return self.driver.find_element(By.ID, "auth-mfa-otpcode")
    
    @property
    def signin_btn(self):
        return self.driver.find_element(By.ID, "auth-signin-button")
    
    def did_load(self):
        try:
            return self.signin_btn and self.otp_input
        except:
            return False
        
    def otp(self, otp_secret: str) -> None:
        import pyotp
        totp_gen = pyotp.TOTP(otp_secret)

        old_url = self.driver.current_url
        self.otp_input.send_keys(totp_gen.now())
        self.signin_btn.click()
        WebDriverWait(self.driver, 10).until(lambda driver: driver.current_url != old_url)


class PrimeLoginPasswordPage(PageObject):
    @property
    def password_input(self):
        return self.driver.find_element(By.ID, "ap_password")

    @property
    def signin_btn(self):
        return self.driver.find_element(By.ID, "signInSubmit")

    def password(self, password: str) -> PrimeOTPPage:
        self.password_input.send_keys(password)
        self.signin_btn.click()
        return PrimeOTPPage(self.driver)
    
    def did_load(self):
        try:
            return self.signin_btn and self.password
        except:
            return False


class PrimeLoginEmailPage(PageObject):
    def __init__(self, driver):
        super().__init__(driver)
        self.driver.get("https://www.amazon.com/gp/sign-in.html")

    @property
    def email_input(self):
        return self.driver.find_element(By.ID, "ap_email")

    @property
    def continue_btn(self):
        return self.driver.find_element(By.ID, "continue")

    def username(self, email: str) -> PrimeLoginPasswordPage:
        self.email_input.send_keys(email)
        self.continue_btn.click()
        return PrimeLoginPasswordPage(self.driver)

    def did_load(self):
        try:
            return self.email_input and self.continue_btn
        except:
            return False


@dataclass
class OrderLink:
    """example: https://www.amazon.com/gp/css/order-details?orderID=111-1602829-9424211&ref=ppx_yo2ov_dt_b_fed_order_details"""
    href: str

    def get_order_id(self):
        parsed_url = urlparse(self.href)
        query_params = parse_qs(parsed_url.query)
        if 'orderID' in query_params:
            return query_params['orderID'][0]
        return None


class OrdersSummaryPage(PageObject):
    def __init__(self, driver, url="https://www.amazon.com/gp/css/order-history/ref=oh_surl_yo"):
        super().__init__(driver)
        self.driver.get(url)
    
    @property
    def next_page_btn(self):
        return self.driver.find_element(By.CSS_SELECTOR, 'ul.a-pagination .a-last a')

    def _get_order_links(self):
        return self.driver.find_elements(By.CSS_SELECTOR, '[href*="gp/css/order-details"], [href*="/gp/your-account/order-details"]')

    def get_order_ids(self) -> list[OrderLink]:
        return list(set([
            OrderLink(l.get_attribute('href')).get_order_id() 
            for l in self._get_order_links()
        ]))
    
    def maybe_next_page(self) -> Optional['OrdersSummaryPage']:
        try:
            self.next_page_btn
        except:
            return None
        
        return self.__class__(self.driver, self.next_page_btn.get_attribute('href'))
    
    def did_load(self):
        try:
            return self._get_order_links()
        except:
            return False


class OrderPage(PageObject):
    def __init__(self, driver, order_id: str):
        super().__init__(driver)
        self.order_id = order_id
        self.driver.get(f"https://www.amazon.com/gp/css/summary/print.html?orderID={order_id}")

    def did_load(self):
        try:
            return self.order_id in str(self)
        except:
            return False
    
    def __str__(self):
        return self.driver.page_source

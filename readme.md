# Amazon Orders WebScrapper
This repo scraps your Amazon Order Summary page with a headless browser, and downloads receipts. This involves:
1. Logging in with a username, password, and TOTP
2. Visiting the order-summary page, grabbing all order-ids.
3. Clicking the "next" button at the bottom of the page. 
4. Repeat steps 2-3 until there are no more pages.
5. Visiting every order-id page and downloading the receipt.
6. Saving each receipt into a specified folder as HTML.

### Example Usage:
```
python main.py -e 'user@email.com' -p 'hunter2' -t 'your_52_digit_totp_secret' -o './receipts'
```

Or, set the environmental variables `AP_EMAIL`, `AP_PASSWORD`, and `AP_TOTP` for email, password, and totp secret respectively.

```
python main.py -o './receipts'
```

### Why?
* The wonderful minds behind the **AWS CLOUD** cannot provide an OAuth API 🙃
* Amazon is mostly server-side generated, and AFAIK there's no direct API call that can grab these details.
* Amazon killed the "download orders as CSV" feature.

### Two-Factor Auth with TOTP tokens
Amazon will always use 2FA to authenticate you. If you have 2FA disabled in your settings it'll text and email you. As a result this repo requires that you use a TOTP app. For example, Google Authenticator.

With Google Authenticator, export your Amazon TOTP to a QR code. Use any QR app to parse that QR Code to text. Then use [this repo](github.com/dim13/otpauth) to convert the URL from that QR-Code into a base32 secret.
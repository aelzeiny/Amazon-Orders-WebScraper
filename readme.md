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

### Docker
The image carries Chromium, a matching chromedriver and a virtual display, so the only thing it needs from the
host is one mounted directory for its state:

| path in the mount | what it is |
|---|---|
| `receipts/` | one HTML receipt per order, named by order id (the `-o` folder) |
| `profile/` | the Chromium profile: cookies carry over between runs |

```
docker build -t amazon-orders-webscraper .
docker run --rm --env-file .env --user "$(id -u):$(id -g)" -v "$PWD/data:/data" amazon-orders-webscraper
```
Arguments after the image name go to `main.py`. `--user` keeps the files in the mounted directory owned by you. The credentials come from `.env` (see `.env.example`).

### What keeps Amazon from blocking the scraper
Amazon does not serve a captcha to automation it dislikes; it serves a "Sorry! Something went wrong on our end"
page, and the sign-in form never appears. These practices apply wherever you run it (the Dockerfile bakes them
in), in order of how much they matter:

1. **Do not run headless.** `--headless` is what Amazon fingerprints. The container runs a normal, headed Chromium
   on a virtual display (`xvfb-run`), which looks like a desktop browser. On a desktop, pass `-head false` to
   `main.py` and it uses your real display instead.
2. **Keep the browser profile.** A fresh profile is a new, unknown device every run, and unknown devices are what
   get blocked. With `AP_PROFILE_DIR` set (the image points it at `/data/profile`), cookies persist, the password
   page's "Keep me signed in" is ticked, and the next run usually finds the orders page already open
   (`Already signed in` in the log) with no sign-in at all. When Amazon does ask again, it recognises the device
   and often skips the email step; the scraper handles both. Delete `profile/` to force a full sign-in.
3. **Let the browser tell the truth.** Do not spoof the user agent: a made-up string contradicts the client hints
   the real browser sends (its actual OS and version), which is itself a signal. Use a chromedriver that matches
   your Chrome version, whatever platform you are on; `-c` points at one, otherwise the scraper fetches a match.
4. **Use a TOTP secret, not SMS.** The sign-in is fully automatic only with `AP_TOTP` (see below). A remembered
   device rarely gets asked for it.
5. **Run one instance per profile.** Chromium refuses to share a profile between two live browsers. The scraper
   clears a stale lock left by a killed run, but do not schedule overlapping runs against the same mount.

Two container details are easy to get wrong: `xvfb-run` waits for the X server's `SIGUSR1` "ready" signal, which a
container's PID 1 never receives, so the image starts through `tini` (also reaps the browser processes a crashed
run leaves behind); and Chromium in a Linux container needs `--no-sandbox` and `--disable-dev-shm-usage`, which
the scraper always sets.

### Why?
* The wonderful minds behind the **AWS CLOUD** cannot provide an OAuth API 🙃
* Amazon is mostly server-side generated, and AFAIK there's no direct API call that can grab these details.
* Amazon killed the "download orders as CSV" feature.

### Two-Factor Auth with TOTP tokens
Amazon will always use 2FA to authenticate you. If you have 2FA disabled in your settings it'll text and email you. As a result this repo requires that you use a TOTP app. For example, Google Authenticator.

With Google Authenticator, export your Amazon TOTP to a QR code. Use any QR app to parse that QR Code to text. Then use [this repo](github.com/dim13/otpauth) to convert the URL from that QR-Code into a base32 secret.
# Boosty Blog to RSS

This repo is Work In Progress.

# How-to

Clone repo to your local computer then run commands^

```bash
pipenv shell
pipenv install
python3 boosty_to_rss.py zanesli
>>> Enter your phone number: +71234567890
>>> SMS Code: 111111
>>> Destructor called, vehicle deleted.
```

Upload file `zanesli.rss` to any HTTP hosting. You may choose any other boosty blog (but why would you need that?).

All authentication info is stored on your computer in `config.json`. On next run you will not need to enter your phone and code from sms. Some time in future it will break, because token will expire and script doesn't handle it. Then you should delete `config.json` and reauthenticate.

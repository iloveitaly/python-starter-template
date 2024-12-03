# Localias on GitHub Actions

This GitHub Action installs and configures [Localias](https://github.com/peterldowns/localias) to enable HTTPS domains for CI tests. It handles certificate installation and system configuration to ensure proper HTTPS functionality in testing environments.

## Features

- Installs and runs Localias as a daemon
- Configures system CA certificates
- Sets up NSS database for Chrome/Chromium compatibility (for playright, cypress, etc)
- Validates HTTPS functionality with curl tests based on a domain in `.localias.yml`

## Usage


```yaml
steps:
  - uses: iloveitaly/github-actions-localias@master
```


## What it does

1. Installs Localias if not present
2. Starts Localias daemon
3. Waits for self-signed certificate generation
4. Refreshes system CA certificates
5. Creates and configures NSS database for Chrome/Chromium
6. Validates HTTPS setup with curl tests


## Development Notes

* You'll see an error message (with a typo) `not NSS security databases found` even if the NSS DB exists. This occurs
  even under `sudo -E` and it really shouldn't [because the directory it references definitely exists](https://github.com/smallstep/truststore/blob/d71bcdef66e239112d877b3e531e1011795efdf7/truststore_nss.go#L16).
* `curl` will succeed if retried multiple times. I have no idea why this is happening. There must be some CA store refresh process which runs async. Rather than trying to understand what is going on, we just retry a handful of times.
* Installing `libnss3-tools` does not initialize the NSS DB. You must do this manually.
* `curl` does not use the NSS DB but Chromium does.
* `sudo localias debug cert --print | sudo tee -a /etc/ssl/certs/ca-certificates.crt` executes correctly with caddy, this is not necessary.
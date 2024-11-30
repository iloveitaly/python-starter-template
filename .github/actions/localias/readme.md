

* You'll see an error message (with a typo) `not NSS security databases found` even if the NSS DB exists. This occurs
  even under `sudo -E` and it really shouldn't [because the directory it references definitely exists](https://github.com/smallstep/truststore/blob/d71bcdef66e239112d877b3e531e1011795efdf7/truststore_nss.go#L16).
* `curl` will succeed if retried multiple times. I have no idea why this is happening. There must be some CA store refresh process which runs async. Rather than trying to understand what is going on, we just retry a handful of times.
* Installing `libnss3-tools` does not initialize the NSS DB. You must do this manually.
* `curl` does not use the NSS DB but Chromium does.
* `sudo localias debug cert --print | sudo tee -a /etc/ssl/certs/ca-certificates.crt` executes correctly with caddy, this is not necessary.
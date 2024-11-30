#!/usr/bin/env bash

set -v

banner_echo() {
  printf "\n\033[0;36m%s   \033[0m\n" "$1"
}

# when this directory is properly configured, you should see the following files: cert9.db  key4.db  pkcs11.txt
[ ! -d "$HOME/.pki/nssdb" ] && mkdir -p "$HOME/.pki/nssdb" && certutil -d sql:$HOME/.pki/nssdb -N --empty-password

banner_echo "Checking for NSS DB..."
# ls -l $HOME/.pki/nssdb

# banner_echo "Installed certificates:"
# certutil -L -d sql:${HOME}/.pki/nssdb

if ! command -v localias >/dev/null & then
  banner_echo "Installing localias"
  cat "$GITHUB_ACTION_PATH/install.sh" | sh -s -- --yes
fi

banner_echo "where is the cert"
sudo localias debug cert

banner_echo "Starting localias..."
# don't run as daemon so we can see the logs
sudo localias start

# when the daemon has finished initializing
cert_location=$(sudo localias debug cert)
daemon_success=false

for i in {1..5}; do
  banner_echo "Checking for self-signed cert: $cert_location..."

  if sudo [ -f "$cert_location" ]; then
    daemon_success=true
  else
    sleep 2
  fi

  if $daemon_success; then
    break
  fi
done

$daemon_success || exit 1

# localias (caddy) appends the self-signed certificate to /etc/ssl/certs/ca-certificates.crt
# but the system is not refreshed, which causes curl and various other systems to *not* pick up on the new certificate
banner_echo "Refreshing system CA certs..."
sudo update-ca-certificates --fresh

# leave enough time for localias to initialize and generate certificates
# TODO there's got to be a more deterministic way to handle this
# sleep 15

# certs are *not* installed by Caddy in the right location by default
# specifically, we know this fixes `curl` so it respects our self-signed SSL certificates
banner_echo "Installing locally signed cert"
# sudo localias debug cert --print | sudo tee -a /etc/ssl/certs/ca-certificates.crt

# sudo update-ca-certificates --fresh

# https://stackoverflow.com/a/75352343/129415
# TODO should we set this here? makes httpie work?
# REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
# export NODE_EXTRA_CA_CERTS="/path/to/cert.pem"

banner_echo "Datetime config..."
timedatectl

# TODO should pick a domain from the environment and test it
curl_success=false
for i in {1..5}; do
  banner_echo "Checking HTTPs via curl..."
  curl -vvv --head https://api-test.localhost && curl_success=true && break || sleep 1
done
$curl_success || exit 1

banner_echo "Creating shared NSS DB..."
# when this directory is properly configured, you should see the following files: cert9.db  key4.db  pkcs11.txt
[ ! -d "$HOME/.pki/nssdb" ] && mkdir -p "$HOME/.pki/nssdb" && certutil -d sql:$HOME/.pki/nssdb -N --empty-password

# https://chromium.googlesource.com/chromium/src/+/master/docs/linux/cert_management.md
banner_echo "Installing certificates for Chrome and others using shared NSS DB..."
sudo certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n localias-cert -i $(sudo localias debug cert)

banner_echo "Installed certificates:"
certutil -L -d sql:${HOME}/.pki/nssdb

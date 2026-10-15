#!/bin/sh
# Chrome resolves *.localhost to loopback and does not consult /etc/hosts.
# Forward the container's loopback 80/443 to the host, where localias listens.

set -eu

host_ip_from_gateway_hex() {
  # /proc/net/route stores the gateway as little-endian hex
  gw=$1
  a=$(printf '%d' "0x$(printf '%s' "$gw" | cut -c7-8)")
  b=$(printf '%d' "0x$(printf '%s' "$gw" | cut -c5-6)")
  c=$(printf '%d' "0x$(printf '%s' "$gw" | cut -c3-4)")
  d=$(printf '%d' "0x$(printf '%s' "$gw" | cut -c1-2)")
  printf '%s.%s.%s.%s\n' "$a" "$b" "$c" "$d"
}

if [ "${1:-}" = "--print-host-ip" ]; then
  host_ip_from_gateway_hex "$2"
  exit 0
fi

route_file=${ROUTE_FILE:-/proc/net/route}
gw=$(awk '$2=="00000000" {print $3; exit}' "$route_file")

if [ -z "$gw" ]; then
  echo "chrome localhost proxy: no default route in $route_file" >&2
  exit 1
fi

host_ip=$(host_ip_from_gateway_hex "$gw")
echo "forwarding loopback 80/443 to ${host_ip}"

# background jobs must be children of this shell. a $(...) subshell sends them SIGHUP.
pids=""

forward_port() {
  port=$1
  socat "TCP-LISTEN:${port},fork,reuseaddr,bind=127.0.0.1" "TCP:${host_ip}:${port}" &
  pids="$pids $!"
}

forward_port 80
forward_port 443

if [ -r /proc/net/if_inet6 ] && grep -q '^00000000000000000000000000000001 ' /proc/net/if_inet6; then
  socat "TCP6-LISTEN:80,fork,reuseaddr,ipv6only=1,bind=[::1]" "TCP:${host_ip}:80" &
  pids="$pids $!"
  socat "TCP6-LISTEN:443,fork,reuseaddr,ipv6only=1,bind=[::1]" "TCP:${host_ip}:443" &
  pids="$pids $!"
fi

port_is_listening() {
  port_hex=$(printf '%04X' "$1")
  # state 0A is LISTEN. match the local port only, not an outbound :443.
  awk -v port="$port_hex" '
    NR > 1 && toupper($4) == "0A" && toupper($2) ~ ":" port "$" { found = 1 }
    END { exit found ? 0 : 1 }
  ' /proc/net/tcp
}

sleep 0.2

if ! port_is_listening 80 || ! port_is_listening 443; then
  echo "chrome localhost proxy: loopback 80/443 is not listening" >&2
  kill $pids 2>/dev/null || true
  exit 1
fi

stop_forwards() {
  kill $pids 2>/dev/null || true
}

trap 'stop_forwards; exit 0' TERM INT

while true; do
  for pid in $pids; do
    if ! kill -0 "$pid" 2>/dev/null; then
      stop_forwards
      exit 1
    fi
  done

  sleep 1
done

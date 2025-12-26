#!/usr/bin/env bash

set -euo pipefail

IP="$(getent ahostsv4 host.docker.internal | awk 'NR==1{print $1}')"
echo "address=/.localhost/${IP}" > /etc/dnsmasq.d/host-gateway.conf

cat /etc/resolv.conf | grep -E "^nameserver" | sed -e 's/nameserver\s*/server=/g' > /etc/dnsmasq.d/resolv.conf

modify_conf() {
  [ -f /etc/resolv.conf ] && cp /etc/resolv.conf /etc/resolv.conf.bak && echo "nameserver 127.0.0.1" > /etc/resolv.conf
  cat /etc/hosts > /etc/hosts.bak
  cat /etc/hosts | sed '/localhost/d' | tee /etc/hosts
}

restore_conf() {
  [ -f /etc/resolv.conf.bak ] && cat /etc/resolv.conf.bak > /etc/resolv.conf && rm /etc/resolv.conf.bak
  [ -f /etc/hosts.bak ] && cat /etc/hosts.bak > /etc/hosts && rm /etc/hosts.bak
}

cleanup() {
  [ -n "$DNSMASQ_PID" ] && kill $DNSMASQ_PID 2>/dev/null
  restore_conf
}

trap cleanup EXIT INT TERM
modify_conf

/usr/sbin/dnsmasq --conf-file=/etc/dnsmasq.conf --keep-in-foreground &
DNSMASQ_PID=$!

wait $DNSMASQ_PID
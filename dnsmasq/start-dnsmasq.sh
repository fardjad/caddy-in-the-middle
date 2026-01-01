#!/usr/bin/env bash

set -euo pipefail

cat /etc/resolv.conf | grep -E "^nameserver" | sed -e 's/nameserver\s*/server=/g' > /etc/dnsmasq.d/resolv.conf

modify_conf() {
  [ -f /etc/resolv.conf ] && cp /etc/resolv.conf /etc/resolv.conf.bak && echo "nameserver 127.0.0.1" > /etc/resolv.conf
}

restore_conf() {
  [ -f /etc/resolv.conf.bak ] && cat /etc/resolv.conf.bak > /etc/resolv.conf && rm /etc/resolv.conf.bak
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
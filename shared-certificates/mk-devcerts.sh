#!/usr/bin/env bash

set -euo pipefail

# Outputs go to ./certs
# - certs/rootCA.pem (PEM) -> trust this in OS trust stores
# - certs/rootCA.cer (DER) -> handy for Windows
#
# Notes / docs:
# - https://github.com/cloudflare/cfssl
# - https://caddyserver.com/docs/caddyfile/directives/tls

cd "$(dirname "$0")" || exit 1

for cmd in cfssl cfssljson openssl; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "'$cmd' is not installed or not in PATH."
    exit 1
  fi
done

OUTDIR="${OUTDIR:-certs}"
mkdir -p "$OUTDIR"

PFX_PASSWORD="${PFX_PASSWORD:-secret}"

cat <<EOF > "$OUTDIR/ca-csr.json" 
{
  "CN": "CITM Root CA",
  "key": { "algo": "rsa", "size": 4096 },
  "names": [],
  "ca": { "expiry": "876000h" }
}
EOF

# 9600h is the maximum lifetime supported by Apple
cat <<EOF > "$OUTDIR/ca-config.json"
{
  "signing": {
    "default": { "expiry": "876000h" },
    "profiles": {
      "server": {
        "usages": ["signing","key encipherment","server auth"],
        "expiry": "9600h"
      },
      "client": {
        "usages": ["signing","key encipherment","client auth"],
        "expiry": "9600h"
      }
    }
  }
}
EOF

if [[ ! -f "$OUTDIR/rootCA.pem" || ! -f "$OUTDIR/rootCA-key.pem" ]]; then
  echo "Generating local Root CA..."
  (cd "$OUTDIR" && cfssl genkey -initca ca-csr.json | cfssljson -bare rootCA)
  openssl x509 -in "$OUTDIR/rootCA.pem" -outform DER -out "$OUTDIR/rootCA.cer"
fi

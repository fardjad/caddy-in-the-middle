FROM cfssl/cfssl:latest AS cfssl

FROM ubuntu

COPY --from=cfssl --chown=root:root /workdir/bin/* /usr/bin/
RUN <<EOF
apt-get update
apt-get install -y openssl
EOF

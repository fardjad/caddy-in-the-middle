# Shared Certificates

This directory contains a bash script (`mk-devcerts.sh`) that generates a Root
CA for CaddyInTheMiddle. This Root CA is used to sign server certificates
on-demand. The generated Root CA can be trusted in other environments (such as
machines, containers, or applications) to enable secure communication with
CaddyInTheMiddle.

You can also run the script in a container to avoid installing dependencies
locally. To do so, run:

```bash
docker compose run --rm maker
```

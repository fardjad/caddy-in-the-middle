# Development Root CA Generation

CITM expects a Root CA certificate and key to be available as:

- `rootCA.pem`
- `rootCA-key.pem`

### Prerequisites

The following tools are required in `PATH`:

- `cfssl` and `cfssljson` from
  [Cloudflare CFSSL](https://github.com/cloudflare/cfssl)
- `openssl` from [OpenSSL](https://github.com/openssl/openssl)

### 1) Output Directory

```bash
mkdir -p certs
```

The command above creates the output directory.

### 2) CA CSR Definition

File: `certs/ca-csr.json`

```json
{
  "CN": "CITM Root CA",
  "key": { "algo": "rsa", "size": 4096 },
  "names": [],
  "ca": { "expiry": "876000h" }
}
```

This sets the Root CA common name and creates a 4096-bit RSA key. The CA expiry
is set to `876000h` (about 100 years).

### 3) CA Signing Config

File: `certs/ca-config.json`

```json
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
```

`9600h` is used for leaf certificate profiles to stay within Apple's maximum
supported lifetime for server/client certificates.

### 4) Root CA Keypair Generation

Command execution directory: `certs`

```bash
cd certs
cfssl genkey -initca ca-csr.json | cfssljson -bare rootCA
```

Generated files:

- `rootCA.pem`
- `rootCA-key.pem`

### 5) DER Export (Optional)

```bash
openssl x509 -in rootCA.pem -outform DER -out rootCA.cer
```

### 6) Output Verification

```bash
ls -l rootCA.pem rootCA-key.pem
```

### 7) OS Trust Store Registration (Optional)

Local HTTPS validation can be enabled by registering the generated Root CA in
the operating system trust store.

Windows trust-store import commonly uses the DER-encoded certificate
(`rootCA.cer`) generated in Step 5.

macOS example:

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain rootCA.pem
```

Debian/Ubuntu example:

```bash
sudo cp rootCA.pem /usr/local/share/ca-certificates/citm-root-ca.crt
sudo update-ca-certificates
```

Windows PowerShell example:

```powershell
Import-Certificate -FilePath .\rootCA.cer -CertStoreLocation Cert:\LocalMachine\Root
```

import datetime
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_root_ca(output_dir: Path) -> None:
    """
    Generates a self-signed Root CA certificate and private key.

    Args:
        output_dir: Directory where the generated files will be saved.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    public_key = private_key.public_key()

    builder = x509.CertificateBuilder()

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "CITM Root CA"),
        ]
    )

    builder = builder.subject_name(subject)
    builder = builder.issuer_name(issuer)
    builder = builder.public_key(public_key)
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.not_valid_before(datetime.datetime.now(datetime.timezone.utc))
    builder = builder.not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    )

    builder = builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True
    )
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_cert_sign=True,
            crl_sign=True,
            content_commitment=False,
            key_agreement=False,
            data_encipherment=False,
            key_encipherment=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )
    builder = builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(public_key),
        critical=False,
    )

    certificate = builder.sign(private_key=private_key, algorithm=hashes.SHA256())

    with open(output_dir / "rootCA-key.pem", "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(output_dir / "rootCA.pem", "wb") as f:
        f.write(certificate.public_bytes(serialization.Encoding.PEM))

    with open(output_dir / "rootCA.cer", "wb") as f:
        f.write(certificate.public_bytes(serialization.Encoding.DER))

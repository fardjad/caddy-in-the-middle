using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;

namespace Testcontainers.CaddyInTheMiddle;

/// <summary>
/// Helper class for generating self-signed certificates for testing.
/// </summary>
public static class CaddyInTheMiddleCertificates
{
    /// <summary>
    /// Generates a self-signed Root CA certificate and private key in the specified output directory.
    /// Creates 'rootCA.pem', 'rootCA-key.pem', and 'rootCA.cer'.
    /// </summary>
    /// <param name="outputDir">The directory where the certificate files will be generated.</param>
    public static void Generate(string outputDir)
    {
        using var rsa = RSA.Create(4096);
        var req = new CertificateRequest(
            "CN=CITM Root CA",
            rsa,
            HashAlgorithmName.SHA256,
            RSASignaturePadding.Pkcs1
        );

        req.CertificateExtensions.Add(new X509BasicConstraintsExtension(
            true,
            false,
            0,
            true
        ));
        req.CertificateExtensions.Add(new X509KeyUsageExtension(
            X509KeyUsageFlags.DigitalSignature | X509KeyUsageFlags.KeyCertSign | X509KeyUsageFlags.CrlSign,
            true
        ));
        req.CertificateExtensions.Add(new X509SubjectKeyIdentifierExtension(req.PublicKey, false));

        var expiration = DateTimeOffset.UtcNow.AddYears(1);
        using var cert = req.CreateSelfSigned(DateTimeOffset.UtcNow, expiration);

        var certPem = cert.ExportCertificatePem();
        File.WriteAllText(Path.Combine(outputDir, "rootCA.pem"), certPem);

        var keyPem = rsa.ExportPkcs8PrivateKeyPem();
        File.WriteAllText(Path.Combine(outputDir, "rootCA-key.pem"), keyPem);

        File.WriteAllBytes(Path.Combine(outputDir, "rootCA.cer"), cert.Export(X509ContentType.Cert));
    }
}
using Docker.DotNet.Models;
using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Configurations;

namespace Testcontainers.CaddyInTheMiddle;

/// <summary>
/// Configuration for the CaddyInTheMiddle container.
/// </summary>
public class CaddyInTheMiddleConfiguration : ContainerConfiguration
{
    /// <summary>
    /// Initializes a new instance of the <see cref="CaddyInTheMiddleConfiguration" /> class.
    /// </summary>
    /// <param name="certsDirectory">Directory containing root CA certificates.</param>
    /// <param name="caddyfileDirectory">Directory containing custom Caddyfile configurations.</param>
    /// <param name="citmNetwork">Docker network to connect to.</param>
    /// <param name="dnsNames">DNS names to register for service discovery.</param>
    /// <param name="mocksDirectory">Directory containing mock templates.</param>
    /// <param name="mockPaths">Specific mock paths to load.</param>
    public CaddyInTheMiddleConfiguration(
        string? certsDirectory = null,
        string? caddyfileDirectory = null,
        string? citmNetwork = null,
        string[]? dnsNames = null,
        string? mocksDirectory = null,
        string[]? mockPaths = null)
    {
        CertsDirectory = certsDirectory;
        CaddyfileDirectory = caddyfileDirectory;
        CitmNetwork = citmNetwork;
        DnsNames = dnsNames;
        MocksDirectory = mocksDirectory;
        MockPaths = mockPaths;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="CaddyInTheMiddleConfiguration" /> class.
    /// </summary>
    /// <param name="resourceConfiguration">The Docker resource configuration.</param>
    public CaddyInTheMiddleConfiguration(IResourceConfiguration<CreateContainerParameters> resourceConfiguration)
        : base(resourceConfiguration)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="CaddyInTheMiddleConfiguration" /> class.
    /// </summary>
    /// <param name="resourceConfiguration">The Docker resource configuration.</param>
    public CaddyInTheMiddleConfiguration(IContainerConfiguration resourceConfiguration)
        : base(resourceConfiguration)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="CaddyInTheMiddleConfiguration" /> class.
    /// </summary>
    /// <param name="resourceConfiguration">The Docker resource configuration.</param>
    public CaddyInTheMiddleConfiguration(CaddyInTheMiddleConfiguration resourceConfiguration)
        : this(new CaddyInTheMiddleConfiguration(), resourceConfiguration)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="CaddyInTheMiddleConfiguration" /> class.
    /// </summary>
    /// <param name="oldValue">The old configuration value.</param>
    /// <param name="newValue">The new configuration value.</param>
    public CaddyInTheMiddleConfiguration(CaddyInTheMiddleConfiguration oldValue, CaddyInTheMiddleConfiguration newValue)
        : base(oldValue, newValue)
    {
        CertsDirectory = BuildConfiguration.Combine(oldValue.CertsDirectory, newValue.CertsDirectory);
        CaddyfileDirectory = BuildConfiguration.Combine(oldValue.CaddyfileDirectory, newValue.CaddyfileDirectory);
        CitmNetwork = BuildConfiguration.Combine(oldValue.CitmNetwork, newValue.CitmNetwork);
        DnsNames = BuildConfiguration.Combine(oldValue.DnsNames, newValue.DnsNames);
        MocksDirectory = BuildConfiguration.Combine(oldValue.MocksDirectory, newValue.MocksDirectory);
        MockPaths = BuildConfiguration.Combine(oldValue.MockPaths, newValue.MockPaths);
    }

    /// <summary>
    /// Gets the directory containing root CA certificates.
    /// </summary>
    public string? CertsDirectory { get; }

    /// <summary>
    /// Gets the directory containing custom Caddyfile configurations.
    /// </summary>
    public string? CaddyfileDirectory { get; }

    /// <summary>
    /// Gets the Docker network to connect to.
    /// </summary>
    public string? CitmNetwork { get; }

    /// <summary>
    /// Gets the DNS names to register for service discovery.
    /// </summary>
    public string[]? DnsNames { get; }

    /// <summary>
    /// Gets the directory containing mock templates.
    /// </summary>
    public string? MocksDirectory { get; }

    /// <summary>
    /// Gets the specific mock paths to load.
    /// </summary>
    public string[]? MockPaths { get; }
}
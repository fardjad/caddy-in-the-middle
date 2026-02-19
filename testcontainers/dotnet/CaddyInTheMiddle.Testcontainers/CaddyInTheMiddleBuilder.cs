using Docker.DotNet.Models;
using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Configurations;

namespace CaddyInTheMiddle.Testcontainers;

/// <summary>
/// A fluent builder for creating <see cref="CaddyInTheMiddleContainer" /> instances.
/// </summary>
public class CaddyInTheMiddleBuilder : ContainerBuilder<CaddyInTheMiddleBuilder, CaddyInTheMiddleContainer,
    CaddyInTheMiddleConfiguration>
{
    /// <summary>
    /// The Docker image to use for the container.
    /// </summary>
    public static readonly string CaddyInTheMiddleImage = $"fardjad/citm:{typeof(CaddyInTheMiddleBuilder).Assembly.GetName().Version?.ToString(3) ?? "0.0.0"}";

    /// <summary>
    /// The exposed HTTP port (80).
    /// </summary>
    public const ushort HttpPort = 80;

    /// <summary>
    /// The exposed HTTPS port (443).
    /// </summary>
    public const ushort HttpsPort = 443;

    /// <summary>
    /// The user-mapped port for the HTTP proxy.
    /// </summary>
    public const ushort HttpProxyPort = 8380;

    /// <summary>
    /// The user-mapped port for the SOCKS5 proxy.
    /// </summary>
    public const ushort SocksProxyPort = 8381;

    /// <summary>
    /// The user-mapped port for the Admin API.
    /// </summary>
    public const ushort AdminPort = 3858;

    /// <summary>
    /// Initializes a new instance of the <see cref="CaddyInTheMiddleBuilder" /> class.
    /// </summary>
    public CaddyInTheMiddleBuilder() : this(new CaddyInTheMiddleConfiguration())
    {
        DockerResourceConfiguration = Init().DockerResourceConfiguration;
    }

    private CaddyInTheMiddleBuilder(CaddyInTheMiddleConfiguration resourceConfiguration)
        : base(resourceConfiguration)
    {
        DockerResourceConfiguration = resourceConfiguration;
    }

    /// <inheritdoc />
    protected override CaddyInTheMiddleConfiguration DockerResourceConfiguration { get; }

    /// <summary>
    /// Sets the directory containing root CA certificates.
    /// </summary>
    /// <param name="certsDirectory">The directory path.</param>
    /// <returns>The builder instance.</returns>
    public CaddyInTheMiddleBuilder WithCertsDirectory(string certsDirectory)
    {
        return Merge(DockerResourceConfiguration, new CaddyInTheMiddleConfiguration(certsDirectory))
            .WithBindMount(certsDirectory, "/certs");
    }

    /// <summary>
    /// Sets the directory containing custom Caddyfile configurations.
    /// </summary>
    /// <param name="caddyfileDirectory">The directory path.</param>
    /// <returns>The builder instance.</returns>
    public CaddyInTheMiddleBuilder WithCaddyfileDirectory(string caddyfileDirectory)
    {
        return Merge(DockerResourceConfiguration,
                new CaddyInTheMiddleConfiguration(caddyfileDirectory: caddyfileDirectory))
            .WithBindMount(caddyfileDirectory, "/etc/caddy/conf.d");
    }

    /// <summary>
    /// Connects the container to the specified Docker network and sets the 'citm_network' label.
    /// </summary>
    /// <param name="citmNetwork">The network name.</param>
    /// <returns>The builder instance.</returns>
    public CaddyInTheMiddleBuilder WithCitmNetwork(string citmNetwork)
    {
        return Merge(DockerResourceConfiguration, new CaddyInTheMiddleConfiguration(citmNetwork: citmNetwork))
            .WithNetwork(citmNetwork)
            .WithLabel("citm_network", citmNetwork);
    }

    /// <summary>
    /// Sets the DNS names for the container for service discovery.
    /// </summary>
    /// <param name="dnsNames">The DNS names.</param>
    /// <returns>The builder instance.</returns>
    public CaddyInTheMiddleBuilder WithDnsNames(params string[] dnsNames)
    {
        var joinedDnsNames = string.Join(",", dnsNames);
        return Merge(DockerResourceConfiguration, new CaddyInTheMiddleConfiguration(dnsNames: dnsNames))
            .WithLabel("citm_dns_names", joinedDnsNames);
    }

    /// <summary>
    /// Sets the directory containing mock templates.
    /// </summary>
    /// <param name="mocksDirectory">The directory path.</param>
    /// <returns>The builder instance.</returns>
    public CaddyInTheMiddleBuilder WithMocksDirectory(string mocksDirectory)
    {
        var builder = Merge(DockerResourceConfiguration,
                new CaddyInTheMiddleConfiguration(mocksDirectory: mocksDirectory))
            .WithBindMount(mocksDirectory, "/citm-mocks/");

        // If mock paths are not explicitly set yet, set the default
        if (DockerResourceConfiguration.MockPaths == null || DockerResourceConfiguration.MockPaths.Length == 0)
            builder = builder.WithEnvironment("MOCK_PATHS", "/citm-mocks/**/*.mako");

        return builder;
    }

    /// <summary>
    /// Sets specific mock paths to load.
    /// </summary>
    /// <param name="mockPaths">The glob patterns for mock files.</param>
    /// <returns>The builder instance.</returns>
    public CaddyInTheMiddleBuilder WithMockPaths(params string[] mockPaths)
    {
        foreach (var mockPath in mockPaths)
        {
            var normalizedPath = Path.GetFullPath(mockPath);
            if (!normalizedPath.StartsWith("/citm-mocks/", StringComparison.Ordinal))
            {
                throw new ArgumentException($"Mock path '{mockPath}' must be under '/citm-mocks/'.");
            }
        }
        
        var joinedMockPaths = string.Join(",", mockPaths);
        return Merge(DockerResourceConfiguration, new CaddyInTheMiddleConfiguration(mockPaths: mockPaths))
            .WithEnvironment("MOCK_PATHS", joinedMockPaths);
    }

    /// <inheritdoc />
    public override CaddyInTheMiddleContainer Build()
    {
        Validate();
        return new CaddyInTheMiddleContainer(DockerResourceConfiguration);
    }

    /// <inheritdoc />
    protected sealed override CaddyInTheMiddleBuilder Init()
    {
        return base.Init()
            .WithImage(CaddyInTheMiddleImage)
            .WithPortBinding(HttpPort, true)
            .WithPortBinding(HttpsPort, true)
            .WithPortBinding(HttpProxyPort, true)
            .WithPortBinding(SocksProxyPort, true)
            .WithPortBinding(AdminPort, true)
            .WithBindMount("/var/run/docker.sock", "/var/run/docker.sock")
            .WithWaitStrategy(Wait.ForUnixContainer().UntilContainerIsHealthy());
    }

    /// <inheritdoc />
    protected override CaddyInTheMiddleBuilder Clone(
        IResourceConfiguration<CreateContainerParameters> resourceConfiguration)
    {
        return Merge(DockerResourceConfiguration, new CaddyInTheMiddleConfiguration(resourceConfiguration));
    }

    /// <inheritdoc />
    protected override CaddyInTheMiddleBuilder Clone(IContainerConfiguration resourceConfiguration)
    {
        return Merge(DockerResourceConfiguration, new CaddyInTheMiddleConfiguration(resourceConfiguration));
    }

    /// <inheritdoc />
    protected override CaddyInTheMiddleBuilder Merge(CaddyInTheMiddleConfiguration oldValue,
        CaddyInTheMiddleConfiguration newValue)
    {
        return new CaddyInTheMiddleBuilder(new CaddyInTheMiddleConfiguration(oldValue, newValue));
    }

    /// <inheritdoc />
    protected override void Validate()
    {
        base.Validate();
        if (string.IsNullOrWhiteSpace(DockerResourceConfiguration.CertsDirectory))
            throw new ArgumentException("CertsDirectory is required. Use WithCertsDirectory().");
    }
}
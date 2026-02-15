# Testcontainers CaddyInTheMiddle Module

A [Testcontainers](https://github.com/testcontainers/testcontainers-dotnet) module for [CaddyInTheMiddle](https://github.com/fardjad/caddy-in-the-middle), designed to simplify integration testing where you need a programmable reverse proxy or MITM proxy.

This library allows you to spin up a pre-configured Caddy instance in Docker, complete with mock responses, custom certificates, and proxy settings, all from your .NET test code.

## Getting Started

1.  **Install the package**:
    ```bash
    dotnet add package Testcontainers.CaddyInTheMiddle
    ```

2.  **Generate Test Certificates**:
    Integration tests typically require trusted certificates. This library includes a helper to generate valid self-signed Root CA certificates on the fly.

3.  **Start the Container**:
    Use the `CaddyInTheMiddleBuilder` to configure and build the container instance.

## Usage Example

Here is a complete example using xUnit:

```csharp
using Testcontainers.CaddyInTheMiddle;
using Xunit;

public class MyIntegrationTests : IAsyncLifetime
{
    private readonly CaddyInTheMiddleContainer _container;
    private readonly string _certsDir;

    public MyIntegrationTests()
    {
        // Create a temporary directory for certs
        _certsDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        Directory.CreateDirectory(_certsDir);

        // Generate the Root CA certificates
        CaddyInTheMiddleCertificates.Generate(_certsDir);

        // Configure the container
        _container = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory(_certsDir)
            // Optional: Provide a directory of mock response files
            // .WithMocksDirectory(Path.Combine(Directory.GetCurrentDirectory(), "mocks"))
            .Build();
    }

    public Task InitializeAsync() => _container.StartAsync();

    public async Task DisposeAsync()
    {
        await _container.DisposeAsync();
        Directory.Delete(_certsDir, true);
    }

    [Fact]
    public async Task ShouldProxyRequest()
    {
        // Create an HttpClient configured to use the container's proxy
        using var handler = _container.CreateHttpClientHandler();
        using var client = new HttpClient(handler);

        // Make a request through MITMProxy in the citm container
        var response = await client.GetAsync("https://registered-dns-name-in-citm-network:1234/blabla");
        
        Assert.True(response.IsSuccessStatusCode);
    }
}
```

## Configuration

The `CaddyInTheMiddleBuilder` provides a fluent API for customization:

*   **`WithCertsDirectory(string path)`** (Required): Path to the directory containing `rootCA.pem` and `rootCA-key.pem`.
*   **`WithMocksDirectory(string path)`**: Mounts a directory of mock templates (e.g., `*.mako` files) into the container.
*   **`WithCaddyfileDirectory(string path)`**: Mounts a directory containing a custom `Caddyfile` if you need advanced Caddy configuration.
*   **`WithCitmNetwork(string networkName)`**: Connects the container to a specific Docker network. This enables automatic service discovery: if other containers on this network have the `citm_dns_names` label, their DNS names will be automatically resolved by the `dnsmasq` instance running inside the CITM container.
*   **`WithDnsNames(params string[] names)`**: Sets the `citm_dns_names` label on the container. This leverages CITM's built-in service discovery to register these DNS names.

## Helper Methods

Once the container is running and healthy, you can access helpful properties and methods:

*   **`CreateHttpClientHandler(bool ignoreSslErrors = true)`**: Returns an `HttpClientHandler` pre-configured with the correct proxy settings.
*   **`GetHttpProxyAddress()`**: Returns the address of the HTTP proxy (e.g., `http://localhost:32768`).
*   **`GetSocksProxyAddress()`**: Returns the address of the SOCKS5 proxy.
*   **`GetAdminBaseUrl()`**: Returns the base URL for the Caddy admin API.
*   **`GetCaddyHttpBaseUrl()` / `GetCaddyHttpsBaseUrl()`**: Returns the base URLs for direct access to Caddy.

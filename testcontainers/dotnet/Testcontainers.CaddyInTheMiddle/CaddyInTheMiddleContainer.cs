using System.Net;
using DotNet.Testcontainers.Containers;
using JetBrains.Annotations;

namespace Testcontainers.CaddyInTheMiddle;

/// <summary>
/// Represents a CaddyInTheMiddle container.
/// </summary>
public sealed class CaddyInTheMiddleContainer(CaddyInTheMiddleConfiguration configuration)
    : DockerContainer(configuration)
{
    [UsedImplicitly] 
    // this is used in tests
    private readonly CaddyInTheMiddleConfiguration _configuration = configuration;

    /// <summary>
    /// Gets the base URL for HTTP requests to Caddy (port 80).
    /// </summary>
    /// <returns>The HTTP base URL.</returns>
    public string GetCaddyHttpBaseUrl()
    {
        return new UriBuilder("http", Hostname, GetMappedPublicPort(CaddyInTheMiddleBuilder.HttpPort)).ToString();
    }

    /// <summary>
    /// Gets the base URL for HTTPS requests to Caddy (port 443).
    /// </summary>
    /// <returns>The HTTPS base URL.</returns>
    public string GetCaddyHttpsBaseUrl()
    {
        return new UriBuilder("https", Hostname, GetMappedPublicPort(CaddyInTheMiddleBuilder.HttpsPort)).ToString();
    }

    /// <summary>
    /// Gets the address of the HTTP proxy (port 8380).
    /// </summary>
    /// <returns>The HTTP proxy address.</returns>
    public string GetHttpProxyAddress()
    {
        return $"http://{Hostname}:{GetMappedPublicPort(CaddyInTheMiddleBuilder.HttpProxyPort)}";
    }

    /// <summary>
    /// Gets the address of the SOCKS5 proxy (port 8381).
    /// </summary>
    /// <returns>The SOCKS5 proxy address.</returns>
    public string GetSocksProxyAddress()
    {
        return $"socks5://{Hostname}:{GetMappedPublicPort(CaddyInTheMiddleBuilder.SocksProxyPort)}";
    }

    /// <summary>
    /// Gets the base URL for the Caddy admin API (port 3858).
    /// </summary>
    /// <returns>The Admin API base URL.</returns>
    public string GetAdminBaseUrl()
    {
        return new UriBuilder("http", Hostname, GetMappedPublicPort(CaddyInTheMiddleBuilder.AdminPort)).ToString();
    }

    /// <summary>
    /// Creates an <see cref="HttpClientHandler" /> configured to use the container's HTTP proxy.
    /// </summary>
    /// <param name="ignoreSslErrors">If true, ignores SSL errors (useful for self-signed certs).</param>
    /// <returns>A configured HttpClientHandler.</returns>
    public HttpClientHandler CreateHttpClientHandler(bool ignoreSslErrors = true)
    {
        var handler = new HttpClientHandler
        {
            Proxy = new WebProxy(GetHttpProxyAddress()),
            UseProxy = true
        };

        if (ignoreSslErrors)
        {
            handler.ServerCertificateCustomValidationCallback = HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }

        return handler;
    }
}
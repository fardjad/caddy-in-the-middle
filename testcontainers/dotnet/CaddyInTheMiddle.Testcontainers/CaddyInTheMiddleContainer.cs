using System.Net;
using DotNet.Testcontainers.Containers;
using JetBrains.Annotations;

namespace CaddyInTheMiddle.Testcontainers;

/// <summary>
/// Represents a CaddyInTheMiddle container.
/// </summary>
public sealed class CaddyInTheMiddleContainer(CaddyInTheMiddleConfiguration configuration)
    : DockerContainer(configuration)
{
    [UsedImplicitly] 
    // this is used in tests
    private readonly CaddyInTheMiddleConfiguration _configuration = configuration;

    private string GetHostnameWithSubdomains(string[]? subdomains)
    {
        var baseHostname = Hostname.ToLocalhostIfLoopback();
        if (subdomains == null || subdomains.Length == 0)
        {
            return baseHostname;
        }

        return $"{string.Join(".", subdomains)}.{baseHostname}";
    }

    /// <summary>
    /// Gets the base URL for HTTP requests to Caddy (port 80).
    /// </summary>
    /// <param name="subdomains">Optional subdomains to prepend to the hostname.</param>
    /// <returns>The HTTP base URL.</returns>
    public string GetCaddyHttpBaseUrl(params string[] subdomains)
    {
        return new UriBuilder("http", GetHostnameWithSubdomains(subdomains), GetMappedPublicPort(CaddyInTheMiddleBuilder.HttpPort)).ToString();
    }

    /// <summary>
    /// Gets the base URL for HTTPS requests to Caddy (port 443).
    /// </summary>
    /// <param name="subdomains">Optional subdomains to prepend to the hostname.</param>
    /// <returns>The HTTPS base URL.</returns>
    public string GetCaddyHttpsBaseUrl(params string[] subdomains)
    {
        return new UriBuilder("https", GetHostnameWithSubdomains(subdomains), GetMappedPublicPort(CaddyInTheMiddleBuilder.HttpsPort)).ToString();
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
    /// <param name="subdomains">Optional subdomains to prepend to the hostname.</param>
    /// <returns>The Admin API base URL.</returns>
    public string GetAdminBaseUrl(params string[] subdomains)
    {
        return new UriBuilder("https", GetHostnameWithSubdomains(subdomains), GetMappedPublicPort(CaddyInTheMiddleBuilder.AdminPort)).ToString();
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
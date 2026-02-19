using System.Net;

namespace CaddyInTheMiddle.Testcontainers;

/// <summary>
/// Provides extension methods for hostname string manipulation. 
/// Particularly useful for normalizing Testcontainers hostnames to support local subdomains.
/// </summary>
public static class HostnameExtensions
{
    /// <summary>
    /// Converts loopback IP addresses (like 127.0.0.1 or ::1) to "localhost".
    /// Leaves non-loopback IPs or actual hostnames unchanged.
    /// </summary>
    public static string ToLocalhostIfLoopback(this string hostname)
    {
        if (string.IsNullOrWhiteSpace(hostname))
        {
            return hostname;
        }

        if (IPAddress.TryParse(hostname, out var ipAddress) && IPAddress.IsLoopback(ipAddress))
        {
            return "localhost";
        }

        return hostname;
    }
}
using CaddyInTheMiddle.Testcontainers;

namespace CaddyInTheMiddle.Testcontainers.Tests;

public class HostnameExtensionsTests
{
    [Theory]
    [InlineData("127.0.0.1", "localhost")]
    [InlineData("::1", "localhost")]
    [InlineData("192.168.1.100", "192.168.1.100")]
    [InlineData("example.com", "example.com")]
    [InlineData("", "")]
    [InlineData(null, null)]
    public void ToLocalhostIfLoopback_ShouldReturnExpectedResult(string hostname, string expected)
    {
        // Act
        var result = hostname.ToLocalhostIfLoopback();

        // Assert
        Assert.Equal(expected, result);
    }
}

namespace CaddyInTheMiddle.Testcontainers.Tests;

[TestClass]
public class HostnameExtensionsTests
{
    [TestMethod]
    [DataRow("127.0.0.1", "localhost")]
    [DataRow("::1", "localhost")]
    [DataRow("192.168.1.100", "192.168.1.100")]
    [DataRow("example.com", "example.com")]
    [DataRow("", "")]
    [DataRow(null, null)]
    public void ToLocalhostIfLoopback_ShouldReturnExpectedResult(string hostname, string expected)
    {
        // Act
        var result = hostname.ToLocalhostIfLoopback();

        // Assert
        Assert.AreEqual(expected, result);
    }
}

using JetBrains.Annotations;

namespace CaddyInTheMiddle.Testcontainers.Tests;

[TestSubject(typeof(CaddyInTheMiddleContainer))]
[TestClass]
public class CaddyInTheMiddleContainerTest
{
    private static string _certsDirectory = null!;
    private static string _mocksDirectory = null!;
    private static CaddyInTheMiddleContainer _container = null!;

    [ClassInitialize]
    public static async Task ClassInitialize(TestContext context)
    {
        _certsDirectory = Directory.CreateDirectory(Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString())).FullName;
        _mocksDirectory = Directory.CreateDirectory(Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString())).FullName;

        CaddyInTheMiddleCertificates.Generate(_certsDirectory);

        _container = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory(_certsDirectory)
            .WithMocksDirectory(_mocksDirectory)
            .Build();

        await _container.StartAsync(context.CancellationToken);
    }

    [ClassCleanup]
    public static async Task ClassCleanup()
    {
        if (Directory.Exists(_certsDirectory))
        {
            Directory.Delete(_certsDirectory, true);
        }

        if (Directory.Exists(_mocksDirectory))
        {
            Directory.Delete(_mocksDirectory, true);
        }

        await _container.DisposeAsync();
    }

    [TestMethod]
    public void ShouldStartContainer()
    {
        Assert.AreEqual(DotNet.Testcontainers.Containers.TestcontainersStates.Running, _container.State);
        Assert.AreEqual(DotNet.Testcontainers.Containers.TestcontainersHealthStatus.Healthy, _container.Health);
    }

    [TestMethod]
    public void ShouldReturnValidCaddyHttpBaseUrl()
    {
        var url = _container.GetCaddyHttpBaseUrl("s1", "s2");
        Assert.StartsWith("http://", url);
        Assert.Contains("s1.s2", url);
        Assert.IsTrue(Uri.TryCreate(url, UriKind.Absolute, out _));
    }

    [TestMethod]
    public void ShouldReturnValidCaddyHttpsBaseUrl()
    {
        var url = _container.GetCaddyHttpsBaseUrl("s1", "s2");
        Assert.StartsWith("https://", url);
        Assert.Contains("s1.s2", url);
        Assert.IsTrue(Uri.TryCreate(url, UriKind.Absolute, out _));
    }

    [TestMethod]
    public void ShouldReturnValidHttpProxyAddress()
    {
        var address = _container.GetHttpProxyAddress();
        Assert.StartsWith("http://", address);
        Assert.Contains(_container.Hostname, address);
        Assert.Contains(":", address);
    }

    [TestMethod]
    public void ShouldReturnValidSocksProxyAddress()
    {
        var address = _container.GetSocksProxyAddress();
        Assert.StartsWith("socks5://", address);
        Assert.Contains(_container.Hostname, address);
        Assert.Contains(":", address);
    }

    [TestMethod]
    public void ShouldReturnValidAdminBaseUrl()
    {
        var url = _container.GetAdminBaseUrl("utils", "citm");
        Assert.StartsWith("https://", url);
        Assert.Contains("utils.citm", url);
        Assert.IsTrue(Uri.TryCreate(url, UriKind.Absolute, out _));
    }

    [TestMethod]
    public void ShouldCreateConfiguredHttpClientHandler()
    {
        using var handler = _container.CreateHttpClientHandler();
        Assert.IsNotNull(handler);
        Assert.IsNotNull(handler.Proxy);
        Assert.IsTrue(handler.UseProxy);
    }
}
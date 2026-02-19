using JetBrains.Annotations;

namespace CaddyInTheMiddle.Testcontainers.Tests;

[TestSubject(typeof(CaddyInTheMiddleContainer))]
[UsedImplicitly]
public class CaddyInTheMiddleContainerFixture : IAsyncLifetime
{
    public CaddyInTheMiddleContainer Container { get; }
    private readonly string _certsDirectory;
    private readonly string _mocksDirectory;

    public CaddyInTheMiddleContainerFixture()
    {
        _certsDirectory = Directory.CreateDirectory(Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString())).FullName;
        _mocksDirectory = Directory.CreateDirectory(Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString())).FullName;

        CaddyInTheMiddleCertificates.Generate(_certsDirectory);

        Container = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory(_certsDirectory)
            .WithMocksDirectory(_mocksDirectory)
            .Build();
    }

    public Task InitializeAsync()
    {
        return Container.StartAsync();
    }

    public Task DisposeAsync()
    {
        if (Directory.Exists(_certsDirectory))
        {
            Directory.Delete(_certsDirectory, true);
        }

        if (Directory.Exists(_mocksDirectory))
        {
            Directory.Delete(_mocksDirectory, true);
        }

        return Container.DisposeAsync().AsTask();
    }
}

[TestSubject(typeof(CaddyInTheMiddleContainer))]
public class CaddyInTheMiddleContainerTest(CaddyInTheMiddleContainerFixture fixture)
    : IClassFixture<CaddyInTheMiddleContainerFixture>
{
    private readonly CaddyInTheMiddleContainer _container = fixture.Container;

    [Fact]
    public void ShouldStartContainer()
    {
        Assert.Equal(DotNet.Testcontainers.Containers.TestcontainersStates.Running, _container.State);
        Assert.Equal(DotNet.Testcontainers.Containers.TestcontainersHealthStatus.Healthy, _container.Health);
    }

    [Fact]
    public void ShouldReturnValidCaddyHttpBaseUrl()
    {
        var url = _container.GetCaddyHttpBaseUrl("s1", "s2");
        Assert.StartsWith("http://", url);
        Assert.Contains("s1.s2", url);
        Assert.True(Uri.TryCreate(url, UriKind.Absolute, out _));
    }

    [Fact]
    public void ShouldReturnValidCaddyHttpsBaseUrl()
    {
        var url = _container.GetCaddyHttpsBaseUrl("s1", "s2");
        Assert.StartsWith("https://", url);
        Assert.Contains("s1.s2", url);
        Assert.True(Uri.TryCreate(url, UriKind.Absolute, out _));
    }

    [Fact]
    public void ShouldReturnValidHttpProxyAddress()
    {
        var address = _container.GetHttpProxyAddress();
        Assert.StartsWith("http://", address);
        Assert.Contains(_container.Hostname, address);
        Assert.Contains(":", address);
    }

    [Fact]
    public void ShouldReturnValidSocksProxyAddress()
    {
        var address = _container.GetSocksProxyAddress();
        Assert.StartsWith("socks5://", address);
        Assert.Contains(_container.Hostname, address);
        Assert.Contains(":", address);
    }

    [Fact]
    public void ShouldReturnValidAdminBaseUrl()
    {
        var url = _container.GetAdminBaseUrl("utils", "citm");
        Assert.StartsWith("https://", url);
        Assert.Contains("utils.citm", url);
        Assert.True(Uri.TryCreate(url, UriKind.Absolute, out _));
    }

    [Fact]
    public void ShouldCreateConfiguredHttpClientHandler()
    {
        using var handler = _container.CreateHttpClientHandler();
        Assert.NotNull(handler);
        Assert.NotNull(handler.Proxy);
        Assert.True(handler.UseProxy);
    }
}
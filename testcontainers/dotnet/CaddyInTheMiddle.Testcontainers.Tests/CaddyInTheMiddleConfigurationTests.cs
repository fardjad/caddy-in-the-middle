using System.Reflection;
using DotNet.Testcontainers.Configurations;
using JetBrains.Annotations;

namespace Testcontainers.CaddyInTheMiddle.Tests;

[TestSubject(typeof(CaddyInTheMiddleBuilder))]
public class CaddyInTheMiddleConfigurationTests
{
    [Fact]
    public void ShouldSetCertsDirectory()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .Build()
            .GetConfiguration();

        Assert.Contains(configuration.Mounts, m => m.Source == "/tmp/certs" && m.Target == "/certs");
    }

    [Fact]
    public void ShouldThrowIfCertsDirectoryIsNotSet()
    {
        Assert.Throws<ArgumentException>(() => { new CaddyInTheMiddleBuilder().Build().GetConfiguration(); });
    }

    [Fact]
    public void ShouldSetMocksDirectory()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithMocksDirectory("/tmp/mocks")
            .Build()
            .GetConfiguration();

        Assert.Contains(configuration.Mounts, m => m.Source == "/tmp/mocks" && m.Target == "/citm-mocks/");
    }

    [Fact]
    public void ShouldSetCaddyfileDirectory()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithCaddyfileDirectory("/tmp/caddy")
            .Build()
            .GetConfiguration();

        Assert.Contains(configuration.Mounts, m => m.Source == "/tmp/caddy" && m.Target == "/etc/caddy/conf.d");
    }

    [Fact]
    public void ShouldSetCitmNetwork()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithCitmNetwork("some-network")
            .Build()
            .GetConfiguration();

        Assert.Contains(configuration.Networks, n => n.Name == "some-network");
        Assert.Equal("some-network", configuration.Labels["citm_network"]);
    }

    [Fact]
    public void ShouldMountDockerSocketByDefault()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .Build()
            .GetConfiguration();

        Assert.Contains(configuration.Mounts, m => m.Source == "/var/run/docker.sock" && m.Target == "/var/run/docker.sock");
    }

    [Fact]
    public void ShouldSetDnsNames()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithDnsNames("name1", "name2")
            .Build()
            .GetConfiguration();

        Assert.Equal("name1,name2", configuration.Labels["citm_dns_names"]);
    }

    [Fact]
    public void ShouldSetDefaultMockPaths()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithMocksDirectory("/tmp/mocks")
            .Build()
            .GetConfiguration();

        Assert.Equal("/citm-mocks/**/*.mako", configuration.Environments["MOCK_PATHS"]);
    }

    [Fact]
    public void ShouldOverrideDefaultMockPaths()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithMocksDirectory("/tmp/mocks")
            .WithMockPaths("/citm-mocks/custom-path/*.mako")
            .Build()
            .GetConfiguration();

        Assert.Equal("/citm-mocks/custom-path/*.mako", configuration.Environments["MOCK_PATHS"]);
    }

    [Fact]
    public void ShouldThrowWhenMockPathsAreOutsideOfTheMountedDirectory()
    {
        Assert.Throws<ArgumentException>(() =>
        {
            new CaddyInTheMiddleBuilder()
                .WithCertsDirectory("/tmp/certs")
                .WithMocksDirectory("/tmp/mocks")
                .WithMockPaths("/somewhere-else/*.mako")
                .Build();
        });
    }
}

public static class ContainerExtensions
{
    public static IContainerConfiguration GetConfiguration(this CaddyInTheMiddleContainer container)
    {
        var field = typeof(CaddyInTheMiddleContainer).GetField("_configuration",
            BindingFlags.NonPublic | BindingFlags.Instance);

        if (field != null)
        {
            return (IContainerConfiguration)field.GetValue(container)!;
        }

        throw new Exception("Could not find '_configuration' field in CaddyInTheMiddleContainer.");
    }
}
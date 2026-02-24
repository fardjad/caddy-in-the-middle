using System.Reflection;
using DotNet.Testcontainers.Configurations;
using JetBrains.Annotations;

namespace CaddyInTheMiddle.Testcontainers.Tests;

[TestSubject(typeof(CaddyInTheMiddleBuilder))]
[TestClass]
public class CaddyInTheMiddleConfigurationTests
{
    [TestMethod]
    public void ShouldSetCertsDirectory()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .Build()
            .GetConfiguration();

        Assert.Contains(m => m.Source == "/tmp/certs" && m.Target == "/certs", configuration.Mounts);
    }

    [TestMethod]
    public void ShouldThrowIfCertsDirectoryIsNotSet()
    {
        Assert.Throws<ArgumentException>(() => { new CaddyInTheMiddleBuilder().Build().GetConfiguration(); });
    }

    [TestMethod]
    public void ShouldSetMocksDirectory()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithMocksDirectory("/tmp/mocks")
            .Build()
            .GetConfiguration();

        Assert.Contains(m => m.Source == "/tmp/mocks" && m.Target == "/citm-mocks/", configuration.Mounts);
    }

    [TestMethod]
    public void ShouldSetCaddyfileDirectory()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithCaddyfileDirectory("/tmp/caddy")
            .Build()
            .GetConfiguration();

        Assert.Contains(m => m.Source == "/tmp/caddy" && m.Target == "/etc/caddy/conf.d", configuration.Mounts);
    }

    [TestMethod]
    public void ShouldSetCitmNetwork()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithCitmNetwork("some-network")
            .Build()
            .GetConfiguration();

        Assert.IsTrue(configuration.Networks.Any(n => n.Name == "some-network"));
        Assert.AreEqual("some-network", configuration.Environments["CITM_NETWORK"]);
        Assert.AreEqual("some-network", configuration.Labels["citm_network"]);
    }

    [TestMethod]
    public void ShouldMountDockerSocketByDefault()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .Build()
            .GetConfiguration();

        Assert.Contains(m => m.Source == "/var/run/docker.sock" && m.Target == "/var/run/docker.sock", configuration.Mounts);
    }

    [TestMethod]
    public void ShouldSetDnsNames()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithDnsNames("name1", "name2")
            .Build()
            .GetConfiguration();

        Assert.AreEqual("name1,name2", configuration.Labels["citm_dns_names"]);
    }

    [TestMethod]
    public void ShouldSetDefaultMockPaths()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithMocksDirectory("/tmp/mocks")
            .Build()
            .GetConfiguration();

        Assert.AreEqual("/citm-mocks/**/*.mako", configuration.Environments["MOCK_PATHS"]);
    }

    [TestMethod]
    public void ShouldOverrideDefaultMockPaths()
    {
        var configuration = new CaddyInTheMiddleBuilder()
            .WithCertsDirectory("/tmp/certs")
            .WithMocksDirectory("/tmp/mocks")
            .WithMockPaths("/citm-mocks/custom-path/*.mako")
            .Build()
            .GetConfiguration();

        Assert.AreEqual("/citm-mocks/custom-path/*.mako", configuration.Environments["MOCK_PATHS"]);
    }

    [TestMethod]
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

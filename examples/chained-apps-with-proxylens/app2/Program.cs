using System.Net.Http.Headers;
using System.Text.Json;
using OpenTelemetry.Trace;

var serviceName = Environment.GetEnvironmentVariable("OTEL_SERVICE_NAME") ?? "app2";
var service3BaseUrl = Environment.GetEnvironmentVariable("SERVICE3_BASE_URL")
    ?? "https://app3.internal/";

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls("http://0.0.0.0:8080");

builder.Services.AddHttpClient("downstream", client =>
{
    client.DefaultRequestHeaders.Accept.Add(
        new MediaTypeWithQualityHeaderValue("application/json"));
    client.Timeout = TimeSpan.FromSeconds(10);
});

builder.Services
    .AddOpenTelemetry()
    .WithTracing(tracing => tracing
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation());

var app = builder.Build();

app.MapGet("/", async (HttpContext context, IHttpClientFactory httpClientFactory) =>
{
    try
    {
        var client = httpClientFactory.CreateClient("downstream");
        using var response = await client.GetAsync(service3BaseUrl, context.RequestAborted);
        response.EnsureSuccessStatusCode();

        var downstream = await response.Content.ReadFromJsonAsync<JsonElement>(
            cancellationToken: context.RequestAborted);

        return Results.Json(new
        {
            service = serviceName,
            message = $"{serviceName} called app3",
            downstream,
        });
    }
    catch (Exception exception)
    {
        return Results.Json(new
        {
            service = serviceName,
            error = $"downstream request failed: {exception.Message}",
        }, statusCode: StatusCodes.Status502BadGateway);
    }
});

await app.RunAsync();

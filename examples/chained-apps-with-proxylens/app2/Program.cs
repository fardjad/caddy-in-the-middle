using System.Net.Http.Headers;
using System.Text.Json;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

const string AppName = "app2";
const string ListenUrl = "http://0.0.0.0:8080";

var service3BaseUrl = GetRequiredEnvironmentVariable("SERVICE3_BASE_URL");

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls(ListenUrl);

builder.Services.AddHttpClient("downstream", client =>
{
    client.DefaultRequestHeaders.Accept.Add(
        new MediaTypeWithQualityHeaderValue("application/json"));
    client.Timeout = TimeSpan.FromSeconds(10);
});

builder.Services
    .AddOpenTelemetry()
    .ConfigureResource(resource => resource.AddService(AppName))
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
            service = AppName,
            message = $"{AppName} called app3",
            downstream,
        });
    }
    catch (Exception exception)
    {
        return Results.Json(new
        {
            service = AppName,
            error = $"downstream request failed: {exception.Message}",
        }, statusCode: StatusCodes.Status502BadGateway);
    }
});

await app.RunAsync();

return;

static string GetRequiredEnvironmentVariable(string name) =>
    Environment.GetEnvironmentVariable(name)
    ?? throw new InvalidOperationException($"{name} is required");

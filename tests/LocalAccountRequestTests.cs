using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class LocalAccountRequestTests
{
    [Theory]
    [InlineData("Alice\nsecret", "Alice", "secret")]
    [InlineData("Alice\r\nsecret\r\n", "Alice", "secret")]
    [InlineData("Two Words\npass word", "Two Words", "pass word")]
    public void ParsesNameThenPassword(string contents, string expectedName, string expectedPassword)
    {
        Assert.True(LocalAccountRequest.TryParse(contents, out var name, out var password, out var error));
        Assert.Equal(expectedName, name);
        Assert.Equal(expectedPassword, password);
        Assert.Null(error);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("Alice")]
    [InlineData("Alice\n")]
    [InlineData("\nsecret")]
    [InlineData("   \nsecret")]
    public void RejectsInvalidRequests(string? contents)
    {
        Assert.False(LocalAccountRequest.TryParse(contents, out var name, out var password, out var error));
        Assert.Null(name);
        Assert.Null(password);
        Assert.NotNull(error);
    }
}

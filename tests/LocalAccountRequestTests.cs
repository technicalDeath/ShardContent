using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class LocalAccountRequestTests
{
    [Theory]
    [InlineData("Alice\nsecret", "Alice", "secret")]
    [InlineData("Alice\r\nsecret\r\n", "Alice", "secret")]
    [InlineData("Two Words\npass word", "Two Words", "pass word")]
    public void ParsesOneAccount(string contents, string expectedName, string expectedPassword)
    {
        Assert.True(LocalAccountRequest.TryParse(contents, out var accounts, out var error));
        Assert.Null(error);
        var (name, password) = Assert.Single(accounts);
        Assert.Equal(expectedName, name);
        Assert.Equal(expectedPassword, password);
    }

    [Fact]
    public void ParsesSeveralAccounts()
    {
        Assert.True(LocalAccountRequest.TryParse("Alice\na1\nBob\nb2\n", out var accounts, out _));
        Assert.Equal([("Alice", "a1"), ("Bob", "b2")], accounts);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("Alice")]
    [InlineData("Alice\n")]
    [InlineData("\nsecret")]
    [InlineData("   \nsecret")]
    [InlineData("Alice\na1\nBob")]
    [InlineData("Alice\na1\nBob\n\n")]
    public void RejectsMalformedRequests(string? contents)
    {
        Assert.False(LocalAccountRequest.TryParse(contents, out var accounts, out var error));
        Assert.Null(accounts);
        Assert.NotNull(error);
    }
}

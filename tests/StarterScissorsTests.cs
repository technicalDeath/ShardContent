using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class StarterScissorsTests
{
    [Theory]
    [InlineData(0, true)]
    [InlineData(14399, true)]
    [InlineData(14400, false)]
    [InlineData(14401, false)]
    public void ProtectionEndsAtExactlyFourLoggedInHours(int seconds, bool protectedOnDeath)
    {
        Assert.Equal(protectedOnDeath, StarterScissors.IsProtected(TimeSpan.FromSeconds(seconds)));
    }
}

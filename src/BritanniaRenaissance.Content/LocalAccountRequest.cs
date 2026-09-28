using System.Diagnostics.CodeAnalysis;
using Server;
using Server.Accounting;
using Server.Logging;
using Server.Misc;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Creates one ordinary player account at startup from a request file named by
/// <see cref="EnvironmentVariable"/>. The workspace's "Create Player Account" launcher writes
/// the file while the server is stopped, because local-only hosts disable automatic account
/// creation at login. The file holds the account name on the first line and the password on
/// the second; it is deleted as soon as it is read, whatever the outcome.
/// </summary>
public static class LocalAccountRequest
{
    public const string EnvironmentVariable = "MODERNUO_CREATE_PLAYER_ACCOUNT_FILE";

    private static readonly ILogger Logger = LogFactory.GetLogger(typeof(LocalAccountRequest));
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        // Accounts are loaded with the world, so wait until the server has started.
        if (!string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable(EnvironmentVariable)))
        {
            EventSink.ServerStarted += ProcessRequest;
        }
    }

    /// <summary>
    /// Parses request contents: account name, then password, one per line. Name rules are
    /// checked separately against <see cref="AccountHandler.IsValidUsername"/> at startup.
    /// </summary>
    public static bool TryParse(
        string? contents,
        [NotNullWhen(true)] out string? username,
        [NotNullWhen(true)] out string? password,
        [NotNullWhen(false)] out string? error
    )
    {
        username = null;
        password = null;

        var lines = (contents ?? "").Replace("\r\n", "\n").Split('\n');
        var name = lines.Length > 0 ? lines[0] : "";
        var secret = lines.Length > 1 ? lines[1] : "";

        if (string.IsNullOrWhiteSpace(name))
        {
            error = "the account name is empty";
            return false;
        }

        if (secret.Length == 0)
        {
            error = "the password is empty";
            return false;
        }

        username = name;
        password = secret;
        error = null;
        return true;
    }

    private static void ProcessRequest()
    {
        EventSink.ServerStarted -= ProcessRequest;

        var path = Environment.GetEnvironmentVariable(EnvironmentVariable);
        if (string.IsNullOrWhiteSpace(path))
        {
            return;
        }

        string contents;
        try
        {
            contents = File.ReadAllText(path);
        }
        catch (Exception e)
        {
            Logger.Warning("Player account request {Path} could not be read: {Message}", path, e.Message);
            return;
        }
        finally
        {
            TryDelete(path);
        }

        if (!TryParse(contents, out var username, out var password, out var error))
        {
            Logger.Warning("Player account request rejected: {Reason}.", error);
            return;
        }

        if (!AccountHandler.IsValidUsername(username) || !AccountHandler.IsValidPassword(password))
        {
            Logger.Warning("Player account request rejected: the account name contains a forbidden character or ends with a space or period.");
            return;
        }

        if (Accounts.GetAccount(username) != null)
        {
            Logger.Warning("Player account request skipped: account '{Username}' already exists; its password was not changed.", username);
            return;
        }

        _ = new Account(username, password);
        Logger.Information("Created player account '{Username}' from the local account request.", username);
    }

    private static void TryDelete(string path)
    {
        try
        {
            File.Delete(path);
        }
        catch (Exception e)
        {
            Logger.Warning("Could not delete player account request {Path}: {Message}", path, e.Message);
        }
    }
}

using System.Diagnostics.CodeAnalysis;
using Server;
using Server.Accounting;
using Server.Logging;
using Server.Misc;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Creates ordinary player accounts at startup from a request file named by
/// <see cref="EnvironmentVariable"/>. The workspace's "Create Player Account" launcher and the
/// agent test helpers write the file while the server is stopped, because local-only hosts
/// disable automatic account creation at login. The file holds pairs of lines: account name,
/// then password. It is deleted as soon as it is read, whatever the outcome.
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
    /// Parses request contents: repeated pairs of lines, account name then password. One trailing
    /// newline is allowed. Any malformed pair rejects the whole request. Name rules are checked
    /// separately against <see cref="AccountHandler.IsValidUsername"/> at startup.
    /// </summary>
    public static bool TryParse(
        string? contents,
        [NotNullWhen(true)] out List<(string Username, string Password)>? accounts,
        [NotNullWhen(false)] out string? error
    )
    {
        accounts = null;
        var lines = (contents ?? "").Replace("\r\n", "\n").Split('\n').ToList();
        if (lines.Count > 1 && lines[^1].Length == 0)
        {
            lines.RemoveAt(lines.Count - 1);
        }

        if (lines.Count < 2 || lines.Count % 2 != 0)
        {
            error = "expected pairs of lines (account name, then password)";
            return false;
        }

        var parsed = new List<(string, string)>();
        for (var i = 0; i < lines.Count; i += 2)
        {
            if (string.IsNullOrWhiteSpace(lines[i]))
            {
                error = $"account {i / 2 + 1}: the account name is empty";
                return false;
            }

            if (lines[i + 1].Length == 0)
            {
                error = $"account {i / 2 + 1}: the password is empty";
                return false;
            }

            parsed.Add((lines[i], lines[i + 1]));
        }

        accounts = parsed;
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

        if (!TryParse(contents, out var accounts, out var error))
        {
            Logger.Warning("Player account request rejected: {Reason}.", error);
            return;
        }

        foreach (var (username, password) in accounts)
        {
            if (!AccountHandler.IsValidUsername(username) || !AccountHandler.IsValidPassword(password))
            {
                Logger.Warning("Player account request skipped an entry: the account name contains a forbidden character or ends with a space or period.");
                continue;
            }

            if (Accounts.GetAccount(username) != null)
            {
                Logger.Warning("Player account request skipped: account '{Username}' already exists; its password was not changed.", username);
                continue;
            }

            _ = new Account(username, password);
            Logger.Information("Created player account '{Username}' from the local account request.", username);
        }
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

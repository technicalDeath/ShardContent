# Alpha 3 Phase C: Starter gold readiness

**Decision:** Ready for Alpha 3 enablement, with `alpha3StarterGold` still disabled. This feature-readiness decision does not authorize Phase L activation.

## Current-source review

- The accepted evidence covers the one-time 500-gold grant, a second character on the same account, character deletion followed by account save/restart and recreation, suppression of stock repeatable gold, and an ordinary client's first character. The setup, observed results, and remaining old-account limitation are recorded in [the starter package audit](Alpha-3-Starter-Package-Audit.md#starter-gold-integration).
- ModernUO's current stock backpack path calls `CharacterCreation.StartingGoldAmount` when present and otherwise keeps its 1,000-gold default. A zero amount suppresses only the gold stack; the book, dagger, and candle remain. The added focused UOContent test file covers both a 500-gold stack and suppression while preserving those other stock items.
- `StarterGoldPolicy.Configure` installs its resolver once. With the feature disabled or for a non-player, it returns the stock 1,000. For an ordinary player, a valid account is required; the policy checks the account entitlement tag, whether another character exists, and `Account.TotalGameTime`, then grants 500 only for a new unused account. It records an account tag whether a grant is issued or prior use is detected, preventing a later character from receiving another grant. A missing account reference returns zero to avoid issuing an untracked entitlement.
- Account tags use the existing serialized account `Tags` property; `Account.TotalGameTime` includes deleted-character playtime and is persisted with account state. Existing disposable evidence saved, restarted, and recreated a character without granting again, so this boundary does not need another run.
- The source Alpha 3 acknowledgment remains false, and `alpha3StarterGold` remains false. The current validator independently requires the acknowledgment before this feature flag can validate. This review changed no runtime policy, deployed configuration, account, or world state.

## Evidence decision and remaining limit

The current resolver hook is the gold integration path recorded in the audit. Its creation packet and two-character/restart cases already exercised the installed resolver and stock backpack output. The inspected uncommitted ModernUO edits introducing that narrow resolver and its unit fixture do not reveal a new uncovered case, so no accepted client matrix or test suite was repeated for this review.

The accepted evidence does not include a second ordinary-client creation on the same account. It does verify the second-character denial through the disposable account probe after save/restart. Review of pre-existing accounts whose last character was deleted before this entitlement existed remains required at release time; an account with no saved game time cannot be distinguished from a never-used account by the current signals. Keep that account population review in the Phase L release gate.

# Flame-colour sheet

Chooses the hue of a camp-travel fire (Camp-Travel-Blue-Fire-Proposal.md section 4). On a disposable host with a real client for the character (TestOnlyProbe loaded):

    python -u sheet.py <serial> [hue ...]    # lights a grid of fires, one per hue, by day and at real night (GlobalLight 12); pictures in work/blue-fire/shots
    pwsh -File compose_sheet.ps1             # magnified, labelled day/night sheet (sheet-closeup.png); edit the hue list and the grid origin to match

The grid position (466, 324) is where the 1296 x 839 client window draws the player's tile with the shipped default profile.

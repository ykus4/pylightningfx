# Enums

Every enum is a `StrEnum`, so a member can be passed anywhere a plain string is
accepted and compares equal to its wire value. Raw strings from the API are kept
as-is when they are not a known member, so an unfamiliar value never raises.

::: pylightningfx.enums

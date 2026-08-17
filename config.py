"""Central configuration for CommendBot.

Everything that used to be hardcoded across the cogs lives here: credentials,
branding and the Discord snowflakes of the original deployment. Values are read
from the environment (see ``.env.example``); the defaults below are the IDs of
the original ``gameboosting.top`` deployment and are only useful as a reference
for how the bot was wired up. Point them at your own guild before running.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _str(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _int(name: str, default: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _int_list(name: str, default: tuple[int, ...] = ()) -> list[int]:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return list(default)
    return [int(part) for part in raw.replace(",", " ").split()]


# --------------------------------------------------------------------------
# Credentials
# --------------------------------------------------------------------------
# None of these have defaults on purpose - the bot refuses to start without
# them rather than silently connecting somewhere unexpected.

DISCORD_TOKEN = _str("DISCORD_TOKEN")
MONGODB_URI = _str("MONGODB_URI")

SMTP_HOST = _str("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = _int("SMTP_PORT", 587)
SMTP_USER = _str("SMTP_USER")
SMTP_PASS = _str("SMTP_PASS")

# Steam Web API key - https://steamcommunity.com/dev/apikey
STEAM_API_KEY = _str("STEAM_API_KEY")

# Used by the reseller cog to restart slot workers on a remote host.
VPS_HOST = _str("VPS_HOST")
VPS_USER = _str("VPS_USER", "root")
VPS_PASS = _str("VPS_PASS")

REQUIRED_SETTINGS = ("DISCORD_TOKEN", "MONGODB_URI")


def validate() -> None:
    """Raise if a setting the bot cannot run without is missing."""
    missing = [name for name in REQUIRED_SETTINGS if not globals().get(name)]
    if missing:
        raise RuntimeError(
            "Missing required configuration: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill it in."
        )


# --------------------------------------------------------------------------
# Branding
# --------------------------------------------------------------------------
# The public-facing identity of the service. Embeds, e-mails and the bot's
# presence all read from here.

BRAND_NAME = _str("BRAND_NAME", "CommendBot")
BRAND_URL = _str("BRAND_URL", "https://example.com")
BRAND_DISCORD_URL = _str("BRAND_DISCORD_URL", "https://example.com/discord")
# Direct invite handed to blacklisted users so they can appeal.
SUPPORT_SERVER_INVITE = _str("SUPPORT_SERVER_INVITE", BRAND_DISCORD_URL)
BRAND_RULES_URL = _str("BRAND_RULES_URL", "https://example.com/rules")
BRAND_LOGO_URL = _str("BRAND_LOGO_URL", "")
BRAND_FOOTER_IMAGE = _str("BRAND_FOOTER_IMAGE", "")
BRAND_STEAM_GROUP_URL = _str(
    "BRAND_STEAM_GROUP_URL", "https://steamcommunity.com/groups/csgo-commend-bot"
)
BRAND_FOOTER = _str("BRAND_FOOTER", f"powered by {BRAND_NAME}")
BRAND_COLOR = _int("BRAND_COLOR", 0x0A8F82)

# Mail identity. MAIL_DOMAIN must be a domain you are allowed to send from -
# transactional mail from a domain you do not control gets rejected.
MAIL_DOMAIN = _str("MAIL_DOMAIN", "example.com")
MAIL_FROM_NAME = _str("MAIL_FROM_NAME", BRAND_NAME)
MAIL_NOREPLY = f"noreply@{MAIL_DOMAIN}"
MAIL_PROMO = f"promo@{MAIL_DOMAIN}"
MAIL_FROM_NOREPLY = f"{MAIL_FROM_NAME} <{MAIL_NOREPLY}>"
MAIL_FROM_PROMO = f"{MAIL_FROM_NAME} <{MAIL_PROMO}>"
PAYPAL_EMAIL = _str("PAYPAL_EMAIL", f"commendbot@{MAIL_DOMAIN}")

# Game server players connect to while a slot is commending them.
GAME_SERVER_HOST = _str("GAME_SERVER_HOST", "cs2.example.com")
GAME_SERVER_PORT = _int("GAME_SERVER_PORT", 27015)
GAME_SERVER_CONNECT = f"connect {GAME_SERVER_HOST}:{GAME_SERVER_PORT}"


# --------------------------------------------------------------------------
# Discord: guilds
# --------------------------------------------------------------------------

# Main support/staff guild ("r4p"): roles, staff tooling and owner logs.
SUPPORT_GUILD_ID = _int("SUPPORT_GUILD_ID", 835787802151092234)
# Guild that hosts the slot channels and reseller categories.
SLOT_GUILD_ID = _int("SLOT_GUILD_ID", 949746802163326998)
# Secondary community guild used for invites and feedback.
COMMUNITY_GUILD_ID = _int("COMMUNITY_GUILD_ID", 1099636326237736962)
# Partner guild whose tickets are exempt from the shared-channel check.
PARTNER_GUILD_ID = _int("PARTNER_GUILD_ID", 1165707752996339854)
# Legacy guild referenced by the on_member_join welcome flow.
LEGACY_GUILD_ID = _int("LEGACY_GUILD_ID", 895754999425036309)

# Guilds that receive guild-scoped (instantly synced) slash commands.
TESTING_GUILD_IDS = _int_list(
    "TESTING_GUILD_IDS",
    (835787802151092234, 931983378968895498, 916793162201190481),
)

# Slot whose balances expire on a schedule; customers get one warning DM
# before the reset happens.
RESET_WARNING_SLOT_ID = _int("RESET_WARNING_SLOT_ID", 3)

# Guilds with a bespoke welcome/pricing variant in utils.variables.
CUSTOM_WELCOME_GUILD_IDS = _int_list(
    "CUSTOM_WELCOME_GUILD_IDS", (812256537934036993, 848194836301742087)
)


# --------------------------------------------------------------------------
# Discord: channels
# --------------------------------------------------------------------------

# Owner-facing firehose for joins, leaves and setup events.
OWNER_LOG_CHANNEL_ID = _int("OWNER_LOG_CHANNEL_ID", 937734062230106152)
# Slash command errors and rate-limit trips.
ERROR_LOG_CHANNEL_ID = _int("ERROR_LOG_CHANNEL_ID", 918941115216957523)
# Commend transactions.
TRANSACTION_LOG_CHANNEL_ID = _int("TRANSACTION_LOG_CHANNEL_ID", 1005209951871975515)
# Secondary transaction log (refunds and corrections).
TRANSACTION_LOG_2_CHANNEL_ID = _int("TRANSACTION_LOG_2_CHANNEL_ID", 1004344430221856788)
# Slot state changes pushed by the slot workers.
SLOT_LOG_CHANNEL_ID = _int("SLOT_LOG_CHANNEL_ID", 1096499376228159679)
# Subscription payment log.
SUBSCRIPTION_LOG_CHANNEL_ID = _int("SUBSCRIPTION_LOG_CHANNEL_ID", 1120429184100073614)
# Blacklist / ban announcements.
BAN_LOG_CHANNEL_ID = _int("BAN_LOG_CHANNEL_ID", 1120799418824790026)
# Where the public reseller leaderboard message is kept.
RESELLER_BOARD_CHANNEL_ID = _int("RESELLER_BOARD_CHANNEL_ID", 1005878077009702992)
RESELLER_BOARD_MESSAGE_ID = _int("RESELLER_BOARD_MESSAGE_ID", 1147869855526174831)
# Ticket channel customers are pointed at when a subscription is due.
SUPPORT_TICKET_CHANNEL_ID = _int("SUPPORT_TICKET_CHANNEL_ID", 925719726208978994)
# Feature/report requests from customers.
REQUEST_CHANNEL_ID = _int("REQUEST_CHANNEL_ID", 1008790227202093076)
# Refund requests.
REFUND_CHANNEL_ID = _int("REFUND_CHANNEL_ID", 1022977581802336386)
# Backup copies of generated key batches.
KEY_BACKUP_CHANNEL_ID = _int("KEY_BACKUP_CHANNEL_ID", 1113573738651320390)
# Automatic PayPal payout notifications.
AUTO_PAYOUT_CHANNEL_ID = _int("AUTO_PAYOUT_CHANNEL_ID", 1158009571244261376)
# Invite-reward announcements.
INVITE_CHANNEL_ID = _int("INVITE_CHANNEL_ID", 1165231121383043143)
# Gift/boost notifications.
GIFT_CHANNEL_ID = _int("GIFT_CHANNEL_ID", 1216846928877457539)
# Announcement channel relayed to every reseller guild.
NEWS_CHANNEL_ID = _int("NEWS_CHANNEL_ID", 1152634246658277517)
# Public welcome channel in the legacy guild.
WELCOME_CHANNEL_ID = _int("WELCOME_CHANNEL_ID", 967104311052107797)
# Feedback channel linked from the "thank you" embed.
FEEDBACK_CHANNEL_ID = _int("FEEDBACK_CHANNEL_ID", 1099636327135313964)


# --------------------------------------------------------------------------
# Discord: categories
# --------------------------------------------------------------------------

# Category new reseller slot channels are created under.
SLOT_CATEGORY_ID = _int("SLOT_CATEGORY_ID", 1000428140126031893)
# Overflow category for reward channels.
REWARD_CATEGORY_ID = _int("REWARD_CATEGORY_ID", 1003372945818783744)
# Ticket categories used by the private-channel flow.
TICKET_CATEGORY_ID = _int("TICKET_CATEGORY_ID", 1004844265249185932)
TICKET_ARCHIVE_CATEGORY_ID = _int("TICKET_ARCHIVE_CATEGORY_ID", 954366568635187280)


# --------------------------------------------------------------------------
# Discord: roles
# --------------------------------------------------------------------------

# Granted to customers with an active commend balance.
CUSTOMER_ROLE_ID = _int("CUSTOMER_ROLE_ID", 1102577419757563974)
# Granted to customers who cleared the trust threshold.
TRUSTED_ROLE_ID = _int("TRUSTED_ROLE_ID", 1136316085940006942)
# Community guild member role handed out on join.
COMMUNITY_ROLE_ID = _int("COMMUNITY_ROLE_ID", 1099636326669746200)


# --------------------------------------------------------------------------
# Discord: people
# --------------------------------------------------------------------------

OWNER_ID = _int("OWNER_ID", 949294483579732008)
# Staff who get owner-level access to the admin commands.
ADMIN_IDS = _int_list("ADMIN_IDS", (839124828232744970,))
# Accounts allowed to run staff-only commands besides the owner.
TRUSTED_BOT_IDS = _int_list("TRUSTED_BOT_IDS", (1137739127094255688,))
# Accounts the bot must never try to DM (service accounts, webhook relays).
NO_DM_USER_IDS = _int_list("NO_DM_USER_IDS", (1145489978193891448,))
# Gifters whose transfers get announced in GIFT_CHANNEL_ID.
TRACKED_GIFTER_IDS = _int_list("TRACKED_GIFTER_IDS", (1143289243104448655,))
# Accounts staff may not top up (chargeback history, banned resellers).
BLOCKED_BALANCE_USER_IDS = _int_list("BLOCKED_BALANCE_USER_IDS", (590219297293336586,))
# Shown in the rewards shop embed.
DONATORS = ["PeterLinuxOS", "Sirify"]


# --------------------------------------------------------------------------
# Referral promotion
# --------------------------------------------------------------------------
# Optional affiliate offer surfaced by /promo. Leave PROMO_INVITE_URL empty to
# turn the feature off.

PROMO_PARTNER = _str("PROMO_PARTNER", "our partner")
PROMO_TITLE = _str("PROMO_TITLE", "Referral offer")
PROMO_DESCRIPTION = _str(
    "PROMO_DESCRIPTION",
    "Sign up through our referral link and earn bonus commends.",
)
PROMO_INVITE_URL = _str("PROMO_INVITE_URL", "")
PROMO_CODE = _str("PROMO_CODE", "")
PROMO_THUMBNAIL_URL = _str("PROMO_THUMBNAIL_URL", "")
PROMO_IMAGE_URL = _str("PROMO_IMAGE_URL", "")
PROMO_COLOR = _int("PROMO_COLOR", 0x4286F4)
# Sign-up form linked from the free-commends mail-out.
PROMO_FORM_URL = _str("PROMO_FORM_URL", "")


# --------------------------------------------------------------------------
# Credits
# --------------------------------------------------------------------------
# Shown by /credits. The original listed each contributor's Discord user id;
# those are left out here so publishing the source does not publish other
# people's account ids. Add "<@id>" mentions yourself if you want them back.

CREDITS = [
    ("Developer", "Peter"),
    ("UI Developer", "Peter"),
    ("UI Developer", "Samuel"),
    ("Graphic design", "Lostik"),
]

TRANSLATION_CREDITS = [
    ("English", "Peter"),
    ("Slovak", "Samuel, Peter"),
    ("German", "community contributor"),
    ("Hungarian", "community contributor"),
    ("Portuguese", "community contributor"),
    ("Polish", "community contributor"),
]


# --------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------
# Tutorial screenshots and banners that used to be hotlinked from Discord CDN
# attachments. Those links expire; re-host them and point these at your copies.

IMAGE_TUTORIAL_SETUP = _str("IMAGE_TUTORIAL_SETUP", "")
IMAGE_TUTORIAL_COMMEND = _str("IMAGE_TUTORIAL_COMMEND", "")
IMAGE_TUTORIAL_WELCOME = _str("IMAGE_TUTORIAL_WELCOME", "")
IMAGE_PROMO_BANNER = _str("IMAGE_PROMO_BANNER", "")
IMAGE_WARNING_ICON = _str("IMAGE_WARNING_ICON", "")


# --------------------------------------------------------------------------
# Custom emoji
# --------------------------------------------------------------------------
# These live in the support guild. Replace them with your own or with plain
# unicode - the strings are inlined into embeds as-is.

EMOJI_YES = _str("EMOJI_YES", "<:yes:904125024477278210>")
EMOJI_NO = _str("EMOJI_NO", "<:no:904125314983145572>")
EMOJI_WAIT = _str("EMOJI_WAIT", "<a:wait:930490650401603645>")
EMOJI_QUEUED = _str("EMOJI_QUEUED", "<a:wait:962739109724561418>")
EMOJI_COMMENDING = _str("EMOJI_COMMENDING", "<a:commending:962460310508294164>")
EMOJI_NOT_COMMENDING = _str(
    "EMOJI_NOT_COMMENDING", "<a:notcommending:962460505539219516>"
)


# --------------------------------------------------------------------------
# Legacy branding substitution
# --------------------------------------------------------------------------
# utils/translates.py holds ~850 lines of localised copy with the original
# brand baked into the strings. Rewriting every literal would make the
# translations unreviewable, so instead the tables are rewritten in place at
# import time using this mapping. Anything not listed here is left alone.

LEGACY_BRANDING: dict[str, str] = {
    "<:yes:904125024477278210>": EMOJI_YES,
    "<:no:904125314983145572>": EMOJI_NO,
    "<a:wait:930490650401603645>": EMOJI_WAIT,
    "<a:wait:962739109724561418>": EMOJI_QUEUED,
    "<a:commending:962460310508294164>": EMOJI_COMMENDING,
    "<a:notcommending:962460505539219516>": EMOJI_NOT_COMMENDING,
    "https://gameboosting.top/discord-rules-csgo-commendbot-rules/": BRAND_RULES_URL,
    "https://gameboosting.top/discord": BRAND_DISCORD_URL,
    "https://gameboosting.top/": BRAND_URL,
    "https://gameboosting.top": BRAND_URL,
    "gameboosting.top/discord": BRAND_DISCORD_URL,
    "powered by gameboosting.top": BRAND_FOOTER,
    "gameboosting.top": BRAND_NAME,
    "r4p Services | ": "",
    "r4p Services": BRAND_NAME,
    "GameBoosting": BRAND_NAME,
    "cs2.sinlyxe.cc:27015": f"{GAME_SERVER_HOST}:{GAME_SERVER_PORT}",
    "cs2.sinlyxe.cc": GAME_SERVER_HOST,
}


def apply_branding(value):
    """Recursively replace legacy brand literals inside strings/lists/dicts."""
    if isinstance(value, str):
        for old, new in LEGACY_BRANDING.items():
            if old in value:
                value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [apply_branding(item) for item in value]
    if isinstance(value, tuple):
        return tuple(apply_branding(item) for item in value)
    if isinstance(value, dict):
        return {key: apply_branding(item) for key, item in value.items()}
    return value

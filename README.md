<p align="center">
  <img src="assets/logo.png" alt="r4p Services" width="140">
</p>

# CommendBot

A Discord bot that operated a paid CS:GO / CS2 commend service under the
**r4p Services** brand (gameboosting.top). Customers purchased a balance of
commends, opened a private ticket, connected to a game server, and received
commends on their Steam account while the bot tracked progress and settled their
balance. Resellers could run the service on their own Discord guilds under a
subscription.

The service operated from November 2019 to January 2025. This repository is an
archive of the bot, published for reference. All credentials have been removed
and rotated.

## Overview

CommendBot is the **management and commerce layer** of the service. It does not
deliver commends itself; that was handled by separate worker processes ("slots")
running on isolated accounts. The bot and the workers communicate exclusively
through MongoDB collections — the bot records a request, a worker acts on it, and
the worker writes progress back.

The worker component is published separately, at
[commendbot-slots](https://github.com/PeterLinuxOSS/commendbot-slots). It
automates a Discord user account, which violates Discord's Terms of Service;
that repository documents this plainly and is published for reference, not as
an invitation to run it.

Responsibilities of the bot:

- Customer accounts, balances, and per-slot wallets
- Private ticket channels and the commend session lifecycle
- Purchases (PayPal) and redeemable key generation
- Reseller subscriptions, billing, and a public reseller directory
- Transactional email (verification, recovery, notifications)
- Localised customer-facing copy in six languages
- A daily rewards wheel and an invite-reward system

## Architecture

```
 Customer ──▶ Discord ──▶ CommendBot ──▶ MongoDB ◀──▶ Slot workers
                             │                          (separate repo,
                             │                           isolated hosts)
                             ├─ balances, wallets, tickets
                             ├─ purchases, keys, payouts
                             └─ reseller subscriptions & billing
```

The bot writes commend requests to the `waitinglist` / `slottrans` collections;
workers consume them, drive the commend process, and write status events back.
`cogs/slottrans.py` watches those collections with MongoDB **change streams** and
updates the customer's ticket in real time.

## Commands

The bot registers 56 application commands. The customer-facing subset:

| Command | Purpose |
| --- | --- |
| `/redeem` | Add commends to your balance from a key |
| `/balance` | Show your commend balance |
| `/commend` | Start commending a Steam profile *(menu-driven)* |
| `/stop-commend` | Stop an active commend session |
| `/buy` | Order commends and pay via PayPal |
| `/profile`, `/userinfo` | Account overview and statistics |
| `/giftbalance`, `/transfer` | Move balance between users |
| `/daily` | Daily rewards wheel |
| `/rewards` | Rewards shop |
| `/leaderboard` | Customer leaderboard |
| `/mysubscriptions` | Reseller subscription status |
| `/recovery`, `/verify` | Account recovery and email verification |
| `/setup` | Per-guild setup wizard |
| `/rules`, `/help`, `/credits` | Informational |

Staff and owner commands (balance adjustments, blacklist, panels, slot
management, diagnostics) live in `cogs/commands_admin.py` and are gated on the
owner and `ADMIN_IDS`.

## How the commend flow worked

From the original operator documentation and the live service:

- A customer opened a private channel and started a session against a game server.
- Commends arrived in batches — roughly 20 every 5–10 minutes, with a daily cap
  (2,000 per account on the later CS2 service).
- The game server restarted hourly on the hour; customers had to reconnect within
  ~1 minute 45 seconds or the session paused and unused commends returned to their
  balance.
- The server ran anti-AFK, so customers could remain connected without being kicked.

## Project layout

| Path | Contents |
| --- | --- |
| `main.py` | Entry point: loads cogs, owner commands, daily cron jobs |
| `config.py` | All configuration — credentials, IDs, and branding — from the environment |
| `cogs/commend_menu*.py` | Ticket lifecycle and the customer commend menu |
| `cogs/commands*.py` | Slash commands, split into mixins by theme |
| `cogs/bot_tasks.py` | Scheduled jobs: subscription billing, mailouts, cleanup |
| `cogs/slottrans.py` | Change-stream watchers for slot-worker events |
| `cogs/keygen.py` | Redeemable key generation and redemption |
| `cogs/settings.py`, `cogs/setup_c.py` | Per-guild configuration wizards |
| `cogs/resellers.py`, `cogs/rewards.py` | Reseller directory and rewards shop |
| `utils/translates.py` | Localised copy (EN, DE, SK, PT, HU, PL) |
| `utils/html.py` | Transactional email templates |
| `tools/` | Standalone verification scripts |

The `cogs/*_views.py` and `cogs/commands_*.py` mixin modules are not extensions.
`main.py` loads an explicit `EXTENSIONS` list rather than scanning the directory,
because `cogs/helpers.py` re-exports its `setup()` to importers and directory
scanning would load the same cog more than once.

## Requirements

- Python 3.11
- A MongoDB **replica set** (not a standalone server)

`cogs/slottrans.py` relies on change streams and `utils/mongodb.py` reads the
oplog; both require a replica set. A single node is sufficient:

```bash
mongod --dbpath /var/lib/mongo --replSet rs0
mongosh --eval 'rs.initiate({_id:"rs0", members:[{_id:0, host:"127.0.0.1:27017"}]})'
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env      # fill in the values
python main.py
```

`config.validate()` refuses to start unless `DISCORD_TOKEN` and `MONGODB_URI`
are set.

## Configuration

All operational values are read from the environment via `config.py`: brand name
and URLs, the game-server address, mail identity, the referral offer, and the
Discord IDs of the deployment (guilds, channels, categories, roles, and staff).
The defaults in `config.py` are the identifiers of the original deployment and
serve as a reference; set your own before running.

Localised copy in `utils/translates.py` embeds the original brand in its strings.
Rather than rewrite every translated line, `config.LEGACY_BRANDING` maps the
original literals to the configured values and the tables are rewritten at import
time. The same substitution runs over the HTML email templates.

## Verification

Two scripts under `tools/` validate the bot without a full deployment:

- `tools/test_change_streams.py` — drives the slot-worker watchers against a local
  replica set and asserts they process a real event.
- `tools/live_smoketest.py` — connects to Discord once to confirm the bot starts
  end to end, with the automatic command sync disabled and the database pointed at
  a local instance.

## Development history

The business launched in November 2019 and the bot began in 2020 as a fork of an
open-source CS:GO commend bot, rewritten and extended over the following years:

| Date | Milestone |
| --- | --- |
| Nov 2019 | Service launched |
| 2020 | Bot built on a fork of an open-source commend bot |
| Apr 2021 | Current Discord guild created |
| Oct 2021 | Guild officially reopened after a redesign |
| Jan 2022 | 300 members, 69 customers (first recorded snapshot) |
| 2022 | Rewrite; localisation and the reseller model introduced |
| 2023 | Standalone control panel; email and recovery flows |
| 2024 | v7.0.0 — final production version (this archive) |
| Jan 2025 | CommendBot discontinued |
| Dec 2025 | Business and Discord server closed |

The support guild reached 794 members, but that undercounts actual usage —
customers also reached the bot through dozens of reseller guilds, and many
left the support guild once they stopped using the service. Queried directly
from the production database (aggregate counts only):

| Metric | Value |
| --- | --- |
| Registered accounts | 6,164 |
| Distinct paying customers | 3,703 |
| Guilds the bot was ever configured on | 83 |
| Reseller subscriptions issued | 196 |
| Commends delivered | 1,258,424 (across 25,056 transactions) |
| Redeem keys generated | 1,301 |

The bot ran on `nextcord` with MongoDB (Motor) and was deployed under PM2.

## License

MIT — see `LICENSE`.

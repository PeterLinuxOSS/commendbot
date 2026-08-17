# CommendBot

A Discord bot that ran a CS:GO / CS2 commend service: customers opened a private
ticket, bought or redeemed a balance of commends, connected to a game server and
watched the commends arrive. Resellers could run the same bot on their own guild
under a subscription.

**This is an archive.** The service it belonged to is shut down and the bot is no
longer operated. It is published as-is so the code is useful to read, not because
it is a maintained product. Every credential that was ever in this tree has been
removed and rotated.

## What is actually in here

The bot is the **management layer only**. It never sent a commend itself.

```
customer  ──▶  Discord  ──▶  this bot  ──▶  MongoDB  ──▶  slot workers
                              │                             (separate,
                              │                              not in this repo)
                              └──▶ balances, tickets, subscriptions,
                                   keys, payouts, reseller accounting
```

The commends themselves were performed by "slot" workers running a third-party
reseller pack on a separate host. This bot and the workers communicated through
MongoDB collections (`slottrans`, `serverusers`, `commendbotstatus`) — the bot
wrote a request, a worker picked it up, and the worker wrote progress back. The
worker side is not part of this repository, so **the bot cannot actually deliver
commends on its own.** Everything else — the whole customer, billing and reseller
surface — is here and functional.

## Layout

| Path | What it does |
|---|---|
| `main.py` | Entry point: loads cogs, owner commands, two daily cron jobs |
| `config.py` | Every credential, ID and branding string, read from `.env` |
| `cogs/commend_menu*.py` | Ticket lifecycle and the customer commend menu |
| `cogs/commands*.py` | ~56 slash commands, split into mixins by theme |
| `cogs/bot_tasks.py` | Scheduled jobs: subscription billing, mail-outs, cleanup |
| `cogs/slottrans.py` | Watches MongoDB oplog for slot worker messages |
| `cogs/keygen.py` | Redeemable key generation and redemption |
| `cogs/settings.py`, `cogs/setup_c.py` | Per-guild setup wizards |
| `utils/translates.py` | Six languages (EN, DE, SK, PT, HU, PL) |
| `utils/html.py` | Transactional e-mail templates |

The `cogs/*_views.py` and `cogs/commands_*.py` mixin modules are **not**
extensions — `main.py` loads an explicit `EXTENSIONS` list rather than globbing
the directory, because `from cogs.helpers import *` leaks that module's `setup()`
into everything that imports it.

## Running it

Requires Python 3.11 and a MongoDB instance.

```bash
pip install -r requirements.txt
cp .env.example .env      # then fill it in
python main.py
```

`config.validate()` refuses to start without `DISCORD_TOKEN` and `MONGODB_URI`.

Everything the bot used to hardcode now lives in `config.py`, reading from the
environment: brand name and URLs, the game server address, mail identity, and
roughly seventy Discord snowflakes (guilds, channels, categories, roles, staff).
The defaults in `config.py` are the IDs of the original deployment — they are
there as documentation of how the pieces fit together, and you must point them at
your own guild before the bot does anything useful.

### Branding in the translations

`utils/translates.py` holds ~850 lines of localised copy with the original brand
baked into the strings. Rather than rewrite every literal and make the
translations unreviewable, `config.LEGACY_BRANDING` maps the original literals to
your configured values and the tables are rewritten in place at import time. The
same pass runs over the HTML e-mail templates. If you see the old domain in a
source string, that is why — check what it renders as, not what it says.

## Known rough edges

This is 2020s-era hobby code that grew under a live service. It is published
honestly, not polished into something it never was.

- **Nothing is tested.** There is no test suite. The helpers, embed builders,
  mail templates and DB lookups have been exercised by hand against a local
  MongoDB, but nothing is automated and the Discord-facing paths are unproven.
- **The e-mail templates hotlink Discord CDN attachments** that have long since
  expired. Re-host the images and repoint `config.IMAGE_*`.
- **Error handling is broad.** Bare `except:` blocks were narrowed to
  `except Exception:`, which stops them swallowing `KeyboardInterrupt` and
  `CancelledError`, but they still swallow a lot.

## What changed when this was published

The working history was not public, so this repo starts from a single commit. The
notable differences from the code that ran in production:

- Credentials removed and read from `.env` instead: Discord token, MongoDB URI,
  Brevo SMTP key, Steam Web API key, and a remote host's root password. All of
  them have been rotated.
- Branding, staff identities, contributor Discord IDs, referral codes and ~70
  hardcoded snowflakes moved into `config.py`.
- `commands.py` (3031 lines) and `commend_menu.py` (1834 lines) split into mixin
  and view modules. The registered command surface was verified identical before
  and after: 18 cogs, 56 application commands.
- ~650 unused imports, ~200 lines of commented-out code and several dead
  functions removed.
- **Star imports untangled.** Every `from X import *` outside `utils/__init__.py`
  was replaced with an explicit import list, resolved by importing each module
  and inspecting the real namespaces rather than guessing. Ruff went from 1287
  `F405`s (and `F821` being useless) to zero of both.

Bugs found and fixed on the way through:

- `/adminbalance` took no argument and always reported one hardcoded account's
  balance; it now takes a `user`.
- `banuser` was a global slash command with no permission check — any user could
  ban across every guild the bot was in.
- The daily wheel spin crashed whenever a customer had more than one wallet: the
  select callback called an unbound method and passed the interaction as `self`.
- `lang["on_message-error_field-title"]` raised `KeyError` — a duplicate key in
  all six translation tables had overwritten the intended one.
- `favoriteguilds()` listed the same guild twice, making one branch unreachable.
- A dead error path called `servers["server1"]`, subscripting a string.
- `utils.translates` and `utils.variables` imported each other; whether it worked
  depended on which module Python happened to load first.
- Missing translation keys called `os._exit(3)` at import time; they are now
  reported by `check_translations()` and fall back to English.
- `json` was never imported in `settings.py` or `slottrans.py` — it only ever
  resolved because `cogs/helpers.py` happened to re-export it through a star
  import. `json.loads()` in the slot-worker oplog watcher was one bad path away
  from a `NameError`.
- A new reseller subscription was inserted with `"datetime"` twice: the creation
  time and the expiry. The later key won, so the intended value was silently
  discarded — had the order been the other way round, every subscription would
  have expired the moment it was created.

Verification used throughout: load all cogs into a real `nextcord` Bot and diff
the registered command surface (18 cogs / 56 commands) after every change, then
drive the helpers against a local MongoDB. Both caught regressions that
importing the modules did not — a missing name in a rarely-taken branch does not
fail until that branch runs.

## License

MIT — see `LICENSE`.

"""Connect the bot to Discord once, with every side effect neutralised.

Answers one question: does this bot still start end to end against the real
gateway? It logs in, loads every extension, lets on_ready run, reports what
happened and disconnects.

What is deliberately defused:

* **No command sync.** nextcord's default on_connect calls
  sync_application_commands with delete_unknown=True and register_new=True,
  which would rewrite the live global slash-command set for every guild the
  bot is still in. All four rollout flags are turned off here.
* **Local database.** MONGODB_URI points at a throwaway local mongod, so
  on_ready reads an empty database: no customer DMs, no message edits in real
  guilds, no writes to production data. It must be a single-node **replica
  set**, because cogs/slottrans.py watches the database with change streams,
  which MongoDB refuses to open on a standalone server:

      mongod --dbpath /tmp/cb-mongo --replSet rs0 --fork --logpath /tmp/cb-mongo.log
      mongosh --eval 'rs.initiate({_id:"rs0", members:[{_id:0, host:"127.0.0.1:27017"}]})'
* **Bounded.** Disconnects after TIMEOUT seconds no matter what.
* **Read-only presence.** The bot will appear online for that window. That is
  the one visible effect and it cannot be avoided while still testing login.

Run it yourself - it needs the real token, which this script reads straight
into memory from the original secrets file and never prints:

    python3 tools/live_smoketest.py
"""

import asyncio
import datetime
import json
import logging
import os
import sys
import traceback
from pathlib import Path

TIMEOUT = 90                     # seconds before we disconnect regardless
SECRETS = Path("/root/commendbot/bot_config/secrets.json")
LOCAL_MONGO = "mongodb://127.0.0.1:27017/?directConnection=true"

os.environ["MONGODB_URI"] = LOCAL_MONGO          # never the production cluster
os.environ.setdefault("STEAM_API_KEY", "dummy")
os.environ.setdefault("BRAND_NAME", "CommendBot")

if not SECRETS.exists():
    sys.exit(f"no secrets file at {SECRETS}")
os.environ["DISCORD_TOKEN"] = json.loads(SECRETS.read_text())["TOKEN"]

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.chdir(Path(__file__).resolve().parents[1])

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
log = logging.getLogger("smoketest")

import nextcord  # noqa: E402

import main as botmain  # noqa: E402

bot = botmain.bot

# --- defuse the automatic global command sync --------------------------------
bot._rollout_associate_known = False
bot._rollout_delete_unknown = False
bot._rollout_register_new = False
bot._rollout_update_known = False

report = {"login": False, "ready": False, "guilds": [], "errors": []}


async def require_replica_set():
    """Fail loudly rather than let the slot watchers die quietly."""
    from utils import db
    try:
        status = await db.client.admin.command("replSetGetStatus")
    except Exception as exc:
        sys.exit(
            f"local mongod is not a replica set ({exc}).\n"
            "cogs/slottrans.py needs change streams; start it with --replSet rs0 "
            "and run rs.initiate() - see this file's docstring."
        )
    log.info("mongo replica set %r, state %s",
             status["set"], status["members"][0]["stateStr"])


async def seed_minimum():
    """commend_menu.on_ready does pausetry["pause"] with no None check."""
    from utils import db
    import config
    await db.guildsetting.update_one(
        {"guildid": config.SUPPORT_GUILD_ID},
        {"$setOnInsert": {
            "guildid": config.SUPPORT_GUILD_ID, "pause": True, "setupbot": False,
            "public": False, "sumcurrency": 0,
            "time": datetime.datetime.now(tz=datetime.timezone.utc),
        }},
        upsert=True,
    )


@bot.event
async def on_ready():
    """Replaces main.on_ready so the smoke test controls the outcome."""
    report["login"] = True
    report["guilds"] = [(g.name, g.id, g.member_count) for g in bot.guilds]
    log.info("logged in as %s (%s)", bot.user, bot.user.id)
    log.info("in %d guild(s)", len(bot.guilds))
    for name, gid, members in report["guilds"]:
        log.info("    %-40s %-20s %s members", name[:40], gid, members)

    # run the real handler, but do not let it block on the slot workers
    bot.slottrans_ready = True
    try:
        await botmain.warn_about_balance_reset()
        report["ready"] = True
        log.info("main.warn_about_balance_reset() completed")
    except Exception as exc:
        report["errors"].append(f"warn_about_balance_reset: {exc!r}")
        log.error("warn_about_balance_reset failed", exc_info=True)


async def run():
    await require_replica_set()
    await seed_minimum()
    botmain.load_extensions()
    log.info("loaded %d cogs, %d application commands",
             len(bot.cogs), len(bot.get_all_application_commands()))

    task = asyncio.create_task(bot.start(os.environ["DISCORD_TOKEN"]))
    try:
        await asyncio.wait_for(asyncio.shield(task), timeout=TIMEOUT)
    except asyncio.TimeoutError:
        log.info("timeout reached, disconnecting")
    except nextcord.LoginFailure as exc:
        report["errors"].append(f"login failed: {exc}")
        log.error("login failed - the token is no longer valid: %s", exc)
    except Exception as exc:
        report["errors"].append(repr(exc))
        log.error("unexpected failure", exc_info=True)
    finally:
        if not bot.is_closed():
            await bot.close()
        task.cancel()

    print("\n" + "=" * 60)
    print(f"login ok            : {report['login']}")
    print(f"on_ready completed  : {report['ready']}")
    print(f"guilds              : {len(report['guilds'])}")
    print(f"cogs loaded         : {len(bot.cogs)}")
    print(f"commands registered : {len(bot.get_all_application_commands())} (locally, none synced to Discord)")
    print(f"errors              : {report['errors'] or 'none'}")
    print("=" * 60)
    return 1 if report["errors"] or not report["login"] else 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(run()))
    except KeyboardInterrupt:
        pass
    except Exception:
        traceback.print_exc()
        sys.exit(1)

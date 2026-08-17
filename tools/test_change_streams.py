"""Check that the slot-worker watchers actually run.

cogs/slottrans.py is how the bot hears from the slot workers, and it does that
with MongoDB change streams. Those only exist on a replica set, so on a
standalone mongod both watchers die on startup and the bot silently stops
learning about commend progress. This drives them against a local replica set
and asserts they survive a real event.

    mongod --dbpath /tmp/cb-mongo --replSet rs0 --fork --logpath /tmp/cb-mongo.log
    mongosh --eval 'rs.initiate({_id:"rs0", members:[{_id:0, host:"127.0.0.1:27017"}]})'
    MONGODB_URI='mongodb://127.0.0.1:27017/?directConnection=true' \
        python3 tools/test_change_streams.py

Uses whatever MONGODB_URI points at, so point it at a throwaway database: it
writes to waitinglist and slottrans.
"""

import asyncio
import datetime
import os
import sys
from pathlib import Path

os.environ.setdefault("MONGODB_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
os.environ.setdefault("DISCORD_TOKEN", "dummy")
os.environ.setdefault("STEAM_API_KEY", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.chdir(Path(__file__).resolve().parents[1])

from utils import db  # noqa: E402

results = []


def record(label, passed, detail=""):
    results.append((label, passed))
    print(f"  {'ok  ' if passed else 'FAIL'}  {label}{f': {detail}' if detail else ''}")


class _Channel:
    async def send(self, *a, **k): ...
    async def fetch_message(self, *a, **k): return None


class _Bot:
    """Only the attributes slottrans touches."""
    def __init__(self):
        self.slottrans_ready = False
        self.owner_id = 1
        self.pause = False
        self.loop = asyncio.get_event_loop()
        self._channel = _Channel()
    def get_channel(self, _): return self._channel
    def get_user(self, _): return None
    def get_guild(self, _): return None


def _detached(cls, bot):
    """Build the cog without __init__, which would spawn the watchers itself."""
    cog = cls.__new__(cls)
    cog.bot = bot
    cog.loop = asyncio.get_event_loop()
    return cog


async def main():
    try:
        status = await db.client.admin.command("replSetGetStatus")
        record("mongodb is a replica set", True,
               f"{status['set']} / {status['members'][0]['stateStr']}")
    except Exception as exc:
        record("mongodb is a replica set", False, str(exc))
        print("\nchange streams need a replica set - see this file's docstring.")
        return 1

    for label, database in (("servers", db.servers), ("usersdb", db.users_database)):
        try:
            stream = database.watch()
            await stream.close()
            record(f"{label}.watch() opens", True)
        except Exception as exc:
            record(f"{label}.watch() opens", False, repr(exc))

    from cogs.slottrans import slottrans

    # --- watch_mongodb: a waitinglist insert should be picked up -------------
    await db.waitinglist.delete_many({})
    await db.slottrans.delete_many({})

    bot = _Bot()
    cog = _detached(slottrans, bot)
    task = asyncio.create_task(cog.watch_mongodb())
    await asyncio.sleep(0.5)
    bot.slottrans_ready = True
    await asyncio.sleep(2.0)

    await db.waitinglist.insert_one({
        "type": "start", "status": "wait", "slot_id": 1,
        "steamID64": 76561199095301693, "amount": 50,
        "datetime": datetime.datetime.now(tz=datetime.timezone.utc),
    })

    doc = queued = None
    for _ in range(40):
        await asyncio.sleep(0.25)
        doc = await db.waitinglist.find_one({"type": "start"})
        queued = await db.slottrans.find_one({"type": "start", "push": "post"})
        if doc and doc["status"] == "go" and queued:
            break

    record("watch_mongodb marks the waitinglist entry as go",
           bool(doc and doc["status"] == "go"),
           "" if doc and doc["status"] == "go" else f"status={doc and doc.get('status')!r}")
    record("watch_mongodb queues a slottrans push", bool(queued))
    record("watch_mongodb survives", not (task.done() and task.exception()),
           repr(task.exception()) if task.done() and task.exception() else "")
    task.cancel()

    # --- watch_usersdb: it used to raise TypeError the moment it started -----
    bot2 = _Bot()
    cog2 = _detached(slottrans, bot2)
    task2 = asyncio.create_task(cog2.watch_usersdb())
    await asyncio.sleep(0.3)
    bot2.slottrans_ready = True
    await asyncio.sleep(2.0)

    failed = task2.done() and task2.exception()
    record("watch_usersdb survives", not failed, repr(task2.exception()) if failed else "")
    task2.cancel()

    passed = sum(1 for _, p in results if p)
    print(f"\npassed: {passed}   failed: {len(results) - passed}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

"""Load every cog into a real nextcord Bot and report the command surface.

Run this after any change that touches imports, cog structure, or the
EXTENSIONS list in main.py. It catches import-time errors (missing imports,
circular imports, syntax mistakes introduced by a refactor) that a plain
`python -m compileall` cannot, because it actually executes module bodies
and registers cogs the way main.py does at startup.

Needs no live infrastructure: motor connects lazily, so MongoDB never has to
be reachable just to import the cogs and register their commands. It does
not exercise interactive flows, the change-stream watchers, or a real Discord
connection — see tools/test_change_streams.py and tools/live_smoketest.py for
those, and README.md's "Known rough edges" for what remains unverified.

    python3 tools/load_check.py
"""

import os
import sys
import traceback
from pathlib import Path

os.environ.setdefault("MONGODB_URI", "mongodb://127.0.0.1:1/?directConnection=true&serverSelectionTimeoutMS=200")
os.environ.setdefault("DISCORD_TOKEN", "dummy")
os.environ.setdefault("STEAM_API_KEY", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.chdir(Path(__file__).resolve().parents[1])

import main as botmain  # noqa: E402


def main() -> int:
    bot = botmain.bot
    failed = 0
    for ext in botmain.EXTENSIONS:
        try:
            bot.load_extension(ext)
        except Exception:
            failed += 1
            print(f"FAIL {ext}")
            traceback.print_exc()

    cmds = sorted(c.name for c in bot.get_all_application_commands())
    print(f"\ncogs loaded: {len(bot.cogs)}  failed: {failed}")
    print(f"application commands: {len(cmds)}: {' '.join(cmds)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

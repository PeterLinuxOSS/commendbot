# commendbot

Core of the **CommendBot** system — the engine that performs Steam / CS2 commends (positive account reports).

## Overview
- Bot core with commend-execution logic
- Configuration via `.env` (see `.env.example`)

## CommendBot family
- **commendbot** — core bot (commend logic)
- **commendbot-panel** — server-side control panel (dispatches & manages clients)
- **commendbot-client** — client agent running on the machine (drives Steam/CS2)
- **commendbot-slots** — slot-based instance manager
- **shopmanager** — Discord sales/order bot (keys, licenses)

_Part of the gameboosting service ecosystem._

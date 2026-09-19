# commendbot

Jadro systému **CommendBot** — logika vykonávania Steam/CS2 commendov (reporty/pochvaly účtov).

## Súčasti
- bot core + konfigurácia (`.env.example`)

## Rodina CommendBot
- **commendbot** — jadro bota (commend logika)
- **commendbot-panel** — serverový ovládací panel (spúšťa a riadi klientov)
- **commendbot-client** — klientský agent bežiaci na stroji (ovláda Steam/CS2)
- **commendbot-slots** — slotový systém inštancií
- **shopmanager** — predajný/objednávkový Discord bot (kľúče, licencie)

_Súčasť ekosystému služby gameboosting._

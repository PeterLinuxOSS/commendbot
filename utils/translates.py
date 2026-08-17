import datetime

from termcolor import colored

import config

timestamp = datetime.datetime.now()

# NOTE: this module must not import utils.variables - variables imports
# translates for get_lang(), and closing that loop makes import order decide
# whether the module works.

eng = {
    "lang": "English",
    "greets": [
            "Hello, {username}!",
            "Hi, {username}!",
            "Welcome back, {username}!",
            "Good to see you, {username}!",
            "Howdy, {username}!",
            "Hey there, {username}!",
            "Hello again, {username}!",
            "Hi, {username}! You're back!",
            "Welcome, {username}!",
            "We've missed you, {username}!",
            "What can we do, {username}?",
            "Here to help, {username}!",
            "Ready to start, {username}!",
            "Brightens our day, {username}!",
            "How can we assist, {username}?",
            "Hope you're well, {username}!",
            "Make your day great, {username}!",
            "Nice to have you, {username}!",
            "Long time no see, {username}!",
            "Great to see you, {username}!",
            "Greetings, {username}!",
            "How have you been, {username}?",
            "How's it going, {username}?",
            "What's new, {username}?",
            "How was your day, {username}?",
        ],
    "helpmenu-title": "Commend Bot Help Menu",
    "helpmenu-title2": "Available Commands",
    "helpmenu-description": "**/redeem <key>** • *Add commends to your balance using a key*\n**/balance** • *Check how many commends you have to claim*\n**/deletechannel** • *Delete this channel*\n/recovery - Recover your account via mail\n/verify_now - Add mail to your account\n\nYou can stay AFK on the server.\nUnused commends will be added to /balance within 5 minutes.",
    "helpmenu-author": "Commend Bot Help Menu",

    "on_error": "<:no:904125314983145572> Failure <:no:904125314983145572>",
    "error1": "Your Steam profile link is invalid, please check if your links are valid, try again, or contact support!",
    "error2": "Sorry, this command is in use!",
    "error3": "This user is already receiving commends!",
    "error4": "Sorry, we don't have any available slots, please wait a few minutes and try again.",
    "error5": "You can't use more than 0x commends!",
    "error6": "You don't have enough commends! (You have 0 commends)",
    "error7": "You can only use this command in a private channel (you can create one here)",
    "error8-title": "Commends in Progress",
    "error8-description": "Please wait until the previous order expires before creating a new one. Tip: It can take up to 20 minutes, and you don't need to do anything.",
    "error9": "You don't have enough commends!",
    "error10": "Sorry, but we currently don't have any commends in stock.",
    "error11": "Sorry, all commend slots are in use.",
    "error12": "This server doesn't have active reseller permissions!",
    "error13": "Today you can't use 0c commends, you can only use 0s commends or try after 00:00 UTC!",
    "error14": "Today you can't use 0c commends, you can only use 0u commends because the daily commend limit is 0s per user.",
    "error15": "Amount of commends is not numeric",

    "howitworkis-field1-title": "How It Works?",
    "howitworkis-field1-description": "• Paste this in console **\"`connect cs2.sinlyxe.cc:27015`\"**\n• After paste connect you will be **stuck** on loading screen\n• If you are stuck on loading screen then click green button\n• You will see first commends in few min (in console)\n\nIf You don't connect, the bot will **turn off** and return the unused commends to `/balance` within 5 minutes.\n\n**Make Sure You`ve Read Everything!**",

    "howitworkis-field2-title": "Make Sure You've Read Everything!",
    "howitworkis-field2-description": "**Connect to the server:**",
    "howitworkis-field5-title": "__if server 1 is not working connect to 2__",
    "howitworkis-field5-description": "✅⬇ ⬇ ⬇ ⬇ ⬇✅",
    "howitworkis-button": "Confirm that I'm on the server",

    "commendbotbutton-labe": "Create Private Channel!",
    "commendbotbutton-msg": "<a:wait:930490650401603645>Please wait, Creating your private channel<a:wait:930490650401603645>",
    "commendbotbutton-msg-edit": "Your private channel is here:",
    "commendbotbutton-ping": ", This is your private channel!",

    "Confirm-Confirm": "Confirmed",
    "on_commends_started": "Bot added you to the queue. You will start receiving commends in a few minutes.",
    "restartalert-title": "CSGO Server Restart Alert!",
    "restartalert-description": "The CSGO Commendbot server will restart in **1-2 minutes**! Please make sure to **reconnect** to continue the commend process. To **reconnect**, type `retry` in the __CS:GO console__.",

    "confirm-wait-error": "Please wait 2-4 minutes, the server is currently restarting!",
    "confirm-find-slot": "Finding the best slot for commends!",

    "create-title": "Commend Botting",
    "create-description": "Press the button in this message to get your own channel for Commend Bot.",
    "create-button1": "Start Commending",
    "on_message_finished-title": "Commends Sent",
    "on_message_finished-description": "Commends have been sent.",
    "on_message_finished_field-title": "Current Balance",


    "on_message_done-msg1": "You received all commends!",
    "on_message_done-msg2": "Commending successfully stopped!",
    "on_message_done-msg3": "Commending stopped",
    "on_message_done-msg4-a": "Successfully added",
    "on_message_done-msg4-b": "commends to your balance (New balance",
    "on_message_done-msg4-c": "old balance",


    "on_message-stopped-title": "Commending Stopped",
    "on_message-stopped-description": "Commending Stopped via command",
    "on_message-stopped_field-title": "New Balance:",
    "on_message-stopped_field-title-2": "Amount of Received Commends:",

    "on_message-disconnect-title": "Commending Stopped",
    "on_message-disconnect-description": "Commending Stopped",
    "on_message-disconnect_field-title": "New Balance:",
    "on_message-disconnect_field-title-2": "Amount of Received Commends:",

    "on_message-error-title": "Commending Stopped",
    "on_message-error-description": "Problem with commending, try again",
    "on_message-error_field-title": "New Balance:",
    "on_message-error_field-title-2": "Amount of Received Commends:",

    "menu-title": "Select Your Language: ",
    "menu-english": "English",
    "menu-german": "German",
    "menu-sk/cz": "Slovak/Czech",
    "menu-pt": "Portuguese",
    "menu-pl": "Polish",
    "menu-hu": "Hungarian",

    "pending-reqest-example-a": "Chunk #1 completed with 6/10 commends.",
    "pending-title": "Pending Commends",

    "menu-setup-title": "Setup Private Channels",
    "menu-setup-title-stats": "Setup Stats",
    "menu-setup-description": "**Select what you need in the `Selection` down below!**",
    "lang-update": "Your language has been updated",

    "menu-queue-edit-title": "Queue Manager",

    "commend_stats-title": "Commend Stats",
    "commend_stats-1-name": "Received",
    "commend_stats-2-name": "Pending",
    "commend_stats-3-name": "Total",
    "commend_stats-5-name": "Last Chunk",
    "commend_stats-4-name": "Chunk Status",
    "commend_stats-6-name": "Steam Link",
    "commend_stats-7-name": "Started",
    "commend_stats-8-name": "Next restart",
    "commend_stats-2b-name": "Commends Left",
    "commend_stats-9":"This embed updates every chunk\nYou ll get 20 commends per chunk, chunk = 5-7min",

    "commend-error-select-title": "Choose Which Balance to Use?",
    "commend-error-select-description": "Choose from which slot you want to use the balance:\n",
    "commend-error-select-description-d": "Slot is disabled"
}

    
ger = {
    "lang": "Germany",
    "greets": [
            "Hallo, {username}!",
            "Guten Tag, {username}!",
            "Willkommen zurück, {username}!",
            "Schön, dich zu sehen, {username}!",
            "Wie geht's, {username}?",
            "Hey, {username}!",
            "Hallo wieder, {username}!",
            "Hi, {username}! Du bist zurück!",
            "Willkommen, {username}!",
            "Wir haben dich vermisst, {username}!",
            "Wie können wir helfen, {username}?",
            "Hier, um zu helfen, {username}!",
            "Bereit zu starten, {username}!",
            "Hellt unseren Tag auf, {username}!",
            "Wie können wir assistieren, {username}?",
            "Hoffe, es geht dir gut, {username}!",
            "Machen deinen Tag groß, {username}!",
            "Schön, dich zu haben, {username}!",
            "Lange nicht gesehen, {username}!",
            "Toll, dich zu sehen, {username}!",
            "Grüße, {username}!",
            "Wie geht's dir, {username}?",
            "Wie läuft's, {username}?",
            "Was gibt's Neues, {username}?",
            "Wie war dein Tag, {username}?",
        ],
    "helpmenu-title": "Commend Bot Hilfe Menü",
    "helpmenu-title2": "Dies sind die verfügbaren Befehle für Sie.",
    "helpmenu-description": f"** Commands: ** \n** /redeem <key> ** \n** /balance** \n/recovery - recovery your account via mail \n/verify_now - Add mail in to your account\n\nNutze deine Commends rechtzeitig! Am 30.{timestamp.month}.{timestamp.year} 0:00 CET verfallen sie, wenn du sie noch nicht gesendet hast.",
    "helpmenu-author": "Commend Bot Hilfe Menü",

    "on_error": "<:no:904125314983145572> Failure <:no:904125314983145572>",
    "error1": "Dein Steam Profil Link ist falsch oder funktioniert nicht! Bitte kopiere ihn erneut oder warte auf Support.",
    "error2": "Sorry, dieser Command ist bereits in Benutzung.",
    "error3": "Dieser Nutzer bekommt gerade Commends!",
    "error4": "Sorry, wir haben keinen Platz mehr. Warte 5 Minuten und versuche es erneut!",
    "error5": "Du kannst nicht mehr als 0x Commends senden!",
    "error6": "Du hast keine Commends! (Du hast 0 Commends)",
    "error7": "Du kannst diesen Befehl nur in deinem Privaten Commend Channel nutzen. (Erstelle ihn hier)",
    "error8-title": "Du kriegst bereits Commends",
    "error8-description": "Bitte warte, bis deine bisherige Commend Lieferung fertig ist. Tipp: Es kann bis zu 20 Minuten dauern, du musst nichts weiter machen.",
    "error9": "Du hast keine Commends!",
    "error10": "Sorry, currently we don't have commends for commending",
    "error11": "Sorry, the bot is overused, and we don't have any free slots for commending.",
    "error12": "Dieser Server hat keine aktiven Resell Subs!",
    "error13": "Today you can't use 0c commends, you can only use 0s commends or try after 00:00 UTC!",
    "error14": "For today u can't use 0c commends, you can only use 0u commends because the daily limit of commends is 0s per/user.",
    "error15": "Amount of commends is not numeric",

    "howitworkis-field1-title": "Wie funktioniert es?",
    "howitworkis-field1-description": "Füge dies in die Konsole ein **\"`connect cs2.sinlyxe.cc:27015`\"**\n- Nachdem du dich verbunden hast, wirst du **feststecken**\n- Wenn du auf dem Ladebildschirm feststeckst, klicke auf den grünen Knopf\n- In ein paar Minuten wirst du die ersten Rewards sehen (in der Konsole). \n\nWenn du dich nicht verbindest, wird der Bot **abgeschaltet** und die ungenutzten Belohnungen innerhalb von 5 Minuten an `/balance` zurückgeben.\n\n**Stellt sicher, dass ihr alles gelesen habt!",

    "howitworkis-field2-title": "Lese alles gründlich durch!",
    "howitworkis-field2-description": "Verbinde zu:",
    "howitworkis-field5-title": "Funktioniert der erste Server nicht, verbinde zum 2ten!",
    "howitworkis-field5-description": "✅⬇ ⬇ ⬇ ⬇ ⬇✅",
    "howitworkis-button": "Confirm if you are connected to the server!",

    "commendbotbutton-labe": "Erstelle privaten Channel",
    "commendbotbutton-msg": "<a:wait:930490650401603645> Einen Moment, erstelle deinen privaten Channel <a:wait:930490650401603645>",
    "commendbotbutton-msg-edit": "Dein privater Channel ist hier:",
    "commendbotbutton-ping": ", Das ist dein privater Channel!",

    "Confirm-Confirm": "Bestätige",
    "on_commends_started": "Der Bot hat deinen Account in die Warteschlange hinzugefügt. Du bekommst in 5 Minuten Commends!",
    "restartalert-title": "CSGO Server Neustart Warnung!",
    "restartalert-description": "Der Commend Bot Server wird in 1-2 Minuten neu starten! Bitte rejoin, um weitere Commends zu erhalten. Zum rejoinen, schreibe retry in die CS:GO Konsole.",

    "create-title": "Commend Botting",
    "create-description": "Drücke den Button, um deinen eigenen Commend Bot Channel zu erstellen.",
    "create-button1": "Start Commending",
    "on_message_finished-title": "Commending fertig",
    "on_message_finished-description": "Commending ist fertig.",
    "on_message_finished_field-title": "Aktuelle Balance:",

    "on_message_done-msg1": "Du hast alle Commends erhalten!",
    "on_message_done-msg2": "Commending erfolgreich gestoppt!",
    "on_message_done-msg3": "Commending wurde gestoppt, da du nicht zum Server verbunden hast.",
    "on_message_done-msg4-a": "Erfolgreich hinzugefügt",
    "on_message_done-msg4-b": "Commends wurden deiner Balance hinzugefügt (New balance",
    "on_message_done-msg4-c": "alte Balance",

    "on_message-stopped-title": "Commending gestoppt",
    "on_message-stopped-description": "Commending gestoppt via Befehl",
    "on_message-stopped_field-title": "New Balance:",
    "on_message-stopped_field-title-2": "Amount of got Commends:",
    

    "on_message-disconnect-title": "Commending gestoppt",
    "on_message-disconnect-description": "Commending gestoppt",
    "on_message-disconnect_field-title": "New Balance:",
    "on_message-disconnect_field-title-2":"Anzahl erhaltenen Commends:",

    "on_message-error-title": "Commending gestoppt",
    "on_message-error-description": "Ein Problem beim Commenden ist aufgetreten. Bitte versuche es erneut.",
    "on_message-error_field-title": "New Balance:",
    "on_message-error_field-title-2": "Amount of got Commends:",

    "menu-title": "Wähle deine Sprache: ",
    "menu-english": "English",
    "menu-german": "German",
    "menu-sk/cz": "Slovak/Czech",
    "menu-pt": "Portuguese",
    "menu-pl": "Polish",
    "menu-hu": "Hungarian",

    "pending-reqest-example-a": "Chunk #1 fertig mit 6/10 Elogios.",
    "pending-title": "Ausstehende Commends",

    "confirm-wait-error": "Bitte warte 2-4 Minuten. Die Server werden gerade neu gestartet!",
    "confirm-find-slot": "Suche den bestmöglichen Slot für die Commends!",
    "menu-setup-title": "Private Channels einrichten",
    "menu-setup-title-stats": "Setup Stats",
    "menu-setup-description": "**Wählen Sie in der `Auswahl` unten aus, was Sie benötigen!**",
    "lang-update": "Ihre Sprache wurde aktualisiert",

    "menu-queue-edit-title": "Queue Manager",

    "commend_stats-title": "Commending Stats",
    "commend_stats-1-name": "Received",
    "commend_stats-2-name": "Pending",
    "commend_stats-3-name": "Total",
    "commend_stats-4-name": "Last Chunk",
    "commend_stats-5-name": "Chunk Status",
    "commend_stats-6-name": "Steam Link",
    "commend_stats-7-name": "Process Started",
    "commend_stats-8-name": "Next restart",
    "commend_stats-2b-name": "Commends Left",
    "commend_stats-9":"This embed updates every chunk\nYou ll get 20 commends per chunk, chunk = 5-7min",

    "commend-error-select-title": "Wähle aus, welches Guthaben du verwenden möchtest?",
    "commend-error-select-description": "Wähle aus, aus welchem Slot du das Guthaben verwenden möchtest:\n",
    "commend-error-select-description-d": "Slot ist deaktiviert"
}


sk = {
    "lang": "Slovak",
    "greets": [
            "Ahoj, {username}!",
            "Dobrý deň, {username}!",
            "Vitaj späť, {username}!",
            "Fajn ťa vidieť, {username}!",
            "Ako sa máš, {username}?",
            "Hej, {username}!",
            "Zdravím, {username}!",
            "Ahoj, {username}! Si naspäť!",
            "Vitaj, {username}!",
            "Postrácali sme ťa, {username}!",
            "Ako môžeme pomôcť, {username}?",
            "Pripravení na štart, {username}!",
            "Rozžiari tvoj deň, {username}!",
            "Ako môžeme asistovať, {username}?",
            "Dúfame, že sa máš dobre, {username}!",
            "Spravíme tvoj deň úžasným, {username}!",
            "Těší nás, že si tu, {username}!",
            "Dlho sme ťa nevideli, {username}!",
            "Je super ťa vidieť, {username}!",
            "Čau, {username}!",
            "Ako sa máš, {username}?",
            "Ako ide, {username}?",
            "Čo nové, {username}?",
            "Ako prebiehal tvoj deň, {username}?",
        ],
    "helpmenu-title": "Nápoveda pre Commend Bota",
    "helpmenu-title2": "Tu sú dostupné príkazy pre vás.",
    "helpmenu-description": "**Príkazy:** \n**/redeem <kľúč>** \n**/balance** \n**/deletechannel**\n/recovery - obnovte váš účet cez e-mail\n/verify_now - Pridajte e-mail k vášmu účtu \n\nNevyužitý zostatok bude vrátený späť na váš účet.\nKomendovanie nie je okamžité, dostanete 0-25 komend každých 5-15 minút.",
    "helpmenu-author": "Nápoveda pre Commend Bota",

    "on_error": "<:no:904125314983145572> Chyba <:no:904125314983145572>",
    "error1": "Váš odkaz na Steam profil je neplatný, uistite sa, že váš odkaz je platný a skúste to znova, alebo kontaktujte podporu!",
    "error2": "Ľutujeme, tento príkaz je momentálne používaný!",
    "error3": "Tento používateľ dostáva komendy!",
    "error4": "Ľutujeme, nemáme žiadne voľné miesto pre komendovanie, počkajte niekoľko minút a skúste to znova.",
    "error5": "Nemôžete použiť viac ako 0x komend!",
    "error6": "Nemáte dostatok komend! (Máte 0 komend)",
    "error7": "Tento príkaz môžete spustiť iba v súkromnom kanáli (Môžete ho vytvoriť tu",
    "error8-title": "Už sa komenduje",
    "error8-description": "Prosím, počkajte, kým sa predchádzajúca objednávka neskončí, než vytvoríte novú. Tip: Môže to trvať až 20 minút, nemusíte nič robiť.",
    "error9": "Nemáte dostatok commends!",
    "error10": "Ľutujeme, momentálne nemáme commends na sklade",
    "error11": "Ľutujeme, všetky miesta na komendovanie sú obsadené",
    "error12": "Tento server nemá aktívne resell službu!",
    "error13": "Dnes nemôžete použiť 0c commends, môžete použiť iba 0s commends, reset bude o 00:00 UTC!",
    "error14": "Dnes nemôžete použiť 0c commends, môžete použiť iba 0u commends, pretože denný limit commends je 0s na/používateľa",
    "error15": "Množstvo komend nie je číselné",

    "howitworkis-field1-title": "Ako to funguje?",
    "howitworkis-field1-description": "Toto vložte do konzoly **`pripojiť cs2.sinlyxe.cc:27015`**\n- Po pripojení sa **zaseknete**\n- Ak sa zaseknete na načítacej obrazovke, kliknite na zelené tlačidlo\n- Za niekoľko minút uvidíte prvé odmeny (v konzole). \n\nAk sa nepripojíte, bot sa **vypne** a do 5 minút vráti nepoužité odmeny do `/balansu`.\n\n**Uistite sa, že ste si všetko prečítali!",

    "howitworkis-field2-title": "Uistite sa, že ste si prečítali všetko!",
    "howitworkis-field2-description": "**Pripojte sa na:**",
    "howitworkis-field5-title": "__keď 1. server nefunguje, pripojte sa na 2. server__",
    "howitworkis-field5-description": "✅⬇ ⬇ ⬇ ⬇ ⬇✅",
    "howitworkis-button": "Potvrdiť, že ste pripojení k serveru!",

    "commendbotbutton-labe": "Vytvoriť súkromný kanál!",
    "commendbotbutton-msg": "<a:wait:930490650401603645>Prosím, počkajte, vytváram váš súkromný kanál<a:wait:930490650401603645>",
    "commendbotbutton-msg-edit": "váš súkromný kanál je tu:",
    "commendbotbutton-ping": ", Toto je váš súkromný kanál!",

    "Confirm-Confirm": "Potvrdiť",
    "on_commends_started": "Bot vás pridal do fronty na komendovanie. Komendy začnete dostávať o pár minút.",
    "restartalert-title": "Upozornenie na reštart CSGO servera!",
    "restartalert-description": "CSGO server Commendbotu sa reštartuje o **1-2 minúty**! Uistite sa, že sa **znovu pripojíte** pre pokračovanie v komendovaní. Na **znovupripojenie** napíšte do konzoly CS:GO príkaz `retry`.",

    "confirm-wait-error": "Počkajte prosím 2-4 minúty, server sa momentálne reštartuje!",
    "confirm-find-slot": "Hľadanie najlepšieho možného miesta pre komendovanie!",

    "create-title": "Komendovanie bota",
    "create-description": "Stlačením tlačidla v tejto správe získate svoj vlastný kanál pre Commend Bota.",
    "create-button1": "Začať komendovanie",

    "on_message_finished-title": "Komendovanie dokončené",
    "on_message_finished-description": "Komendovanie bolo dokončené.",
    "on_message_finished_field-title": "Aktuálny zostatok",

    "on_message_done-msg1": "Dostali ste všetky komendy!",
    "on_message_done-msg2": "Komendovanie úspešne zastavené!",
    "on_message_done-msg3": "Komendovanie zastavené",
    "on_message_done-msg4-a": "Úspešne pridané",
    "on_message_done-msg4-b": "komendy na váš zostatok (Nový zostatok",
    "on_message_done-msg4-c": "starý zostatok",

    "on_message-stopped-title": "Komendovanie zastavené",
    "on_message-stopped-description": "Komendovanie zastavené cez príkaz",
    "on_message-stopped_field-title": "Nový zostatok:",
    "on_message-stopped_field-title-2": "Množstvo dostanutých komend:",

    "on_message-disconnect-title": "Komendovanie zastavené",
    "on_message-disconnect-description": "Komendovanie zastavené",
    "on_message-disconnect_field-title": "Nový zostatok:",
    "on_message-disconnect_field-title-2":"Počet obdržaných pochvál:",

    "on_message-error-title": "Komendovanie zastavené",
    "on_message-error-description": "Bol problém s komendovaním, skúste to znova",
    "on_message-error_field-title": "Nový zostatok:",
    "on_message-error_field-title-2": "Množstvo dostanutých komend:",

    "menu-title": "Vyberte si váš jazyk:",
    "menu-english": "Angličtina",
    "menu-german": "Nemčina",
    "menu-sk/cz": "Slovenčina/Čeština",
    "menu-pt": "Portugalčina/Portugues",
    "menu-pl": "Poľština",
    "menu-hu": "Maďarčina",

    "pending-reqest-example-a": "Časť #1 dokončená s 6/10 komendami.",
    "pending-title": "Čakajúce komendy",

    "menu-setup-title": "Nastaviť súkromné kanály",
    "menu-setup-title-stats": "Nastaviť štatistiky",
    "menu-setup-description": "**Vyberte si, čo potrebujete v `Výbere` nižšie!**",
    "lang-update": "Váš jazyk bol aktualizovaný",

    "menu-queue-edit-title": "Manažér fronty",

    "commend_stats-title": "Štatistiky komendovania",
    "commend_stats-1-name": "Dostanuté komendy",
    "commend_stats-2-name": "Čakajúce komendy",
    "commend_stats-3-name": "Použité komendy",
    "commend_stats-5-name": "Posledná časť",
    "commend_stats-4-name": "Stav ",
    "commend_stats-6-name": "Odkaz na Steam",
    "commend_stats-7-name": "Začiatok procesu",
    "commend_stats-8-name": "Dialší reštart",
    "commend_stats-2b-name": "Zostávajúce komendy",
    "commend_stats-9":"This embed updates every chunk\nYou ll get 20 commends per chunk, chunk = 5-7min",

    "commend-error-select-title": "Vyberte, aký zostatok chcete použiť?",
    "commend-error-select-description": "Vyberte zo zoznamu, z akého slotu chcete použiť zostatok:\n",
    "commend-error-select-description-d": "Slot je zakázaný"
}

pt = {
    "lang": "Português",
    "greets": [
            "Olá, {username}!",
            "Oi, {username}!",
            "Bem-vindo de volta, {username}!",
            "Que bom te ver, {username}!",
            "Como você está, {username}?",
            "E aí, {username}!",
            "Oi, {username}! Bem-vindo de volta!",
            "Saudações, {username}!",
            "É bom tê-lo, {username}!",
            "Já faz um tempo, {username}!",
            "Oi, {username}! Como você está?",
            "É ótimo te ver, {username}!",
            "Ei, {username}! Que bom que você voltou!",
            "Olá novamente, {username}!",
            "Oi, {username}! Você está de volta!",
            "Bem-vindo, {username}!",
            "Sentimos sua falta, {username}!",
            "O que podemos fazer por você hoje, {username}?",
            "Estamos aqui para ajudar, {username}!",
            "Pronto para começar, {username}?",
            "Sua presença alegra o nosso dia, {username}!",
            "Como podemos ajudar hoje, {username}?",
            "Esperamos que esteja bem, {username}!",
            "Estamos aqui para tornar seu dia incrível, {username}!",
        ],
    "helpmenu-title": "Menu de Ajuda do Bot de Elogios",
    "helpmenu-title2": "Abaixo estão os comandos disponíveis para você.",
    "helpmenu-description": "**Comandos:** \n**/redeem <chave>** \n**/balance** \n/recovery - recuperar sua conta via e-mail \n/verify_now - Adicionar e-mail à sua conta \n\nO saldo não utilizado será adicionado de volta em 10 minutos.",
    "helpmenu-author": "Menu de Ajuda do Bot de Elogios",

    "on_error": "<:no:904125314983145572> Falha <:no:904125314983145572>",
    "error1": "Seu link de perfil Steam é inválido, por favor, certifique-se de digitá-lo corretamente ou entre em contato com o suporte!",
    "error2": "Desculpe, esse comando já está sendo usado!",
    "error3": "Esse usuário já está recebendo elogios!",
    "error4": "Desculpe, não temos mais vagas disponíveis para elogios, aguarde alguns minutos e tente novamente.",
    "error5": "Você não pode usar mais de 0x elogios por vez!",
    "error6": "Você não tem elogios suficientes! (Você tem 0 elogios)",
    "error7": "Você só pode executar esse comando em um canal privado (Você pode criar aqui",
    "error8-title": "Já foi elogiado",
    "error8-description": "Por favor, espere até a ordem atual terminar antes de criar uma nova. Dica: Pode levar até 20 minutos, não é necessário fazer nada.",
    "error9": "Você não tem saldo e elogios suficientes!",
    "error10": "Desculpe, atingimos o limite diário de elogios",
    "error11": "Desculpe, todas as vagas de elogios estão preenchidas",
    "error12": "Esse servidor não possui uma inscrição ativa para revenda!",
    "error13": "Hoje você pode usar 0c elogios, você só pode usar 0s elogios ou depois de 00:00 UTC!",
    "error14": "Hoje você não pode usar 0c, só pode usar 0s elogios, pois o limite diário por usuário é 0s",
    "error15": "A quantidade de elogios não é numérica",

    "howitworkis-field1-title": "Como funciona?",
    "howitworkis-field1-description": " Cola isto na consola **\"`connect cs2.sinlyxe.cc:27015`\"**\n- Depois de te ligares, ficarás **preso**\n- Se ficares preso no ecrã de carregamento, clica no botão verde\n- Dentro de alguns minutos verás as primeiras recompensas (na consola). \n\nSe não te ligares, o bot irá **desligar-se** e devolver as recompensas não utilizadas ao `/balanço` dentro de 5 minutos.\n\n**Certifica-te que leste tudo!",

    "howitworkis-field2-title": "Certifique-se de ler tudo com atenção!",
    "howitworkis-field2-description": "**Conecte-se em:**",
    "howitworkis-field5-title": "__Quando o primeiro servidor não estiver disponível, conecte-se ao segundo servidor__",
    "howitworkis-field5-description": "✅⬇ ⬇ ⬇ ⬇ ⬇✅",
    "howitworkis-button": "Clique aqui para confirmar que está conectado ao servidor!",

    "commendbotbutton-labe": "Clique aqui para criar um canal privado!",
    "commendbotbutton-msg": "<a:wait:930490650401603645>Aguarde, estamos criando seu canal privado<a:wait:930490650401603645>",
    "commendbotbutton-msg-edit": "Seu canal privado está aqui:",
    "commendbotbutton-ping": ", Este é o seu canal privado!",

    "Confirm-Confirm": "Confirmar",
    "on_commends_started": "O Bot foi adicionado à fila de elogios. Você começará a receber seus elogios em alguns minutos",
    "restartalert-title": "Alerta de reinício do servidor CSGO!",
    "restartalert-description": "O servidor de elogios será reiniciado em **1-2 minutos**! Certifique-se de **Reconectar** para continuar o processo de elogios. Para **Reconectar**, digite o comando `retry` no __console do CS:GO.__",

    "confirm-wait-error": "Aguarde 2-4 minutos, o servidor está reiniciando!",
    "confirm-find-slot": "Procurando o melhor slot para elogios!",

    "create-title": "Bot de Elogios",
    "create-description": "Clique no botão nesta mensagem para criar seu próprio canal de elogios.",
    "create-button1": "Iniciar Elogios",
    "on_message_finished-title": "Elogios Finalizados",
    "on_message_finished-description": "Os elogios foram concluídos.",
    "on_message_finished_field-title": "Saldo Atual",

    "on_message_done-msg1": "Você recebeu todos os elogios!",
    "on_message_done-msg2": "Elogios interrompidos com sucesso!",
    "on_message_done-msg3": "Elogios interrompidos",
    "on_message_done-msg4-a": "Adicionados com sucesso",
    "on_message_done-msg4-b": "ao saldo de elogios (Novo saldo",
    "on_message_done-msg4-c": "saldo anterior",

    "on_message-stopped-title": "Elogios Interrompidos",
    "on_message-stopped-description": "Elogios interrompidos através de comando",
    "on_message-stopped_field-title": "Novo saldo:",
    "on_message-stopped_field-title-2": "Quantidade de elogios recebidos:",

    "on_message-disconnect-title": "Elogios Interrompidos",
    "on_message-disconnect-description": "Elogios interrompidos",
    "on_message-disconnect_field-title": "Novo saldo:",
    "on_message-disconnect_field-title-2": "Quantidade de elogios recebidos:",

    "on_message-error-title": "Elogios Interrompidos",
    "on_message-error-description": "Houve um problema com os elogios, tente novamente",
    "on_message-error_field-title": "Novo saldo:",
    "on_message-error_field-title-2": "Quantidade de elogios recebidos:",

    "menu-title": "Selecione o seu Idioma: ",
    "menu-english": "Inglês",
    "menu-german": "Alemão",
    "menu-sk/cz": "Eslovaco/Tcheco",
    "menu-pt": "Português/Português",
    "menu-pl": "Polonês",
    "menu-hu": "Húngaro",

    "pending-reqest-example-a": "Chunk #1 finalizado com 6/10 elogios.",
    "pending-title": "Elogios Pendentes",

    "menu-setup-title": "Configurar Canais Privados",
    "menu-setup-title-stats": "Configurar Estatísticas",
    "menu-setup-description": "**Selecione o que você precisa no menu `Selecionar` abaixo!**",
    "lang-update": "Seu idioma foi atualizado",

    "menu-queue-edit-title": "Gerenciador de Filas",

    "commend_stats-title": "Estatísticas de Elogios",
    "commend_stats-1-name": "Elogios Recebidos",
    "commend_stats-2-name": "Elogios Pendentes",
    "commend_stats-3-name": "Elogios Usados",
    "commend_stats-4-name": "Última Parte",
    "commend_stats-5-name": "Status da Parte",
    "commend_stats-6-name": "Link Steam",
    "commend_stats-7-name": "Processo Iniciado",
    "commend_stats-8-name": "Próxima reinicialização",
    "commend_stats-2b-name": "Elogios Restantes",
    "commend_stats-9":"This embed updates every chunk\nYou ll get 20 commends per chunk, chunk = 5-7min",

    "commend-error-select-title": "Selecione qual saldo deseja usar?",
    "commend-error-select-description": "Selecione de qual slot deseja usar o saldo:\n",
    "commend-error-select-description-d": "Slot está desativado"
}

hu = {
    "lang": "Magyar",
    "greets": [
            "Helló, {username}!",
            "Üdv, {username}!",
            "Üdvözöljük újra, {username}!",
            "Öröm látni, {username}!",
            "Hogy vagy, {username}?",
            "Szia, {username}!",
            "Helló, {username}! Üdvözöljük újra!",
            "Üdvözletek, {username}!",
            "Jó, hogy itt vagy, {username}!",
            "Régen nem láttunk, {username}!",
            "Szia, {username}! Hogy vagy?",
            "Nagyszerű téged látni, {username}!",
            "Helló újra, {username}!",
            "Szia, {username}! Visszajöttél!",
            "Üdv, {username}!",
            "Hiányoztál nekünk, {username}!",
            "Miben segíthetünk ma, {username}?",
            "Itt vagyunk, hogy segítsünk, {username}!",
            "Készen állsz a kezdésre, {username}?",
            "Jelenlétetted felvidítja a napunkat, {username}!",
            "Hogyan segíthetünk ma, {username}?",
            "Reméljük, jól vagy, {username}!",
            "Itt vagyunk, hogy lenyűgözővé tegyük a napod, {username}!",
        ],
    "helpmenu-title": "Dicsérő Bot Súgó Menü",
    "helpmenu-title2": "Ezek az Ön számára elérhető parancsok.",
    "helpmenu-description": "**Parancsok:** \n**/redeem <kulcs>** \n**/balance** \n/recovery - fiók visszaállítása e-mailen keresztül \n/verify_now - e-mail hozzáadása a fiókjához\n\n**Győződjön meg róla, hogy egyenlegét minden hónapban visszaállítjuk 2022. június 1-jén 0:00 CET-kor**\nA fel nem használt egyenleg 10 percen belül hozzáadódik.",
    "helpmenu-author": "Dicsérő Bot Súgó Menü",

    "on_error": "<:no:904125314983145572> Hiba <:no:904125314983145572>",
    "error1": "A Steam-profil linkje érvénytelen, kérjük, ellenőrizze, hogy a linkek érvényesek-e, próbálja újra, vagy forduljon az ügyfélszolgálathoz!",
    "error2": "Elnézést, ez a parancs használatban van!",
    "error3": "Ez a felhasználó már dicséri!",
    "error4": "Sajnáljuk, nincs szabad helyünk a dicsérethez, várjon néhány percet, és próbálja újra.",
    "error5": "Nem használhatsz 0x ajánlást!",
    "error6": "Nincs elég dicséreted! (0 dicséreted van)",
    "error7": "Ezt a parancsot csak privát csatornában futtathatja (itt hozhatja létre)",
    "error8-title": "Már dicsérik",
    "error8-description": "Kérjük, várja meg, amíg az előző megrendelés lejár, mielőtt újat hozna létre. Tipp: Akár 20 percig is eltarthat, és semmit sem kell tennie.",
    "error9": "Nincs elég dicséreted!",
    "error10": "Sajnos jelenleg nincs ajánlás raktáron",
    "error11": "Sajnáljuk, de az összes dicsérő hely foglalt",
    "error12": "Ennek a szervernek nincs aktív viszonteladói alja!",
    "error13": "Ma nem használhatod a 0c ajánlásokat, csak a 0s ajánlásokat használhatod, vagy próbálkozz 00:00 UTC után!",
    "error14": "Ma nem használhatod a 0c ajánlásokat, csak a 0u ajánlásokat használhatod, mert az ajánlások napi limitje 0 mp/felhasználó",
    "error15": "Az ajánlások mennyisége nem szám",

    "howitworkis-field1-title": "Hogyan működik?",
    "howitworkis-field1-description": "• Illessze be ezt a konzolba: **\"`connect cs2.sinlyxe.cc:27015`\"**\n• A csatlakozás beillesztése után **elakad** a betöltési képernyőn\n• Ha elakad a betöltési képernyőn, kattintson a zöld gombra \n• Néhány percen belül látni fogja az első ajánlásokat (konzolon)\n\nHa nem csatlakozik, a bot **kikapcsol**, és 5 percen belül visszaküldi a fel nem használt ajánlásokat a `/balance` mappába.\n \n**Győződjön meg róla, hogy mindent elolvasott!**",

    "howitworkis-field2-title": "Mindenképpen olvass el mindent!",
    "howitworkis-field2-description": "**Csatlakozás:**",
    "howitworkis-field5-title": "__Ha az 1. szerver nem működik, csatlakozzon a 2.-hoz__",
    "howitworkis-field5-description": "✅⬇ ⬇ ⬇ ⬇ ⬇✅",
    "howitworkis-button": "Kattintson ide, ha fent van a szerveren, hogy elkezdődjön a dicséret!",

    "commendbotbutton-labe": "Hozzon létre egy privát csatornát!",
    "commendbotbutton-msg": "<a:wait:930490650401603645>Kérjük, várjon, amíg létrehozzuk a privát csatornáját<a:wait:930490650401603645>",
    "commendbotbutton-msg-edit": "A privát csatornája itt található:",
    "commendbotbutton-ping": ", Ez az Ön privát csatornája!",

    "Confirm-Confirm": "Megerősít",
    "on_commends_started": "A Bot hozzáadta Önt az ajánlósorhoz. Néhány percen belül elkezdi fogadni az ajánlásokat",
    "restartalert-title": "CSGO Szerver újraindítási riasztás!",
    "restartalert-description": "A Commendbot CSGO szerver **1-2 percen belül** újraindul! Ügyeljen arra, hogy **újra csatlakozzon**, hogy az ajánlási folyamat folytatódjon. Az **újracsatlakozáshoz** írja be a `retry` parancsot a __CS:GO konzolba.__",

    "confirm-wait-error": "Kérjük, várjon 2-4 percet, a szerver jelenleg újraindul!",
    "confirm-find-slot": "A lehető legjobb hely keresése az ajánláshoz!",

    "create-title": "Dicsérő Bot",
    "create-description": "Nyomja meg az üzenetben található gombot, hogy saját csatornát hozzon létre a Dicsérő Bot számára.",
    "create-button1": "Ajánlás indítása",
    "on_message_finished-title": "A dicséret befejeződött",
    "on_message_finished-description": "A dicséret befejeződött.",
    "on_message_finished_field-title": "Aktuális egyenleg:",

    "on_message_done-msg1": "Minden dicséretet megkapott!",
    "on_message_done-msg2": "Az ajánlás sikeresen leállt!",
    "on_message_done-msg3": "Az ajánlás leállt, mert nem csatlakozott a szerverhez",
    "on_message_done-msg4-a": "Sikeresen hozzáadva",
    "on_message_done-msg4-b": "ajánlást az egyenlegéhez (Új egyenleg",
    "on_message_done-msg4-c": "régi egyenleg",

    "on_message-stopped-title": "Ajánlás Leállt",
    "on_message-stopped-description": "Ajánlás leállítva parancs segítségével",
    "on_message-stopped_field-title": "Új egyenleg:",
    "on_message-stopped_field-title-2": "Megkapott ajánlások száma:",

    "on_message-disconnect-title": "Ajánlás Leállt",
    "on_message-disconnect-description": "Ajánlás leállítva",
    "on_message-disconnect_field-title": "Új egyenleg:",
    "on_message-disconnect_field-title-2":"Megkapott dicséretek száma:",

    "on_message-error-title": "Ajánlás Leállt",
    "on_message-error-description": "Probléma volt az ajánlás közben, próbálja újra",
    "on_message-error_field-title": "Új egyenleg:",
    "on_message-error_field-title-2": "Megkapott ajánlások száma:",

    "menu-title": "Válassza ki a nyelvet: ",
    "menu-english": "Angol",
    "menu-german": "Német",
    "menu-sk/cz": "Szlovák/Cseh",
    "menu-pt": "Portugál",
    "menu-pl": "Lengyel",
    "menu-hu": "Magyar",

    "pending-reqest-example-a": "Az 1. darab 6/10 dicséretet kapott.",
    "pending-title": "Függőben lévő ajánlások",

    "menu-setup-title": "Privát Csatornák Beállítása",
    "menu-setup-title-stats": "Statisztika Beállítása",
    "menu-setup-description": "**Válassza ki, mire van szüksége a `Választás` menüben!**",
    "lang-update": "A nyelve frissítve lett",

    "menu-queue-edit-title": "Sorkezelő",

    "commend_stats-title": "Dicséret Statisztika",
    "commend_stats-1-name": "Fogadott Ajánlások",
    "commend_stats-2-name": "Függőben Lévő Ajánlások",
    "commend_stats-3-name": "Felhasznált Ajánlások",
    "commend_stats-4-name": "Utolsó Darab",
    "commend_stats-5-name": "Részlet Státusz",
    "commend_stats-6-name": "Steam Link",
    "commend_stats-7-name": "Folyamat Elindult",
    "commend_stats-8-name": "Következő újraindítás",
    "commend_stats-2b-name": "Hátralévő Ajánlások",
    "commend_stats-9":"This embed updates every chunk\nYou ll get 20 commends per chunk, chunk = 5-7min",
    "commend-error-select-title": "Válassza ki, milyen egyenleget szeretne használni?",
    "commend-error-select-description": "Válassza ki, melyik slotból szeretné használni az egyenleget:\n",
    "commend-error-select-description-d": "A hely le van tiltva"
}

pl = {
    "lang": "Polish",
    "greets": [
            "Cześć, {username}!",
            "Hej, {username}!",
            "Witaj z powrotem, {username}!",
            "Miło cię widzieć, {username}!",
            "Jak się masz, {username}?",
            "Ej, {username}!",
            "Cześć, {username}! Witamy z powrotem!",
            "Pozdrowienia, {username}!",
            "Miło cię tu widzieć, {username}!",
            "Dawno cię nie widzieliśmy, {username}!",
            "Cześć, {username}! Jak się masz?",
            "Świetnie cię widzieć, {username}!",
            "Hej, {username}! Fajnie, że wróciłeś!",
            "Cześć ponownie, {username}!",
            "Cześć, {username}! Jesteś z powrotem!",
            "Witaj, {username}!",
            "Tęskniliśmy za tobą, {username}!",
            "W czym możemy pomóc dziś, {username}?",
            "Jesteśmy tutaj, aby pomóc, {username}!",
            "Gotowy do rozpoczęcia, {username}?",
            "Twoja obecność rozjaśnia nasz dzień, {username}!",
            "Jak możemy pomóc dzisiaj, {username}?",
            "Mamy nadzieję, że masz się dobrze, {username}!",
            "Jesteśmy tu, aby twój dzień był niesamowity, {username}!",
        ],
    "helpmenu-title": "Dicsérő Bot Pomoc",
    "helpmenu-title2": "Dostępne komendy.",
    "helpmenu-description": "**/redeem <klucz>** • *Dodaj pochwały do salda za pomocą klucza*\n**/balance** • *Sprawdź ile masz pochwał do odebrania*\n**/deletechannel** • *Usuń ten kanał*\n/recovery - odzyskaj konto za pomocą poczty\n/verify_now - Dodaj pocztę do swojego konta\n\nMożesz stać AFK na serwerze.\nNiewykorzystane pochwały zostaną dodane do /balance w ciągu 5 minut.",
    "helpmenu-author": "Dicsérő Bot Pomoc",

    "on_error": "<:no:904125314983145572> Błąd <:no:904125314983145572>",
    "error1": "Twój link do profilu Steam jest nieprawidłowy, upewnij się, że twój link jest prawidłowy, spróbuj ponownie lub skontaktuj się z pomocą techniczną!",
    "error2": "Przepraszam, to polecenie jest aktualnie używane!",
    "error3": "Ten użytkownik już otrzymuje pochwały!",
    "error4": "Przepraszamy, nie mamy żadnych wolnych miejsc, poczekaj kilka minut i spróbuj ponownie.",
    "error5": "Nie możesz użyć więcej niż 0x pochwał!",
    "error6": "Nie masz wystarczającej ilości pochwał! (Masz 0 pochwał)",
    "error7": "Możesz użyć tej komendy tylko na prywatnym kanale (Możesz go utworzyć tutaj)",
    "error8-title": "Pochwały są wysyłane",
    "error8-description": "Proszę poczekać aż poprzednie zamówienie się zakończy przed utworzeniem nowego. Tip: To może potrwać do 20 minut nie musisz nic robić.",
    "error9": "Nie masz wystarczającej ilości pochwał!",
    "error10": "Przepraszamy, ale obecnie nie posiadamy pochwał w magazynie.",
    "error11": "Przepraszam, ale wszystkie miejsca na pochwały zostały wykorzystane.",
    "error12": "Ten serwer nie ma aktywnych uprawnień do odsprzedaży!",
    "error13": "Dzisiaj nie możesz użyć 0c pochwał, możesz użyć tylko 0s pochwał lub spróbować po 00:00 UTC!",
    "error14": "Na dzień dzisiejszy nie możesz wysłać 0c pochwał, możesz używać tylko 0u pochwał, ponieważ dzienny limit pochwał wynosi 0s na użytkownika.",
    "error15": "Ilość pochwał nie jest liczbą",

    "howitworkis-field1-title": "Jak to działa?",
    "howitworkis-field1-description": "• Wklej to w konsoli **\"`connect cs2.sinlyxe.cc:27015`\"**\n• Po wklejeniu połączenia **utkniesz** na ekranie ładowania\n• Jeśli utkniesz na ekranie ładowania, kliknij zielony przycisk\n• Pierwsze Pochwały pojawią się za kilka minut (w konsoli)\n\nJeśli się nie połączysz, bot **wyłączy się** i zwróci niewykorzystane pochwały do `/balance` w ciągu 5 minut.\n\n**Upewnij się, że przeczytałeś wszystko!**",

    "howitworkis-field2-title": "Upewnij się, że przeczytałeś wszystko!",
    "howitworkis-field2-description": "**Połącz się z serwerem:**",
    "howitworkis-field5-title": "__gdy 1 serwer nie działa połącz się z 2__",
    "howitworkis-field5-description": "✅⬇ ⬇ ⬇ ⬇ ⬇✅",
    "howitworkis-button": "Potwierdzam, że jestem na serwerze",

    "commendbotbutton-labe": "Stwórz kanał prywatny!",
    "commendbotbutton-msg": "<a:wait:930490650401603645> Proszę czekać, Trwa tworzenie prywatnego kanału <a:wait:930490650401603645>",
    "commendbotbutton-msg-edit": "Twój prywatny kanał znajduje się tutaj:",
    "commendbotbutton-ping": ", To jest twój prywatny kanał!",

    "Confirm-Confirm": "Potwierdzone",
    "on_commends_started": "Bot dodał Cię do kolejki. Zaczniesz otrzymywać pochwały za kilka minut.",
    "restartalert-title": "Restart Serwera CSGO!",
    "restartalert-description": "Serwer CSGO Commendbot zostanie zrestartowany za **1-2 minuty**! Upewnij się, że **ponownie dołączyłeś**, aby proces commend był kontynuowany. Aby **ponownie dołączyć**, wpisz `retry` w konsoli __CS:GO.__",

    "confirm-wait-error": "Proszę czekać 2-4 minuty, serwer jest w trakcie restartu!",
    "confirm-find-slot": "Szukanie najlepszego slotu do pochwał!",

    "create-title": "Commend Botting",
    "create-description": "Naciśnij przycisk w tej wiadomości, aby uzyskać swój własny kanał do pochwał.",
    "create-button1": "Rozpocznij Pochwalanie",
    "on_message_finished-title": "Zakończono Wysyłanie Pochwał",
    "on_message_finished-description": "Wysyłanie pochwał zostało zakończone.",
    "on_message_finished_field-title": "Aktualne Saldo",

    "on_message_done-msg1": "Otrzymałeś wszystkie pochwały!",
    "on_message_done-msg2": "Wysyłanie pochwał zostało zakończone sukcesem!",
    "on_message_done-msg3": "Wysyłanie pochwał zostało zatrzymane",
    "on_message_done-msg4-a": "Pomyślnie dodano",
    "on_message_done-msg4-b": "pochwał do twojego salda (Nowe saldo",
    "on_message_done-msg4-c": "stare saldo",

    "on_message-stopped-title": "Wysyłanie pochwał zostało zatrzymane",
    "on_message-stopped-description": "Wysyłanie pochwał zostało zatrzymane za pomocą komendy",
    "on_message-stopped_field-title": "Nowe saldo:",
    "on_message-stopped_field-title-2": "Ilość otrzymanych pochwał:",

    "on_message-disconnect-title": "Wysyłanie pochwał zostało zatrzymane",
    "on_message-disconnect-description": "Wysyłanie pochwał zostało zatrzymane",
    "on_message-disconnect_field-title": "Nowe saldo:",
    "on_message-disconnect_field-title-2": "Ilość otrzymanych pochwał:",

    "on_message-error-title": "Wysyłanie pochwał zostało zatrzymane",
    "on_message-error-description": "Problem z wysyłaniem pochwał, spróbuj jeszcze raz",
    "on_message-error_field-title": "Nowe saldo:",
    "on_message-error_field-title-2": "Ilość otrzymanych pochwał:",

    "menu-title": "Wybierz język: ",
    "menu-english": "Angielski",
    "menu-german": "Niemiecki",
    "menu-sk/cz": "Słowacki/Czeski",
    "menu-pt": "Portugalski",
    "menu-pl": "Polski",
    "menu-hu": "Węgierski",

    "pending-reqest-example-a": "Chunk #1 zakończył z 6/10 pochwałami.",
    "pending-title": "Oczekujące pochwały",

    "menu-setup-title": "Ustawienia kanałów prywatnych",
    "menu-setup-title-stats": "Statystyki ustawień",
    "menu-setup-description": "**Wybierz to, czego potrzebujesz w `Wyborze` poniżej!**",
    "lang-update": "Twój język został zaktualizowany",

    "menu-queue-edit-title": "Manager kolejki",

    "commend_stats-title": "Status pochwał",
    "commend_stats-1-name": "Ilość otrzymanych",
    "commend_stats-2-name": "Oczekujące",
    "commend_stats-3-name": "Ilość pochwał",
    "commend_stats-5-name": "Ostatni Chunk",
    "commend_stats-4-name": "Status Chunka",
    "commend_stats-6-name": "Link Steam",
    "commend_stats-7-name": "Rozpoczęto",
    "commend_stats-8-name": "Restart",
    "commend_stats-2b-name": "Pozostałe Pochwały",
    "commend_stats-9":"Ten embed aktualizuje się co chunk\nOtrzymasz do 20 Pochwał na chunk, chunk = 5-7 min.",

    "commend-error-select-title": "Wybierz które saldo chcesz użyć?",
    "commend-error-select-description": "Wybierz z którego slotu chcesz użyć salda:\n",
    "commend-error-select-description-d": "Slot jest wyłączony"
}



LANGUAGES = (eng, ger, sk, pt, hu, pl)


def check_translations(verbose: bool = False) -> list[str]:
    """Report keys present in the English table but missing from a translation.

    The original bot called os._exit(3) here, which killed the process on
    import whenever a translation fell behind. Missing keys are reported
    instead - get_lang() already falls back to English.
    """
    missing = []
    for table in LANGUAGES[1:]:
        gaps = [key for key in eng if key not in table]
        missing.extend(f"{table['lang']}: {key}" for key in gaps)
        if verbose:
            status = f"{len(gaps)} missing" if gaps else "complete"
            print(colored(f"translation check - {table['lang']}: {status}", "yellow" if gaps else "green"))
    return missing


# Rewrite the brand baked into the localised copy (see config.LEGACY_BRANDING).
for _table in LANGUAGES:
    _table.update(config.apply_branding(_table))
del _table
from telethon import TelegramClient, events
from datetime import datetime, timezone
import logging, re

logging.basicConfig(format='[%(levelname) %(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

api_id = 123456789
api_hash = 'secret_hash'

client = TelegramClient('user_session', api_id, api_hash)

destination_channel = "@shahed_alarm"
channels = ["@AndroStav", "@kpszsu", "@war_monitor", "@smolii_ukraine", "@kiev_pravyy_bereg", "@kudy_letyt", 
            "@UaNazhyvo", "@eRadarrua", "@monitoringwarua", "@truvogaradar", "@mon1tor_ua", "@strategicontrol", "@vanek_nikolaev"]

#triggers = ["академ", "святошин", "білич", "белич", "ірпін", "ірпен", "ирпен", "коцюбин", "буч", "лавін", "лавин"]
triggers = ["академ", "святошин", "б[іе]лич", "[іи]рп[іе]н", "коцюбин", "буч", "лав[іи]н"]
black_list = ["дтп", "академ[іи]к", "грн", "\\$", "телефон", "реклам", "новин", "👇"]

async def main():
    await client.start()
    print("Бота запущено")
    
    me = await client.get_me()
    print("-----------------------------------------")
    print(f"ID: {me.id}")
    print(f"Ім'я: {me.first_name}")
    print(f"Номер телефону: {me.phone}")
    print("-----------------------------------------")
    
    last_message = { "time": None, "found_triggers": set(), "number": 0}
    info_message = None
    
    @client.on(events.NewMessage(chats=channels))
    async def forwardmess(event):
        nonlocal last_message, info_message
        
        if event.message.text:
            #triggered_word = next((trigger for trigger in triggers if trigger in event.raw_text.lower()), None)
            found_triggers = {trigger for trigger in triggers if re.search(trigger, event.raw_text, re.IGNORECASE)}
            
            #if any(trigger.lower() in event.raw_text.lower() for trigger in triggers):
            if found_triggers:
                #if not any(black_word in event.raw_text.lower() for black_word in black_list):
                if not any(re.search(black_word, event.raw_text, re.IGNORECASE) for black_word in black_list):
                    if not last_message["time"] or (event.date - last_message["time"]).seconds > 480 \
                        or (not any(re.search(trigger, event.raw_text, re.IGNORECASE) for trigger in last_message["found_triggers"]) and (event.date - last_message["time"]).seconds > 180):
                        
                        last_message["number"] = 1
                        print(f"\n{event.date}")
                        print(f"Пересилаю повідомлення:\n{event.raw_text}")
                        await event.forward_to(destination_channel)
                        
                        last_message["time"] = event.date
                        last_message["found_triggers"] = found_triggers
                        info_message = None
                    else:
                        last_message["number"] += 1
                        last_message["found_triggers"].update(found_triggers)
                        
                        trigger_text = ", ".join(last_message["found_triggers"])
                        
                        if not info_message:
                            info_message = await client.send_message(destination_channel, f"Повідомлень: {last_message['number']}\nТригери:\n{trigger_text}")
                        else:
                            await info_message.edit(f"Повідомлень: {last_message['number']}\nТригери:\n{trigger_text}")
                        print(f"\nПовідомлень: {last_message['number']}\nТригери:\n{trigger_text}")
                        
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())

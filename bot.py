from telethon import TelegramClient, events
from datetime import datetime, timezone
import logging, re, configparser

logging.basicConfig(format='[%(levelname)s %(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

def load_config(filename):
    config = configparser.ConfigParser()
    with open(filename, "r", encoding="utf-8") as f:
        config.read_file(f)
    
    if not config.sections():
        logging.error(f"Не вдалося завантажити конфігурацію з файлу: {filename}")
        return None
    
    logging.info("Конфігурація завантажена")
    return config

config = load_config("config.ini")
if config is None:
    raise Exception("Конфігурація не завантажена")
    
session = config["General"]["session"]
api_id = config["General"]["api_id"]
api_hash = config["General"]["api_hash"]
    
delay_long = int(config["Delays"]["delay_long"])
delay_short = int(config["Delays"]["delay_short"])
    
destination_channel = config["Channels"]["destination_channel"]
channels = config["Channels"]["channels"].split(", ")
    
triggers = config["Triggers"]["triggers"].split(", ")
black_list = config["Triggers"]["black_list"].split(", ")
client = TelegramClient(session, api_id, api_hash)

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
            found_triggers = {trigger for trigger in triggers if re.search(trigger, event.raw_text, re.IGNORECASE)}
            
            if found_triggers:
                if not any(re.search(black_word, event.raw_text, re.IGNORECASE) for black_word in black_list):
                    if not last_message["time"] or (event.date - last_message["time"]).seconds > delay_long \
                        or (not any(re.search(trigger, event.raw_text, re.IGNORECASE) for trigger in last_message["found_triggers"]) and (event.date - last_message["time"]).seconds > delay_short):
                        
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

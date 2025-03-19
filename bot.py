from telethon import TelegramClient, events
from datetime import datetime, timezone
import logging, re, configparser, asyncio

# логування
logging.basicConfig(format='[%(levelname)s %(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO, filename="bot.log")

# завантаження конфігу
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

# запис конфігів в змінні
session = config["General"]["session"]
api_id = config["General"]["api_id"]
api_hash = config["General"]["api_hash"]

delay_long = int(config["Delays"]["delay_long"])
delay_short = int(config["Delays"]["delay_short"])

destination_channel = config["Channels"]["destination_channel"]
channels = config["Channels"]["channels"].split(", ")

# перевірка каналів, id чи ніки
if not destination_channel.startswith('@'): destination_channel = int(destination_channel)
channels = [channel if channel.startswith('@') else int(channel) for channel in channels]

triggers = config["Triggers"]["triggers"].split(", ")
black_list = config["Triggers"]["black_list"].split(", ")
client = TelegramClient(session, api_id, api_hash)

# блокування асинхронних функцій
lock = asyncio.Lock()

async def main():
    await client.start()
    logging.info("Бота запущено")
    print("Бота запущено")
    
    me = await client.get_me()
    print("-----------------------------------------")
    print(f"ID: {me.id}")
    print(f"Ім'я: {me.first_name}")
    print(f"Номер телефону: {me.phone}")
    print("-----------------------------------------")
    
    # інфа про останнє повідомлення
    last_message = { "time": None, "found_triggers": set(), "number": 0}
    info_message = None
    
    @client.on(events.NewMessage(chats=channels))
    async def forwardmess(event):
        nonlocal last_message, info_message
        
        async with lock:
            if event.message.text:
                found_triggers = {trigger for trigger in triggers if re.search(trigger, event.raw_text, re.IGNORECASE)}
                
                if found_triggers:
                    if not any(re.search(black_word, event.raw_text, re.IGNORECASE) for black_word in black_list):
                        time_diff = (event.date - last_message["time"]).seconds if last_message["time"] else 0
                        
                        if not last_message["time"] \
                        or time_diff > delay_long \
                        or (not any(re.search(trigger, event.raw_text, re.IGNORECASE) for trigger in last_message["found_triggers"]) \
                        and time_diff > delay_short):
                            
                            last_message["number"] = 1
                            logging.info(f"Пересилаю повідомлення:\n{event.raw_text}")
                            await event.forward_to(destination_channel)
                            
                            last_message["time"] = event.date
                            last_message["found_triggers"] = found_triggers
                            info_message = None
                        else:
                            last_message["number"] += 1
                            last_message["found_triggers"].update(found_triggers)

                            trigger_text = ", ".join(last_message["found_triggers"])
                            
                            mess = f"Повідомлень: {last_message['number']}\nТригери:\n{trigger_text}"
                            if not info_message:
                                logging.info("Створюю інформаційне повідомлення")
                                info_message = await client.send_message(destination_channel, mess)
                            else:
                                logging.info("Редагую інформаційне повідомлення")
                                await info_message.edit(mess)
                            logging.info(mess)
                        
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())

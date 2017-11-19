import asyncio
from aiotg import Bot, Chat
from domain_info_collector import fetch_domains_info
import db

with open('token.secret', 'r') as f:
    token = f.read()

bot = Bot(token)


@bot.command(r"/check +")
async def check(chat: Chat, match):
    domain_name = chat.message['text'].split("check ")[-1]
    domain = db.get_domain(domain_name)
    if domain:
        return await chat.send_text(f"{domain['domain']} истечёт {domain['expiration_date']}.")
    else:
        return await chat.send_text(f"Домен {domain_name} не найден.")


@bot.command(r"/add_domain +")
async def add_domain(chat: Chat, match):
    domain_name = chat.message['text'].split("add_domain ")[-1]
    if db.get_domain(domain_name):
        return await chat.send_text("Домен уже добавлен.")
    fetched_domains = await fetch_domains_info([domain_name])
    if fetched_domains:
        fetched_domain = fetched_domains[-1]
        db.add_domain(fetched_domain)
        return await chat.send_text(f"Домен {fetched_domain['domain']} успешно добавлен.")
    else:
        return await chat.send_text(f"Не удалось собрать информацию о {domain_name}.")


@bot.command(r"/update_domain +")
async def update_domain(chat: Chat, match):
    domain_name = chat.message['text'].split("update_domain ")[-1]
    if not db.get_domain(domain_name):
        return await chat.send_text("Добавьте домен командой /add_domains.")
    fetched_domains = await fetch_domains_info([domain_name])
    if fetched_domains:
        fetched_domain = fetched_domains[-1]
        db.add_domain(fetched_domain)
        return await chat.send_text(f"Домен {fetched_domain['domain']} успешно обновлён.")
    else:
        return await chat.send_text(f"Не удалось собрать информацию о {domain_name}.")


@bot.command(r"/add_domains +")
async def add_domains(chat: Chat, match):
    domain_names = set(
        chat.message['text'].split("/add_domains ")[-1]
            .strip().replace('\n', '').split(',')
    )
    for domain_name in domain_names.copy():
        if db.get_domain(domain_name):
            await chat.send_text(f"Домен {domain_name} уже добавлен и будет пропущен.")
            domain_names.remove(domain_name)

    fetched_domains = await fetch_domains_info(domain_names)
    if fetched_domains:
        for fetched_domain in fetched_domains:
            db.add_domain(fetched_domain)
            fetched_names = "\n".join((d['domain'] for d in fetched_domains))
        return await chat.send_text(f"Успешно добавлены: \n{fetched_names}")
    else:
        return await chat.send_text(f"Не удалось собрать информацию о доменах.")


@bot.command(r"/delete +")
async def delete_domain(chat: Chat, match):
    domain_name = chat.message['text'].split("delete ")[-1]
    db.delete_by_domain_name(domain_name)
    return await chat.send_text(f"Домен {domain_name} удалён.")


@bot.command(r"/check_domains [0-9]+")
async def check_domains(chat: Chat, match):
    days = int(chat.message['text'].split('check_domains ')[-1])
    domains = db.get_domains_expire_in(days)
    msg = "\n".join([f"{domain['domain']} истекает {domain['expiration_date']}" for domain in domains])
    if not msg:
        msg = "Все домены в порядке."
    return await chat.send_text(msg)


@bot.command(r"/subscribe")
async def subscribe(chat: Chat, match):
    user = {'chat_id': chat.id, 'name': str(chat.sender)}
    db.add_user(user)
    return await chat.send_text("Буду оповещать вас ежемесячно об истекающих доменах.")


@bot.command(r"/unsubscribe")
async def unsubscribe(chat: Chat, match):
    db.unsubscribe_user(chat.id)
    return await chat.send_text("Отписали вас от рассылки.")


@bot.command(r'/ping')
async def pong(chat: Chat, match):
    chat.send_text('Pong 🏓')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.loop())

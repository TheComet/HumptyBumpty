import discord
import json
import asyncio
import traceback
import re
import datetime


settings = json.loads(open('settings.json', 'rb').read().decode('utf-8'))
client = discord.Client()
BUMP_CHANNEL_ID = "663516351544950796"
state = "ready"


async def send_message(msg):
    channel = client.get_channel(BUMP_CHANNEL_ID)
    await client.send_message(channel, msg)


async def login():
    email = settings["login"]["email"]
    password = settings["login"]["password"]
    await client.login(email, password, bot=False)
    await client.connect()


async def logout():
    await client.logout()
    print("Logged out")


def match_time_remaining(msg):
    match = re.match(r".*Please wait another (\d+) (seconds|minutes|hours|days) until the server can be bumped", msg)
    if match is None:
        return None
    
    value, unit = match.groups()
    return datetime.timedelta(**{unit: int(value)})


async def bump_in(time_to_next_bump):
    global state
    print(f"bumping in {time_to_next_bump}")
    await asyncio.sleep(time_to_next_bump.seconds)
    await send_message("!d bump")
    state = "ready"


@client.event
async def on_message(message):
    global state
    if message.author.id != "302050872383242240":
        return ()
    remaining = match_time_remaining(message.embeds[0]["description"])
    if remaining is None and state == "ready":
        state = "check"
        await send_message("!d bump")
    if remaining and state != "waiting":
        state = "waiting"
        asyncio.ensure_future(bump_in(remaining))


@client.event
async def on_ready():
    print(f"Running as {client.user.name}")
    await bump_in(datetime.timedelta())


def run():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(login())
    except KeyboardInterrupt:
        loop.run_until_complete(logout())
    except:
        traceback.print_exc()
        loop.run_until_complete(logout())
    finally:
        loop.close()

run()


import discord
import json
import asyncio
import traceback
import re
import datetime


settings = json.loads(open('settings.json', 'rb').read().decode('utf-8'))
client = discord.Client()


class Server(object):
    STATE_READY = 1
    STATE_CHECK = 2
    STATE_WAITING = 3

    def __init__(self, server_id):
        self.state = self.STATE_READY
        self.server_id = server_id

    async def send_message(self, msg):
        channel = client.get_channel(settings["servers"][self.server_id]["bump_channel_id"])
        await client.send_message(channel, msg)

    async def bump_in(self, time_to_next_bump):
        print(f"{self.server_id}: Bumping in {time_to_next_bump.seconds}")
        await asyncio.sleep(time_to_next_bump.seconds)
        try:
            await self.send_message("!d bump")
        except:
            pass
        print(f"{self.server_id}: Bumped")
        self.state = self.STATE_READY

    async def process_message(self, message):
        bot_specific_func = f"process_message_{settings['servers'][self.server_id]['bump_bot_id']}"
        try:
            await getattr(self, bot_specific_func)(message)
        except:
            pass

    async def process_message_302050872383242240(self, message):
        if message.author.id != settings["servers"][self.server_id]["bump_bot_id"]:
            return ()

        desc = message.embeds[0]["description"]
        match = re.match(r".*Please wait another (\d+) (seconds|minutes|hours|days).*", desc)
        remaining = None
        if match is not None:
            value, unit = match.groups()
            remaining = datetime.timedelta(**{unit: int(value)})

        print(f"{self.server_id}: desc: {desc}")
        print(f"{self.server_id}: remaining: {remaining}")
        print(f"{self.server_id}: state: {self.state}")

        if remaining is None and self.state == self.STATE_READY:
            self.state = self.STATE_CHECK
            return await self.send_message("!d bump")

        if remaining and self.state != self.STATE_WAITING:
            self.state = self.STATE_WAITING
            asyncio.ensure_future(self.bump_in(remaining))
            return ()


servers = dict(((server_id, Server(server_id)) for server_id, server in settings["servers"].items()))


async def login():
    email = settings["login"]["email"]
    password = settings["login"]["password"]
    await client.login(email, password, bot=False)
    await client.connect()


async def logout():
    await client.logout()
    print("Logged out")


@client.event
async def on_message(message):
    try:
        await servers[message.server.id].process_message(message)
    except KeyError:
        pass


@client.event
async def on_ready():
    print(f"Running as {client.user.name}")
    for server_id, server in servers.items():
        await server.bump_in(datetime.timedelta())


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

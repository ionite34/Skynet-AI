import os
from bot import BotClient


def run():
    # Create bot
    skynet_bot = BotClient()
    # Run
    skynet_bot.run(os.environ['DISCORD_TOKEN_SKYNET_BETA'])

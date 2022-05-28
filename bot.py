import re
from warnings import warn

import discord
from datetime import datetime, timedelta
from analyzer import Analyzer
from reporter import Reporter


def is_new_user(member):
    """
    Checks if the member is a new user.
    Defined as joined the server within the last 7 days
    """
    # True if joined the server within the last 7 days
    if member.joined_at > (datetime.now() - timedelta(days=7)):
        return True
    return False


class BotClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.analyze = Analyzer()
        self.reporter = Reporter()

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        # send a request to the model without caring about the response
        # just so that the model wakes up and starts loading
        print(self.analyze('This is a self test.'))

    async def on_message(self, message):
        """
        this function is called whenever the bot sees a message in a channel
        """
        # Ignore own messages
        if message.author.id == self.user.id:
            return

        # Ignore message from other bots
        if message.author.bot:
            return

        # Special case if tagged
        if self.user in message.mentions:
            pass  # WIP

        message.content = re.sub(r"<@(.*?)>", '', message.content)
        message.content = message.content.lstrip(' ')
        if not message.content:
            return

        # Query
        detects, detect_dict = self.analyze(message.content)

        # Report cases
        for case in detects:
            # Special case for SPAM, apply only to new users
            if case == 'SPAM' and not is_new_user(message.author):
                continue
            # Otherwise, get the report channel and string
            rep_ch, full_str = self.reporter.report(message.guild, message.channel, message.id,
                                                    message.author.id, case, detect_dict)
            # Send the message to the rep_ch channel
            channel = self.get_channel(rep_ch)
            await channel.send(full_str)

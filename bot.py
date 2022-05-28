import re
from warnings import warn

import discord

# from replace import Replacer
from analyzer import Analyzer
from reporter import Reporter

# Role tag (AI)
ROLE_AI_TAG = "<@&906973835138564116>"

class BotClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.analyze = Analyzer()
        self.emoji_map = {
            'TOXICITY': '😠',
            'SEVERE_TOXICITY': '🤬',
            'IDENTITY_ATTACK': '👿',
            'SPAM': '🚫',
            'THREAT': '🔪',
            'INFLAMMATORY': '💣',
            'SEXUALLY_EXPLICIT': '🍆',
            'FLIRTATION': '💖',
            'INSULT': '💢',
        }

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

        # query
        detects, map = self.analyze(message.content)

        # Reacts
        for detect in detects:
            emoji = self.emoji_map.get(detect)
            if emoji:
                await message.add_reaction(emoji)
            else:
                warn(f'No emoji found for {detect}')

        # Special cases
        special_cases = {
            'SPAM': 'Spam',
            'SEVERE_TOXICITY': 'Severely Toxic',
            'INFLAMMATORY': 'Inflammatory',
            'THREAT': 'Threatening',
        }
        for case in special_cases:
            if case in detects:
                prob = map[case]
                prob = round(prob * 100, 1)
                c_text = special_cases[case]
                await message.reply(f'⚠️ Warning: Your Message was detected ' 
                                    f'as {c_text} with {prob}% Confidence.')
                return
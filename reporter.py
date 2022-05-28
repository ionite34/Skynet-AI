# Reporting
import json
from warnings import warn
from datetime import datetime, timedelta
import requests
from replit import db
from requests import JSONDecodeError


class Reporter:
    def __init__(self):
        # Bot to report to
        self.report_bot_id = '821973078112206891'  # Sentry Bot ID
        # Time limit for repeat reports
        self.time_limit = timedelta(minutes=10)
        # Whether time limit is per category
        self.time_limit_per_category = True
        # Cached report channel
        self.report_channel = {}  # Server ID -> (Time Updated, Channel ID)

    @staticmethod
    def _record_report(guild_id, user_id, msg_id, reason, details):
        """
        Records a report to database

        :param user_id: Discord User ID
        :param msg_id: Full Message ID
        :param reason: Reason
        """
        # Check if server is in database
        if not db[guild_id]:
            db[guild_id] = {}  # Create server entry

        # Check if user is in database
        if not db[guild_id][user_id]:
            db[guild_id][user_id] = {}  # Create user entry

        # Get the current time
        current_time = datetime.now()

        # Add report to user
        db[guild_id][user_id][msg_id] = (current_time, reason, details)

    def _check_reported(self, guild_id, user_id, reason):
        """
        Checks if user has already been recently reported

        :param guild_id: Discord Guild ID
        :param user_id: Discord User ID
        :return: True if report already made on user for the same category
        """
        # Check if server is in database
        if not db[guild_id]:
            return False

        # Check if user is in database
        if not db[guild_id][user_id]:
            return False

        # Get the current time
        current_time = datetime.now()

        # Read all reports for user
        for msg_id, report in db[guild_id][user_id].items():
            # Check any report within the time limit
            if self.time_limit_per_category and report[1] != reason:
                continue
            # If report is within time limit, return True (Exists)
            if current_time - report[0] < self.time_limit:
                return True

    def _get_report_channel(self, guild_id):
        # Check if current report channel in cache
        if guild_id in self.report_channel:
            # If valid report within 15 minutes
            if datetime.now() - self.report_channel[guild_id][0] < timedelta(minutes=15):
                return self.report_channel[guild_id][1]

        # Otherwise, fetch new from API
        res = requests.get(f'https://sentrybot.gg/api/guilds/{guild_id}/integration_channel')
        if not res or res.status_code == 404:
            warn(f'Report Channel request returned 404 for guild [{guild_id}]')
            return None

        try:
            parsed = res.json()  # Parse response to JSON
            state = parsed['success']  # Get success state
        except JSONDecodeError:
            warn(f'Report Channel request returned invalid JSON for guild [{guild_id}]')
            return None

        if not state:
            return None  # If no channel, return None

        channel_id = parsed['data']['channel_id']  # Get channel ID
        return channel_id

    def report(self, guild_id, channel_id, msg_id, user_id, reason, reason_dict):
        # Check if already reported within time limit
        if self._check_reported(guild_id, user_id, reason):
            return

        # Get report channel
        report_channel_id = self._get_report_channel(guild_id)
        if not report_channel_id:
            return  # Skip report if no valid channel

        # Record report
        self._record_report(guild_id, user_id, msg_id, reason, reason_dict)

        # Construct the report json
        mention = f'<@{self.report_bot_id}>'
        perc_reason = round(reason_dict[reason] * 100, 1)
        report_msg = f"{reason} was detected with {perc_reason}% certainty.\n\n"
        for attribute, prob in reason_dict.items():
            if prob < 0.3:
                continue  # Skip low probability attributes
            perc = round(prob * 100, 2)
            report_msg += f'{attribute}: {perc}% Confidence\n'
        report = {
            "jsonrpc": "2.0",
            "id": f"{msg_id}",
            "method": "report",
            "params": {
                "channel_id": f"{channel_id}",
                "message_id": f"{msg_id}",
                "user_id": f"{user_id}",
                "reason": report_msg,
            }
        }
        json_str = json.dumps(report)  # Convert to JSON string
        full_str = f'{mention} {json_str}'

        # Tuple of (report_channel, full_str)
        return report_channel_id, full_str

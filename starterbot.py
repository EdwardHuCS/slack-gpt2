import os

import regex as re
import slack

from gpt2.src import generate_unconditional_samples

slack_token = os.environ["SLACK_API_TOKEN"]
rtmclient = slack.RTMClient(token=slack_token)
client = slack.WebClient(slack_token, timeout=30)

BOT_ID = client.api_call("auth.test")['user_id']
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


def parse_bot_commands(event):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    user_id, message = parse_direct_mention(event["text"])
    if user_id == BOT_ID:
        return message
    return None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (
        None, None)


@slack.RTMClient.run_on(event='message')
def handle(**payload):
    data = payload['data']
    if data.get('message'):
        command = parse_bot_commands(data['message'])
        if command is not None:
            response = generate_unconditional_samples.sample_model(
                nsamples=1,
                length=min(3 * len(command), 300),
                top_k=40,
                command=command)
            webclient = payload['web_client']
            webclient.chat_postMessage(
                channel=data['channel'],
                text=f"{response[0]}",
            )



if __name__ == "__main__":
    rtmclient.start()

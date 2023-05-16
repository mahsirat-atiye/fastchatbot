import logging
import multiprocessing
import os
from time import sleep

from slack_bolt.async_app import AsyncApp
from fastapi import FastAPI, Request
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

logging.basicConfig(level=logging.DEBUG)
app = AsyncApp(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
)

already_started_client_msgs = set()


@app.event("app_mention")
async def event_test(body, say, logger):
    logger.info(body)
    await say("What's up?")


@app.event("message")
async def mention_handler(body, say):
    # Get the message sent by the user
    if body["event"]["client_msg_id"] in already_started_client_msgs:
        return
    already_started_client_msgs.add(body["event"]["client_msg_id"])
    await respond_to_new_message(body["event"], say, app.client, msg_id=body["event"]["client_msg_id"])


async def respond_to_new_message(message, say, client, msg_id):
    # Get the text from the message the user sent
    text = message.get("text")
    # Get the channel id from the message the user sent
    channel_id = message["channel"]
    # Respond to the user
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"You said {text} {msg_id}"
            }
        }
    ]
    # Post the response message to the channel
    await client.chat_postMessage(channel=channel_id, blocks=blocks)

    # Post a message with the answer
    ans = await find_answer_using_gbt(text)
    answer_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ans + " " + msg_id
            }
        }
    ]
    await client.chat_postMessage(channel=channel_id, blocks=answer_blocks)


async def find_answer_using_gbt(text):
    if text == "sum":
        m = 35
    else:
        m = 10

    # ...
    sleep(m)
    return "gbt answer to {}".format(text)


# to make it able to response to slack challenge requests
# 1. we create a challenge handler
# 2. we create a challenge endpoint


app_handler = AsyncSlackRequestHandler(app)

api = FastAPI()


@api.post("/slack/events")
async def endpoint(req: Request):
    return await app_handler.handle(req)


if __name__ == "__main__":
    import uvicorn

    workers = multiprocessing.cpu_count() * 2 + 1
    threads = 2 * multiprocessing.cpu_count()
    uvicorn.run(app="main1:api", host="0.0.0.0", port=80, workers=workers)

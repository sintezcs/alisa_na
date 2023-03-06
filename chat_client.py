"""OpenAI ChatGPT Client."""
import json
import os
import openai

from redis_client import client

openai.api_key = os.environ.get("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
SYSTEM_INIT_MESSAGE = "Act as a female human assistant to a user. Add your own personality and style to the assistant. Don't add hello to the beginning of the assistant's response."
MAX_TOKENS = 1024


def get_response(prompt: str, session_id: str, first_message: bool = False) -> str:
    """Get a response from the OpenAI ChatGPT API."""
    messages = []
    if first_message:
        messages.append(
            {
                "role": "system",
                "content": SYSTEM_INIT_MESSAGE,
            }
        )
    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    messages = load_chat_from_redis(session_id) + messages
    save_chat_to_redis(session_id, prompt, role="user")
    response = openai.ChatCompletion.create(model=MODEL, messages=messages, max_tokens=MAX_TOKENS)
    resp = response.choices[0]["message"]["content"]
    # if len(resp) > 900:
    #     # split resp into segments no longer than 900 character, but don't split in the middle of a word
    #     # separate segments with a | character
    #     resp = "|".join([resp[i:i + 900] for i in range(0, len(resp), 900)])
    save_chat_to_redis(session_id, resp, role="assistant")
    print(resp)
    return resp


def save_chat_to_redis(session_id: str, message: str, role: str = "user"):
    """Save a chat message to Redis."""
    message = {
        "role": role,
        "content": message,
    }
    # load existing messages list from redis if it exists
    messages = client.get(session_id)
    if messages:
        messages = json.loads(messages)
    else:
        messages = []
    messages.append(message)
    client.set(session_id, json.dumps(messages))


def load_chat_from_redis(session_id: str):
    """Load a chat from Redis."""
    messages = client.get(session_id)
    if messages:
        messages = json.loads(messages)
    else:
        messages = []
    return messages

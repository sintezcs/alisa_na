import copy

from fastapi import FastAPI
from rq import Queue

import chat_client
from redis_client import client

q = Queue(connection=client)
app = FastAPI()

MAX_RESP_LENGTH = 900

class State:
    NEW = "new"
    QUESTION_ASKED = "question_asked"
    IS_QUESTION_READY = "is_question_ready"
    RESPONSE = "response"
    QUESTION_ANSWERED = "question_answered"
    QUESTION_ANSWERED_MORE = "question_answered_more"
    BYE = "bye"

class Intents:
    NEW_DIALOG = "NEW_DIALOG"


welcome_resp = {
  "response": {
    "text": "Привет! Задай свой вопрос.",
  },
  "session_state": {
    "state_name": State.NEW,
  },
  "version": "1.0"
}

answered_resp = {
  "response": {
    "text": "",
  },
  "session_state": {
    #"session": {
        "state_name": State.QUESTION_ANSWERED,
     #}
  },
  "version": "1.0"
}

answered_more_resp = {
  "response": {
    "text": "",
  },
  "session_state": {
    #"session": {
        "state_name": State.QUESTION_ANSWERED_MORE,
     #}
  },
  "version": "1.0"
}


question_asked_resp = {
  "response": {
    "text": "Дайте-ка подумать... Готово! Чтобы продолжить, скажите «Дальше».",
  },
  "session_state": {
    #"session": {
        "state_name": State.QUESTION_ASKED,
     #}
  },
  "version": "1.0"
}

waiting_for_answer_resp = {
  "response": {
    "text": "Пока ещё думаю... Чтобы продолжить, скажите «Дальше».",
  },
  "session_state": {
    #"session": {
        "state_name": State.QUESTION_ASKED,
     #}
  },
  "version": "1.0"
}

WHY_QUERIES = ["почему", "а почему"]


def make_chatgpt_request(question: str, session_id: str, first_message: bool) -> str:
    answer = chat_client.get_response(question, session_id, first_message)
    return answer


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/alice")
def response_alice(request: dict):
    session_state = request.get("state", {}).get("session", {})
    session = request.get("session", {})
    if session.get("new"):
        return welcome_resp
    state = session_state.get("state_name", State.NEW)
    session_id = session.get("session_id")

    if request["request"].get("nlu", {}).get("intents", {}).get(Intents.NEW_DIALOG):
        resp = copy.deepcopy(welcome_resp)
        resp["end_session"] = True
        return resp

    match state:
        case State.NEW:
            q.enqueue(make_chatgpt_request, request["request"]["original_utterance"], session_id, True, job_id=session_id)
            resp = copy.deepcopy(question_asked_resp)
            return resp
        case State.QUESTION_ANSWERED:
            q.enqueue(make_chatgpt_request, request["request"]["original_utterance"], session_id, False, job_id = session_id)
            resp = copy.deepcopy(question_asked_resp)
            return resp
        case State.QUESTION_ASKED:
            job = q.fetch_job(session_id)
            print(job)
            if job.is_finished:
                answer = job.result
                resp = copy.deepcopy(answered_resp)
                resp["response"]["text"] = answer
                return resp
            else:
                resp = copy.deepcopy(waiting_for_answer_resp)
                return resp
        # case State.QUESTION_ANSWERED:
        #     return welcome_resp

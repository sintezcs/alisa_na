from fastapi import FastAPI

app = FastAPI()


alice_resp = {
  "response": {
    "text": "Настя любит есть воск.",
  },
  "version": "1.0"
}

alice_resp_2 = {
  "response": {
    "text": "Потому что он вкусный!",
    "end_session": True
  },
  "version": "1.0"
}

WHY_QUERIES = ["почему", "а почему"]

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/alice")
async def response_alice(request: dict):
    if request['request']['command'] in WHY_QUERIES:
        return alice_resp_2

    return alice_resp

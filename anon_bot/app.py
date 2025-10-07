from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .schemas import MessageIn, MessageOut
from .guardrails import enforce_guardrails
from .rules import route

app = FastAPI(title='Anonymous Rule-Based Bot', version='1.0')

# No sessions, cookies, or user IDs — truly anonymous and stateless.
# No logging of raw user input here (keeps it anonymous and reduces risk).

@app.post("/message", response_model=MessageOut)
def message(inbound: MessageIn):
    ok, cleaned_or_reason = enforce_guardrails(inbound.message)
    if not ok:
        return JSONResponse(status_code=200,
                            content={'reply': cleaned_or_reason, 'blocked': True})

    # Rule-based reply (deterministic: no persistence)
    reply = route(cleaned_or_reason)
    return {'reply': reply, 'blocked': False}
from fastapi import APIRouter, Request
import openai

router = APIRouter()

@router.post("/bot/message")
def chat_with_bot(request: Request):
    data = await request.json()
    message = data.get("message")
    # TODO: запрос в OpenAI, если встречается слово "оператор" — перевести оператору
    return {"reply": "..."}

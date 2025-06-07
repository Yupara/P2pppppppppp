from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Чтобы разрешить запросы с React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Адрес фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginData(BaseModel):
    email: str
    password: str

@app.post("/auth/login")
async def login(data: LoginData):
    # Пример простой логики
    if data.email == "user@example.com" and data.password == "1234":
        return {"message": "Login successful", "token": "fake-jwt-token"}
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")

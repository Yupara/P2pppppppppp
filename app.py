from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Подключение статики (CSS, картинки и т.д.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключение шаблонов Jinja2
templates = Jinja2Templates(directory="templates")

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("market.html", {"request": request})

# Страница рынка
@app.get("/market", response_class=HTMLResponse)
async def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request})

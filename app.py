from fastapi import FastAPI
app = FastAPI()
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

fake_users = {}
ads = []

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    fake_users[username] = password
    return RedirectResponse("/login", status_code=302)

@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if fake_users.get(username) == password:
        return RedirectResponse("/market", status_code=302)
    return RedirectResponse("/login", status_code=302)

@app.get("/market")
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

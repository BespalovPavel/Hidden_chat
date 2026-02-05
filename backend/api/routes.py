import uuid
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@router.post("/join_chat", response_class=HTMLResponse)
async def join_chat(request: Request, username: str = Form(...), room_id: str = Form(...)):

    user_id = str(uuid.uuid4())
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "room_id": room_id,
        "username": username,
        "user_id": user_id
    })
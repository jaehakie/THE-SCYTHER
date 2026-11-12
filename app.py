"""낫 TODAY 회의용 프로토타입. 실행: python -m uvicorn app:app --reload"""

from pathlib import Path
import secrets

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from services.game import GameError, GameService
from services.character import CharacterDialogue

ROOT = Path(__file__).resolve().parent
# Also support the ordinary `uvicorn app:app` command. Explicit process
# environment wins over local development settings.
load_dotenv(ROOT / ".env", override=False)
app = FastAPI(title="낫 TODAY", version="0.1.0")
game = GameService(dialogue=CharacterDialogue())
COOKIE = "nottoday_session"


class Action(BaseModel):
    action: str = Field(min_length=1, max_length=40)
    value: str = Field(default="", max_length=2000)
    revision: int = Field(ge=0)
    request_id: str | None = Field(default=None, min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")


class Chat(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    revision: int = Field(ge=0)
    request_id: str | None = Field(default=None, min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")


@app.exception_handler(GameError)
async def game_error(request: Request, exc: GameError):
    return JSONResponse({"detail": exc.message}, status_code=exc.status)


def session_id(request: Request) -> str:
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, "진행 기록이 없습니다. 새 임무를 시작해주세요.")
    return token


@app.get("/")
def index():
    return FileResponse(ROOT / "templates" / "start.html")


@app.get("/play")
def play():
    return FileResponse(ROOT / "templates" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "dialogue_mode": game.dialogue.mode if game.dialogue else "scripted_demo"}


@app.post("/api/game")
def start(request: Request, response: Response):
    token = secrets.token_urlsafe(32)
    state = game.create(token, previous=request.cookies.get(COOKIE))
    response.set_cookie(COOKIE, token, httponly=True, samesite="lax",
                        secure=request.url.scheme == "https", max_age=43200)
    response.headers["Cache-Control"] = "no-store"
    return state


@app.get("/api/game")
def current(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return game.read(session_id(request))


@app.post("/api/action")
def action(payload: Action, request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return game.act(session_id(request), payload.action, payload.value, payload.revision, payload.request_id)


@app.post("/api/chat")
def chat(payload: Chat, request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return game.act(session_id(request), "chat", payload.message, payload.revision, payload.request_id)


app.mount("/assets", StaticFiles(directory=ROOT / "public" / "assets"), name="assets")

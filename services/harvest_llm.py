"""services/harvest_llm.py — 수확자 자유 대화 + 선택지 판정 (FastAPI)

app.py 에 추가:
    from services.harvest_llm import router as harvest_router
    app.include_router(harvest_router)            # POST /api/harvest/talk

API 키: 코드에 적지 않는다. 프로젝트 루트의 .env(=.gitignore 대상)에서 읽는다.
    OPENAI_API_KEY=...        (필수)
    GAME_MODEL=gpt-6-luna     (선택)
    HARVEST_ENV_FILE=경로     (선택: .env 가 다른 곳에 있을 때)
※ 모델 호출 형식은 README 의 '모델 연결 가이드'에 맞게 _ask() 한 곳만 확인하세요.
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.harvest_prompts import build_system

log = logging.getLogger("harvest")
ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    """.env 를 읽어 환경 변수에 올린다. 이미 설정된 값은 덮어쓰지 않고, 키 값은 출력하지 않는다."""
    env = Path(os.getenv("HARVEST_ENV_FILE") or ROOT / ".env")
    if not env.is_file():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env)
    except ImportError:  # python-dotenv 가 없으면 직접 읽는다
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.replace("export ", "", 1).strip()
            os.environ.setdefault(k, v.strip().strip('"').strip("'"))


_load_env()

router = APIRouter(prefix="/api/harvest", tags=["harvest"])
MODEL = os.getenv("GAME_MODEL", "gpt-6-luna")
WHO = ("스승", "이윤제")


class Talk(BaseModel):
    who: str = Field(min_length=1, max_length=10)
    scene: Optional[str] = Field(default=None, max_length=40)
    message: str = Field(min_length=1, max_length=300)
    options: Optional[list] = None      # 선택지 판정이 필요한 장면에서 라벨 목록
    state: dict = Field(default_factory=dict)
    history: list = Field(default_factory=list)


def _client():
    from openai import OpenAI  # requirements.txt 에 openai 추가
    return OpenAI()


def _ask(system: str, history: list, user: str) -> str:
    transcript = "\n".join(f"{h['who']}: {h['text']}" for h in history)
    resp = _client().responses.create(
        model=MODEL,
        reasoning={"effort": "none"},   # 기본 none, 필요한 기능만 low 로 비교
        instructions=system,
        input=f"[최근 대화]\n{transcript}\n\n[플레이어]\n{user}",
    )
    return resp.output_text.strip()


def _clean_history(raw: list) -> list:
    out = []
    for h in raw[-8:]:
        if isinstance(h, dict):
            out.append({"who": str(h.get("who", ""))[:10], "text": str(h.get("text", ""))[:300]})
    return out


def _demo(who: str, scene: Optional[str], msg: str, options: Optional[list], reason: str) -> dict:
    """API 키가 없거나 호출이 실패해도 화면이 멈추지 않게 하는 임시 답변."""
    reply = "질문은 분명히 해라. 계율은 바뀌지 않는다." if who == "스승" else "…아이들 이야기는 길게 하고 싶지 않습니다."
    choice = 0
    if options and scene == "ask":
        if re.search(r"미루|설득|그만|하지 ?말|다음에", msg):
            choice = 2
        elif re.search(r"알겠|따르|하겠", msg):
            choice = 3
        elif re.search(r"왜|정말|혹시|통계|가족|아이|딸|의문|질문", msg):
            choice = 1
    return {"choice": choice, "reply": "" if choice else reply, "mode": "demo", "reason": reason}


def talk_core(p: Talk) -> dict:
    if p.who not in WHO:
        raise HTTPException(400, "who 는 '스승' 또는 '이윤제' 여야 합니다.")
    options = [str(o)[:80] for o in (p.options or [])][:8] or None
    if not os.getenv("OPENAI_API_KEY"):
        log.warning("harvest: OPENAI_API_KEY 가 없어 임시 답변을 씁니다 (.env 위치: %s)", ROOT / ".env")
        return _demo(p.who, p.scene, p.message, options, "no_key")
    system = build_system(p.who, p.scene, p.state, options)
    try:
        out = _ask(system, _clean_history(p.history), p.message.strip())
        if options:
            m = re.search(r"\{.*\}", out, re.S)
            j = json.loads(m.group(0)) if m else {}
            return {"choice": int(j.get("choice", 0)), "reply": str(j.get("reply", "")), "mode": "llm"}
        return {"choice": 0, "reply": out, "mode": "llm"}
    except Exception as e:
        # 키가 노출될 수 있는 오류 메시지는 남기지 않고, 종류와 상태 코드만 기록한다
        log.warning("harvest: LLM 호출 실패 (%s, status=%s) — 임시 답변으로 대체",
                    type(e).__name__, getattr(e, "status_code", None))
        return _demo(p.who, p.scene, p.message, options, "error")


@router.post("/talk")
def talk(payload: Talk):
    # def(동기) 라우트: FastAPI 가 스레드풀에서 실행하므로 동기 OpenAI 클라이언트를 써도 서버가 막히지 않는다.
    return talk_core(payload)

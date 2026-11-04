"""준비 단계 연결 확인용 스모크 테스트 — 실제 FastAPI 앱(app.py)을 그대로 불러서 확인합니다.

프로젝트 루트에서, venv 를 켠 상태로:
    python scripts/harvest_smoke.py

httpx 가 없다는 오류가 나면:  pip install httpx
서버를 띄울 필요는 없습니다. 키는 프로젝트 루트의 .env 에서 읽으며, 읽지 못하면 임시 답변(mode=demo)으로 통과하고 WARN 으로 알려 줍니다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402

c = TestClient(app)
ok = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name, extra)
    ok.append(bool(cond))


r = c.get("/harvest")
check("GET /harvest (페이지)", r.status_code == 200 and "harvest.js" in r.text, r.status_code)

for path in [
    "/assets/css/harvest.css",
    "/assets/js/harvest.js",
    "/assets/images/harvest/intro1.jpg",
    "/assets/images/harvest/reaper_m.jpg",
    "/assets/images/harvest/reaper_f.jpg",
    "/assets/images/harvest/profile_master.jpg",
    "/assets/images/harvest/logo.png",
]:
    check(f"GET {path}", c.get(path).status_code == 200)

body = {"who": "스승", "scene": "ask", "message": "왜 하필 이 사람이죠?",
        "options": ["스승에게 의문을 제기한다", "수확을 미루자고 설득한다", "스승의 말을 따른다"],
        "state": {"name": "한서", "gender": "f"}, "history": []}
r = c.post("/api/harvest/talk", json=body)
r1 = r.json() if r.status_code == 200 else {}
check("POST /api/harvest/talk (선택지 판정)", r.status_code == 200 and "choice" in r1 and "reply" in r1, r1)

r = c.post("/api/harvest/talk", json={"who": "이윤제", "scene": "tea", "message": "따님들 이야기를 듣고 싶어요", "state": {}, "history": []})
r2 = r.json() if r.status_code == 200 else {}
check("POST /api/harvest/talk (자유 대화)", r.status_code == 200 and r2.get("reply"), r2)

modes = {x for x in (j.get("mode") for j in (r1, r2)) if x}
if modes == {"llm"}:
    print("INFO  GPT 호출 성공 (mode=llm)")
else:
    reasons = {j.get("reason") for j in (r1, r2)}
    hint = {"no_key": "OPENAI_API_KEY 를 읽지 못했습니다. .env 위치(프로젝트 루트)와 변수 이름을 확인하세요.",
            "error": "키는 읽었지만 호출이 실패했습니다. 서버 로그의 'harvest: LLM 호출 실패' 줄과 _ask() 의 호출 형식·모델 이름을 확인하세요."}
    print("WARN  임시 답변(mode=demo) —", " / ".join(hint.get(x, str(x)) for x in reasons))

check("잘못된 who → 400", c.post("/api/harvest/talk", json={"who": "아무개", "message": "안녕"}).status_code == 400)
check("301자 입력 → 422", c.post("/api/harvest/talk", json={"who": "스승", "message": "가" * 301}).status_code == 422)
check("message 누락 → 422", c.post("/api/harvest/talk", json={"who": "스승"}).status_code == 422)

print("\n결과:", "모두 통과" if all(ok) else f"실패 {ok.count(False)}건 — 위 FAIL 줄을 알려주세요")
sys.exit(0 if all(ok) else 1)

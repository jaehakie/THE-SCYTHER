"""서버가 장면 전환·단서·엔딩을 관리한다. 메모리 저장은 단일 프로세스 시연용."""

from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock
from time import monotonic

from .dialogue import respond

IMAGE = "/assets/images/"
CLUES = {
    "calendar": {"title": "달력", "text": "내일 날짜에 ‘큰딸 생일 ♥’이 적혀 있다. 다른 날짜에도 가족의 일정을 챙기는 메모가 남아 있다.", "image": None, "x": 15, "y": 32},
    "family": {"title": "가족사진", "text": "이윤제와 아내, 두 딸이 환하게 웃고 있다. 기록에 따르면 아내는 2년 전 수확으로 세상을 떠났다.", "image": "notion-7.png", "x": 36, "y": 19},
    "diagnosis": {"title": "서랍 1 · 진단서", "text": "미납 고지서 사이에서 진단서를 발견했다. ‘폐암 말기, 생존율 5%’. 고지서 한 장에는 액수가 가려진 ‘합의금’ 항목도 있다.", "image": "notion-8.png", "x": 33, "y": 44},
    "letter": {"title": "서랍 2 · 편지", "text": "찢어진 편지에 ‘그때 내가 그런 일 저질러서 미안하다…’라는 문장이 남아 있다. 이후 내용은 알아볼 수 없다. 이 문장만으로 사건을 확정할 수 없다.", "image": "notion-5.png", "x": 40, "y": 62},
    "computer": {"title": "컴퓨터", "text": "동료의 이메일 제목은 ‘내일 감찰 온대, 조심…’. 비밀번호가 걸려 있어 본문은 읽을 수 없다.", "image": None, "x": 85, "y": 33},
    "workwear": {"title": "의자 · 작업복", "text": "의자에 걸린 공장 작업복에는 먼지와 얼룩이 짙게 남아 있다.", "image": None, "x": 77, "y": 65},
}
CHOICES = [
    {"id": "warn", "title": "대상에게 몰래 경고한다", "tag": "규칙 위반"},
    {"id": "lie", "title": "수확한 척하고 스승에게 거짓말한다", "tag": "규칙 위반"},
    {"id": "target", "title": "이윤제만 수확한다. 딸들은 살린다", "tag": "선택"},
    {"id": "all", "title": "계율 4조대로 모두 수확한다", "tag": "원칙"},
    {"id": "give_up", "title": "포기한다. 선택하지 못하겠다", "tag": "포기"},
]
RESULTS = {
    "warn": ("풀부스", "FULVUS", "gold", "당신은 경고를 택했습니다.", "규칙 위반의 위험을 감수하고 이 가족에게 기회를 남겼습니다.", 12),
    "lie": ("풀부스", "FULVUS", "gold", "당신은 거짓 보고를 택했습니다.", "명령과 다른 행동을 하고, 그 선택의 책임을 마주하게 됩니다.", 12),
    "target": ("카이룰레우스", "CAERULEUS", "blue", "당신은 이윤제만 수확했습니다.", "대상자에 대한 임무를 수행하면서 딸들의 생명은 남겼습니다.", 13),
    "all": ("루베르", "RUBER", "red", "당신은 계율대로 모두 수확했습니다.", "저항한 가족에게도 규칙을 적용하는 선택을 했습니다.", 14),
    "give_up": ("선택을 포기한 수확자", "AN UNFINISHED CHOICE", "muted", "당신은 수확을 포기했습니다.", "수습 수확자의 자격을 잃습니다. 선택하지 않은 순간도 당신의 기록에 남습니다.", 15),
}


class GameError(Exception):
    def __init__(self, message: str, status: int = 409):
        self.message, self.status = message, status


@dataclass
class Session:
    stage: str = "selection"
    revision: int = 0
    clues: list[str] = field(default_factory=list)
    messages: list[dict] = field(default_factory=list)
    intel: bool = False
    topic: str | None = None
    choice: str | None = None
    turns: int = 0
    touched: float = field(default_factory=monotonic)


class GameService:
    def __init__(self):
        self.sessions: dict[str, Session] = {}
        self.lock = RLock()

    def create(self, token: str, previous: str | None = None) -> dict:
        with self.lock:
            now = monotonic()
            self.sessions = {k: s for k, s in self.sessions.items() if now - s.touched < 43200}
            if previous:
                self.sessions.pop(previous, None)
            if len(self.sessions) >= 500:
                raise GameError("현재 시연 접속자가 많습니다. 잠시 뒤 다시 시도해주세요.", 503)
            self.sessions[token] = Session()
            return self._view(self.sessions[token])

    def _get(self, token: str) -> Session:
        state = self.sessions.get(token)
        if state is None or monotonic() - state.touched >= 43200:
            self.sessions.pop(token, None)
            raise GameError("시연 기록이 만료되었거나 서버가 재시작되었습니다. 새 임무를 시작해주세요.", 401)
        state.touched = monotonic()
        return state

    def read(self, token: str) -> dict:
        with self.lock:
            return self._view(self._get(token))

    def _say(self, state: Session, speaker: str, text: str):
        state.messages.append({"id": len(state.messages) + 1, "speaker": speaker, "text": text})

    def act(self, token: str, action: str, value: str, revision: int) -> dict:
        with self.lock:
            s = self._get(token)
            if revision != s.revision:
                raise GameError("진행 상태가 바뀌었습니다. 최신 화면을 확인한 뒤 다시 시도해주세요.")
            if action == "select" and s.stage == "selection":
                if value != "yoonje":
                    raise GameError("현재는 이윤제의 임무만 열려 있습니다.", 400)
                s.stage = "briefing"
                self._say(s, "mentor", "오늘의 마지막 대상자는 이윤제다. 마흔네 살, 공장 노동자. 기록을 읽고 궁금한 것은 물어보거라.")
            elif action == "enter" and s.stage == "briefing":
                s.stage = "conversation"
                self._say(s, "narrator", "그가 차를 내왔다. 두 딸은 방에서 잠들어 있다. 거실에는 낮은 조명만 켜져 있다.")
                self._say(s, "yoonje", "차가 식기 전에 드세요. 아이들 깨면 안 되니까… 조용히요.")
            elif action == "chat" and s.stage in {"briefing", "conversation"}:
                value = value.strip()
                if not value:
                    raise GameError("메시지를 입력해주세요.", 400)
                if s.turns >= 100:
                    raise GameError("이번 시연의 대화 한도에 도달했습니다. 판단을 내리거나 새 임무를 시작해주세요.", 429)
                self._say(s, "user", value)
                speaker = "mentor" if s.stage == "briefing" else "yoonje"
                # 행동 지문은 탐색으로 연결하되, 단순한 질문이 단서를 발견한 것으로 처리되지 않는다.
                normalized = "".join(value.split())
                clue = None
                if speaker == "yoonje" and any(w in normalized for w in ("살펴", "조사", "열어", "들여다", "유심히", "확인한다", "읽는다")):
                    for words, key in [(("서랍2", "두번째서랍", "편지"), "letter"), (("서랍", "진단서"), "diagnosis"), (("달력",), "calendar"), (("가족사진", "사진"), "family"), (("컴퓨터", "이메일"), "computer"), (("작업복", "의자"), "workwear")]:
                        if any(w in normalized for w in words):
                            clue = key
                            break
                if clue:
                    self._discover(s, clue)
                    s.topic = clue
                else:
                    reply, s.topic = respond(value, speaker, set(s.clues), s.intel, s.topic)
                    self._say(s, speaker, reply)
                s.turns += 1
            elif action == "inspect" and s.stage == "conversation":
                if value not in CLUES:
                    raise GameError("조사할 수 없는 물건입니다.", 400)
                self._discover(s, value)
            elif action == "intel" and s.stage == "conversation":
                if not s.intel:
                    s.intel = True
                    self._say(s, "mentor", "새 기록이 도착했다. 5년 전 직장 내 괴롭힘 의혹은 증거 불충분으로 징계 무효, 2년 전 성희롱 의혹은 합의 종결로 적혀 있다. 모두 확인되지 않은 의혹이다. 기록과 사실을 혼동하지 말거라.")
            elif action == "decide" and s.stage == "conversation":
                if not s.intel:
                    raise GameError("스승에게 도착한 추가 기록을 먼저 확인해주세요.")
                s.stage = "decision"
                self._say(s, "narrator", "딸들이 방에서 나와 아버지 앞을 막아선다. 규율과 이 가족의 삶, 그리고 너 자신의 책임이 한자리에 놓인다.")
            elif action == "back" and s.stage == "decision":
                s.stage = "conversation"
            elif action == "choose" and s.stage == "decision":
                if value not in RESULTS:
                    raise GameError("유효한 선택이 아닙니다.", 400)
                s.choice, s.stage = value, "ending"
            else:
                raise GameError("지금 장면에서는 할 수 없는 행동입니다.")
            s.revision += 1
            return self._view(s)

    def _discover(self, s: Session, key: str):
        if key not in s.clues:
            s.clues.append(key)
            self._say(s, "narrator", CLUES[key]["title"] + " — " + CLUES[key]["text"])

    def _view(self, s: Session) -> dict:
        result = None
        if s.choice:
            name, latin, color, title, body, picture = RESULTS[s.choice]
            names = [CLUES[k]["title"] for k in s.clues]
            evidence = "당신은 " + ", ".join(names) + "을(를) 확인한 뒤 선택했습니다." if names else "당신은 집 안의 단서를 확인하지 않은 채 선택했습니다."
            result = {"name": name, "latin": latin, "color": color, "title": title, "body": body,
                      "evidence": evidence, "image": f"{IMAGE}notion-{picture}.png",
                      "mentor": "네가 무엇을 살폈는지, 무엇을 남겼는지 기억하고 있다. 이제 네 선택의 이유를 스스로에게 물어보거라."}
        return deepcopy({"stage": s.stage, "revision": s.revision, "messages": s.messages,
                         "clues": [{"id": k, **CLUES[k]} for k in s.clues],
                         "objects": [{"id": k, "title": v["title"].replace(" · 진단서", "").replace(" · 편지", ""), "x": v["x"], "y": v["y"]} for k, v in CLUES.items()],
                         "intel": s.intel, "choices": CHOICES if s.stage == "decision" else [],
                         "result": result, "turns": s.turns, "mode": "scripted_demo"})

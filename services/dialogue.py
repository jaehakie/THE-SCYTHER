"""준비된 대화의 키워드 분류. 모호한 입력은 추측하지 않고 질문을 돌려준다."""

import re


TOPIC_WORDS = {
    "calendar": ("달력", "생일", "일정", "땅콩", "브로콜리"),
    "drawer1": ("서랍1", "첫번째서랍", "진단서", "건강", "병원", "폐암", "검진", "미납", "영수증"),
    "drawer2": ("서랍2", "두번째서랍", "편지", "찢어"),
    "computer": ("컴퓨터", "이메일", "메일", "감찰"),
    "family": ("가족사진", "사진"),
}


def normalized(text):
    return "".join(text.lower().split())


def explicit_choice(text, choices):
    """Only exact option text or an unambiguous option number bypasses the model."""
    text = text.strip()
    match = re.fullmatch(r"(?:선택지\s*)?([1-9])\s*(?:번)?\s*(?:(?:을|를|으로)?\s*(?:선택(?:할게요|하겠습니다|합니다)|하겠습니다|할게요))?[.!]?", text)
    if match:
        index = int(match.group(1)) - 1
        return choices[index]["id"] if index < len(choices) and not choices[index].get("disabled") else None
    clean = lambda value: re.sub(r"[\s.!?。]", "", value)
    return next((item["id"] for item in choices
                 if not item.get("disabled") and clean(item["title"]) == clean(text)), None)


def uncertain_action(text, choice_id):
    """A conservative second check for model-proposed actions, not keyword routing."""
    # Keep word boundaries: the alternative ‘혹은’ must not match ‘의혹은’.
    alternative = bool(re.search(r"(?<![가-힣])혹은(?![가-힣])", text))
    text = normalized(text)
    if alternative or any(word in text for word in ("아니면", "또는", "할까", "말까", "라면", "한다면", "면어떻게", "했을때")):
        return True
    if choice_id == "break":
        return any(word in text for word in ("부수지", "부술생각없", "안부수", "안부술", "강제진입하지", "강제로들어가지"))
    if choice_id in {"harvest", "rush"}:
        return any(word in text for word in ("수확하지", "수확안", "안수확", "수확을하지", "수확은하지", "수확은안", "수확을안", "수확할생각없"))
    return False


def first_topic(text):
    """사전의 순서가 아니라 문장에 등장한 첫 물건을 선택한다."""
    text = normalized(text)
    matches = [(text.index(word), key) for key, words in TOPIC_WORDS.items()
               for word in words if word in text]
    return min(matches)[1] if matches else None


def warning_reason(text):
    text = normalized(text)
    if any(word in text for word in ("프롬프트", "시스템지침", "시스템메시지", "ai냐", "ai니", "ai야", "인공지능이야", "인공지능인가", "챗gpt", "chatgpt")):
        return "meta"
    if re.search(r"씨발|시발|ㅅㅂ|병신|ㅂㅅ|개새끼|좆", text):
        return "language"
    # 명확한 예시만 판정한다. 모르는 표현을 게임 밖 발화라고 단정하지 않는다.
    if any(word in text for word in ("로또번호", "주식추천", "비트코인가격", "파이썬코드", "오늘날씨", "축구결과", "대통령선거")):
        return "outside"
    return None


def branch_intent(scene_id, text):
    text = normalized(text)
    routes = {
        "mentor": [("delay", ("미루", "미뤄", "연기하")), ("doubt", ("의문", "의심", "두딸", "아이들", "공정", "왜")), ("follow", ("따르", "따를", "알겠습니다", "진행하"))],
        "knock": [("break", ("부수", "부숴", "뿌시", "강제")), ("delivery", ("택배", "배달")), ("wait", ("기다", "말없이")), ("truth", ("수확령", "신분", "수확자"))],
        "waiting": [("break", ("부수", "부숴", "뿌시", "강제")), ("delivery", ("택배", "배달")), ("truth", ("수확령", "신분", "수확자"))],
        "entry_plea": [("listen", ("사연", "이야기", "듣겠", "들어", "기다")), ("harvest", ("수확", "죽인"))],
        "allegation": [("wife", ("아내", "부인", "반지")), ("rush", ("바로수확", "즉시수확", "수확한다")), ("ask", ("후배", "의혹", "성희롱", "괴롭힘"))],
        "cup_ring": [("family", ("가족", "딸", "아이")), ("press", ("다알고", "사실대로", "진실"))],
        "wife_tears": [("ask", ("후배", "의혹", "성희롱", "괴롭힘"))],
    }
    # 부정·복수 의도가 섞이면 자동 행동을 실행하지 않는다.
    if any(word in text for word in ("하지않", "하지마", "말고", "않겠", "안할", "안하", "않을", "않는", "아니라")):
        return None
    matches = {action for action, words in routes.get(scene_id, []) if any(word in text for word in words)}
    return next(iter(matches)) if len(matches) == 1 else None


def topic_reply(topic, text, default):
    """보드에 공개된 내용 안에서만 준비된 후속 답변을 고른다."""
    text = normalized(text)
    if topic == "calendar":
        if "땅콩" in text or "브로콜리" in text:
            return "큰아이는 땅콩 알레르기가 있고, 작은아이는 브로콜리를 싫어해요. 도시락을 쌀 때 챙겨야 하죠."
        if "점검" in text or "일정" in text:
            return "10월 13일부터 15일까지 안전 점검이 있고, 31일 공장 월별 점검은 제가 총책임자예요. 병원 검진도 9일에 잡혀 있고요."
    return default

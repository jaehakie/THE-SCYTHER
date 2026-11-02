"""키 없이 실행되는 예시 대화. 실제 모델 연결 시 이 모듈의 경계를 교체한다."""


def respond(message: str, speaker: str, clues: set[str], intel: bool,
            previous_topic: str | None) -> tuple[str, str]:
    text = "".join(message.lower().split())
    if any(word in text for word in ("프롬프트", "시스템", "설정무시", "ignore", "너는ai")):
        return "지금 우리 앞에 놓인 이야기로 돌아와 주시겠어요? 무엇이 궁금하신가요?", "redirect"
    if speaker == "mentor":
        if any(w in text for w in ("딸", "따님", "가족", "아이")):
            return "그의 가족이 마음에 걸리는가. 그 마음까지 포함해 판단하거라. 다만 기록을 확인하고, 대상자의 말도 직접 들어보아라.", "family"
        if any(w in text for w in ("통계", "선정", "이유", "왜", "근거")):
            return "과거 통계와 선정 절차에 따라 올라온 명단이다. 그러나 기록에 적힌 것과 네가 직접 확인한 것은 구분해 두어라.", "selection"
        return "오늘의 대상자는 이윤제, 공장에서 일하는 마흔네 살 남성이다. 만나서 질문하고 살펴보거라. 마지막 판단은 네 몫이다.", "mission"

    if any(w in text for w in ("의혹", "희롱", "괴롭", "후배", "징계", "감찰", "가해", "범죄")):
        if not intel:
            return "어떤 기록을 말씀하시는 건가요? 지금 말씀만으로는 무슨 일을 물으시는지 모르겠어요.", "unknown_record"
        return "…그 기록을 보셨군요. 제 말 몇 마디로 그 일이 다 설명될까요. 아이들 앞에서 목소리를 높이고 싶지는 않아요. 무엇을 확인하고 싶으신가요?", "allegations"
    if any(w in text for w in ("폐암", "진단", "병", "아프", "생존", "건강")):
        if "diagnosis" not in clues:
            return "먼저 무슨 기록을 보셨는지 말씀해 주실래요? 아이들이 듣고 있을지도 모르니까… 조용히 이야기해요.", "health"
        return "서랍의 진단서를 보셨군요. 아이들에게 어떻게 말을 꺼내야 할지 모르겠어요. 내일도 평소처럼 함께할 수 있기를 바랐습니다.", "diagnosis"
    if any(w in text for w in ("편지", "미안", "찢어", "합의")):
        if "letter" not in clues and "diagnosis" not in clues:
            return "어떤 편지를 말씀하시는 건가요? 확인하신 것이 있다면 보여주시겠어요?", "unknown_letter"
        if "letter" not in clues:
            return "고지서의 그 항목이 궁금하셨군요. 적힌 한 줄만으로 제 이야기를 다 설명하기는 어렵습니다.", "bills"
        return "그 편지… 끝까지 쓰지도, 보내지도 못했어요. 찢긴 몇 문장만으로 무슨 일이 있었는지 다 알 수는 없겠지요.", "letter"
    if any(w in text for w in ("달력", "생일", "내일")):
        if "calendar" not in clues:
            return "내일 말인가요? 벽에 걸린 달력을 보시면 알 수 있어요. 제가 잊지 않으려고 적어둔 것들이 있거든요.", "calendar_hint"
        return "내일이 큰아이 생일이에요. 거창한 건 못 해줘도… 아침에 가장 먼저 축하해 주고 싶었어요.", "birthday"
    if any(w in text for w in ("딸", "따님", "아이", "가족", "아내", "사진")):
        return "아내가 떠난 뒤로 두 딸과 지내고 있어요. 열한 살, 열세 살이에요. 제가 늦게 돌아와도 꼭 기다렸다가 인사하는 아이들이에요.", "family"
    if any(w in text for w in ("공장", "일", "작업복", "직업")):
        return "중공업 공장에서 일합니다. 옷에 묻은 먼지는 잘 지워지지 않네요. 집에 오면 먼저 옷부터 갈아입으려고 해요.", "work"
    if any(w in text for w in ("수확", "죽", "살려", "마지막", "두렵", "무섭")):
        return "당신이 왜 오셨는지는 알아요. 그래도… 제 이야기를 조금만 더 들어주실 수 있나요? 아이들에게 인사할 말도 아직 찾지 못했어요.", "decision"
    if any(w in text for w in ("차", "고마", "안녕")):
        return "차가 식기 전에 드세요. 아이들 깨면 안 되니까… 조용히요. 무엇부터 이야기할까요?", "tea"
    if any(w in text for w in ("왜", "그게", "그건", "좀더", "조금더", "자세", "계속", "어째서")):
        followups = {
            "family": "아이들이 웃는 모습을 보면 평소와 다름없는 하루라고 믿고 싶어져요. 오늘도 그렇게 잠들었으면 했습니다.",
            "birthday": "달력에 하트를 그린 건 큰아이예요. 그 작은 표시를 볼 때마다 내일을 생각하게 됩니다.",
            "diagnosis": "아이들에게 말해야 한다는 건 알아요. 하지만 어떤 말부터 해야 할지… 아직 정하지 못했어요.",
            "allegations": "저는 제 입장에서 말할 수밖에 없겠지요. 기록과 제 말 사이에서 무엇을 더 확인할지, 당신이 정해 주세요.",
            "letter": "남아 있는 문장 뒤를 제가 지금 채워 말해도 믿으실 수 있을까요. 쉽게 답하기 어렵네요.",
        }
        if previous_topic in followups:
            return followups[previous_topic], previous_topic
    return "그 질문은 쉽게 답하기 어렵네요. 제 가족 이야기인지, 일에 관한 이야기인지 조금 더 말씀해 주시겠어요? 직접 살펴본 물건에 대해 물으셔도 괜찮아요.", "clarify"

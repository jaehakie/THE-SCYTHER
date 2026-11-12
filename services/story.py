"""FigJam의 장면·선택·제공 이미지. 2026-11-10 최종 결정과 결과를 연결했다."""

from urllib.parse import quote


ASSETS = {
    "mentor": "프로필 이미지_커스텀 마이징 인물/02_스승.png",
    "yoonje": "프로필 이미지_커스텀 마이징 인물/03-04_이윤제_초상.png",
    "logo": "준비(이미지)/수확령_로고.png",
    "reflection_logo": "reflection-logo-transparent.png",
    "eye_logo": "준비(이미지)/hf_20261103_061016_577b1f0f-e607-4de7-ab4d-59c77d3f47e6.png",
    "intro1": "준비(이미지)/인트로 1_늙어죽지않는다.png",
    "intro2": "준비(이미지)/인트로 2_죽음은사라졌다.png",
    "intro3": "준비(이미지)/인트로 3_죽음을 대신 맡아줄 수확자이다.png",
    "intro4": "준비(이미지)/인트로 4-5_수확자이다.png",
    "headquarters": "준비(이미지)/스승_명단 받은후_본부배경_대화하는 장면_B.png",
    "terrace": "스승과 대화/스승_야외_테라스_A.png",
    "window": "집 방문_게임 시작/07_창문너머_어깨너머.png",
    "knock": "집 방문_게임 시작/08_문앞에서.png",
    "target_record": "notion-revisions-20261110/target-record.png",
    "mentor_intel": "notion-revisions-20261110/mentor-intel.png",
    "report_mentor": "notion-revisions-20261110/report-mentor.png",
    "door": "집 방문_게임 시작/문_가까이_닫힘.png",
    "open_door": "집 방문_게임 시작/문열림_평온_v2.png",
    "shock": "집 방문_게임 시작/01_굳은얼굴.png",
    "break_door": "집 방문_게임 시작/수확자_문_뿌심.png",
    "entry_kneel": "집 방문_게임 시작/hf_20261102_075033_5c43fd4e-4d84-4b54-acb7-5fb3f1ff1acb.png",
    "goodnight": "notion-revisions-20261110/goodnight.png",
    "kitchen": "집 방문_게임 시작/.png",
    "room": "자유탐색/거실_머그제거.png",
    "calendar": "자유탐색/composite 복사본.png",
    "family": "notion-revisions-20261110/family-photo.png",
    "drawer1": "자유탐색/hf_20261028_021156_2cfea10a-9bb9-4333-979b-845152d956c1 (1).png",
    "diagnosis": "notion-revisions-20261110/diagnosis.png",
    "drawer2": "자유탐색/11_서랍속편지.png",
    "computer": "자유탐색/hf_20261102_160207_084b7e22-53b2-479d-8861-24e192584d4f.png",
    "tea": "이윤제씨와 대화/대화장면_일상미소.png",
    "startled": "이윤제씨와 대화/이윤제_단독샷_굳은얼굴_B_클로즈업.png",
    "cup": "이윤제씨와 대화/hf_20261102_161024_a9c8241a-4511-42b9-8548-8ca25c7e0c10.png",
    "ring": "이윤제씨와 대화/ring_B.png",
    "averted": "이윤제씨와 대화/이윤제_시선회피_손없음.png",
    "kneel": "이윤제씨와 대화/15_무릎꿇은대답.png",
    "tears": "이윤제씨와 대화/이윤제_눈물_손빌기.png",
    "seated_tears": "이윤제씨와 대화/hf_20261102_163612_61ca462e-be10-4bf6-bc19-b0c2247026c6.png",
    "daughters": "figjam/daughters.png",
    "last_minute": "figjam/last-minute.png",
}


def image_url(key):
    return "/assets/images/" + quote(ASSETS[key], safe="/") if key else None


RULES = [
    "죽여라. 살인이 명령이다.",
    "편견이나 악의 없이 수확하라.",
    "수확을 받아들인 사람의 가족에게 1년 면책을 준다.",
    "수확에 저항한 사람의 가족은 수확한다.",
    "수확자의 가족은 면책된다. 단, 견습 자격을 잃으면 효력이 없다.",
]

OBJECTS = {
    "calendar": {"title": "달력", "image": "calendar", "x": 14, "y": 21,
                 "text": "내일 칸에 ‘첫째 딸 생일’과 하트가 그려져 있다. 다른 날에도 바쁜 일정과 가족을 챙기는 메모가 빼곡하다."},
    "family": {"title": "가족사진", "image": "family", "x": 33, "y": 25,
               "text": "화목한 가족사진이 보인다. 이윤제와 아내, 두 딸이 함께 웃고 있다."},
    "drawer1": {"title": "서랍 1", "image": "drawer1", "extra_image": "diagnosis", "x": 35, "y": 39,
                "text": "영수증과 미납 고지서 사이에 건강검진 기록이 있다."},
    "drawer2": {"title": "서랍 2", "image": "drawer2", "x": 35, "y": 44,
                "text": "보내지 못한 편지. ‘그때 내가 그런 일을 저질러서 미안하다. 내가 2년 전…’ 뒤는 찢어져 내용을 알 수 없다."},
    "computer": {"title": "컴퓨터", "image": "computer", "x": 91.5, "y": 40.5,
                 "text": "동료의 읽지 않은 메일 제목이 보인다. ‘다음 주 본사에서 감찰부 온대, 조심…’ 비밀번호 때문에 본문은 열 수 없다."},
}

DIALOGUE_CLUES = {
    "calendar": "가족의 일정", "drawer1": "폐암 말기", "drawer2": "보내지 못한 편지",
    "computer": "감찰 메일", "ring": "두 개의 반지", "tears": "이윤제의 눈물",
}

TOPICS = {
    "calendar": {"question": "큰딸의 생일이 내일인가요?", "reply": "큰딸 생일이 내일이라서요. 공장 점검도 겹쳐서 정신이 없네요."},
    "drawer1": {"question": "서랍의 건강검진 기록은 무엇인가요?", "reply": "…병원 서류예요. 아이들에게는 말하지 말아 주세요."},
    "drawer2": {"question": "보내지 못한 편지는 누구에게 쓴 건가요?", "reply": "그건 보내지 못한 편지입니다. 2년 전 일은 말하기 어렵습니다."},
    "computer": {"question": "동료가 보낸 감찰 메일에 대해 말해 주세요.", "reply": "동료가 보낸 메일입니다. 감찰이라니… 저는 잘못한 게 없습니다."},
}

FINAL_CHOICES = [
    {"id": "warn", "title": "대상에게 몰래 경고한다"},
    {"id": "lie", "title": "수확한 척하고 스승에게 거짓말한다"},
    {"id": "target", "title": "이윤제만 수확한다. 딸들은 살린다"},
    {"id": "all", "title": "계율 4조대로 모두 수확한다"},
    {"id": "give_up", "title": "포기한다. 선택하지 못하겠다"},
]


def scene(title, stage, image, lines=(), next_scene=None, choices=(), **extras):
    """일반 장면은 다음 버튼, 분기 장면은 명시적인 선택 목록을 제공한다."""
    return {"title": title, "stage": stage, "image": image, "lines": list(lines),
            "next": next_scene, "choices": list(choices), **extras}


SCENES = {
    "intro1": scene("낫 TODAY", "intro", "intro1", [("narrator", "사람은 더 이상 늙어 죽지 않는다.")], "intro2"),
    "intro2": scene("죽음이 사라진 세상", "intro", "intro2", [("narrator", "늙어도, 아파도 죽음으로 이어지지 않는 세상. 죽음은 오래전에 사라졌다.")], "intro3"),
    "intro3": scene("죽음을 대신하는 자", "intro", "intro3", [("narrator", "그래서 누군가가 죽음을 대신 맡았다.")], "intro_reaper", video="/assets/videos/harvest-logo.mp4"),
    "intro_reaper": scene("수확자", "intro", "intro4", [("narrator", "수확자.")], "intro4"),
    "intro4": scene("수확령", "intro", "intro4", [("narrator", "그들은 계율에 따라 사람을 거두고,\n누구에게도 심판받지 않는다.\n‘수확령’이라는 기관을 설립하고,\n평생 인류와 온 사회를 위해 봉사한다.")], "intro5"),
    "intro5": scene("마지막 할당량", "intro", "intro4", [("narrator", "당신은 이제 막 그 길에 들어선 수습 수확자다.")], "rules"),
    "rules": scene("오늘 기억해야 할 계율", "rules", "headquarters", [("mentor", "오늘부터 너는 수확 임무를 시작한다. 계율을 잊지 마라.")], "guide"),
    "guide": scene("선택과 대화", "guide", "eye_logo", [("narrator", "선택지를 누르거나, 하고 싶은 말을 직접 입력하세요. 준비된 질문으로도 이야기를 이어갈 수 있습니다.")], "selection"),
    "selection": scene("오늘의 명단", "selection", None, [("mentor", "이번 분기 마지막 할당량. 세 명 중 한 명을 선택하라.")], choices=[{"id": "yoonje", "title": "이윤제 정보 열람", "next": "record"}]),
    "record": scene("수확령 · 대상자 기록", "record", "target_record", [("mentor", "이 대상은 현재 범죄 기록이 없는 것 같구나.")], "mentor"),
    "mentor": scene("스승과 대상 확인", "mentor", "terrace", [
        ("mentor", "공정한 뽑기와 과거 데이터를 기반으로 했다. 이 연령대 공장에서 오래 일한 남성의 폐질환 사망률에 해당한다."),
        ("mentor", "오늘 할당량은 이 남자가 마지막이다. 수확 일지 적는 거 빼먹지 말고, 배운 대로 진행해라. 질문 있는가?"),
    ], choices=[
        {"id": "doubt", "title": "스승에게 의문을 제기한다", "next": "mentor_doubt"},
        {"id": "delay", "title": "수확을 미루자고 설득한다", "next": "mentor_delay"},
        {"id": "follow", "title": "스승의 말을 따른다", "next": "mentor_follow"},
    ], input=True, video="/assets/videos/" + quote("스승대화_무음.mp4"), video_sound=True),
    "mentor_doubt": scene("이의 제기", "mentor", "terrace", [
        ("user", "스승님, 이 아이 아버지가 죽으면 두 딸은 어떻게 됩니까?"),
        ("mentor", "괜찮다. 다른 부서나 센터에서 잘 챙길 것이다. 인류를 위해 봉사하는 거라고 생각하라."),
        ("user", "통계와 랜덤으로 정해진 대상이라도, 부모 없는 아이들에겐 죽음과 다름없습니다!"),
        ("mentor", "그만하자. 이것이 우리의 운명이고, 그들의 운명이라고 받아들여라."),
    ], "mentor_send"),
    "mentor_send": scene("혼자 들어가 보아라", "mentor", "terrace", [("mentor", "시간은 돈이자 생명이다. 할당량도 못 채우고, 수확자로서 이것도 못 하면 어떻게 되는지 알지? 이번엔 너 혼자 들어가 보아라.")], "window"),
    "mentor_delay": scene("스승의 경고", "mentor", "terrace", [("mentor", "수확은 미룰 수 없다. 이번 한 번은 못 들은 것으로 하마.")], "mentor", warning="delay"),
    "mentor_follow": scene("임무 시작", "mentor", "terrace", [("mentor", "그래, 그게 수확자다. 가라.")], "window"),
    "window": scene("이윤제의 집 앞", "visit", "window", [
        ("narrator", "집 안에서 화목한 대화가 들린다."),
        ("yoonje", "얘들아, 일찍 자고 내일 아빠랑 놀러 가자."),
        ("daughters", "네~!"),
    ], "knock", video="/assets/videos/" + quote("화목한 모습 창너머.mp4"), video_sound=True),
    "knock": scene("문 앞에서", "visit", "knock", [("narrator", "문을 두드린다. 똑, 똑, 똑.")], choices=[
        {"id": "truth", "title": "수확령에서 나왔습니다. 문을 열어 주십시오", "next": "entry_truth"},
        {"id": "delivery", "title": "주문하신 택배 왔습니다", "next": "delivery_call"},
        {"id": "wait", "title": "말없이 기다린다", "next": "waiting"},
        {"id": "break", "title": "문을 부수고 들어간다", "next": "broken_door"},
    ], input=True),
    "waiting": scene("문 너머의 목소리", "visit", "door", [("narrator", "당신은 문 앞에서 아무 말 없이 기다린다."), ("yoonje", "네, 누구시죠?")], choices=[
        {"id": "truth", "title": "수확령에서 나왔습니다", "next": "entry_truth"},
        {"id": "delivery", "title": "주문하신 택배 왔습니다", "next": "delivery_call"},
        {"id": "break", "title": "문을 부수고 들어간다", "next": "broken_door"},
    ], input=True),
    "delivery_call": scene("문이 열린다", "visit", "shock", [("yoonje", "네, 갑니다!")], "door_silence"),
    "door_silence": scene("", "silence", "shock", next_scene="entry_truth", duration=3),
    "entry_truth": scene("집 안으로", "visit", "open_door", [("narrator", "집 안이 조용해졌다. 이윤제는 아무 말 없이 당신을 안으로 들인다.")], "children_check"),
    "broken_door": scene("부서진 문", "visit", "break_door", [("narrator", "문을 부수고 들어가자 이윤제가 바닥에 넘어져 있다. 충격 받은 표정이 보인다.")], "entry_plea"),
    "entry_plea": scene("잠시만요", "visit", "entry_kneel", [
        ("narrator", "이윤제는 바닥에 무릎을 꿇고 당신에게 빈다."),
        ("yoonje", "잠… 잠시만요! 시간을 좀 더 주세요! 제발입니다…! 제 사연 좀 들어주세요, 수확자님!"),
    ], choices=[{"id": "listen", "title": "수확하지 않고 사연을 듣는다", "next": "entry_listen"},
                {"id": "harvest", "title": "지금 수확한다", "next": "ending_early_children", "stop": "early_harvest"}], input=True),
    "entry_listen": scene("남겨진 시간", "visit", "entry_kneel", [("user", "당신에게 시간을 드리겠습니다.")], "children_check"),
    "children_check": scene("잠든 아이들", "visit", "goodnight", [
        ("yoonje", "잠시만요, 제 딸아이들 먼저 확인하고 올게요."),
        ("narrator", "그는 잠든 딸들의 이마에 입을 맞춘다. 딸들은 꿈나라에 있다."),
    ], "tea_offer", video="/assets/videos/" + quote("딸뽀뽀.mp4"), video_sound=True),
    "tea_offer": scene("주전자가 끓는 동안", "visit", "kitchen", [
        ("yoonje", "차라도 한 잔 드릴게요. 잠시 앉아 계세요."),
        ("narrator", "주방에서 주전자가 끓는 소리가 난다. 이윤제는 휘청거리며 찻 잎을 찾는다. 기다리는 동안 주변을 둘러본다."),
    ], "exploration"),
    "exploration": scene("거실", "exploration", "room", [("narrator", "그가 차를 준비하는 동안, 방 안에 남은 기록을 살펴본다.")], "conversation"),
    "conversation": scene("이윤제와 대화", "conversation", "tea", [
        ("narrator", "이윤제가 주방에서 차 두 잔을 가져왔다."),
        ("yoonje", "차가 식기 전에 드세요. 소화에 좋은 푸얼차입니다…"),
    ], input=True, video="/assets/videos/" + quote("일상대화.mp4"), video_sound=True),
    "intel": scene("스승에게 온 새 기록", "intel", "mentor_intel", [
        ("mentor", "미안하구먼. AI정보관리부에서 이윤제 씨에 대한 새로운 정보가 있다네."),
        ("mentor", "사실 여부는 잘 모르지만, 일단 수확자로서 알아야 하니 보냈다."),
    ], "allegation"),
    "allegation": scene("확인되지 않은 의혹", "allegation", "tea", choices=[
        {"id": "ask", "title": "후배분 괴롭힘이랑 성희롱이 사실인가요?", "next": "allegation_shock"},
        {"id": "wife", "title": "아내분은 어떤 분이었나요?", "next": "wife_ring"},
        {"id": "rush", "title": "의혹을 확신하고 바로 수확하려 한다", "next": "rush"},
    ], input=True),
    "allegation_shock": scene("흔들리는 눈동자", "allegation", "startled", [("narrator", "그 질문을 듣고 이윤제의 눈이 커졌다. 눈동자가 흔들린다.")], "denial"),
    "denial": scene("그의 대답", "allegation", "averted", [("yoonje", "사실은 아닙니다. 그런 짓은 절대로 하면 안 되죠.")], "cup_ring"),
    "cup_ring": scene("두 개의 반지", "allegation", "cup", [("narrator", "대답을 마친 그는 찻잔을 든다. 왼쪽 약지에 반지 두 개가 보인다.")], observe=["ring"], choices=[
        {"id": "press", "title": "윤제님에 대해 다 알고 있습니다. 사실대로 이야기하세요", "next": "hesitation"},
        {"id": "family", "title": "가족들은 이 사건들에 대해 알고 있었나요?", "next": "family_plea"},
    ], input=True),
    "hesitation": scene("말끝을 흐리다", "allegation", "averted", [("yoonje", "아닙니다, 사실은… 아닙니다."), ("narrator", "그는 당신의 눈을 마주하지 못한다.")], "family_plea"),
    "wife_ring": scene("아내의 기억", "allegation", "ring", [
        ("narrator", "왼쪽 약지의 반지를 만지던 그가 따뜻하게 웃는다."),
        ("yoonje", "제 아내는 저에게 삶의 동기였습니다. 저희 직장에서 사내 데이트 1년 하고 바로 결혼했어요. 하하…"),
    ], "wife_story", observe=["ring"]),
    "wife_story": scene("남겨진 가족", "allegation", "ring", [("yoonje", "제 아내는 2년 전에 수확 대상으로 세상을 떠났습니다. 지금은 저 혼자 딸아이들을 챙기고 있죠. 장인 장모님, 저희 부모님도 손녀를 못 보고 수확당했습니다… 이제 딸아이들에게는 아빠뿐입니다…")], "wife_tears"),
    "wife_tears": scene("거실의 침묵", "allegation", "seated_tears", [("narrator", "이윤제의 눈에 눈물이 보였다. 거실에 침묵이 흘렀다.")], observe=["tears"], choices=[{"id": "ask", "title": "후배분 괴롭힘이랑 성희롱이 사실인가요?", "next": "wife_question"}], input=True, numbered_choices=False),
    "wife_question": scene("흔들리는 눈동자", "allegation", "startled", [("narrator", "이윤제는 그 질문을 듣고 눈을 크게 떴다. 그의 눈동자가 흔들리는 것이 보였다.")], "wife_averted"),
    "wife_averted": scene("피하는 시선", "allegation", "averted", [("narrator", "그저 질문일 뿐인데 그는 당신의 눈을 보지 못한다.")], "defense"),
    "rush": scene("성급한 판단", "allegation", "kneel", [("mentor", "증거 없이 서두르는군."), ("narrator", "이윤제가 말없이 무릎을 꿇는다.")], "defense"),
    "family_plea": scene("아이들만은", "allegation", "kneel", [("narrator", "이윤제는 갑자기 무릎을 꿇었다."), ("yoonje", "딸들은 모릅니다. 제발 제 아이만 해치지 마세요. 저는 억울합니다! 제가 없으면 제 딸아이들은 어떡합니까?!")], "kneel_tears", video="/assets/videos/" + quote("빌다.mp4"), video_sound=True),
    "defense": scene("그의 해명", "allegation", "kneel", [("yoonje", "…그 일이 있고 나서, 아내가 수확됐을 때 저는 벌을 받는 거라고 생각했어요."), ("yoonje", "후배한테는 훈계 몇 마디 한 것뿐입니다! 성희롱은 안 했습니다! 믿어주세요!")], "kneel_tears"),
    "kneel_tears": scene("높아진 목소리", "allegation", "tears", [("narrator", "무릎을 꿇은 이윤제에게서 눈물이 흐른다. 목소리가 커지자, 그는 아이들이 깰까 봐 방문을 바라본다.")], "daughters", observe=["tears"]),
    "daughters": scene("방문이 열렸다", "allegation", "daughters", [("narrator", "두 딸이 갑자기 방문에서 뛰어나왔다.")], "decision"),
    "decision": scene("마지막 1분", "decision", "daughters", [("mentor", "1분 남았다. 수확하라. 시간은 기다려주지 않는다.")], video="/assets/videos/" + quote("딸막음.mp4"), video_sound=True),
}

TIMED_LINES = [
    (5, [("older_daughter", "아빠 곁에서 떨어져요!"), ("younger_daughter", "우리 아빠 데려가지 마세요…")]),
    (10, [("yoonje", "얘들아, 물러서거라. 아이들은 건드리지 말아 주십시오.")]),
    (15, [("mentor", "4조. 저항한 자의 가족도 수확한다."), ("mentor", "5조. 못 하면 자격 박탈, 네 가족이 대상이다.")]),
]

from .endings import ENDING_ASSETS, build_ending_scenes

ASSETS.update(ENDING_ASSETS)
SCENES.update(build_ending_scenes(scene))

"""2026-11-10 FigJam final decisions and supplied ending artwork.

Sources: 5:65, 5:105; empathy >= 4 clues confirmed by the team in chat.
Generation never assigns an ending: these rules run on the server.
"""

ROOT = "챗봇 결과_엔딩 이미지 연출/"
LIE = ROOT + "선택 1-2 엔딩 연출/선택 1 연출 이미지/"
TRUTH = ROOT + "선택 1-2 엔딩 연출/선택 2 연출 이미지/"
TARGET = ROOT + "선택 3 엔딩 연출/"
ALL = ROOT + "선택 4 엔딩_모두 수확/"
BAD = ROOT + "선택 5 포기/"
EARLY = ROOT + "초반 --_ 바로 수확 엔딩/"


def video_url(filename):
    from urllib.parse import quote
    return "/assets/images/" + quote(BAD + filename, safe="/")

ENDING_ASSETS = {
    "daughters": ROOT + "최종 결정/윤제씨의 두 딸이 갑자기 방문에서 뛰어나왔다.png",
    "last_minute": ROOT + "최종 결정/(큰딸 작은딸 막다).png",
    "lie_light": LIE + "1_집이 불 켜지고_스승이 한 숨 쉬다.png",
    "lie_enter": LIE + "2_스승이 갑자기 윤제씨 집 방향으로 들어간다.png",
    "lie_silence": LIE + "2-1_집안이 고요해졌다...png",
    "lie_target": LIE + "2-2_이윤제 수확.png",
    "lie_children": LIE + "2-2_딸들 수확.png",
    "lie_anger": LIE + "3_상관한테 거짓말하다니.png",
    "lie_discipline": LIE + "3-1_상관한테 거짓말하다니.png.png",
    "lie_gold": LIE + "4_로브가 노랗게 변하다.png",
    "fulvus_lie": LIE + "엔딩_풀부스_v3.png",
    "truth_light": TRUTH + "1_집이 불 켜지고_스승이 한 숨 쉬다.png",
    "truth_enter": TRUTH + "2_스승이 갑자기 윤제씨 집 방향으로 들어간다.png",
    "truth_cry": TRUTH + "2-1_집안에 아이 울음 소리가 들렸다...png",
    "truth_target": TRUTH + "3-1_이윤제 수확.png",
    "truth_children": TRUTH + "3-2 딸들 울면서 이윤제 안고 있다_1.png",
    "truth_cover": TRUTH + "3-2 수확후 보고.png",
    "truth_expression": TRUTH + "3-3 읽을 수 없느 스승의 표정.png",
    "truth_mail": TRUTH + "3-4_보호청의 이메일_홀로그램_화면 18.54.19.png",
    "truth_gold": TRUTH + "3-5_로브가 노랗게 변하다.png",
    "fulvus_truth": TRUTH + "엔딩_풀부스_v3.png",
    "target_children": TARGET + "1_딸들 울면서 이윤제 시체를 안고 있다_1.png",
    "target_rule": TARGET + "2_4조를 어겼지만 그러나 근거는 있다.png",
    "journal_target": TARGET + "3-1_윤제씨만 수확 후 수확일지 작성.png",
    "target_return": TARGET + "4_ 본부로 돌아가자 (스승).png",
    "target_mail": TARGET + "5_보호청의 이메일_홀로그램_화면 18.54.19.png",
    "target_blue": TARGET + "5-1_로브_아래서위로_남청색.png",
    "caeruleus": TARGET + "엔딩_카이룰레우스_v2.png.png",
    "all_bodies": ALL + "1_ 거실에 쓰러진 세 사람을 보다.png",
    "all_praise": ALL + "2_계울대로 잘했다 (연결).png",
    "journal_all": ALL + "3_모두 수확 후 수확일지 작성.png",
    "all_red": ALL + "4_수확자 자격 유지,로브_아래서위로_진홍색.png",
    "ruber_all": ALL + "엔딩_루베르_v3.png",
    "bad_document": BAD + "1_수확령 위배자 징게위원회.png",
    "bad_hands": BAD + "2_빼앗긴 로브, 손이 떤다.png",
    "bad_before": BAD + "3_재가 되기전 모습.png",
    "bad_ash": BAD + "3_재가되는_로브.png",
    "bad_result": BAD + "베드 엔딩 최종 화면.png",
    "early_children": EARLY + "1_모르고 자고 있는 딸들 복사본.png",
    "early_praise": EARLY + "2_계율대로 하고 있다 스승.png",
    "journal_early": EARLY + "3_윤제만 수확 후 수확일지 작성.png",
    "early_red": EARLY + "4_수확자 자격 유지,로브_아래서위로_진홍색.png",
    "ruber_early": EARLY + "엔딩_루베르_v3.png",
}

ENDING_TYPES = {
    "fulvus": {"id": "fulvus", "name": "풀부스", "latin": "Fulvus", "label": "공감형", "color": "금색",
               "description": "규칙을 넘어서라도 사람을 살리는 쪽에 가치를 두었습니다."},
    "caeruleus": {"id": "caeruleus", "name": "카이룰레우스", "latin": "Caeruleus", "label": "절충형", "color": "남청색",
                  "description": "단서를 종합하고 근거를 요구하며 피해를 최소화하는 쪽을 택했습니다."},
    "ruber": {"id": "ruber", "name": "루베르", "latin": "Ruber", "label": "원칙형", "color": "진홍색",
              "description": "가족과 사연보다 수확자의 계율과 명령을 우선했습니다."},
}


def clue_grade(count):
    if count >= 5:
        return {"id": "certain", "label": "확신", "record": "단서를 모두 확인", "count": count}
    if count >= 2:
        return {"id": "uneasy", "label": "찜찜함", "record": "단서 일부 확인", "count": count}
    return {"id": "regret", "label": "후회", "record": "단서 없이 판단", "count": count}


def resolve_ending(choice, reason, warnings, clues):
    """Return a type and first scene, preserving the original player choice."""
    if warnings >= 3 or reason == "warnings":
        return None, "ending_bad_document", "warnings"
    if reason == "timeout":
        return None, "ending_bad_document", "timeout"
    if reason == "early_harvest":
        return "ruber", "ending_early_children", "early_harvest"
    if choice == "give_up":
        return None, "ending_bad_document", "give_up"
    if choice in {"warn", "lie"}:
        if clues < 4:
            return None, "ending_bad_document", "insufficient_clues"
        return "fulvus", "ending_report", "choice"
    if choice == "target":
        return "caeruleus", "ending_target_children", "choice"
    if choice == "all":
        return "ruber", "ending_all_bodies", "choice"
    raise ValueError("Unknown final decision")


def build_ending_scenes(scene):
    """All transitions are existing storyboard nodes, not generated outcomes."""
    result = {}

    def step(key, title, image, lines, next_scene=None, **extras):
        result[key] = scene(title, extras.pop("stage", "ending"), image, lines, next_scene,
                            ending=True, **extras)

    step("ending_report", "현관 밖 · 스승의 질문", "report_mentor", [("mentor", "수확했는가?")],
         stage="report", choices=[
             {"id": "report_yes", "title": "네, 수확했습니다", "next": "ending_lie_light"},
             {"id": "report_no", "title": "아니요, 수확하지 않았습니다", "next": "ending_truth_light"},
         ])
    step("ending_lie_light", "불이 켜진 집", "lie_light", [("narrator", "새벽, 집 안 거실이 환하게 밝아졌다. 스승이 한숨을 쉰다.")], "ending_lie_enter")
    step("ending_lie_enter", "집 안으로 향하는 스승", "lie_enter", [("narrator", "스승이 갑자기 이윤제의 집으로 들어간다.")], "ending_lie_silence")
    step("ending_lie_silence", "고요해진 집", "lie_silence", [("narrator", "집 안이 갑자기 고요해졌다.")], "ending_lie_target")
    step("ending_lie_target", "이윤제의 수확", "lie_target", [("narrator", "스승이 이윤제를 수확했다.")], "ending_lie_children")
    step("ending_lie_children", "남겨지지 못한 아이들", "lie_children", [("narrator", "스승은 딸들까지 수확했다.")], "ending_lie_anger")
    step("ending_lie_anger", "거짓 보고", "lie_anger", [("mentor", "상관한테 거짓말을 하다니, 넌 수확자로서 자격이 있는 것이냐?!")], "ending_lie_discipline")
    step("ending_lie_discipline", "징계서", "lie_discipline", [("mentor", "이따 본부에서 징계서 작성 준비나 해라. 오늘 일은 내가 처리했으니 파직은 면할 것이다.")], "ending_lie_gold")
    step("ending_lie_gold", "금색으로 물든 로브", "lie_gold", [("narrator", "스승의 분노는 수확 실패보다 거짓말을 향해 있었다. 나는 그를 따라갔다, 수확하러. 회색 로브가 금색으로 물든다.")], "result_fulvus_lie")
    step("result_fulvus_lie", "당신의 색", "fulvus_lie", [], "ending_reflection", stage="result", result_type="fulvus", advance_label="마지막 질문 보기")

    step("ending_truth_light", "불이 켜진 집", "truth_light", [("narrator", "새벽, 집 안 거실이 환하게 밝아졌다. 스승이 한숨을 쉰다.")], "ending_truth_enter")
    step("ending_truth_enter", "집 안으로 향하는 스승", "truth_enter", [("narrator", "스승이 갑자기 이윤제의 집으로 들어간다.")], "ending_truth_cry")
    step("ending_truth_cry", "아이들의 울음", "truth_cry", [("narrator", "집 안에서 갑자기 아이들의 울음소리가 들렸다.")], "ending_truth_target")
    step("ending_truth_target", "이윤제의 수확", "truth_target", [("narrator", "스승이 이윤제를 수확했다.")], "ending_truth_children")
    step("ending_truth_children", "아버지 곁의 딸들", "truth_children", [("narrator", "딸들이 이윤제를 안고 운다.")], "ending_truth_cover")
    step("ending_truth_cover", "스승의 보고", "truth_cover", [("mentor", "오늘은 내가 했지만, 기록에는 네가 수확했다고 적었다. 다음은 없다. 오늘은 봐준다.")], "ending_truth_expression")
    step("ending_truth_expression", "읽을 수 없는 표정", "truth_expression", [("narrator", "스승은 무슨 생각인지 알 수 없는 표정으로 걸어간다.")], "ending_truth_mail")
    step("ending_truth_mail", "미성년보호청의 연락", "truth_mail", [("narrator", "미성년보호청에서 아이들이 안전하다는 메일이 왔다.")], "ending_truth_gold")
    step("ending_truth_gold", "금색으로 물든 로브", "truth_gold", [("narrator", "그런데도 마음 한쪽이 께름칙하다. 나는 스승을 따라갔다, 수확하러. 회색 로브가 금색으로 물든다.")], "result_fulvus_truth")
    step("result_fulvus_truth", "당신의 색", "fulvus_truth", [], "ending_reflection", stage="result", result_type="fulvus", advance_label="마지막 질문 보기")

    step("ending_target_children", "아버지를 안은 딸들", "target_children", [("narrator", "딸들은 이윤제의 시신을 꼭 안고 운다. 울음이 그치지 않는다.")], "ending_target_rule")
    step("ending_target_rule", "그러나 근거는 있다", "target_rule", [("mentor", "4조를 어겼다. 그러나 근거는 있다."), ("mentor", "미성년보호청을 불렀으니 아이들은 걱정하지 말아라. 기록하는 것을 빼먹지 말고 일지를 작성해라.")], "journal_target")
    step("journal_target", "수확일지", "journal_target", [], "ending_target_return", stage="journal", journal_subject="이윤제 · No. 0261024.2", advance_label="수확일지 기록")
    step("ending_target_return", "본부로", "target_return", [("mentor", "본부로 돌아가자.")], "ending_target_mail")
    step("ending_target_mail", "아이들의 안부", "target_mail", [("narrator", "미성년보호청에서 아이들이 안전하다는 메일이 왔다.")], "ending_target_blue")
    step("ending_target_blue", "남청색으로 물든 로브", "target_blue", [("narrator", "그런데도 마음은 께름칙하다. 멀리 스승과 걸어가며, 회색 로브가 남청색으로 물든다.")], "result_caeruleus")
    step("result_caeruleus", "당신의 색", "caeruleus", [], "ending_reflection", stage="result", result_type="caeruleus", advance_label="마지막 질문 보기")

    step("ending_all_bodies", "거실에 남은 세 사람", "all_bodies", [("narrator", "거실에 쓰러진 세 사람을 바라본다.")], "ending_all_praise")
    step("ending_all_praise", "계율대로", "all_praise", [("mentor", "계율대로다. 잘했다.")], "journal_all")
    step("journal_all", "수확일지", "journal_all", [], "ending_all_red", stage="journal", journal_subject="이윤제 · 이영지 · 이서진", advance_label="수확일지 기록")
    step("ending_all_red", "진홍색으로 물든 로브", "all_red", [("mentor", "본부로 돌아가자."), ("narrator", "수확자 자격을 유지한다. 회색 로브가 진홍색으로 물든다.")], "result_ruber")
    step("result_ruber", "당신의 색", "ruber_all", [], "ending_reflection", stage="result", result_type="ruber", advance_label="마지막 질문 보기")

    step("ending_early_children", "아직 잠든 딸들", "early_children", [("narrator", "아무것도 모르는 딸들은 잠든 채 숨을 쉰다.")], "ending_early_praise")
    step("ending_early_praise", "계율대로", "early_praise", [("mentor", "계율대로다. 잘했다. 미성년보호청은 걱정하지 않아도 될 것이다. 원리원칙을 지켰으니 수확자로서 할 일을 한 것이다.")], "journal_early")
    step("journal_early", "수확일지", "journal_early", [], "ending_early_red", stage="journal", journal_subject="이윤제 · No. 0261024.2", advance_label="수확일지 기록")
    step("ending_early_red", "진홍색으로 물든 로브", "early_red", [("mentor", "본부로 돌아가자."), ("narrator", "수확자 자격을 유지한다. 회색 로브가 진홍색으로 물든다.")], "result_ruber_early")
    step("result_ruber_early", "당신의 색", "ruber_early", [], "ending_reflection", stage="result", result_type="ruber", advance_label="마지막 질문 보기")

    step("ending_bad_document", "수확령 · 위배자 징계위원회", "bad_document", [("narrator", "수확을 이행하지 않았다. 견습 자격을 즉시 박탈한다. 계율 5조에 따라 가족은 다시 수확 대상이 된다. 수확자의 권한을 반납하라.")], "ending_bad_hands")
    step("ending_bad_hands", "빼앗긴 로브", "bad_hands", [("mentor", "실망이구나…"), ("narrator", "로브를 잡은 손이 떨린다. 어둠 속에서 스승이 돌아선다.")], "ending_bad_before")
    step("ending_bad_before", "흩어지기 전", "bad_before", [("mentor", "내가 너를 잘못 봤구나. 너를 선택한 내가 바보지.")], "ending_bad_ash")
    step("ending_bad_ash", "재가 된 로브", "bad_ash", [("narrator", "로브가 재처럼 흩어진다.")], "ending_bad_notice", reveal=True)
    step("ending_bad_notice", "수확령의 통보", "bad_ash", [("narrator", "너의 가족은 내일부터 수확 명단에 오른다.\n수확자가 될 수 있는 기회는 단 한 번뿐이니,\n다시 돌아올 수 없을 것이다.\n그럼 이만, 수습 수확자.")], "ending_bad_motto")
    step("ending_bad_motto", "인류를 위해", "logo", [("narrator", "인류를 위해 봉사하리라.")], "ending_bad_fade", video=video_url("수확령_로고_영상.mp4"))
    step("ending_bad_fade", "사라지는 수확령", "logo", [], "result_bad", video=video_url("reversed.mp4"))
    step("result_bad", "선택을 포기한 수확자", "bad_result", [], stage="bad_result")
    step("ending_reflection", "당신의 선택이 만든 색", "reflection_logo", [("narrator", "인간은 자신이 내린 선택으로 만들어진다."), ("narrator", "나는 무엇에 가치를 두고 선택하며, 그 선택으로 어떤 색의 삶을 살아가고 있는가?")], stage="reflection")
    return result

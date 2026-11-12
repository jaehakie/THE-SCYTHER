"""Scene routing, generated replies and confirmation boundaries without paid calls."""
import json
import unittest

import httpx

from services.character import CharacterDialogue, ModelConfig
from services.game import GameError, GameService
from services.story import OBJECTS, SCENES


class SceneDialogueTest(unittest.TestCase):
    def setUp(self):
        self.payloads = []
        self.result = {"intent": "reply", "choice_id": None, "reply": "지금 말씀을 듣고 있습니다."}

        def provider(request):
            payload = json.loads(request.content)
            self.payloads.append(payload)
            text = json.dumps(self.result, ensure_ascii=False) if "text" in payload else self.result["reply"]
            return httpx.Response(200, json={"status": "completed", "output": [
                {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]},
            ]})

        self.adapter = CharacterDialogue(ModelConfig(api_key="test-only", model="test-model"), httpx.MockTransport(provider))
        self.service = GameService(clock=lambda: 1000, dialogue=self.adapter)
        self.counter = 0

    def at(self, scene, clues=True):
        self.counter += 1
        token = f"session-{self.counter}"
        self.service.create(token)
        state = self.service.sessions[token]
        state.clues = list(OBJECTS) if clues else []
        self.service._enter(state, scene)
        return token

    def chat(self, token, text, request="request-1", revision=None):
        revision = self.service.read(token)["revision"] if revision is None else revision
        return self.service.act(token, "chat", text, revision, request)

    def test_every_existing_input_has_context_and_generated_reply(self):
        expected = {key for key, scene in SCENES.items() if scene.get("input")}
        self.assertEqual(set(self.adapter.scenes), expected)
        for scene in expected:
            with self.subTest(scene=scene):
                token = self.at(scene)
                result = self.chat(token, "지금 어떤 마음인지 더 말해 주세요")
                self.assertEqual(result["scene_id"], scene)
                self.assertTrue(result["dialogue_enabled"])
                self.assertEqual(result["messages"][-1]["speaker"], self.adapter.scenes[scene]["speaker"])
                self.assertEqual(result["messages"][-1]["text"], self.result["reply"])
                self.assertEqual(result["question_count"], int(scene == "conversation"))
                if scene != "conversation":
                    schema = self.payloads[-1]["text"]["format"]
                    self.assertTrue(schema["strict"])
                    self.assertEqual(set(schema["schema"]["properties"]["choice_id"]["enum"]),
                                     {item["id"] for item in SCENES[scene]["choices"]} | {None})

    def test_option_number_routes_every_choice_and_is_idempotent_after_move(self):
        for scene_id, scene in SCENES.items():
            if not scene.get("input") or not scene["choices"]:
                continue
            for index, choice in enumerate(scene["choices"]):
                with self.subTest(scene=scene_id, choice=choice["id"]):
                    token = self.at(scene_id)
                    before_calls = len(self.payloads)
                    result = self.chat(token, f"{index + 1}번")
                    self.assertEqual(len(self.payloads), before_calls, "Exact option numbers need no model call")
                    if choice["id"] == "harvest":
                        self.assertEqual(result["scene_id"], scene_id)
                        self.assertEqual(result["confirmation"]["id"], "harvest")
                        self.assertIsNone(result["stop_reason"])
                    else:
                        self.assertEqual(result["scene_id"], choice["next"])
                        self.assertEqual(result["history"][-1]["choice"], choice["id"])
                    retry = self.chat(token, f"{index + 1}번", revision=0)
                    self.assertEqual(retry, result)

    def test_semantic_choices_use_only_current_scene_and_move(self):
        cases = [("mentor", "follow", "가르쳐 주신 대로 하겠습니다"),
                 ("knock", "delivery", "소포를 가지고 왔어요"),
                 ("waiting", "truth", "수확령에서 방문했습니다"),
                 ("entry_plea", "listen", "무슨 사정인지 들려주세요"),
                 ("allegation", "wife", "부인과 어떤 사이셨나요"),
                 ("cup_ring", "family", "이 일을 자녀들도 아나요"),
                 ("wife_tears", "ask", "후배에 대한 의혹을 설명해 주세요")]
        for scene, choice, text in cases:
            with self.subTest(scene=scene):
                self.result = {"intent": "choose", "choice_id": choice, "reply": ""}
                token = self.at(scene)
                result = self.chat(token, text)
                self.assertEqual(result["history"][-1]["choice"], choice)
                self.assertEqual(result["scene_id"], next(item["next"] for item in SCENES[scene]["choices"] if item["id"] == choice))
                self.assertNotIn('"next":', self.payloads[-1]["instructions"])

    def test_ambiguous_and_negative_actions_cannot_be_auto_executed(self):
        self.result = {"intent": "choose", "choice_id": "break", "reply": ""}
        for text in ("문을 부수지 않고 기다릴까, 택배라고 할까?", "문은 부수지 마세요", "문을 부순다면 어떻게 되나요?"):
            with self.subTest(text=text):
                token = self.at("knock")
                result = self.chat(token, text)
                self.assertEqual(result["scene_id"], "knock")
                self.assertEqual(result["history"], [])
                self.assertEqual(result["messages"][-1]["speaker"], "yoonje")

    def test_harvest_always_requires_existing_confirmation(self):
        self.result = {"intent": "choose", "choice_id": "harvest", "reply": ""}
        token = self.at("entry_plea")
        result = self.chat(token, "더 듣지 않고 지금 수확하겠습니다")
        self.assertEqual(result["scene_id"], "entry_plea")
        self.assertIsNone(result["stop_reason"])
        self.assertEqual(result["confirmation"]["id"], "harvest")
        final = self.service.act(token, "choose", "harvest", result["revision"])
        self.assertEqual(final["stop_reason"], "early_harvest")

    def test_allegation_suffix_and_other_action_negation_do_not_block_intent(self):
        self.result = {"intent": "choose", "choice_id": "ask", "reply": ""}
        token = self.at("wife_tears")
        result = self.chat(token, "직장 후배에게 했다는 괴롭힘 의혹은 사실인가요?")
        self.assertEqual(result["scene_id"], "wife_question")
        self.result = {"intent": "choose", "choice_id": "harvest", "reply": ""}
        token = self.at("entry_plea")
        result = self.chat(token, "사연은 듣지 않겠습니다. 지금 수확을 실행하겠습니다.")
        self.assertEqual(result["confirmation"]["id"], "harvest")
        token = self.at("entry_plea")
        result = self.chat(token, "수확하지 않겠습니다. 이야기를 들을게요.")
        self.assertIsNone(result["confirmation"])
        self.assertEqual(result["scene_id"], "entry_plea")

    def test_disabled_choice_is_excluded_and_cannot_return_from_model(self):
        token = self.at("mentor")
        self.service.sessions[token].warnings.append("delay")
        before = self.service.read(token)
        self.result = {"intent": "choose", "choice_id": "delay", "reply": ""}
        with self.assertRaises(GameError) as error:
            self.chat(token, "다음번으로 미루죠")
        self.assertEqual(error.exception.status, 502)
        choices = self.payloads[-1]["text"]["format"]["schema"]["properties"]["choice_id"]["enum"]
        self.assertNotIn("delay", choices)
        self.assertEqual(self.service.read(token), before)

    def test_invalid_model_action_cannot_change_state(self):
        for result in ({"intent": "choose", "choice_id": "new_ending", "reply": ""},
                       {"intent": "reply", "choice_id": "follow", "reply": "이동합니다"},
                       {"intent": "reply", "choice_id": None, "reply": ""}):
            with self.subTest(result=result):
                self.result = result
                token = self.at("mentor")
                before = self.service.read(token)
                with self.assertRaises(GameError):
                    self.chat(token, "아무 이야기")
                self.assertEqual(self.service.read(token), before)

    def test_mentor_and_yoonje_use_separate_conversation_context(self):
        token = self.at("mentor")
        self.chat(token, "스승님께만 비밀로 제 별명을 말할게요")
        self.service._enter(self.service.sessions[token], "knock")
        self.chat(token, "누구 계신가요", "request-2")
        self.assertEqual(len(self.payloads[-1]["input"]), 1)
        self.assertNotIn("스승님께만 비밀", self.payloads[-1]["instructions"])
        self.assertNotIn("공정한 뽑기와 과거 데이터", self.payloads[-1]["instructions"])
        self.assertIn("아직 문이 열리지 않았다", self.payloads[-1]["instructions"])

    def test_mentor_prompt_is_not_living_room_and_lore_respects_progress(self):
        token = self.at("mentor", clues=False)
        self.chat(token, "감찰 메일과 병원 서류, 후배 의혹은요")
        prompt = self.payloads[-1]["instructions"]
        self.assertNotIn("차가 식기 전에", prompt)
        self.assertNotIn("폐암 말기", prompt)
        self.assertNotIn("later_allegation", prompt)
        self.assertIn("스승", prompt)
        token = self.at("knock", clues=False)
        self.chat(token, "서랍의 건강검진 기록과 편지에 대해 말해 주세요")
        prompt = self.payloads[-1]["instructions"]
        self.assertNotIn("병원 서류예요", prompt)
        self.assertNotIn("그건 보내지 못한 편지입니다", prompt)
        self.assertNotIn("폐암 말기", prompt)
        token = self.at("allegation")
        self.chat(token, "후배 의혹과 감찰 메일을 설명해 주세요")
        self.assertIn("later_allegation", self.payloads[-1]["instructions"])


if __name__ == "__main__":
    unittest.main()

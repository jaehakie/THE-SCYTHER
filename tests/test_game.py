import unittest

from fastapi.testclient import TestClient

from app import app


class GameFlowTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.state = self.client.post("/api/game").json()

    def act(self, action, value=""):
        r = self.client.post("/api/action", json={"action": action, "value": value, "revision": self.state["revision"]})
        self.assertEqual(r.status_code, 200, r.text)
        self.state = r.json()
        return self.state

    def chat(self, text):
        r = self.client.post("/api/chat", json={"message": text, "revision": self.state["revision"]})
        self.assertEqual(r.status_code, 200, r.text)
        self.state = r.json()
        return self.state["messages"][-1]["text"]

    def enter(self):
        self.act("select", "yoonje")
        self.act("enter")

    def test_full_play_records_evidence_and_ending(self):
        self.enter()
        self.act("inspect", "calendar")
        self.assertIn("생일", self.chat("내일은 무슨 날인가요?"))
        self.act("intel")
        self.act("decide")
        self.act("choose", "target")
        self.assertEqual(self.state["result"]["name"], "카이룰레우스")
        self.assertIn("달력", self.state["result"]["evidence"])
        self.assertEqual(self.client.get("/api/game").json(), self.state)

    def test_sessions_are_isolated_and_reset_only_affects_self(self):
        self.enter()
        self.act("inspect", "letter")
        other = TestClient(app)
        other_state = other.post("/api/game").json()
        self.assertEqual(other_state["clues"], [])
        self.assertEqual(other_state["stage"], "selection")
        self.assertEqual(len(self.client.get("/api/game").json()["clues"]), 1)
        self.client.post("/api/game")
        self.assertEqual(self.client.get("/api/game").json()["clues"], [])
        self.assertEqual(other.get("/api/game").json(), other_state)

    def test_questions_do_not_unlock_undiscovered_facts(self):
        self.enter()
        reply = self.chat("진단서가 있나요?")
        self.assertNotIn("폐암", reply)
        self.assertEqual(self.state["clues"], [])
        reply = self.chat("직장 내 괴롭힘 의혹이 사실인가요?")
        self.assertNotIn("징계", reply)
        self.assertFalse(self.state["intel"])

    def test_natural_action_and_repeated_inspection(self):
        self.enter()
        self.chat("서랍을 열어 진단서를 살펴본다")
        self.assertEqual([c["id"] for c in self.state["clues"]], ["diagnosis"])
        count = len(self.state["messages"])
        self.act("inspect", "diagnosis")
        self.assertEqual(len(self.state["messages"]), count)
        self.assertIn("진단서", self.chat("그 진단서에 대해 이야기해주세요"))

    def test_followup_uses_previous_topic(self):
        self.enter()
        self.chat("따님들 이야기를 듣고 싶어요")
        self.assertIn("아이들", self.chat("조금 더 자세히요"))
        self.assertIn("아이들", self.chat("조금 더 이야기해주세요"))

    def test_invalid_transitions_and_stale_requests_do_not_change_state(self):
        payload = {"action": "choose", "value": "all", "revision": 0}
        self.assertEqual(self.client.post("/api/action", json=payload).status_code, 409)
        self.act("select", "yoonje")
        payload = {"action": "enter", "revision": 0}
        self.assertEqual(self.client.post("/api/action", json=payload).status_code, 409)
        self.assertEqual(self.client.get("/api/game").json()["stage"], "briefing")

    def test_unknown_objects_and_empty_chat_are_rejected(self):
        self.enter()
        base = {"action": "inspect", "value": "made_up", "revision": self.state["revision"]}
        self.assertEqual(self.client.post("/api/action", json=base).status_code, 400)
        for text in ("", "   ", "x" * 2001):
            r = self.client.post("/api/chat", json={"message": text, "revision": self.state["revision"]})
            self.assertIn(r.status_code, (400, 422))

    def test_missing_session_is_recoverable(self):
        c = TestClient(app)
        self.assertEqual(c.get("/api/game").status_code, 401)
        self.assertEqual(c.post("/api/game").status_code, 200)

    def test_all_five_endings_and_terminal_state(self):
        for choice, expected in [("warn", "풀부스"), ("lie", "풀부스"), ("target", "카이룰레우스"), ("all", "루베르"), ("give_up", "선택을 포기한 수확자")]:
            with self.subTest(choice=choice):
                self.state = self.client.post("/api/game").json()
                self.enter()
                self.act("intel")
                self.act("decide")
                self.act("choose", choice)
                self.assertEqual(self.state["result"]["name"], expected)
                r = self.client.post("/api/chat", json={"message": "다시", "revision": self.state["revision"]})
                self.assertEqual(r.status_code, 409)

    def test_public_pages_assets_and_private_reference_boundary(self):
        for url in ("/", "/health", "/assets/css/style.css", "/assets/js/app.js", "/assets/images/notion-6.png"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get("/reference/notion-25.png").status_code, 404)
        self.assertEqual(self.client.get("/services/game.py").status_code, 404)


if __name__ == "__main__":
    unittest.main()

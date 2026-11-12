"""Final storyboard rules, including the team's confirmed empathy threshold."""
import unittest

from services.endings import clue_grade, resolve_ending
from services.game import GameError, GameService
from services.story import DIALOGUE_CLUES, OBJECTS, SCENES


class EndingTest(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.game = GameService(clock=lambda: self.now)
        self.view = self.game.create("player")

    def act(self, action, value="", request_id=None):
        self.view = self.game.act("player", action, value, self.view["revision"], request_id)
        return self.view

    def decision_fixture(self, clues=6, warnings=0):
        # Isolate every boundary, including counts unreachable on some story paths.
        state = self.game.sessions["player"]
        state.dialogue_clues = list(DIALOGUE_CLUES)[:clues]
        state.warnings = ["delay"] * warnings
        self.game._enter(state, "decision")
        self.now += 15
        self.view = self.game.read("player")

    def complete(self, report="report_no"):
        scenes = []
        for _ in range(25):
            scenes.append(self.view["scene_id"])
            if self.view["stage"] in {"reflection", "bad_result"}:
                return scenes
            if self.view["stage"] == "report":
                self.act("choose", report)
            elif self.view["stage"] == "journal":
                self.act("journal", "관찰한 단서와 판단의 근거를 기록합니다.")
            else:
                self.assertTrue(self.view["can_advance"], self.view["scene_id"])
                self.act("advance")
        self.fail("Ending did not terminate")

    def test_thresholds_all_choices_and_warning_priority(self):
        for clues in range(7):
            for choice in ("warn", "lie", "target", "all", "give_up"):
                with self.subTest(clues=clues, choice=choice):
                    actual, first, reason = resolve_ending(choice, "choice", 0, clues)
                    expected = ({"target": "caeruleus", "all": "ruber"}.get(choice)
                                if choice not in {"warn", "lie"} else "fulvus" if clues >= 4 else None)
                    self.assertEqual(actual, expected)
                    self.assertEqual(first == "ending_bad_document", expected is None)
                    self.assertEqual(resolve_ending(choice, "choice", 3, clues)[2], "warnings")
        self.assertEqual([clue_grade(n)["id"] for n in range(7)],
                         ["regret", "regret", "uneasy", "uneasy", "uneasy", "certain", "certain"])

    def test_empathy_report_branches_keep_original_choice(self):
        for choice in ("warn", "lie"):
            for report in ("report_yes", "report_no"):
                self.view = self.game.create("player")
                self.decision_fixture(4)
                self.act("choose", choice)
                self.assertIsNone(self.view["result"])
                scenes = self.complete(report)
                self.assertEqual(self.view["final_choice"], choice)
                self.assertEqual(self.view["report_answer"], "yes" if report == "report_yes" else "no")
                self.assertEqual(self.view["result"]["id"], "fulvus")
                self.assertIn("ending_lie_children" if report == "report_yes" else "ending_truth_mail", scenes)
                self.assertNotIn("ending_truth_mail" if report == "report_yes" else "ending_lie_children", scenes)
                self.assertEqual(self.view["ending_grade"]["label"], "찜찜함")

    def test_journals_and_colored_results_complete(self):
        for choice, expected in (("target", "caeruleus"), ("all", "ruber")):
            self.view = self.game.create("player")
            self.decision_fixture(2)
            self.act("choose", choice)
            scenes = self.complete()
            self.assertEqual(self.view["result"]["id"], expected)
            self.assertEqual(self.view["ending_status"], "complete")
            self.assertEqual(self.view["journal"]["clue_record"], "단서 일부 확인")
            self.assertIn("journal_" + choice, scenes)
            self.assertFalse(self.view["can_advance"])
            self.assertIn("인간은", self.view["messages"][0]["text"])

    def test_bad_paths_have_no_color_or_common_reflection(self):
        for mode in ("give_up", "timeout", "warnings", "insufficient_clues"):
            with self.subTest(mode=mode):
                self.view = self.game.create("player")
                self.decision_fixture(3 if mode == "insufficient_clues" else 6,
                                      3 if mode == "warnings" else 0)
                if mode == "timeout":
                    self.now += 45
                    self.view = self.game.read("player")
                else:
                    self.act("choose", "warn" if mode == "insufficient_clues" else "give_up")
                self.assertEqual(self.view["ending_reason"], mode)
                scenes = self.complete()
                self.assertEqual(self.view["scene_id"], "result_bad")
                self.assertIsNone(self.view["result"])
                self.assertNotIn("ending_reflection", scenes)
                self.assertEqual(self.view["ending_status"], "complete")

    def test_journal_validation_retry_and_reload(self):
        self.decision_fixture()
        self.act("choose", "target")
        self.act("advance")
        self.act("advance")
        self.assertEqual(self.view["stage"], "journal")
        before = self.game.read("player")
        for action, value in (("advance", ""), ("journal", "  "), ("journal", "x" * 2001)):
            with self.assertRaises(GameError):
                self.act(action, value)
            self.assertEqual(self.game.read("player"), before)
        content = '<script>alert("x")</script>\n원문 기록'
        revision = self.view["revision"]
        self.act("journal", content, "journal-1")
        completed = self.view
        self.assertEqual(self.game.act("player", "journal", content, revision, "journal-1"), completed)
        self.assertEqual(self.game.read("player")["journal"]["content"], content)
        with self.assertRaises(GameError):
            self.game.act("player", "journal", "different", revision, "journal-1")

    def test_final_choice_retry_and_frozen_time(self):
        self.decision_fixture()
        revision = self.view["revision"]
        self.act("choose", "target", "final-1")
        self.assertEqual(self.game.act("player", "choose", "target", revision, "final-1"), self.view)
        self.now += 120
        self.assertEqual(self.game.read("player")["time_left"], 45)
        self.assertEqual(self.game.read("player")["ending_reason"], "choice")

    def test_empathy_all_reports_have_no_journal_or_extra_note_step(self):
        for choice in ("warn", "lie"):
            for report in ("report_yes", "report_no"):
                with self.subTest(choice=choice, report=report):
                    self.view = self.game.create("player")
                    self.decision_fixture()
                    self.act("choose", choice)
                    self.act("choose", report)
                    for _ in range(20):
                        if self.view["stage"] == "result":
                            break
                        self.assertNotEqual(self.view["stage"], "journal")
                        self.act("advance")
                    self.assertEqual(self.view["result"]["id"], "fulvus")
                    self.assertIsNone(self.view["journal"])
                    self.assertNotIn("result_note", self.view)
                    before = self.game.read("player")
                    with self.assertRaises(GameError):
                        self.act("ending_note", "추가 일지")
                    self.assertEqual(self.game.read("player"), before)
                    self.act("advance")
                    self.assertEqual(self.view["stage"], "reflection")

    def test_removed_result_note_cannot_change_other_scenes(self):
        before = self.view
        with self.assertRaises(GameError):
            self.act("ending_note", "잘못된 시점")
        self.assertEqual(self.game.read("player"), before)

    def test_actual_early_path_and_new_session_clear_ending(self):
        previous_run = self.view["run_id"]
        self.assertEqual(self.game.read("player")["run_id"], previous_run)
        for _ in range(30):
            scene = self.view["scene_id"]
            selections = {"selection": "yoonje", "mentor": "follow", "knock": "break", "entry_plea": "harvest"}
            if self.view["stop_reason"]:
                break
            self.act("choose", selections[scene]) if scene in selections else self.act("advance")
        self.assertEqual(self.view["stop_reason"], "early_harvest")
        self.assertIsNone(self.view["final_choice"])
        self.complete()
        self.assertEqual(self.view["result"]["id"], "ruber")
        self.assertEqual(self.view["ending_grade"]["label"], "후회")
        self.assertIn("이윤제", self.view["journal"]["subject"])
        new = self.game.create("new", previous="player")
        self.assertNotEqual(new["run_id"], previous_run)
        for field in ("journal", "result", "ending_reason", "ending_grade", "report_answer", "final_choice"):
            self.assertIsNone(new[field])
        with self.assertRaises(GameError):
            self.game.read("player")

    def test_all_ending_scenes_terminate_without_cycles(self):
        def walk(key, visited):
            self.assertNotIn(key, visited, key)
            scene = SCENES[key]
            if not scene["next"] and not scene["choices"]:
                self.assertIn(scene["stage"], {"reflection", "bad_result"})
            for next_key in ([scene["next"]] if scene["next"] else []) + [c["next"] for c in scene["choices"]]:
                walk(next_key, visited | {key})
        for key, scene in SCENES.items():
            if scene.get("ending"):
                walk(key, set())


if __name__ == "__main__":
    unittest.main()

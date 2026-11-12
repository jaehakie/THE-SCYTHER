"""Read-only scene navigation, narrative boundaries and racing requests."""
from copy import deepcopy
from dataclasses import asdict
from threading import Event, Thread
import unittest
from unittest.mock import patch

from services.character import CharacterDialogue, ModelConfig
from services.game import GameError, GameService
from services.story import DIALOGUE_CLUES, OBJECTS


class NavigationTest(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.game = GameService(clock=lambda: self.now)
        self.view = self.game.create("player")

    def act(self, action, value="", request_id=None):
        self.view = self.game.act("player", action, value, self.view["revision"], request_id)
        return self.view

    def until(self, target):
        for _ in range(40):
            if self.view["scene_id"] == target:
                return
            self.act("advance")
        self.fail(target)

    def gameplay(self):
        state = asdict(self.game.sessions["player"])
        for key in ("revision", "review_index", "completed_requests", "touched"):
            state.pop(key)
        return state

    def reject(self, action, value=""):
        before = self.game.read("player")
        with self.assertRaises(GameError):
            self.act(action, value)
        self.assertEqual(self.game.read("player"), before)

    def test_preparation_review_reload_and_return_never_reenter_story(self):
        self.assertFalse(self.view["can_back"])
        self.reject("back")
        self.act("advance")
        first = deepcopy(self.view)
        self.act("advance")
        latest = deepcopy(self.view)
        original = self.gameplay()
        self.act("back", request_id="back-1")
        self.assertEqual(self.view["scene_id"], first["scene_id"])
        self.assertEqual(self.view["messages"], first["messages"])
        self.assertTrue(self.view["reviewing"])
        self.assertEqual(self.gameplay(), original)
        self.assertEqual(self.game.read("player"), self.view)
        # A lost response retry must not walk two steps back.
        self.assertEqual(self.game.act("player", "back", "", latest["revision"], "back-1"), self.view)
        for action, value in (("advance", ""), ("choose", "yoonje"), ("chat", "hello"),
                              ("journal", "edit"), ("ending_note", "edit"), ("inspect", "calendar"), ("lantern", "")):
            self.reject(action, value)
        self.act("back")
        self.assertEqual(self.view["scene_id"], "intro1")
        self.assertFalse(self.view["can_back"])
        self.reject("back")
        self.act("forward")
        self.act("forward")
        self.assertFalse(self.view["reviewing"])
        self.assertEqual(self.view["scene_id"], latest["scene_id"])
        self.assertEqual(self.view["messages"], latest["messages"])
        self.assertEqual(self.gameplay(), original)
        self.reject("forward")

    def test_event_and_choice_boundaries_through_actual_story(self):
        self.until("selection")
        self.assertFalse(self.view["can_back"])
        self.act("choose", "yoonje")
        self.assertFalse(self.view["can_back"])
        self.act("advance")
        self.assertTrue(self.view["can_back"])
        self.act("back")
        self.assertEqual(self.view["scene_id"], "record")
        self.assertFalse(self.view["can_back"])
        self.act("forward")
        self.act("choose", "delay")
        self.assertFalse(self.view["can_back"])
        self.assertEqual(self.view["warn_count"], 1)
        self.act("advance")
        self.act("back")
        self.assertEqual(self.view["warn_count"], 1)
        self.act("forward")
        self.assertTrue(next(c for c in self.view["choices"] if c["id"] == "delay")["disabled"])
        self.act("choose", "doubt")
        self.assertFalse(self.view["can_back"])
        self.act("advance")
        self.act("back")
        self.assertEqual(self.view["scene_id"], "mentor_doubt")
        self.assertFalse(self.view["can_back"])
        self.act("forward")
        self.act("advance")
        self.assertEqual(self.view["scene_id"], "window")
        self.assertFalse(self.view["can_back"])
        self.act("advance")
        self.assertTrue(self.view["can_back"])
        self.act("choose", "delivery")
        self.assertFalse(self.view["can_back"])
        self.act("advance")
        self.assertEqual(self.view["stage"], "silence")
        self.reject("back")
        self.now += 3
        self.view = self.game.read("player")
        self.assertEqual(self.view["scene_id"], "entry_truth")
        self.assertFalse(self.view["can_back"])
        self.until("exploration")
        self.assertFalse(self.view["can_back"])
        for key in OBJECTS:
            self.act("inspect", key)
        self.act("advance")
        self.assertEqual(self.view["scene_id"], "conversation")
        self.assertFalse(self.view["can_back"])
        self.act("topic", "calendar")
        self.act("finish_chat")
        self.assertEqual(self.view["scene_id"], "intel")
        self.assertFalse(self.view["can_back"])
        self.act("advance")
        self.act("back")
        self.assertEqual(self.view["scene_id"], "intel")
        self.assertEqual(len(self.view["clues"]), 5)
        self.assertEqual(self.view["clue_count"], 1)
        self.assertEqual(self.view["warn_count"], 1)
        self.act("forward")
        self.act("choose", "wife")
        self.assertFalse(self.view["can_back"])
        self.until("wife_tears")
        original = self.gameplay()
        self.act("back")
        self.assertEqual(self.view["scene_id"], "wife_story")
        self.assertIn("tears", [c["id"] for c in self.view["dialogue_clues"]])
        self.act("forward")
        self.assertEqual(self.gameplay(), original)
        self.act("choose", "ask")
        self.assertFalse(self.view["can_back"])
        self.until("daughters")
        self.assertFalse(self.view["can_back"])
        self.act("advance")
        self.assertEqual(self.view["scene_id"], "decision")
        self.reject("back")
        self.now += 16
        self.view = self.game.read("player")
        self.assertEqual(self.view["time_left"], 44)
        self.reject("back")
        self.now += 44
        self.view = self.game.read("player")
        self.assertEqual(self.view["ending_reason"], "timeout")
        self.assertFalse(self.view["can_back"])

    def test_journal_result_and_saved_basis_are_not_undone(self):
        for choice in ("target", "all", "warn"):
            with self.subTest(choice=choice):
                self.view = self.game.create("player")
                state = self.game.sessions["player"]
                state.dialogue_clues = list(DIALOGUE_CLUES)
                self.game._enter(state, "decision")
                self.now += 15
                self.view = self.game.read("player")
                self.act("choose", choice)
                self.assertFalse(self.view["can_back"])
                for _ in range(25):
                    if self.view["stage"] == "result":
                        break
                    if self.view["stage"] == "report":
                        self.act("choose", "report_no")
                        self.assertFalse(self.view["can_back"])
                    elif self.view["stage"] == "journal":
                        self.assertFalse(self.view["can_back"])
                        self.act("journal", "원래 작성한 근거")
                        self.assertFalse(self.view["can_back"])
                    else:
                        self.act("advance")
                self.assertEqual(self.view["stage"], "result")
                self.assertFalse(self.view["can_back"])
                self.act("advance")
                self.assertEqual(self.view["stage"], "reflection")
                original = self.gameplay()
                self.act("back")
                self.assertEqual(self.view["stage"], "result")
                self.assertTrue(self.view["reviewing"])
                self.reject("ending_note", "바꿀 근거")
                self.reject("journal", "바꿀 근거")
                self.act("forward")
                self.assertEqual(self.gameplay(), original)
                if choice == "warn":
                    self.assertIsNone(self.view["journal"])
                else:
                    self.assertEqual(self.view["journal"]["content"], "원래 작성한 근거")

    def test_session_isolation_reset_and_stale_navigation(self):
        self.act("advance")
        revision = self.view["revision"]
        self.act("back")
        with self.assertRaises(GameError):
            self.game.act("player", "back", "", revision)
        other = self.game.create("other")
        self.assertFalse(other["can_back"])
        self.assertFalse(other["reviewing"])
        new = self.game.create("fresh", previous="player")
        self.assertFalse(new["can_back"])
        self.assertFalse(new["reviewing"])
        self.assertNotEqual(new["run_id"], self.view["run_id"])

    def test_generated_choices_and_review_do_not_call_provider(self):
        adapter = CharacterDialogue(ModelConfig(mode="mock"))
        self.game.dialogue = adapter
        self.game._enter(self.game.sessions["player"], "mentor")
        self.view = self.game.read("player")
        self.act("chat", "2번", "choice-1")
        self.assertEqual(self.view["scene_id"], "mentor_delay")
        self.assertFalse(self.view["can_back"])
        self.act("advance")
        original = self.gameplay()
        with patch.object(adapter, "respond_scene", side_effect=AssertionError("Provider called during review")):
            self.act("back")
            self.reject("chat", "말 바꾸기")
            self.act("forward")
        self.assertEqual(self.gameplay(), original)

    def test_navigation_invalidates_a_late_model_reply(self):
        started, release = Event(), Event()
        adapter = CharacterDialogue(ModelConfig(mode="mock"))
        self.game.dialogue = adapter
        self.game._enter(self.game.sessions["player"], "window")
        self.game._enter(self.game.sessions["player"], "knock")
        self.view = self.game.read("player")
        original = self.gameplay()
        revision, errors = self.view["revision"], []

        def slow(*args):
            started.set()
            release.wait(5)
            return {"choice_id":None, "reply":"늦게 도착한 답변"}

        def send():
            try:
                self.game.act("player", "chat", "지금 어떤 상황이죠?", revision, "slow-1")
            except GameError as error:
                errors.append(error.status)

        with patch.object(adapter, "respond_scene", side_effect=slow):
            worker = Thread(target=send)
            worker.start()
            try:
                self.assertTrue(started.wait(2))
                self.act("back")
            finally:
                release.set()
                worker.join(5)
        self.assertEqual(errors, [409])
        self.assertTrue(self.game.read("player")["reviewing"])
        self.act("forward")
        self.assertEqual(self.gameplay(), original)


if __name__ == "__main__":
    unittest.main()

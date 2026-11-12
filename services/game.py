"""서버가 장면·단서·경고·실제 시간을 관리하는 단일 프로세스 시연."""

from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock
from time import monotonic
from uuid import uuid4

from .dialogue import branch_intent, explicit_choice, first_topic, normalized, topic_reply, uncertain_action, warning_reason
from .character import DialogueError
from .endings import ENDING_TYPES, clue_grade, resolve_ending
from .navigation import locks_back
from .story import DIALOGUE_CLUES, FINAL_CHOICES, OBJECTS, RULES, SCENES, TIMED_LINES, TOPICS, image_url


class GameError(Exception):
    def __init__(self, message: str, status: int = 409):
        self.message, self.status = message, status


@dataclass
class Session:
    run_id: str = field(default_factory=lambda: uuid4().hex)
    scene_id: str = "intro1"
    revision: int = 0
    clues: list[str] = field(default_factory=list)
    dialogue_clues: list[str] = field(default_factory=list)
    messages: list[dict] = field(default_factory=list)
    scene_start: int = 0
    history: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    question_count: int = 0
    topic_counts: dict[str, int] = field(default_factory=dict)
    topic: str | None = None
    image: str | None = None
    lantern_on: bool = False
    choice: str | None = None
    stop_reason: str | None = None
    entered_at: float = 0
    decision_started: float | None = None
    decision_elapsed: float = 0
    timed_beats: int = 0
    touched: float = 0
    recent_turns: list[dict] = field(default_factory=list)
    completed_requests: dict[str, tuple] = field(default_factory=dict)
    pending_choice: str | None = None
    ending_type: str | None = None
    ending_reason: str | None = None
    ending_grade: dict | None = None
    report_answer: str | None = None
    journal: dict | None = None
    back_scenes: list[dict] = field(default_factory=list)
    review_index: int | None = None


class GameService:
    def __init__(self, clock=monotonic, dialogue=None):
        self.sessions: dict[str, Session] = {}
        self.lock = RLock()
        self.clock = clock
        self.dialogue = dialogue
        self.inflight: set[str] = set()

    def create(self, token: str, previous: str | None = None) -> dict:
        with self.lock:
            now = self.clock()
            self.sessions = {key: state for key, state in self.sessions.items() if now - state.touched < 43200}
            if len(self.sessions) >= 500 and previous not in self.sessions:
                raise GameError("현재 시연 접속자가 많습니다. 잠시 뒤 다시 시도해주세요.", 503)
            if previous:
                self.sessions.pop(previous, None)
            state = Session(touched=now)
            self._enter(state, "intro1")
            self.sessions[token] = state
            return self._view(state)

    def _get(self, token):
        state = self.sessions.get(token)
        if state is None or self.clock() - state.touched >= 43200:
            self.sessions.pop(token, None)
            raise GameError("진행 기록이 만료되었거나 서버가 재시작되었습니다. 새 임무를 시작해주세요.", 401)
        state.touched = self.clock()
        self._sync_time(state)
        return state

    def read(self, token):
        with self.lock:
            return self._view(self._get(token))

    def _say(self, state, speaker, text, image=None):
        state.messages.append({"id": len(state.messages) + 1, "speaker": speaker, "text": text,
                               "image": image_url(image), "scene_id": state.scene_id})

    def _enter(self, state, scene_id, *, chosen=False):
        if state.messages:
            if locks_back(state.scene_id, scene_id, chosen=chosen):
                state.back_scenes.clear()
            else:
                # Store a display snapshot, never a restorable game state.
                state.back_scenes.append(self._live_view(state))
        state.review_index = None
        scene = SCENES[scene_id]
        state.scene_id = scene_id
        state.scene_start = len(state.messages)
        state.entered_at = self.clock()
        state.image = scene["image"]
        if scene["stage"] == "exploration":
            state.lantern_on = False
        lines = scene["lines"]
        if scene_id == "conversation" and self.dialogue:
            opening = self.dialogue.card["scene"]
            lines = [("narrator", opening["opening_narration"]), ("yoonje", opening["greeting"])]
        for speaker, text in lines:
            self._say(state, speaker, text)
        for clue in scene.get("observe", []):
            self._discover_dialogue(state, clue)
        if scene.get("warning"):
            self._warn(state, scene["warning"])
        if scene_id == "decision":
            state.decision_started = self.clock()

    def _finish(self, state, reason):
        if state.stop_reason is not None:
            return
        if state.decision_started is not None:
            state.decision_elapsed = min(60, self.clock() - state.decision_started)
        state.stop_reason = reason
        state.ending_type, first_scene, state.ending_reason = resolve_ending(
            state.choice, reason, len(state.warnings), len(state.dialogue_clues))
        state.ending_grade = clue_grade(len(state.dialogue_clues))
        self._enter(state, first_scene, chosen=True)
        explanation = {
            "warnings": "위배자 징계위원회로 넘긴다.",
            "insufficient_clues": "증거 없이 감정으로 판단했다. 계율 5조다.",
        }.get(state.ending_reason)
        if explanation:
            self._say(state, "mentor", explanation)

    def _sync_time(self, state):
        if state.scene_id == "door_silence" and self.clock() - state.entered_at >= SCENES["door_silence"]["duration"]:
            self._enter(state, "entry_truth")
            state.revision += 1
        if state.scene_id != "decision":
            return
        elapsed = self.clock() - state.decision_started
        changed = False
        while state.timed_beats < len(TIMED_LINES) and elapsed >= TIMED_LINES[state.timed_beats][0]:
            if state.timed_beats == 0:
                state.image = "last_minute"
            for speaker, text in TIMED_LINES[state.timed_beats][1]:
                self._say(state, speaker, text)
            state.timed_beats += 1
            changed = True
        if elapsed >= 60:
            self._finish(state, "timeout")
            changed = True
        if changed:
            state.revision += 1

    def act(self, token, action, value, revision, request_id=None):
        # Generation uses a snapshot outside the global lock. Other users and reset
        # remain responsive while the provider is working.
        if self.dialogue and action in {"chat", "topic"}:
            with self.lock:
                state = self._get(token)
                if state.review_index is not None:
                    raise GameError("이전 장면을 보는 중입니다. 현재 장면으로 돌아온 뒤 대화해주세요.")
                generated = bool(SCENES[state.scene_id].get("input")) and (action == "chat" or state.scene_id == "conversation")
                cached = request_id and request_id in state.completed_requests
            if generated or cached:
                return self._generated_act(token, action, value, revision, request_id)
        with self.lock:
            current = self._get(token)
            if request_id and request_id in current.completed_requests:
                if current.completed_requests[request_id] != (action, value):
                    raise GameError("같은 요청 번호에 다른 내용을 보낼 수 없습니다.")
                return self._view(current)
            if revision != current.revision:
                raise GameError("진행 상태가 바뀌었습니다. 최신 화면을 확인한 뒤 다시 시도해주세요.")
            if current.review_index is not None and action not in {"back", "forward"}:
                raise GameError("이전 장면에서는 기록을 바꿀 수 없습니다. 현재 장면으로 돌아와주세요.")
            # 실패한 요청은 일부 기록만 남기지 않는다. 시간 진행은 요청 성공 여부와 독립적이다.
            state = deepcopy(current)
            if action not in {"back", "forward"}:
                state.pending_choice = None
            scene = SCENES[state.scene_id]
            if action == "back":
                index = len(state.back_scenes) if state.review_index is None else state.review_index
                if index <= 0:
                    raise GameError("이 지점에서는 이전 장면으로 돌아갈 수 없습니다.")
                state.review_index = index - 1
            elif action == "forward":
                if state.review_index is None:
                    raise GameError("이미 현재 장면입니다.")
                index = state.review_index + 1
                state.review_index = index if index < len(state.back_scenes) else None
            elif action == "advance":
                self._advance(state)
            elif action == "choose":
                self._choose(state, value)
            elif action == "inspect" and scene["stage"] == "exploration":
                self._inspect(state, value)
            elif action == "lantern" and scene["stage"] == "exploration":
                state.lantern_on = not state.lantern_on
            elif action == "topic" and scene["stage"] == "conversation":
                if value not in TOPICS:
                    raise GameError("선택할 수 없는 질문입니다.", 400)
                self._question(state, TOPICS[value]["question"], value)
            elif action == "finish_chat" and scene["stage"] == "conversation":
                if state.question_count == 0:
                    raise GameError("한 가지 질문을 나눈 뒤 대화를 마무리할 수 있습니다.")
                self._enter(state, "intel")
            elif action == "chat" and scene.get("input"):
                self._chat(state, value)
            elif action == "journal" and scene["stage"] == "journal":
                content = value.strip()
                if not content or len(content) > 2000:
                    raise GameError("판단 근거를 1~2000자로 기록해주세요.", 400)
                state.journal = {"subject": scene["journal_subject"], "content": content,
                                 "clue_record": state.ending_grade["record"]}
                self._enter(state, scene["next"])
            else:
                raise GameError("지금 장면에서는 할 수 없는 행동입니다.")
            state.revision += 1
            self._remember_request(state, request_id, (action, value))
            self.sessions[token] = state
            return self._view(state)

    def _generated_act(self, token, action, value, revision, request_id):
        with self.lock:
            current = self._get(token)
            fingerprint = (action, value)
            if request_id and request_id in current.completed_requests:
                if current.completed_requests[request_id] != fingerprint:
                    raise GameError("같은 요청 번호에 다른 메시지를 보낼 수 없습니다.")
                return self._view(current)
            if token in self.inflight:
                raise GameError("앞선 답변을 생성 중입니다. 잠시 뒤 다시 보내주세요.")
            if current.review_index is not None:
                raise GameError("이전 장면에서는 대화할 수 없습니다. 현재 장면으로 돌아와주세요.")
            if revision != current.revision or not SCENES[current.scene_id].get("input"):
                raise GameError("진행 상태가 바뀌었습니다. 최신 화면을 확인해주세요.")
            if action == "topic":
                if current.scene_id != "conversation" or value not in TOPICS:
                    raise GameError("선택할 수 없는 질문입니다.", 400)
                text, topic = TOPICS[value]["question"], value
            else:
                text, topic = value.strip(), first_topic(value)
            if not text or len(text) > 2000:
                raise GameError("1~2000자의 메시지를 입력해주세요.", 400)
            if len(current.messages) >= 600:
                raise GameError("이번 세션의 대화 한도에 도달했습니다. 새 임무를 시작해주세요.", 429)
            state = deepcopy(current)
            source_scene = state.scene_id
            speaker = self.dialogue.scenes[source_scene]["speaker"]
            turns = [turn for turn in state.recent_turns if turn.get("speaker", "yoonje") == speaker]
            context = self._dialogue_context(state, speaker)
            choice_id = explicit_choice(text, context["choices"]) if source_scene != "conversation" else None
            state.pending_choice = None
            self.inflight.add(token)
        try:
            try:
                reply = ""
                if source_scene == "conversation":
                    reply = self.dialogue.generate(text, turns, source_scene, state.clues)
                elif choice_id is None:
                    result = self.dialogue.respond_scene(text, turns, source_scene, state.clues, context)
                    choice_id, reply = result["choice_id"], result["reply"]
                    if choice_id and uncertain_action(text, choice_id):
                        choice_id = None
                        reply = "어느 쪽을 택하겠다는 뜻인지 분명히 말해 보아라." if speaker == "mentor" else "어떻게 하시겠다는 뜻인지 한 번만 더 말씀해 주시겠어요?"
            except DialogueError as exc:
                raise GameError(exc.message, exc.status) from None
            self._say(state, "user", text)
            if choice_id:
                choice = next((item for item in context["choices"] if item["id"] == choice_id and not item.get("disabled")), None)
                if not choice:
                    raise GameError("지금 장면에서 선택할 수 없는 진행입니다.")
                if choice.get("requires_confirmation"):
                    state.pending_choice = choice_id
                else:
                    self._choose(state, choice_id)
                    reply = "\n".join(item["text"] for item in state.messages[state.scene_start:]
                                      if item["speaker"] in {speaker, "narrator"})
            else:
                if not reply.strip():
                    raise GameError("빈 답변을 받았습니다. 다시 보내주세요.", 502)
                image = OBJECTS[topic]["image"] if source_scene == "conversation" and topic in OBJECTS else None
                self._say(state, speaker, reply, image)
                if source_scene == "conversation":
                    state.question_count += 1
                    if topic in TOPICS:
                        state.topic = topic
                        state.image = image
                        state.topic_counts[topic] = state.topic_counts.get(topic, 0) + 1
                        self._discover_dialogue(state, topic)
                        if topic == "drawer1":
                            self._say(state, "narrator", "서랍에서 확인한 건강검진 기록.", "diagnosis")
            if reply:
                state.recent_turns = (state.recent_turns + [{"user": text, "reply": reply, "speaker": speaker, "scene_id": source_scene}])[-6:]
            self._remember_request(state, request_id, fingerprint)
            with self.lock:
                latest = self._get(token)
                if latest.revision != revision or latest.scene_id != source_scene:
                    raise GameError("답변 생성 중 장면이 바뀌었습니다. 최신 화면에서 다시 보내주세요.")
                state.revision += 1
                state.touched = self.clock()
                self.sessions[token] = state
                return self._view(state)
        finally:
            with self.lock:
                self.inflight.discard(token)

    def _remember_request(self, state, request_id, fingerprint):
        if request_id:
            state.completed_requests[request_id] = fingerprint
            while len(state.completed_requests) > 64:
                del state.completed_requests[next(iter(state.completed_requests))]

    def _dialogue_context(self, state, speaker):
        scene = SCENES[state.scene_id]
        # Include only events already shown to this interlocutor. Private mentor
        # exchanges must not become Yoonje's own memory.
        allowed = {key for key, item in SCENES.items()
                   if (item["stage"] == "mentor" if speaker == "mentor" else item["stage"] not in {"intro", "rules", "guide", "selection", "record", "mentor", "intel"})}
        seen = [{"speaker": item["speaker"], "text": item["text"]} for item in state.messages
                if item.get("scene_id") in allowed and item["speaker"] in {speaker, "narrator"}][-12:]
        context = {"id": state.scene_id, "title": scene["title"],
                   **self.dialogue.scenes[state.scene_id], "already_seen": seen,
                   "choices": [{"id": item["id"], "title": item["title"], "number": index + 1,
                                "disabled": item["id"] == "delay" and "delay" in state.warnings,
                                "requires_confirmation": item["id"] == "harvest" or bool(item.get("stop"))}
                               for index, item in enumerate(scene["choices"])]}
        if speaker == "mentor":
            context["target_record"] = self.dialogue.card["background"]
            context["known_rules"] = RULES
        return context

    def _advance(self, state):
        scene = SCENES[state.scene_id]
        if scene["stage"] == "journal":
            raise GameError("판단 근거를 적고 수확일지를 기록해주세요.")
        if not scene["next"] or scene["stage"] == "silence":
            raise GameError("지금은 다음 장면으로 이동할 수 없습니다.")
        if scene["stage"] == "exploration" and len(state.clues) < len(OBJECTS):
            raise GameError("방 안의 다섯 물건을 모두 확인해주세요.")
        self._enter(state, scene["next"])

    def _choose(self, state, value):
        state.pending_choice = None
        scene = SCENES[state.scene_id]
        if not scene["choices"] and scene["stage"] != "decision":
            raise GameError("지금 장면에서는 선택할 수 없습니다.")
        if scene["stage"] == "decision":
            if state.timed_beats < len(TIMED_LINES):
                raise GameError("계율 안내 뒤에 선택할 수 있습니다.")
            if value not in {choice["id"] for choice in FINAL_CHOICES}:
                raise GameError("유효한 선택이 아닙니다.", 400)
            state.choice = value
            state.history.append({"scene": state.scene_id, "choice": value})
            self._finish(state, "choice")
            return
        choice = next((item for item in scene["choices"] if item["id"] == value), None)
        if not choice:
            raise GameError("이 장면에 없는 선택입니다.", 400)
        if value == "delay" and "delay" in state.warnings:
            raise GameError("이미 경고를 받은 선택입니다.")
        state.history.append({"scene": state.scene_id, "choice": value})
        if state.scene_id == "ending_report":
            state.report_answer = "yes" if value == "report_yes" else "no"
        if choice.get("stop"):
            self._finish(state, choice["stop"])
        else:
            self._enter(state, choice["next"], chosen=True)

    def _inspect(self, state, key):
        if key not in OBJECTS:
            raise GameError("조사할 수 없는 물건입니다.", 400)
        if key not in state.clues:
            state.clues.append(key)
            self._say(state, "narrator", OBJECTS[key]["text"])

    def _discover_dialogue(self, state, key):
        if key not in state.dialogue_clues:
            state.dialogue_clues.append(key)

    def _warn(self, state, reason):
        state.warnings.append(reason)
        count = len(state.warnings)
        if count >= 3:
            self._finish(state, "warnings")
        elif count == 2:
            self._say(state, "mentor", "마지막 경고다.")
        elif reason != "delay":
            self._say(state, "mentor", "수확과 상관없는 말 하면 위배자 징계위원회다. 규칙대로 해라. 다 듣고 있다.")

    def _question(self, state, text, topic=None):
        state.question_count += 1
        self._say(state, "user", text)
        reason = warning_reason(text)
        if reason:
            reply = "무슨 말씀인지 모르겠습니다." if reason == "meta" else "수확자님, 올바른 언어를 사용해 주세요."
            self._say(state, "yoonje", reply)
            self._warn(state, reason)
        elif topic in TOPICS:
            state.topic = topic
            state.image = OBJECTS[topic]["image"]
            state.topic_counts[topic] = state.topic_counts.get(topic, 0) + 1
            reply = topic_reply(topic, text, TOPICS[topic]["reply"])
            self._say(state, "yoonje", reply, OBJECTS[topic]["image"])
            if topic == "drawer1":
                self._say(state, "narrator", "서랍에서 확인한 건강검진 기록.", "diagnosis")
            self._discover_dialogue(state, topic)
            if state.topic_counts[topic] == 3:
                self._say(state, "mentor", "같은 물건을 세 번 물었구나. 달력, 서랍, 컴퓨터를 함께 생각해보아라.")
        elif topic == "family":
            self._say(state, "yoonje", "제 아내와 두 딸이 함께 찍은 사진입니다.", "family")
            self._say(state, "mentor", "달력, 서랍, 컴퓨터 위주로 다시 생각해보아라.")
        else:
            self._say(state, "yoonje", "어떤 이야기를 묻는지 조금 더 말씀해주시겠어요? 달력, 병원 서류, 편지나 메일에 관해 물으셔도 됩니다.")
        if state.question_count == 10 and state.scene_id == "conversation":
            self._say(state, "mentor", "시간이 없다. 마무리하라.")

    def _chat(self, state, text):
        text = text.strip()
        if not text or len(text) > 2000:
            raise GameError("1~2000자의 메시지를 입력해주세요.", 400)
        if len(state.messages) >= 600:
            raise GameError("이번 시연의 대화 한도에 도달했습니다. 준비된 선택지로 진행해주세요.", 429)
        if state.scene_id == "conversation":
            topic = first_topic(text)
            if not topic and any(word in normalized(text) for word in ("더이야기", "더자세", "그이야기")):
                topic = state.topic
            self._question(state, text, topic)
            return
        intent = branch_intent(state.scene_id, text)
        if intent:
            self._say(state, "user", text)
            self._choose(state, intent)
        else:
            self._say(state, "user", text)
            reason = warning_reason(text)
            if reason and SCENES[state.scene_id]["stage"] == "allegation":
                self._say(state, "yoonje", "무슨 말씀인지 모르겠습니다.")
                self._warn(state, reason)
            else:
                speaker = "mentor" if state.scene_id == "mentor" else "narrator"
                self._say(state, speaker, "어떤 뜻인지 확실하지 않습니다. 아래 선택지로 의도를 알려주세요.")

    def _view(self, state):
        live = self._live_view(state)
        index = len(state.back_scenes) if state.review_index is None else state.review_index
        reviewing = state.review_index is not None
        view = deepcopy(state.back_scenes[index]) if reviewing else live
        if reviewing:
            # Reading old text must not rewind warnings, clues, choices, journals,
            # recent model turns, request receipts, or the server clock.
            for key in ("run_id", "revision", "history", "clues", "dialogue_clues", "clue_count", "warn_count",
                        "question_count", "lantern_on", "final_choice", "choice_title", "stop_reason", "ending_status",
                        "ending_reason", "ending_grade", "report_answer", "journal", "time_left",
                        "last_request_id"):
                view[key] = live[key]
            view.update(input=False, dialogue_enabled=False, choices=[], topics=[], can_advance=False, confirmation=None)
        view.update(reviewing=reviewing, can_back=index > 0, can_forward=reviewing,
                    back_title=state.back_scenes[index - 1]["title"] if index > 0 else None,
                    forward_is_current=reviewing and index + 1 == len(state.back_scenes))
        return view

    def _live_view(self, state):
        scene = SCENES[state.scene_id]
        now = self.clock()
        elapsed = now - state.decision_started if state.scene_id == "decision" else state.decision_elapsed
        choices = [{"id": item["id"], "title": item["title"],
                    "disabled": item["id"] == "delay" and "delay" in state.warnings}
                   for item in scene["choices"]]
        ready = state.scene_id == "decision" and state.timed_beats == len(TIMED_LINES)
        if ready:
            choices = FINAL_CHOICES
        objects = [{"id": key, **item, "image": image_url(item["image"]),
                    "extra_image": image_url(item.get("extra_image"))} for key, item in OBJECTS.items()]
        visible_objects = objects if scene["stage"] in {"exploration", "conversation", "intel", "allegation", "decision", "pending"} else []
        selected = next((item for item in FINAL_CHOICES if item["id"] == state.choice), None)
        stage = scene["stage"]
        result = ENDING_TYPES.get(state.ending_type) if stage in {"result", "reflection"} else None
        ending_status = ("complete" if stage in {"reflection", "bad_result"} else
                         "in_progress" if scene.get("ending") else "not_started")
        return deepcopy({
            "run_id": state.run_id,
            "stage": scene["stage"], "scene_id": state.scene_id,
            "title": self.dialogue.card["scene"]["title"] if self.dialogue and state.scene_id == "conversation" else scene["title"],
            "revision": state.revision, "image": image_url(state.image),
            "video": scene.get("video"), "video_sound": bool(scene.get("video_sound")),
            "numbered_choices": scene.get("numbered_choices", True),
            "messages": state.messages[state.scene_start:], "history": state.history,
            "choices": choices, "can_advance": bool(scene["next"]) and stage not in {"silence", "journal"},
            "advance_label": scene.get("advance_label"), "reveal": bool(scene.get("reveal")),
            "input": bool(scene.get("input")), "objects": visible_objects,
            "dialogue_enabled": bool(self.dialogue and scene.get("input")),
            "clues": [item for item in objects if item["id"] in state.clues],
            "dialogue_clues": [{"id": key, "title": DIALOGUE_CLUES[key]} for key in state.dialogue_clues],
            "clue_count": len(state.dialogue_clues), "warn_count": len(state.warnings),
            "question_count": state.question_count, "lantern_on": state.lantern_on,
            "topics": [{"id": key, "question": item["question"]} for key, item in TOPICS.items()] if scene["stage"] == "conversation" else [],
            "rules": RULES, "portraits": {key: image_url(key) for key in ("mentor", "yoonje", "logo")},
            "time_left": max(0, 60 - elapsed) if state.decision_started is not None else None,
            "silent_remaining": max(0, scene["duration"] - (now - state.entered_at)) if scene["stage"] == "silence" else None,
            "decision_ready": ready, "final_choice": state.choice, "choice_title": selected["title"] if selected else None,
            "stop_reason": state.stop_reason, "ending_status": ending_status,
            "ending_reason": state.ending_reason, "ending_grade": state.ending_grade,
            "report_answer": state.report_answer, "result": result,
            "journal": state.journal, "journal_subject": scene.get("journal_subject"),
            "mode": self.dialogue.mode if self.dialogue else "scripted_demo",
            "character_name": self.dialogue.card["name"] if self.dialogue else "이윤제",
            "last_request_id": next(reversed(state.completed_requests), None),
            "confirmation": next(({"id": item["id"], "title": item["title"]} for item in scene["choices"]
                                  if item["id"] == state.pending_choice), None),
        })

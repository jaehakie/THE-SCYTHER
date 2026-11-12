"""Story event boundaries for scene navigation; independent of ending rules."""

from .story import SCENES


EVENT_SCENES = {
    "preparation": ("intro1", "intro2", "intro3", "intro_reaper", "intro4", "intro5", "rules", "guide"),
    "assignment": ("selection", "record", "mentor", "mentor_doubt", "mentor_send", "mentor_delay", "mentor_follow"),
    "approach": ("window", "knock", "waiting", "delivery_call"),
    "entry": ("entry_truth", "broken_door", "entry_plea", "entry_listen", "children_check", "tea_offer"),
    "exploration": ("exploration",),
    "conversation": ("conversation",),
    "investigation": ("intel", "allegation", "allegation_shock", "denial", "cup_ring", "hesitation", "wife_ring",
                      "wife_story", "wife_tears", "wife_question", "wife_averted", "rush", "family_plea", "defense", "kneel_tears"),
    "decision": ("daughters", "decision"),
}
SCENE_EVENTS = {scene_id: event for event, scenes in EVENT_SCENES.items() for scene_id in scenes}


def event_key(scene_id):
    scene = SCENES[scene_id]
    if scene_id in SCENE_EVENTS:
        return SCENE_EVENTS[scene_id]
    if scene["stage"] in {"result", "reflection", "bad_result"}:
        return "result"
    if scene["stage"] == "journal":
        return "journal"
    if scene.get("ending"):
        return "ending"
    return scene_id


def locks_back(source, target, *, chosen=False):
    """A choice, event boundary, or timed scene starts a fresh navigation section."""
    timed = {"silence", "decision"}
    return chosen or event_key(source) != event_key(target) or bool(
        timed & {SCENES[source]["stage"], SCENES[target]["stage"]})

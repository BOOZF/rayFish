import asyncio
import sys
from pathlib import Path

from camel.memories.records import MemoryRecord
from camel.messages import BaseMessage
from camel.types import OpenAIBackendRole
from oasis.social_platform.platform_utils import PlatformUtils

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from oasis_limits import (  # noqa: E402
    FEED_MESSAGE_PREFIX,
    FEED_REMOVED_MESSAGE,
    apply_limits,
    cap_comments,
    strip_old_feeds,
)


def test_cap_comments_keeps_newest():
    posts = [{"comments": [{"comment_id": i} for i in range(12)]}, {"comments": []}, {}]
    cap_comments(posts, limit=3)
    assert [c["comment_id"] for c in posts[0]["comments"]] == [9, 10, 11]
    assert posts[1]["comments"] == []


def _record(role, make_message, content):
    return MemoryRecord(
        message=make_message(role.value, content), role_at_backend=role
    ).to_dict()


def test_strip_old_feeds_only_changes_stored_feeds():
    feed = _record(OpenAIBackendRole.USER, BaseMessage.make_user_message, f"{FEED_MESSAGE_PREFIX} big feed")
    question = _record(OpenAIBackendRole.USER, BaseMessage.make_user_message, "What do you think?")
    reply = _record(OpenAIBackendRole.ASSISTANT, BaseMessage.make_assistant_message, f"{FEED_MESSAGE_PREFIX} quoted")
    strip_old_feeds([feed, question, reply])
    assert feed["message"]["content"] == FEED_REMOVED_MESSAGE
    assert question["message"]["content"] == "What do you think?"
    assert reply["message"]["content"].endswith("quoted")


def test_apply_limits_patches_oasis(monkeypatch):
    from oasis.social_agent.agent import SocialAgent

    records = [_record(OpenAIBackendRole.USER, BaseMessage.make_user_message, f"{FEED_MESSAGE_PREFIX} feed")]

    class Agent:
        memory = type("M", (), {"_chat_history_block": type("B", (), {"storage": type("S", (), {"memory_list": records})})})

    async def fails(self):
        raise RuntimeError("step failed")

    monkeypatch.setattr(SocialAgent, "perform_action_by_llm", fails)
    monkeypatch.setattr(PlatformUtils, "_add_comments_to_posts", lambda self, rows: [{"comments": list(range(20))}])
    apply_limits()

    assert len(PlatformUtils._add_comments_to_posts(None, [])[0]["comments"]) == 8
    try:
        asyncio.run(SocialAgent.perform_action_by_llm(Agent()))
    except RuntimeError:
        pass
    assert records[0]["message"]["content"] == FEED_REMOVED_MESSAGE

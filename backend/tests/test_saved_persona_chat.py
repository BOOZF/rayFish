import json

import pytest

from app.services.saved_persona_chat import answer_from_saved_data, has_saved_activity


class FakeLLM:
    def __init__(self, replies):
        self.replies = list(replies)
        self.messages = []

    def chat(self, messages, **kwargs):
        self.messages.append(messages)
        return self.replies.pop(0)


@pytest.fixture
def sim_dir(tmp_path):
    (tmp_path / "reddit_profiles.json").write_text(
        json.dumps(
            [
                {"name": "Aisyah", "persona": "A careful condo buyer."},
                {"name": "Bala", "persona": "A furniture seller."},
            ]
        )
    )
    actions = {
        "twitter": [
            {"agent_id": 0, "round": 3, "action_type": "QUOTE_POST", "action_args": {"quote_content": "Check the postcode."}},
            {"agent_id": 1, "round": 4, "action_type": "CREATE_POST", "action_args": {"content": "Bala twitter post"}},
        ],
        "reddit": [
            {"event_type": "simulation_start"},
            {"agent_id": 0, "round": 5, "action_type": "CREATE_COMMENT", "action_args": {"content": "Test the delete button."}},
            {"agent_id": 0, "round": 6, "action_type": "LIKE_POST", "action_args": {"post_id": 1}},
        ],
    }
    for platform, rows in actions.items():
        (tmp_path / platform).mkdir()
        (tmp_path / platform / "actions.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows)
        )
    return str(tmp_path)


def test_reply_uses_only_that_personas_activity_from_both_platforms(sim_dir):
    llm = FakeLLM(["I would check first."])

    data = answer_from_saved_data(
        sim_dir, [{"agent_id": 0, "prompt": "Would you stay?"}], llm=llm
    )

    answer = data["result"]["results"]["saved_0"]
    assert answer["response"] == "I would check first."
    assert answer["reconstructed"] is True
    system, user = llm.messages[0]
    assert "Check the postcode." in system["content"]
    assert "Test the delete button." in system["content"]
    assert "A careful condo buyer." in system["content"]
    assert "Bala twitter post" not in system["content"]
    assert user["content"] == "Would you stay?"


def test_empty_model_reply_is_retried(sim_dir):
    llm = FakeLLM(["", "  ", "Second thoughts."])

    data = answer_from_saved_data(sim_dir, [{"agent_id": 0, "prompt": "Why?"}], llm=llm)

    assert data["result"]["results"]["saved_0"]["response"] == "Second thoughts."


def test_all_empty_replies_raise_instead_of_returning_blank(sim_dir):
    llm = FakeLLM(["", "", ""])

    with pytest.raises(RuntimeError):
        answer_from_saved_data(sim_dir, [{"agent_id": 0, "prompt": "Why?"}], llm=llm)


def test_unknown_agent_is_rejected(sim_dir):
    with pytest.raises(ValueError):
        answer_from_saved_data(sim_dir, [{"agent_id": 9, "prompt": "Hi"}], llm=FakeLLM([]))


def test_has_saved_activity(sim_dir, tmp_path_factory):
    assert has_saved_activity(sim_dir) is True
    assert has_saved_activity(str(tmp_path_factory.mktemp("empty"))) is False

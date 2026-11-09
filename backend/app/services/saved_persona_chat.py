"""Answer persona questions from saved run data after the simulation process has closed.

These replies are reconstructed: a new model call reads the persona's profile and
saved actions. It is not the agent that lived through the run.
"""

import csv
import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from ..utils.llm_client import LLMClient

PLATFORMS = ("twitter", "reddit")
TEXT_ACTIONS = {"CREATE_POST", "QUOTE_POST", "CREATE_COMMENT"}
MAX_PERSONA_CHARS = 6000
MAX_ACTIONS_PER_PLATFORM = 40
MAX_ACTION_CHARS = 700
EMPTY_REPLY_ATTEMPTS = 3
MAX_WORKERS = 5


def has_saved_activity(sim_dir: str) -> bool:
    return any(
        os.path.exists(os.path.join(sim_dir, platform, "actions.jsonl"))
        for platform in PLATFORMS
    )


def _load_profiles(sim_dir: str) -> List[Dict[str, Any]]:
    reddit_path = os.path.join(sim_dir, "reddit_profiles.json")
    if os.path.exists(reddit_path):
        with open(reddit_path, encoding="utf-8") as f:
            return json.load(f)

    twitter_path = os.path.join(sim_dir, "twitter_profiles.csv")
    if os.path.exists(twitter_path):
        with open(twitter_path, encoding="utf-8", newline="") as f:
            return [
                {
                    "name": row.get("name", ""),
                    "bio": row.get("description", ""),
                    "persona": row.get("user_char", ""),
                }
                for row in csv.DictReader(f)
            ]

    return []


def _action_text(action: Dict[str, Any]) -> str:
    args = action.get("action_args") or {}
    return args.get("quote_content") or args.get("content") or ""


def _load_activity(sim_dir: str, agent_id: int) -> Dict[str, List[str]]:
    activity: Dict[str, List[str]] = {}
    for platform in PLATFORMS:
        path = os.path.join(sim_dir, platform, "actions.jsonl")
        if not os.path.exists(path):
            continue

        lines = []
        with open(path, encoding="utf-8") as f:
            for raw_line in f:
                action = json.loads(raw_line)
                if action.get("agent_id") != agent_id:
                    continue
                text = _action_text(action)
                if action.get("action_type") in TEXT_ACTIONS and text:
                    lines.append(
                        f"Round {action.get('round')}, {action['action_type']}: "
                        f"{text[:MAX_ACTION_CHARS]}"
                    )
        activity[platform] = lines[-MAX_ACTIONS_PER_PLATFORM:]
    return activity


def _build_messages(
    profile: Dict[str, Any],
    activity: Dict[str, List[str]],
    question: str,
) -> List[Dict[str, str]]:
    persona = profile.get("persona") or profile.get("bio") or ""
    sections = []
    for platform, lines in activity.items():
        body = "\n".join(lines) if lines else "(no written posts or comments)"
        sections.append(f"What you wrote on {platform.capitalize()}:\n{body}")

    system = (
        f"You are {profile.get('name') or 'this persona'}, a simulated persona from a "
        "market simulation. You are not a real person. Stay in character.\n\n"
        f"Your profile:\n{persona[:MAX_PERSONA_CHARS]}\n\n"
        + "\n\n".join(sections)
        + "\n\nBase your answer on this profile and what you wrote. Don't invent posts, "
        "purchases, test results or experiences that aren't listed. If your saved activity "
        "doesn't cover the question, say so, then give the view your profile suggests. "
        "Reply in the language of the question, in under 150 words."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]


def _answer_one(
    llm: LLMClient,
    sim_dir: str,
    profiles: List[Dict[str, Any]],
    interview: Dict[str, Any],
) -> Dict[str, Any]:
    agent_id = interview["agent_id"]
    if not 0 <= agent_id < len(profiles):
        raise ValueError(f"Unknown agent_id: {agent_id}")

    messages = _build_messages(
        profiles[agent_id],
        _load_activity(sim_dir, agent_id),
        interview["prompt"],
    )
    reply = ""
    for _ in range(EMPTY_REPLY_ATTEMPTS):
        reply = (llm.chat(messages=messages, temperature=0.7, max_tokens=4000) or "").strip()
        if reply:
            break
    if not reply:
        raise RuntimeError(f"The model returned no reply for agent {agent_id}")

    return {
        "agent_id": agent_id,
        "response": reply,
        "platform": "saved",
        "reconstructed": True,
    }


def answer_from_saved_data(
    sim_dir: str,
    interviews: List[Dict[str, Any]],
    llm: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """Return the same shape as a batch interview, with results keyed `saved_<agent_id>`."""
    llm = llm or LLMClient()
    profiles = _load_profiles(sim_dir)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        answers = list(
            pool.map(lambda item: _answer_one(llm, sim_dir, profiles, item), interviews)
        )

    return {
        "success": True,
        "reconstructed": True,
        "result": {
            "interviews_count": len(answers),
            "results": {f"saved_{a['agent_id']}": a for a in answers},
        },
    }

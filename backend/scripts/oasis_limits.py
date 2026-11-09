"""Keep long OASIS runs from growing without limit.

OASIS stores every feed an agent reads in that agent's chat history and sends
the whole history on each turn. Long runs then use tens of GB of memory and hit
LLM rate limits. These limits keep what the agent did, so interviews still work,
and drop the old feeds and excess comments.
"""

from functools import wraps

MAX_COMMENTS_PER_POST = 8
FEED_MESSAGE_PREFIX = "Please perform social media actions after observing"
FEED_REMOVED_MESSAGE = "Please perform social media actions. [Earlier feed removed.]"


def cap_comments(posts, limit=MAX_COMMENTS_PER_POST):
    """Keep only the newest comments on each post."""
    for post in posts:
        comments = post.get("comments")
        if comments and len(comments) > limit:
            post["comments"] = comments[-limit:]
    return posts


def strip_old_feeds(records):
    """Replace stored feed text in chat history records, leaving other records as they are."""
    for record in records:
        message = record.get("message", {})
        content = message.get("content")
        if (
            record.get("role_at_backend") == "user"
            and isinstance(content, str)
            and content.startswith(FEED_MESSAGE_PREFIX)
        ):
            message["content"] = FEED_REMOVED_MESSAGE


def apply_limits():
    """Patch OASIS once, before any agents run."""
    from oasis.social_agent.agent import SocialAgent
    from oasis.social_platform.platform_utils import PlatformUtils

    original_add_comments = PlatformUtils._add_comments_to_posts
    original_perform_action = SocialAgent.perform_action_by_llm

    @wraps(original_add_comments)
    def add_comments_with_cap(self, posts_results):
        return cap_comments(original_add_comments(self, posts_results))

    @wraps(original_perform_action)
    async def perform_action_then_strip_feed(self):
        try:
            return await original_perform_action(self)
        finally:
            strip_old_feeds(self.memory._chat_history_block.storage.memory_list)

    PlatformUtils._add_comments_to_posts = add_comments_with_cap
    SocialAgent.perform_action_by_llm = perform_action_then_strip_feed

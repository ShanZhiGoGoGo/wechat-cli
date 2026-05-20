"""Shared command option filters."""

import click

from ..core.messages import msg_type_matches

BOOL_CHOICE = click.Choice(("true", "false"))
MSG_TYPE_CHOICE = click.Choice((
    "text", "image", "voice", "video", "sticker",
    "location", "link", "file", "call", "system",
))


def parse_bool_option(value):
    if value is None:
        return None
    return value == "true"


def matches_chat_filter(username, display_name, chat):
    chat = (chat or "").strip()
    if not chat:
        return True
    chat_lower = chat.lower()
    return (
        chat_lower == (username or "").lower()
        or chat_lower == (display_name or "").lower()
        or chat_lower in (display_name or "").lower()
    )


def matches_is_group(username, expected):
    expected = parse_bool_option(expected)
    if expected is None:
        return True
    return ("@chatroom" in (username or "")) == expected


def matches_unread(unread_count, expected):
    expected = parse_bool_option(expected)
    if expected is None:
        return True
    return ((unread_count or 0) > 0) == expected


def matches_session_filters(username, display_name, unread_count, raw_msg_type, chat=None, is_group=None, unread=None, msg_type=None):
    return (
        matches_chat_filter(username, display_name, chat)
        and matches_is_group(username, is_group)
        and matches_unread(unread_count, unread)
        and (not msg_type or msg_type_matches(raw_msg_type, msg_type))
    )

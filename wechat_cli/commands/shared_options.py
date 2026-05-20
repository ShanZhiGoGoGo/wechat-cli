"""Shared Click option definitions with consistent metavar and help text."""

import click

from .filters import BOOL_CHOICE, MSG_TYPE_CHOICE
from ..output.formatter import QUERY_FORMATS, EXPORT_FORMATS, INIT_FORMATS


def add_common_options(*, pagination=False, chat=False, is_group=False,
                      msg_type=False, unread=False, time_range=False,
                      query=False, detail=False, media=False,
                      query_formats=True, export_formats=False, init_formats=False):
    """Decorator factory that adds commonly-used options with unified help text.

    Uses metavar="" to hide Click's default type hints; all type info
    goes in the help description instead.
    """
    def decorator(func):
        if pagination:
            click.option("--limit", metavar="", default=20, help="返回数量 (默认 20)")(func)
            click.option("--offset", metavar="", default=0, help="分页偏移量 (默认 0)")(func)
        if chat:
            click.option("--chat", metavar="", default="", help="按聊天名或 username 过滤")(func)
        if is_group:
            click.option("--is-group", "is_group_filter", default=None, type=BOOL_CHOICE, help="群聊过滤 (true/false)")(func)
        if msg_type:
            click.option("--msg-type", "msg_type_filter", default=None, type=MSG_TYPE_CHOICE,
                         metavar="", help="消息类型: text, image, voice, video, sticker, location, link, file, call, system")(func)
        if unread:
            click.option("--unread", "unread_filter", default=None, type=BOOL_CHOICE, help="未读过滤 (true/false)")(func)
        if time_range:
            click.option("--from", "from_time", metavar="", default="", help="起始时间 (YYYY-MM-DD [HH:MM[:SS]])")(func)
            click.option("--to", "to_time", metavar="", default="", help="结束时间 (YYYY-MM-DD [HH:MM[:SS]])")(func)
        if query:
            click.option("--query", metavar="", default=None, help="搜索关键词")(func)
        if detail:
            click.option("--detail", metavar="", default=None, help="查看联系人详情 (传入昵称/备注/wxid)")(func)
        if media:
            click.option("--media", is_flag=True, help="解析媒体文件路径")(func)
        if query_formats:
            click.option("--format", "fmt", default="json", type=click.Choice(QUERY_FORMATS),
                         metavar="", help="输出格式: json, ndjson, table, text (默认 json)")(func)
        if export_formats:
            click.option("--format", "fmt", default="markdown", type=click.Choice(EXPORT_FORMATS),
                         metavar="", help="导出格式: markdown, txt, json, ndjson (默认 markdown)")(func)
        if init_formats:
            click.option("--format", "fmt", default="text", type=click.Choice(INIT_FORMATS),
                         metavar="", help="输出格式: text, json (默认 text)")(func)
        click.option("--fields", metavar="", default=None, help="字段选择器 (逗号分隔)")(func)
        return func
    return decorator

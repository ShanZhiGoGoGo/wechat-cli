"""search-messages 命令"""

import os
import sqlite3
from contextlib import closing

import click

from ..core.contacts import get_contact_names
from ..core.messages import (
    MSG_TYPE_FILTERS,
    MSG_TYPE_NAMES,
    collect_chat_search,
    parse_time_range,
    resolve_chat_context,
    resolve_chat_contexts,
    search_all_messages,
    validate_pagination,
    _candidate_page_size,
    _page_ranked_entries,
)
from .filters import BOOL_CHOICE, SESSION_MSG_TYPE_CHOICE, matches_is_group, parse_bool_option
from ..output.formatter import Column, QUERY_FORMATS, render_result


@click.command("search")
@click.argument("keyword")
@click.option("--chat", multiple=True, help="限定聊天对象（可多次指定）")
@click.option("--start-time", default="", help="起始时间")
@click.option("--end-time", default="", help="结束时间")
@click.option("--limit", default=20, help="返回数量（最大500）")
@click.option("--offset", default=0, help="分页偏移量")
@click.option("--format", "fmt", default="json", type=click.Choice(QUERY_FORMATS), help="输出格式")
@click.option("--type", "msg_type", default=None, type=click.Choice(MSG_TYPE_NAMES), help="消息类型过滤")
@click.option("--msg-type", "new_msg_type", default=None, type=SESSION_MSG_TYPE_CHOICE, help="消息类型过滤: text/link/file")
@click.option("--is-group", default=None, type=BOOL_CHOICE, help="是否只搜索群聊: true/false")
@click.option("--unread", default=None, type=BOOL_CHOICE, help="是否只搜索有未读的会话: true/false")
@click.pass_context
def search(ctx, keyword, chat, start_time, end_time, limit, offset, fmt, msg_type, new_msg_type, is_group, unread):
    """搜索消息内容

    \b
    示例:
      wechat-cli search "Claude"                         # 全局搜索
      wechat-cli search "Claude" --chat "AI交流群"        # 在指定群搜索
      wechat-cli search "开会" --chat "群A" --chat "群B"  # 同时搜多个群
      wechat-cli search "Claude" --is-group true --unread true
      wechat-cli search "你好" --start-time "2026-04-01" --limit 50
    """
    app = ctx.obj

    try:
        validate_pagination(limit, offset)
        start_ts, end_ts = parse_time_range(start_time, end_time)
        if msg_type and new_msg_type and msg_type != new_msg_type:
            raise ValueError("--type 和 --msg-type 不能同时指定不同的消息类型")
    except ValueError as e:
        click.echo(f"错误: {e}", err=True)
        ctx.exit(2)

    names = get_contact_names(app.cache, app.decrypted_dir)
    candidate_limit = _candidate_page_size(limit, offset)
    chat_names = list(chat)
    effective_msg_type = new_msg_type or msg_type
    type_filter = MSG_TYPE_FILTERS[effective_msg_type] if effective_msg_type else None
    unread_usernames = _load_unread_usernames(app, ctx) if unread is not None else None

    if len(chat_names) == 1:
        # 单聊搜索
        chat_ctx = resolve_chat_context(chat_names[0], app.msg_db_keys, app.cache, app.decrypted_dir)
        if not chat_ctx:
            click.echo(f"找不到聊天对象: {chat_names[0]}", err=True)
            ctx.exit(1)
        if not chat_ctx['db_path']:
            click.echo(f"找不到 {chat_ctx['display_name']} 的消息记录", err=True)
            ctx.exit(1)
        if _matches_context_filters(chat_ctx, is_group, unread, unread_usernames):
            entries, failures = collect_chat_search(
                chat_ctx, names, keyword, app.display_name_fn,
                start_ts=start_ts, end_ts=end_ts, candidate_limit=candidate_limit,
                msg_type_filter=type_filter,
            )
        else:
            entries, failures = [], []
        scope = chat_ctx['display_name']

    elif len(chat_names) > 1:
        # 多聊搜索
        resolved, unresolved, missing = resolve_chat_contexts(chat_names, app.msg_db_keys, app.cache, app.decrypted_dir)
        if not resolved:
            click.echo("错误: 没有可查询的聊天对象", err=True)
            ctx.exit(1)
        entries = []
        failures = []
        resolved = [rc for rc in resolved if _matches_context_filters(rc, is_group, unread, unread_usernames)]
        for rc in resolved:
            e, f = collect_chat_search(
                rc, names, keyword, app.display_name_fn,
                start_ts=start_ts, end_ts=end_ts, candidate_limit=candidate_limit,
                msg_type_filter=type_filter,
            )
            entries.extend(e)
            failures.extend(f)
        if unresolved:
            failures.append("未找到: " + "、".join(unresolved))
        scope = f"{len(resolved)} 个聊天对象"

    else:
        # 全局搜索
        entries, failures = search_all_messages(
            app.msg_db_keys, app.cache, names, keyword, app.display_name_fn,
            start_ts=start_ts, end_ts=end_ts, candidate_limit=candidate_limit,
            msg_type_filter=type_filter,
            context_filter=lambda search_ctx: _matches_context_filters(search_ctx, is_group, unread, unread_usernames),
        )
        scope = "全部消息"

    paged = _page_ranked_entries(entries, limit, offset)

    result_lines = [item[1] for item in paged]
    data = {
        'scope': scope,
        'keyword': keyword,
        'count': len(paged),
        'offset': offset,
        'limit': limit,
        'start_time': start_time or None,
        'end_time': end_time or None,
        'type': effective_msg_type or None,
        'results': result_lines,
        'failures': failures if failures else None,
    }
    records_key = 'results'
    if fmt in ('ndjson', 'table'):
        data = {**data, 'result_records': [{'result': line} for line in result_lines]}
        records_key = 'result_records'
    render_result(
        data, fmt, records_key=records_key,
        columns=[Column("result", "RESULT", min_width=40, max_width=120)],
        text_fn=_format_search_text,
    )


def _load_unread_usernames(app, ctx):
    path = app.cache.get(os.path.join("session", "session.db"))
    if not path:
        click.echo("错误: 无法解密 session.db", err=True)
        ctx.exit(3)
    unread_usernames = set()
    with closing(sqlite3.connect(path)) as conn:
        rows = conn.execute("SELECT username, unread_count FROM SessionTable").fetchall()
    for username, unread_count in rows:
        if unread_count and unread_count > 0:
            unread_usernames.add(username)
    return unread_usernames


def _matches_context_filters(search_ctx, is_group, unread, unread_usernames):
    username = search_ctx.get('username', '')
    if not matches_is_group(username, is_group):
        return False
    expected_unread = parse_bool_option(unread)
    if expected_unread is None:
        return True
    return (username in (unread_usernames or set())) == expected_unread


def _format_search_text(data):
    if not data['results']:
        return f"在 {data['scope']} 中未找到包含 \"{data['keyword']}\" 的消息"
    header = (
        f"在 {data['scope']} 中搜索 \"{data['keyword']}\" 找到 {data['count']} 条结果"
        f"（offset={data['offset']}, limit={data['limit']}）"
    )
    if data['start_time'] or data['end_time']:
        header += f"\n时间范围: {data['start_time'] or '最早'} ~ {data['end_time'] or '最新'}"
    if data['failures']:
        header += "\n查询失败: " + "；".join(data['failures'])
    return header + ":\n\n" + "\n\n".join(data['results'])

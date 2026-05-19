"""get-chat-history 命令"""

import click

from ..core.contacts import get_contact_names
from ..core.messages import (
    MSG_TYPE_FILTERS,
    MSG_TYPE_NAMES,
    collect_chat_history,
    parse_time_range,
    resolve_chat_context,
    validate_pagination,
)
from ..output.formatter import Column, QUERY_FORMATS, render_result


@click.command("history")
@click.argument("chat_name")
@click.option("--limit", default=50, help="返回的消息数量")
@click.option("--offset", default=0, help="分页偏移量")
@click.option("--start-time", default="", help="起始时间 YYYY-MM-DD [HH:MM[:SS]]")
@click.option("--end-time", default="", help="结束时间 YYYY-MM-DD [HH:MM[:SS]]")
@click.option("--format", "fmt", default="json", type=click.Choice(QUERY_FORMATS), help="输出格式")
@click.option("--type", "msg_type", default=None, type=click.Choice(MSG_TYPE_NAMES), help="消息类型过滤")
@click.option("--media", is_flag=True, help="解析媒体文件路径（图片/文件/视频/语音）")
@click.pass_context
def history(ctx, chat_name, limit, offset, start_time, end_time, fmt, msg_type, media):
    """获取指定聊天的消息记录

    \b
    示例:
      wechat-cli history "张三"                          # 最近 50 条消息
      wechat-cli history "张三" --limit 100 --offset 50  # 分页查询
      wechat-cli history "AI交流群" --start-time "2026-04-01" --end-time "2026-04-02"
      wechat-cli history "张三" --format table            # 表格输出
    """
    app = ctx.obj

    try:
        validate_pagination(limit, offset, limit_max=None)
        start_ts, end_ts = parse_time_range(start_time, end_time)
    except ValueError as e:
        click.echo(f"错误: {e}", err=True)
        ctx.exit(2)

    chat_ctx = resolve_chat_context(chat_name, app.msg_db_keys, app.cache, app.decrypted_dir)
    if not chat_ctx:
        click.echo(f"找不到聊天对象: {chat_name}", err=True)
        ctx.exit(1)
    if not chat_ctx['db_path']:
        click.echo(f"找不到 {chat_ctx['display_name']} 的消息记录", err=True)
        ctx.exit(1)

    names = get_contact_names(app.cache, app.decrypted_dir)
    type_filter = MSG_TYPE_FILTERS[msg_type] if msg_type else None
    lines, failures = collect_chat_history(
        chat_ctx, names, app.display_name_fn,
        start_ts=start_ts, end_ts=end_ts, limit=limit, offset=offset,
        msg_type_filter=type_filter, resolve_media=media, db_dir=app.db_dir,
    )

    data = {
        'chat': chat_ctx['display_name'],
        'username': chat_ctx['username'],
        'is_group': chat_ctx['is_group'],
        'count': len(lines),
        'offset': offset,
        'limit': limit,
        'start_time': start_time or None,
        'end_time': end_time or None,
        'type': msg_type or None,
        'messages': lines,
        'failures': failures if failures else None,
    }
    records_key = 'messages'
    if fmt in ('ndjson', 'table'):
        data = {**data, 'message_records': [{'message': line} for line in lines]}
        records_key = 'message_records'
    render_result(
        data, fmt, records_key=records_key,
        columns=[Column("message", "MESSAGE", min_width=40, max_width=120)],
        text_fn=_format_history_text,
    )


def _format_history_text(data):
    header = f"{data['chat']} 的消息记录（返回 {data['count']} 条，offset={data['offset']}, limit={data['limit']}）"
    if data['is_group']:
        header += " [群聊]"
    if data['start_time'] or data['end_time']:
        header += f"\n时间范围: {data['start_time'] or '最早'} ~ {data['end_time'] or '最新'}"
    if data['failures']:
        header += "\n查询失败: " + "；".join(data['failures'])
    if data['messages']:
        return header + ":\n\n" + "\n".join(data['messages'])
    return f"{data['chat']} 无消息记录"

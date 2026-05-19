"""members 命令 — 查询群聊成员列表"""

import click

from ..core.contacts import get_contact_names, resolve_username, get_group_members
from ..output.formatter import Column, QUERY_FORMATS, render_result


@click.command("members")
@click.argument("group_name")
@click.option("--format", "fmt", default="json", type=click.Choice(QUERY_FORMATS), help="输出格式")
@click.pass_context
def members(ctx, group_name, fmt):
    """查询群聊成员列表

    \b
    示例:
      wechat-cli members "AI交流群"
      wechat-cli members "群名" --format table
    """
    app = ctx.obj

    username = resolve_username(group_name, app.cache, app.decrypted_dir)
    if not username:
        click.echo(f"找不到: {group_name}", err=True)
        ctx.exit(1)

    if '@chatroom' not in username:
        click.echo(f"{group_name} 不是一个群聊", err=True)
        ctx.exit(1)

    names = get_contact_names(app.cache, app.decrypted_dir)
    display_name = names.get(username, username)

    result = get_group_members(username, app.cache, app.decrypted_dir)

    data = {
        'group': display_name,
        'username': username,
        'member_count': len(result['members']),
        'owner': result['owner'],
        'members': result['members'],
    }
    render_result(
        data, fmt, records_key='members',
        columns=[
            Column("display_name", "DISPLAY NAME", min_width=12, max_width=28),
            Column("username", "USERNAME", min_width=16, max_width=32),
            Column("remark", "REMARK", min_width=8, max_width=24),
            Column("nick_name", "NICK", min_width=8, max_width=24),
        ],
        text_fn=_format_members_text,
    )


def _format_members_text(data):
    lines = []
    for m in data['members']:
        line = f"{m['display_name']}  ({m['username']})"
        if m['remark']:
            line += f"  备注: {m['remark']}"
        lines.append(line)
    header = f"{data['group']} 的群成员（共 {data['member_count']} 人）"
    if data['owner']:
        header += f"，群主: {data['owner']}"
    return header + ":\n\n" + "\n".join(lines)

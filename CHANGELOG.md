# Changelog

## 2026-05-19

- Add `--schema` flag to all commands — outputs JSON schema and exits without querying
- Add `total` and `has_more` to paginated output (sessions, history, search, contacts, unread, favorites, new-messages)
- Add `--fields` selector to query commands — comma-separated field filter for JSON/NDJSON output
- Unify `--msg-type` across all commands with full 10-value choice (text/image/voice/video/sticker/location/link/file/call/system); `--type` kept as deprecated alias on history/search
- Add `--limit` to `new-messages` and `members` commands
- Unify help text — remove `INTEGER`/`TEXT` metavar, use clean descriptions with defaults and value lists
- Add ndjson and table output formats (new `output_ndjson`, `output_table`, `Column` in formatter.py)
- Add search keyword highlighting in text/table output (yellow bg, black fg); respects NO\_COLOR and non-TTY
- Add colored `warning:` prefix for deprecation messages (yellow bold on TTY)
- Fix time format inconsistency — unify to `YYYY-MM-DD HH:MM` across all commands (sessions, unread, new-messages, favorites, history, search)
- Fix `--fields` + text/table format causing KeyError — `filter_fields` now only applies to json/ndjson
- Fix `isinstance(data, 'dict')` typo in formatter.py

## 2026-04-06

- docs: add acknowledgement to wechat-decrypt (a378923)
- docs: add Full Disk Access prerequisite for macOS (1eced78)

## 2026-04-05

- docs: add system requirements (macOS ≥ 26.3.1, WeChat ≤ 4.1.8.100) (019ef4e)

## 2026-04-04

- Add --media flag to resolve media file paths for images/files/videos (v0.2.4) (f6410d3)
- Add safety notice and disclaimer to both READMEs (86590e7)
- Add re-signing safety notice: no ban risk, may affect auto-update (7b9139b)
- Preserve WeChat original entitlements when re-signing (v0.2.3) (7158422)
- Add version command, bump to 0.2.2 (b794ad1)
- Add update instructions and macOS task\_for\_pid troubleshooting to READMEs (ab890df)
- Bump version to 0.2.1 with auto re-sign support (6b36f92)
- Auto re-sign WeChat when task\_for\_pid fails on macOS (2b1fc0a)
- Sync Agent installation guide and init screenshots to English README (3d75bde)
- Add Agent installation guide and init screenshots to README\_CN (c14b8dc)
- Redesign READMEs: add badges, AI agent guides, npm as recommended install (e6f79af)
- Add npm distribution support with PyInstaller binary (f51e89c)
- Initial release: wechat-cli v0.2.0 (e64006b)


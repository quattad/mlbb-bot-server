# Suggest Heroes: Multi-Step Conversation Design

## Overview

Replace the single-message `/team_counter` command with a multi-step `/suggest_heroes` conversation flow. The bot collects the user's team lineup and (optionally) the enemy team lineup across separate messages, then runs the agent to suggest 3-5 heroes.

## Conversation Flow

```
User: /suggest_heroes
Bot:  "Please enter your team lineup (1-5 heroes, comma-separated)."

User: "Zilong, Yu Zhong, Ruby"
Bot:  "Got it! Now enter the enemy team lineup, or type skip to get
       suggestions based on your team only."

User: "Fanny, Lancelot"  OR  "skip"
Bot:  <agent response with 3-5 hero suggestions>
```

## Approach

Use `ConversationHandler` from python-telegram-bot v22. It provides built-in per-user state management, timeout handling, and state transitions.

## States

```python
USER_TEAM = 0    # waiting for user's team lineup
ENEMY_TEAM = 1   # waiting for enemy team lineup or "skip"
```

## Handler Functions

| Function | Trigger | Action |
|---|---|---|
| `suggest_heroes_start` | `/suggest_heroes` command | Prompt for user team, return `USER_TEAM` |
| `suggest_heroes_user_team` | Text message in `USER_TEAM` | Validate lineup (1-5 heroes). If valid: store in `context.user_data["user_lineup"]`, prompt for enemy team, return `ENEMY_TEAM`. If invalid: re-prompt with error, stay in `USER_TEAM`. |
| `suggest_heroes_enemy_team` | Text message in `ENEMY_TEAM` | If "skip": call agent with `enemy_heroes="None"`. Otherwise: validate lineup. If valid: call agent. If invalid: re-prompt, stay in `ENEMY_TEAM`. On success or agent error: return `ConversationHandler.END`. |
| `suggest_heroes_timeout` | 5-min inactivity | Send "Session expired. Send /suggest_heroes to start again." |

## State Storage

Per-user via `context.user_data` (managed by framework):

```python
context.user_data["user_lineup"] = ["Zilong", "Yu Zhong", "Ruby"]
```

Enemy lineup is used immediately and not stored.

## Validation

Shared `_parse_lineup(text: str) -> list[str] | None` helper:
- Split on commas, strip whitespace, filter empties
- Return list of hero names if 1-5 heroes, otherwise `None`

## Skill Template

`skills/suggest-heroes/SKILL.md` receives `{user_heroes}` and `{enemy_heroes}`.

- When enemy team provided: `enemy_heroes="Fanny, Lancelot"`
- When skipped: `enemy_heroes="None"`

The skill instructions adapt: if no enemy team, suggest heroes based on team synergy and general meta strength instead of counter-picking.

Suggest 3-5 heroes (changed from 5-7).

## `build_handlers` Change

Currently returns `list[tuple[str, HandlerFunc]]` and `main.py` wraps each in `CommandHandler`. Updated to return `list[BaseHandler]` directly, since `ConversationHandler` is not a `CommandHandler`. `main.py` calls `app.add_handler(h)` on each.

## Re-entry & Timeout

- Sending `/suggest_heroes` at any point restarts the conversation.
- After 5 minutes of inactivity, the conversation expires with a message.

## Error Handling

- Invalid lineup: re-prompt with error, stay in current state
- Agent exception: reply with unavailability message, end conversation
- Timeout: send expiry message, conversation ends

## Renames

All `team_counter` / `team-counter` references renamed to `suggest_heroes` / `suggest-heroes`:
- `skills/team-counter/` -> `skills/suggest-heroes/`
- `config.py` command key and skill path
- `bot/handlers.py` function names and handler map
- All test files and doc references

## Files Changed

- `bot/handlers.py` - multi-step conversation handlers
- `bot/main.py` - accept handler objects from `build_handlers`
- `config.py` - rename command key and skill path
- `skills/suggest-heroes/SKILL.md` - rename, update content (3-5 heroes, optional enemy team)
- `tests/test_handlers.py` - rewrite for conversation handler functions
- `tests/test_main.py` - update for new `build_handlers` return type
- `tests/test_config.py` - update command key/path assertions
- `docs/plans/` - update references

## Testing

Each handler function tested independently with mocked Update/Context. No need to test `ConversationHandler` wiring (framework responsibility).

Coverage target: 100% line coverage.

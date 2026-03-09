# Generating Suggestions Intermediate Message Design

**Goal:** Add a "Generating suggestions..." acknowledgement message between enemy team input and the hero suggestion response in the `/suggest_heroes` conversation.

**Architecture:** Single-line addition to `suggest_heroes_enemy_team` handler after input validation resolves `enemy_heroes`, before the agent `try` block. Tests updated to expect two `reply_html` calls on success/error paths.

---

## Flow Change

**Before:**
1. User enters enemy team lineup (or `skip`)
2. Bot responds with hero suggestions (or error)

**After:**
1. User enters enemy team lineup (or `skip`)
2. Bot responds: `"Generating suggestions..."`
3. Bot responds with hero suggestions (or error)

The intermediate message is always sent once input is valid — including on agent failure.

## `skip` Case-Insensitivity

Already implemented via `text.lower() == "skip"`. No change required. Existing `test_skip_case_insensitive` (tests `"SKIP"`) already covers this.

## Files Changed

### `bot/handlers.py`

In `suggest_heroes_enemy_team`, add one `reply_html` call after `enemy_heroes` is resolved, before the `try` block:

```python
await update.effective_message.reply_html("Generating suggestions...")

try:
    prompt = load_skill(...)
    result = await agent.run(prompt)
    await update.effective_message.reply_html(result)
except Exception:
    ...
```

### `tests/test_handlers.py`

Four tests in `TestSuggestHeroesEnemyTeam` assert `reply_html` call counts/content and must be updated:

- `test_valid_lineup_calls_agent`: change `assert_called_once_with("<b>Pick Fanny</b>")` → assert 2 calls; first is `"Generating suggestions..."`, second is agent result
- `test_skip_calls_agent_with_none`: same pattern
- `test_skip_case_insensitive`: same pattern
- `test_agent_error_sends_error_message`: change `call_args[0][0]` → assert 2 calls; first is `"Generating suggestions..."`, second contains `"unavailable"`

`test_invalid_lineup_reprompts` is unchanged (returns early before the intermediate message).

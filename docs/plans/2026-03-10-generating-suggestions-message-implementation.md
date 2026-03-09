# Generating Suggestions Intermediate Message Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Generating suggestions..." acknowledgement message in `suggest_heroes_enemy_team` between input validation and the agent call.

**Architecture:** One-line addition to `bot/handlers.py` after `enemy_heroes` is resolved. Four tests in `tests/test_handlers.py` that assert a single `reply_html` call must be updated to expect two calls in the correct order.

**Tech Stack:** python-telegram-bot v22, pytest, pytest-asyncio (asyncio_mode=auto), 100% coverage enforced.

---

### Task 1: Update tests to expect the intermediate message, then implement it

**Files:**
- Modify: `tests/test_handlers.py:116-206`
- Modify: `bot/handlers.py:86-96`

---

**Step 1: Update `test_valid_lineup_calls_agent` to expect 2 reply calls**

In `tests/test_handlers.py`, replace the assertion block in `test_valid_lineup_calls_agent` (currently line 131):

```python
# BEFORE
assert result == ConversationHandler.END
update.effective_message.reply_html.assert_called_once_with("<b>Pick Fanny</b>")
assert "Zilong" in agent.last_prompt
assert "Fanny" in agent.last_prompt
```

```python
# AFTER
assert result == ConversationHandler.END
calls = update.effective_message.reply_html.call_args_list
assert len(calls) == 2
assert calls[0][0][0] == "Generating suggestions..."
assert calls[1][0][0] == "<b>Pick Fanny</b>"
assert "Zilong" in agent.last_prompt
assert "Fanny" in agent.last_prompt
```

**Step 2: Run the test to verify it fails**

```bash
pytest tests/test_handlers.py::TestSuggestHeroesEnemyTeam::test_valid_lineup_calls_agent -v
```

Expected: FAIL — `AssertionError: assert 1 == 2` (only 1 reply call currently exists)

**Step 3: Update `test_skip_calls_agent_with_none` to expect 2 reply calls**

Replace the assertion block (currently line 149-150):

```python
# BEFORE
assert result == ConversationHandler.END
assert "None" in agent.last_prompt
```

```python
# AFTER
assert result == ConversationHandler.END
calls = update.effective_message.reply_html.call_args_list
assert len(calls) == 2
assert calls[0][0][0] == "Generating suggestions..."
assert "None" in agent.last_prompt
```

**Step 4: Update `test_skip_case_insensitive` to expect 2 reply calls**

Replace the assertion block (currently line 165-167):

```python
# BEFORE
assert result == ConversationHandler.END
assert "None" in agent.last_prompt
```

```python
# AFTER
assert result == ConversationHandler.END
calls = update.effective_message.reply_html.call_args_list
assert len(calls) == 2
assert calls[0][0][0] == "Generating suggestions..."
assert "None" in agent.last_prompt
```

**Step 5: Update `test_agent_error_sends_error_message` to expect 2 reply calls**

Replace the assertion block (currently lines 203-206):

```python
# BEFORE
assert result == ConversationHandler.END
reply_text = update.effective_message.reply_html.call_args[0][0]
assert "unavailable" in reply_text.lower()
```

```python
# AFTER
assert result == ConversationHandler.END
calls = update.effective_message.reply_html.call_args_list
assert len(calls) == 2
assert calls[0][0][0] == "Generating suggestions..."
assert "unavailable" in calls[1][0][0].lower()
```

**Step 6: Run all four updated tests to confirm they all fail**

```bash
pytest tests/test_handlers.py::TestSuggestHeroesEnemyTeam -v
```

Expected: 4 failures (the 4 updated tests), 1 pass (`test_invalid_lineup_reprompts` is unchanged)

**Step 7: Add the intermediate message to `bot/handlers.py`**

In `bot/handlers.py`, in the `handler` inner function of `suggest_heroes_enemy_team`, add the reply call after `user_lineup = context.user_data["user_lineup"]` and before the `try` block:

```python
# BEFORE (lines 87-96)
        user_lineup = context.user_data["user_lineup"]

        try:
            prompt = load_skill(
                skill_path,
                user_heroes=", ".join(user_lineup),
                enemy_heroes=enemy_heroes,
            )
            result = await agent.run(prompt)
            await update.effective_message.reply_html(result)
        except Exception:
```

```python
# AFTER
        user_lineup = context.user_data["user_lineup"]

        await update.effective_message.reply_html("Generating suggestions...")

        try:
            prompt = load_skill(
                skill_path,
                user_heroes=", ".join(user_lineup),
                enemy_heroes=enemy_heroes,
            )
            result = await agent.run(prompt)
            await update.effective_message.reply_html(result)
        except Exception:
```

**Step 8: Run the full test suite**

```bash
pytest --tb=short -q
```

Expected: all tests pass, 100% coverage

**Step 9: Commit**

```bash
git add bot/handlers.py tests/test_handlers.py
git commit -m "feat: add generating suggestions message before agent call"
```

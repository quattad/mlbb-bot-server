# Suggest Heroes Response Format Design

**Goal:** Enforce a structured output template for the `/suggest_heroes` command response so users get a consistent, concise format.

**Approach:** Update the "Summarizing Suggestions" section in `skills/suggest-heroes/SKILL.md` to include the exact output template with strict instructions to follow it verbatim. No code changes needed.

---

## Output Template

```
Your suggested heroes are as follows:
1. <hero_name>
- Why hero was suggested: <maximum 2 sentence summary>
- Good teammates: <comma-separated list of user team heroes with good synergy>
- Counters: <comma-separated list of enemy heroes this hero counters, or "-" if no enemy team>

2. <hero_name>
...
```

## Files Changed

### `skills/suggest-heroes/SKILL.md`

Replace the "Summarizing Suggestions" section (lines 27–33) with:

```markdown
**Summarizing Suggestions**
- You MUST format your response using EXACTLY the template below. Do NOT add any extra text, preamble, or markdown formatting outside of this template.
- Suggest 3-5 heroes.
- Keep each "Why hero was suggested" entry to a maximum of 2 sentences.
- If no enemy team lineup was provided (enemy_heroes is "None"), set Counters to "-".

Your suggested heroes are as follows:
1. <hero_name>
- Why hero was suggested: <maximum 2 sentence summary of why the hero was chosen>
- Good teammates: <heroes on the user's team that would work well with this hero, comma-separated>
- Counters: <heroes on the enemy team that the hero counters, or "-" if no enemy team was provided>
```

### No other files change

The bot sends the agent's response directly via `reply_html`. The format is enforced entirely by the skill prompt.

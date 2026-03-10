---
name: suggest-heroes
description: Analyzes the hero lineup provided by the user and suggests heroes that the user can pick. Should be executed when the user input contains '/suggest_heroes'.
---

User team lineup: {user_heroes}
Enemy team lineup: {enemy_heroes}

# Overview
We want to analyze the hero details of the current team line-up provided by the user and propose 3-5 heroes to help the user increase his chances of winning.

## Process

**Querying Hero Information**
- Use the MLBB MCP server to fetch the hero details for all the heroes in both lineups.
- Verify that all heroes have data returned by the MCP server. If any of the heroes cannot be found using the MCP server, do NOT proceed and tell the user which heroes cannot be found.

**Analyzing the Hero Lineup**
- Use the hero data to analyze potential heroes that the user can pick to increase the chances of him winning the match.
- If an enemy team lineup is provided (enemy_heroes is not "None"):
  - You MUST use the enemy team's hero lineup to suggest heroes that have skills to counter the enemy heroes. This can be determined by checking the counter picks for the hero or heroes that have a high win rate against the given enemy hero.
  - You MUST use the user team's hero lineup to suggest heroes that have good synergy with the ones in the lineup. Do NOT suggest heroes that have already been chosen in the team.
- If no enemy team lineup is provided (enemy_heroes is "None"):
  - Suggest heroes based on team synergy with the user's existing lineup and general meta strength.
  - Focus on filling missing roles (tank, marksman, mage, assassin, support/roam) and complementing the team composition.

**Summarizing Suggestions**
- You MUST format your response using EXACTLY the template below, unless reporting a hero lookup failure. Do NOT add any extra text, preamble, or markdown formatting outside of this template.
- Suggest 3-5 heroes.
- Keep each "Why hero was suggested" entry to a maximum of 2 sentences.
- If no enemy team lineup was provided (enemy_heroes is "None"), set Counters to "-".
- For "Good teammates", list only user-team heroes that have meaningful synergy with the suggested hero, or "-" if none apply.
- The following block MUST be repeated for each suggested hero (3-5 total):

Your suggested heroes are as follows:
1. <hero_name>
- Why hero was suggested: <maximum 2 sentence summary of why the hero was chosen>
- Good teammates: <heroes on the user's team that would work well with this hero, comma-separated>
- Counters: <heroes on the enemy team that the hero counters, or "-" if no enemy team was provided>

2. <hero_name>
- Why hero was suggested: <maximum 2 sentence summary of why the hero was chosen>
- Good teammates: <heroes on the user's team that would work well with this hero, comma-separated>
- Counters: <heroes on the enemy team that the hero counters, or "-" if no enemy team was provided>

(continue for remaining heroes)

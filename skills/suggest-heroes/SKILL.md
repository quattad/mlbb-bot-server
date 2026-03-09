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
- Provide a list of 3-5 suggested heroes to the user.
- For each suggested hero, the following information should be provided:
1. Hero name
2. Why the hero was suggested
3. Which enemy heroes the suggested hero counters (if enemy team was provided)
4. Which user team heroes the suggested hero would have good synergy with

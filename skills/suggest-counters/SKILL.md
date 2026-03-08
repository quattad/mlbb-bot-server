---
name: suggest-counters
description: Analyzes the hero lineup provided by the user and suggest counter heroes that the user can choose for the team. Should be executed when the user input contains '/suggest-counters', 'Suggest counter heroes...'
---

# Overview
We want to analyze the hero details of the current team line-up provided by the user and propose a 5-7 counter heroes to help the user increase his chances of winning.

## Process

**Understanding the Current Hero Lineup**
- Ask for the current hero lineup of the user's team and enemy team. Prefer hero name separated by a comma (e.g. Layla, Luo Yi). 
- Ask for the current hero lineup of the enemy team. The format should be the same as the current hero lineup of the user.
- You MUST be clear about the hero lineup of both the user's team and enemy team. Do NOT proceed if the lineup is unclear, and re-prompt the user to specify the heroes more clearly if needed.
- You MUST check if the hero count for both lineups for the user's team and enemy team are between 1 to 5. If the count does not fall within the range, you MUST prompt the user to re-enter the user team's lineup or the enemy team's lineup, whichever applies.

**Querying Hero Information**
- Use the MLBB MCP server to fetch the hero details for all the heroes in the lineup.
- Verify that all heroes have data returned by the MCP server. If any of the heroes cannot be found using the MCP server, do NOT proceed and tell the user which heroes cannot be found.

**Analyzing the Hero Lineup**
- Use the hero data to analyze potential heroes that the user can pick to increase the chances of him winning the match.
- You MUST use the enemy team's hero lineup to suggest heroes that have skills to counter the enemy heroes. This can be determined by checking the counter picks for the hero or heroes that have a high win rate against the given enemy hero.
- You MUST use the user team's hero lineup to suggest heroes that have good synergy with the ones in the lineup. Do NOT suggest heroes that have already been chosen in the team. 

**Summarizing Suggestions**
- Provide the list of suggested heroes to the user
- For each suggested hero, the following information should be provided.
1. Hero name
2. Why the hero was suggested
3. Which enemy heroes the suggested hero counters
4. Which user team heroes the suggested hero would have good synergy with
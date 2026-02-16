---
mode: agent
description: "Improve the AI tutor's behavior with better prompt engineering"
---

# Improve Prompt Engineering

Owen wants to make the tutor smarter, more engaging, or better at a specific task. Guide him through iterative prompt refinement.

## Current prompts are in `app/prompts.py`

### Prompt engineering principles to teach:

1. **Be specific** — Vague prompts get vague answers
   - Bad: "You are a tutor"
   - Good: "You are a math tutor for a 7th grader. Use simple language and real-world examples."

2. **Use structure** — Headers, numbered lists, and formatting help the LLM
   - The system prompt should define: persona, principles, constraints, output format

3. **Give examples (few-shot)** — Show the LLM what good output looks like
   ```
   When explaining fractions, use this format:
   1. State the concept
   2. Give a real-world analogy (pizza slices, etc.)
   3. Show the math notation
   4. Ask a check-for-understanding question
   ```

4. **Set constraints** — Tell it what NOT to do
   - "Never give the answer directly. Always ask a guiding question first."
   - "If the student is off-topic, redirect gently."

5. **Use formatting instructions** — Tell it to use LaTeX
   - "Use LaTeX notation for all math: \\( inline \\) and \\[ display \\]"
   - "Use markdown headers and bullet points for structure"

## Iteration workflow:

1. **Identify the problem** — What does the tutor do wrong? (too verbose? gives answers too fast? bad math notation?)
2. **Modify the prompt** in `app/prompts.py`
3. **Test with specific inputs** via the chat UI
4. **Compare before/after** responses
5. **Repeat** until the behavior matches what Owen wants

## Exercises:
- Make the tutor always respond with a question before giving an answer
- Add LaTeX formatting instructions to the system prompt
- Create a "hint mode" that gives progressively more detailed hints
- Adjust the quiz prompt to produce word problems instead of pure recall
- Make the difficulty assessment more nuanced (consider streaks, not just overall accuracy)

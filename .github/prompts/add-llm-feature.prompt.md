---
mode: agent
description: "Add a new LLM-powered feature — prompt engineering + service integration"
---

# Add a New LLM Feature

Owen wants to add a new feature that uses Azure OpenAI. Guide him through prompt engineering and integration.

## Context

This project uses the `openai` SDK via `app/azure_client.py`. All prompts live in `app/prompts.py`.
The client auto-detects Azure AI Foundry vs standard Azure OpenAI endpoints.

## Steps to follow:

1. **Design the prompt** in `app/prompts.py`
   - Explain system prompts vs user prompts
   - Show how to use format strings for dynamic content
   - Discuss temperature, max_tokens, and when to use `response_format={"type": "json_object"}`
   - Teach prompt engineering basics: be specific, give examples, set constraints

2. **Create the service function** in `app/services/`
   - Import `get_openai_client` from `app.azure_client`
   - Import `get_settings` from `app.config` for the deployment name
   - Use `await client.chat.completions.create(...)` — explain the async pattern
   - Parse the response: `response.choices[0].message.content`
   - If JSON output: parse with `json.loads()`, explain error handling

3. **Explain the chat completions API**
   - Messages array: system → conversation history → user
   - Role of system message (sets behavior)
   - Why we trim history (`MAX_HISTORY`) to manage token costs

4. **Test the feature**
   - Use `curl` or the app UI to test interactively
   - Discuss how to iterate on prompts based on output quality

## Teaching moments:
- What are tokens and why do they matter?
- What does temperature control? (creativity vs consistency)
- Why do we use JSON mode for structured outputs?
- How to handle LLM errors gracefully

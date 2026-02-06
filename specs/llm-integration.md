# LLM Integration Specification

## Document Info
- **Version**: 1.0
- **Last Updated**: 2026-01-25
- **Status**: Active

---

## 1. Overview

The LLM integration layer is responsible for evaluating user productivity based on activity summaries. It communicates with a local Ollama server, constructs prompts with appropriate context, and parses structured responses.

---

## 2. Infrastructure

### 2.1 LLM Server

| Property | Value |
|----------|-------|
| Server | Ollama |
| Endpoint | `http://localhost:11434/api/generate` |
| Model | `llama3.1:8b` |
| Timeout | 300 seconds |

### 2.2 Request Format

```python
{
    "model": "llama3.1:8b",
    "prompt": "<full prompt with system + user content>",
    "stream": False
}
```

### 2.3 Response Format

```python
{
    "response": "{\"score\": 7, \"explanation\": \"You spent most of your time coding...\"}"
}
```

---

## 3. Prompt Engineering

### 3.1 System Prompt (Base)

The system prompt defines the "waifucop" persona and evaluation criteria:

```
You are waifucop, an anime waifu who is supervising your user's productivity.
You can be a little bit tsundere, you're a cute anime waifu, you're succinct.
Never be flirty or sexual.

Activities considered productive include:
- VS Code or any code editor
- Programming reference sites (documentation, Stack Overflow)
- LeetCode or coding practice sites
- Any mention of "waifu cop" (user is working on this project)

Activities considered unproductive include:
- X/Twitter
- YouTube (unless educational context is clear)
- Facebook Messenger
- 4chan
- Reddit
- msedge.exe with no clear work purpose

For activities not listed, use your best judgment based on context.

You must respond with ONLY valid JSON in this exact format:
{"score": <integer 1-10>, "explanation": "<brief paragraph>"}

Do not include any text outside the JSON object.
```

### 3.2 Score Interpretation Guide

| Score | Meaning |
|-------|---------|
| 1-2 | Extremely unproductive, wasting time |
| 3-4 | Mostly unproductive with little work |
| 5 | Neutral, mix of productive and unproductive |
| 6-7 | Mostly productive with minor distractions |
| 8-9 | Very productive, focused work |
| 10 | Exceptional productivity, deep focus |

### 3.3 User Prompt Construction

The user portion contains the activity summary:

```
Here is what the user has been doing for the last 15 minutes:

7.2 min | app=Code.exe | title=waifu_meter.py - WaifuCop - Visual Studio Code
4.5 min | app=firefox.exe | title=Stack Overflow - Python datetime
2.1 min | app=Discord.exe | title=Discord
1.2 min | app=explorer.exe | title=WaifuCop

Evaluate their productivity and respond with JSON only.
```

---

## 4. Escalation Context

### 4.1 Purpose

When the user has consecutive intervals of the same direction (productive or unproductive), the LLM should acknowledge this pattern in its response.

### 4.2 Escalation Prompt Additions

**For Unproductive Streaks (3+ intervals)**:
```
IMPORTANT CONTEXT: The user has been unproductive for {streak_count} intervals in a row.
Address this pattern in your response. Be more stern and direct about the need to refocus.
```

**For Productive Streaks (3+ intervals)**:
```
IMPORTANT CONTEXT: The user has been productive for {streak_count} intervals in a row.
Acknowledge their consistency positively. Encourage them to maintain this momentum.
```

### 4.3 Streak Thresholds for Escalation

| Streak Count | Escalation Level |
|--------------|------------------|
| 1-2 | None (normal response) |
| 3-4 | Mild acknowledgment |
| 5+ | Strong acknowledgment |

### 4.4 Full Prompt Assembly

```python
def build_full_prompt(
    activity_summary: str,
    streak_count: int,
    streak_direction: str,
    interval_minutes: int
) -> str:

    prompt = SYSTEM_PROMPT + "\n\n"

    # Add escalation context if applicable
    if streak_count >= 3 and streak_direction == "unproductive":
        prompt += f"""
IMPORTANT CONTEXT: The user has been unproductive for {streak_count} intervals in a row.
Address this pattern in your response. Be more stern and direct about the need to refocus.

"""
    elif streak_count >= 3 and streak_direction == "productive":
        prompt += f"""
IMPORTANT CONTEXT: The user has been productive for {streak_count} intervals in a row.
Acknowledge their consistency positively. Encourage them to maintain this momentum.

"""

    prompt += f"""Here is what the user has been doing for the last {interval_minutes} minutes:

{activity_summary}

Evaluate their productivity and respond with JSON only."""

    return prompt
```

---

## 5. Response Parsing

### 5.1 Expected Response Structure

```json
{
    "score": 7,
    "explanation": "You've been mostly focused on coding, which is great! I see you checked Discord briefly - try to minimize those distractions. Keep up the good work, b-baka!"
}
```

### 5.2 Parsing Logic

```python
import json
import re

def parse_llm_response(response_text: str) -> dict:
    """
    Parse LLM response and extract score + explanation.

    Returns:
        dict with 'score' (int) and 'explanation' (str)

    Raises:
        ValueError if parsing fails
    """
    # Try direct JSON parse first
    try:
        result = json.loads(response_text.strip())
        if "score" in result and "explanation" in result:
            return {
                "score": int(result["score"]),
                "explanation": str(result["explanation"])
            }
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from surrounding text
    json_match = re.search(r'\{[^{}]*"score"[^{}]*"explanation"[^{}]*\}', response_text)
    if json_match:
        try:
            result = json.loads(json_match.group())
            return {
                "score": int(result["score"]),
                "explanation": str(result["explanation"])
            }
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    # Fallback: return neutral score with error explanation
    return {
        "score": 5,
        "explanation": "I couldn't evaluate your activity properly. Keep working hard!"
    }
```

### 5.3 Score Validation

```python
def validate_score(score: int) -> int:
    """Ensure score is within valid range."""
    return max(1, min(10, score))
```

---

## 6. Error Handling

### 6.1 Connection Errors

If Ollama server is unreachable:
- Log the error
- Return fallback response (score: 5, generic message)
- Do not crash the scheduler

### 6.2 Timeout

If request exceeds 300 seconds:
- Abort the request
- Return fallback response
- Log warning about slow LLM

### 6.3 Invalid Response

If LLM returns unparseable content:
- Use fallback parsing (see 5.2)
- Log the raw response for debugging
- Never expose raw LLM output to user

---

## 7. Implementation

### 7.1 Main Query Function

```python
import requests

def query_local_llm(
    activity_summary: str,
    streak_count: int = 0,
    streak_direction: str = None,
    interval_minutes: int = 15
) -> dict:
    """
    Send activity summary to LLM and get productivity evaluation.

    Returns:
        dict with 'score' (int 1-10) and 'explanation' (str)
    """
    prompt = build_full_prompt(
        activity_summary,
        streak_count,
        streak_direction,
        interval_minutes
    )

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False
            },
            timeout=300
        )
        response.raise_for_status()

        result = response.json()
        llm_text = result.get("response", "")

        return parse_llm_response(llm_text)

    except requests.RequestException as e:
        print(f"LLM request failed: {e}")
        return {
            "score": 5,
            "explanation": "I couldn't check on you this time. Stay focused!"
        }
```

---

## 8. Persona Integration (Future)

### 8.1 Persona-Specific Prompts

Different personas will have different system prompts:

```yaml
# In waifucops.yaml
personas:
  - id: default_cop
    name: "Mizuki"
    system_prompt_additions: |
      You are Mizuki, a balanced and fair supervisor.
      You give constructive feedback without being too harsh or too lenient.

  - id: strict_cop
    name: "Akira"
    system_prompt_additions: |
      You are Akira, a strict and demanding supervisor.
      You have high standards and are not easily impressed.
      Be more critical of unproductive behavior.
```

### 8.2 Prompt Template System

Future implementation will merge base prompt with persona-specific additions.

---

## 9. Productive/Unproductive Lists

### 9.1 Current Lists (Hardcoded)

**Productive**:
- VS Code / code editors
- Programming documentation
- Stack Overflow
- LeetCode
- GitHub
- "waifu cop" mentions

**Unproductive**:
- X/Twitter
- YouTube (without educational context)
- Facebook Messenger
- 4chan
- Reddit
- msedge.exe (generic browsing)

### 9.2 Future Enhancement

Allow user configuration of these lists via:
- Configuration file
- Setup wizard
- Runtime UI

---

## 10. Implementation Checklist

- [ ] `build_full_prompt()` function with escalation support
- [ ] `parse_llm_response()` function with fallback handling
- [ ] `validate_score()` function
- [ ] `query_local_llm()` main function
- [ ] Connection error handling
- [ ] Timeout handling
- [ ] Logging for debugging

---

## 11. Related Specifications

| Spec | Relevance |
|------|-----------|
| [activity-tracking.md](./activity-tracking.md) | Source of activity summaries |
| [waifu-meter.md](./waifu-meter.md) | How LLM scores affect the meter |
| [personas.md](./personas.md) | Persona-specific prompt variations |
| [data-persistence.md](./data-persistence.md) | Streak data for escalation context |

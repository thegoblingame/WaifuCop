# Personas Specification

## Document Info
- **Version**: 1.0
- **Last Updated**: 2026-01-25
- **Status**: Active

---

## 1. Overview

The persona system allows WaifuCop to have different characters with distinct personalities, visual appearances, and potentially different evaluation behaviors. Each persona represents a unique "supervisor" experience.

---

## 2. Persona Attributes

### 2.1 Core Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | string | Unique identifier (used in file paths) |
| `name` | string | Display name of the character |
| `personality` | string | Brief description for documentation |
| `images` | object | Paths to mood-based images |

### 2.2 Future Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `system_prompt_additions` | string | LLM prompt customizations |
| `mood_thresholds` | object | Custom thresholds for angry/neutral/happy |
| `scoring_modifiers` | object | Adjustments to scoring algorithm |
| `voice_style` | string | Text style descriptors for LLM |

---

## 3. Configuration Schema

### 3.1 waifucops.yaml Structure

```yaml
# Active persona (which one to use)
active_persona: default_cop

# Persona definitions
personas:
  - id: default_cop
    name: "Mizuki"
    personality: "Mizuki is balanced and fair. She wants the user to get work done but understands everyone needs breaks."
    images:
      angry: waifu_images/default_cop/angry.png
      neutral: waifu_images/default_cop/neutral.png
      happy: waifu_images/default_cop/happy.png

  # Future personas (examples)
  - id: strict_cop
    name: "Akira"
    personality: "Akira is strict and demanding. She has high standards and is not easily impressed."
    images:
      angry: waifu_images/strict_cop/angry.png
      neutral: waifu_images/strict_cop/neutral.png
      happy: waifu_images/strict_cop/happy.png

  - id: gentle_cop
    name: "Yuki"
    personality: "Yuki is gentle and encouraging. She focuses on positive reinforcement."
    images:
      angry: waifu_images/gentle_cop/angry.png
      neutral: waifu_images/gentle_cop/neutral.png
      happy: waifu_images/gentle_cop/happy.png
```

### 3.2 Full Schema (Future)

```yaml
personas:
  - id: string                    # Required: unique identifier
    name: string                  # Required: display name
    personality: string           # Required: description
    images:                       # Required: mood images
      angry: string               # Path to angry image
      neutral: string             # Path to neutral image
      happy: string               # Path to happy image

    # Optional: LLM customization
    system_prompt_additions: |
      Additional instructions for this persona's speaking style.

    voice_style:
      formality: casual|formal    # How formal the language is
      harshness: gentle|balanced|strict  # How critical of bad behavior
      enthusiasm: low|medium|high # Energy level in responses

    # Optional: Custom thresholds
    mood_thresholds:
      angry_max: 30               # Meter <= this = angry
      neutral_max: 70             # Meter <= this = neutral (else happy)

    # Optional: Scoring adjustments
    scoring_modifiers:
      base_delta_multiplier: 1.0  # Multiply all base deltas
      streak_multiplier_cap: 2.0  # Max streak multiplier
      harshness_bias: 0           # Add to negative deltas
```

---

## 4. Image Requirements

### 4.1 Directory Structure

```
waifu_images/
├── default_cop/
│   ├── angry.png
│   ├── neutral.png
│   └── happy.png
├── strict_cop/
│   ├── angry.png
│   ├── neutral.png
│   └── happy.png
└── gentle_cop/
    ├── angry.png
    ├── neutral.png
    └── happy.png
```

### 4.2 Image Specifications

| Property | Recommendation |
|----------|----------------|
| Format | PNG (transparency supported) |
| Resolution | 400x600 minimum |
| Aspect Ratio | Portrait (taller than wide) |
| Background | Transparent or solid color |
| File Size | < 500KB per image |

### 4.3 Mood Guidelines

| Mood | Expression | Body Language |
|------|------------|---------------|
| Angry | Frowning, narrowed eyes | Arms crossed, tense posture |
| Neutral | Calm expression | Relaxed, attentive |
| Happy | Smiling, bright eyes | Open posture, energetic |

---

## 5. Persona Loading

### 5.1 Loading Logic

```python
import yaml

def load_personas(config_path: str = "waifucops.yaml") -> dict:
    """Load persona configuration from YAML file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return {
        "active": config.get("active_persona", "default_cop"),
        "personas": {p["id"]: p for p in config.get("personas", [])}
    }

def get_active_persona(config: dict) -> dict:
    """Get the currently active persona."""
    active_id = config["active"]
    return config["personas"].get(active_id)
```

### 5.2 Image Path Resolution

```python
def get_persona_image(persona: dict, mood: str) -> str:
    """Get the image path for a persona's mood."""
    images = persona.get("images", {})
    return images.get(mood, f"waifu_images/default_cop/{mood}.png")
```

---

## 6. Persona Selection

### 6.1 Current Implementation

The active persona is determined by the `active_persona` field in `waifucops.yaml`.

### 6.2 Future Selection Methods

| Method | Description |
|--------|-------------|
| Config file | Set `active_persona` in YAML |
| Command-line | `--persona strict_cop` argument |
| Random | Rotate through personas randomly |
| Time-based | Different personas for morning/afternoon/evening |
| Performance-based | Stricter persona when meter is low |

---

## 7. Personality Integration

### 7.1 LLM Prompt Customization (Future)

Each persona can have custom additions to the system prompt:

```python
def build_persona_prompt(base_prompt: str, persona: dict) -> str:
    """Build complete prompt with persona customizations."""
    additions = persona.get("system_prompt_additions", "")
    voice = persona.get("voice_style", {})

    persona_context = f"""
You are {persona['name']}.
{persona.get('personality', '')}
"""

    if voice:
        if voice.get("formality") == "formal":
            persona_context += "Speak formally and professionally.\n"
        elif voice.get("formality") == "casual":
            persona_context += "Speak casually like talking to a friend.\n"

        if voice.get("harshness") == "strict":
            persona_context += "Be very critical of unproductive behavior.\n"
        elif voice.get("harshness") == "gentle":
            persona_context += "Be encouraging even when giving criticism.\n"

    return base_prompt + "\n" + persona_context + "\n" + additions
```

### 7.2 Voice Style Examples

**Mizuki (Balanced)**:
> "You spent some time on Twitter, but I see you got back to coding. Try to stay focused! You're doing okay."

**Akira (Strict)**:
> "Twitter again? This is unacceptable. You need to be more disciplined. Get back to work immediately."

**Yuki (Gentle)**:
> "I noticed you took a little break on Twitter. That's okay sometimes! When you're ready, let's get back to those tasks together!"

---

## 8. Scoring Modifiers (Future)

### 8.1 Persona-Specific Scoring

Different personas can have different scoring behaviors:

```python
def apply_persona_scoring(base_delta: int, persona: dict) -> int:
    """Apply persona-specific scoring modifiers."""
    modifiers = persona.get("scoring_modifiers", {})

    # Apply base multiplier
    multiplier = modifiers.get("base_delta_multiplier", 1.0)
    delta = base_delta * multiplier

    # Apply harshness bias (makes negative deltas more severe)
    if base_delta < 0:
        bias = modifiers.get("harshness_bias", 0)
        delta += bias

    return round(delta)
```

### 8.2 Example Configurations

**Strict Persona**:
```yaml
scoring_modifiers:
  base_delta_multiplier: 1.2  # All changes 20% more impactful
  harshness_bias: -2          # Extra penalty for unproductive behavior
```

**Gentle Persona**:
```yaml
scoring_modifiers:
  base_delta_multiplier: 0.8  # All changes 20% less impactful
  harshness_bias: 0           # No extra penalties
```

---

## 9. Default Persona

### 9.1 Mizuki (default_cop)

The default persona shipped with WaifuCop:

```yaml
- id: default_cop
  name: "Mizuki"
  personality: >
    Mizuki is normal. She wants the user to get work done.
    She's balanced and fair - not too harsh, not too lenient.
  images:
    angry: waifu_images/default_cop/angry.png
    neutral: waifu_images/default_cop/neutral.png
    happy: waifu_images/default_cop/happy.png
```

### 9.2 Fallback Behavior

If persona configuration is missing or invalid:
- Use `default_cop` as fallback
- Log warning about configuration issue
- Continue operation (don't crash)

---

## 10. Implementation Checklist

### 10.1 Current (MVP)

- [x] waifucops.yaml with basic structure
- [x] Persona images in correct directory structure
- [ ] `load_personas()` function
- [ ] `get_active_persona()` function
- [ ] `get_persona_image()` function
- [ ] Integration with waifu_popup.py

### 10.2 Future

- [ ] `active_persona` selection in config
- [ ] `system_prompt_additions` support
- [ ] `voice_style` LLM prompt integration
- [ ] `mood_thresholds` customization
- [ ] `scoring_modifiers` implementation
- [ ] Command-line persona override
- [ ] Persona gallery/selection UI

---

## 11. Related Specifications

| Spec | Relevance |
|------|-----------|
| [popup-ui.md](./popup-ui.md) | Image display and selection |
| [llm-integration.md](./llm-integration.md) | Persona-specific prompts |
| [waifu-meter.md](./waifu-meter.md) | Persona scoring modifiers |
| [data-persistence.md](./data-persistence.md) | Storing active persona preference |

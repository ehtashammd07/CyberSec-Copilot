"""
Prompt Builder — optimised for Microsoft Phi (phi, phi3, phi3.5)
Phi is a small model that performs best with:
  - Short, direct instructions
  - Clear structure
  - No excessive preamble
  - Explicit output format requests
"""

# Phi works well with the Alpaca-style instruction format
SYSTEM_PREAMBLE = """You are CyberSec Copilot, an expert cybersecurity AI.
Provide precise, technical, and actionable security analysis.
Be concise and direct. Focus on facts."""


# ── chat prompts ──────────────────────────────────────────────────────────────

def build_chat_prompt(
    user_message: str,
    context: str = "",
    mode: str = "explain",
) -> str:
    """
    Build a prompt for /chat endpoint, tuned for Phi.
    Phi responds well to <|system|> / <|user|> / <|assistant|> tags.
    """
    mode_instruction = {
        "explain": "Explain this cybersecurity topic clearly and technically.",
        "attacker": (
            "Explain from an attacker/red-team perspective (educational use). "
            "Describe how this is exploited, what tools are used, and what the attacker gains."
        ),
        "defender": (
            "Explain from a defender/blue-team perspective. "
            "Describe how to detect this attack in logs, how to prevent it, and how to respond."
        ),
    }.get(mode, "Provide a security analysis.")

    context_block = ""
    if context.strip():
        context_block = f"\n\nRelevant knowledge:\n{context}\n"

    return (
        f"<|system|>\n{SYSTEM_PREAMBLE}\n<|end|>\n"
        f"<|user|>\n"
        f"Mode: {mode.upper()}\n"
        f"Instruction: {mode_instruction}\n"
        f"{context_block}"
        f"Question: {user_message}\n"
        f"<|end|>\n"
        f"<|assistant|>\n"
    )


def build_analysis_prompt(
    threat_type: str,
    content_snippet: str,
    input_type: str,
) -> str:
    """
    Phi-optimised prompt for threat enrichment.
    Shorter content snippet — phi has a smaller context window.
    """
    # Phi handles shorter snippets better
    snippet = content_snippet[:1000]

    return (
        f"<|system|>\n{SYSTEM_PREAMBLE}\n<|end|>\n"
        f"<|user|>\n"
        f"Analyse this {input_type} for the threat: {threat_type}\n\n"
        f"Input:\n```\n{snippet}\n```\n\n"
        f"Respond ONLY with valid JSON (no markdown, no extra text):\n"
        f'{{\n'
        f'  "threat_type": "string",\n'
        f'  "severity": "critical|high|medium|low|info",\n'
        f'  "confidence": 0.0,\n'
        f'  "description": "string",\n'
        f'  "attacker_perspective": "string",\n'
        f'  "defender_perspective": "string",\n'
        f'  "mitigation_steps": ["step1", "step2"],\n'
        f'  "real_world_commands": ["cmd1"],\n'
        f'  "cve_references": [],\n'
        f'  "owasp_category": "string"\n'
        f'}}\n'
        f"<|end|>\n"
        f"<|assistant|>\n"
    )


def build_free_analysis_prompt(content: str, input_type: str) -> str:
    """Generic analysis prompt for phi — kept short."""
    snippet = content[:1500]
    return (
        f"<|system|>\n{SYSTEM_PREAMBLE}\n<|end|>\n"
        f"<|user|>\n"
        f"Analyse this {input_type} for security threats:\n\n"
        f"```\n{snippet}\n```\n\n"
        f"Respond ONLY with JSON:\n"
        f'{{"threat_type":"string","severity":"critical|high|medium|low|info",'
        f'"description":"string","attacker_perspective":"string",'
        f'"defender_perspective":"string","mitigation_steps":[],"real_world_commands":[]}}\n'
        f"<|end|>\n"
        f"<|assistant|>\n"
    )


def build_summary_prompt(threats: list[dict]) -> str:
    threat_list = "\n".join(
        f"- {t['threat_type']} ({t['severity']})" for t in threats
    )
    return (
        f"<|system|>\n{SYSTEM_PREAMBLE}\n<|end|>\n"
        f"<|user|>\n"
        f"Write a 3-sentence executive summary for these threats:\n{threat_list}\n"
        f"Include: risk level, impact, top remediation action.\n"
        f"<|end|>\n"
        f"<|assistant|>\n"
    )

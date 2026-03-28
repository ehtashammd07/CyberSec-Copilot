"""
Analyzer Service
----------------
Classifies input as log data or source code, detects attack patterns /
vulnerabilities, then enriches the result with an LLM deep-dive.
"""
import json
import logging
import re
from typing import Optional

from app.models.schemas import AnalysisType, SeverityLevel, ThreatDetail
from app.services.llm_service import LLMService, get_llm_service
from app.utils.prompt_builder import build_analysis_prompt

logger = logging.getLogger(__name__)


# ── heuristic rule sets ───────────────────────────────────────────────────────

LOG_SIGNATURES: list[dict] = [
    {
        "pattern": re.compile(r"(\$\{jndi:|log4j|log4shell)", re.IGNORECASE),
        "threat": "Log4Shell RCE",
        "severity": SeverityLevel.CRITICAL,
        "cve": "CVE-2021-44228",
        "owasp": "A06:2021 – Vulnerable Components",
    },
    {
        "pattern": re.compile(r"(union\s+select|or\s+1=1|--|sleep\(\d+\)|benchmark\()", re.IGNORECASE),
        "threat": "SQL Injection",
        "severity": SeverityLevel.HIGH,
        "cve": "",
        "owasp": "A03:2021 – Injection",
    },
    {
        "pattern": re.compile(r"(<script[\s>]|javascript:|onerror=|onload=|alert\()", re.IGNORECASE),
        "threat": "Cross-Site Scripting (XSS)",
        "severity": SeverityLevel.HIGH,
        "cve": "",
        "owasp": "A03:2021 – Injection",
    },
    {
        "pattern": re.compile(r"(\.\.\/|\.\.\\|%2e%2e|path\s*traversal)", re.IGNORECASE),
        "threat": "Path Traversal",
        "severity": SeverityLevel.HIGH,
        "cve": "",
        "owasp": "A01:2021 – Broken Access Control",
    },
    {
        "pattern": re.compile(r"(cmd\.exe|/bin/(ba)?sh|wget\s+http|curl\s+-o\s)", re.IGNORECASE),
        "threat": "Command Injection / Shell Execution",
        "severity": SeverityLevel.CRITICAL,
        "cve": "",
        "owasp": "A03:2021 – Injection",
    },
    {
        "pattern": re.compile(r"(failed\s+password|authentication\s+failure|invalid\s+user)", re.IGNORECASE),
        "threat": "Brute-Force / Credential Stuffing",
        "severity": SeverityLevel.MEDIUM,
        "cve": "",
        "owasp": "A07:2021 – Identification Failures",
    },
    {
        "pattern": re.compile(r"(port\s*scan|nmap|masscan|syn\s+flood)", re.IGNORECASE),
        "threat": "Reconnaissance / Port Scanning",
        "severity": SeverityLevel.LOW,
        "cve": "",
        "owasp": "",
    },
    {
        "pattern": re.compile(r"(payload|shellcode|meterpreter|metasploit|exploit)", re.IGNORECASE),
        "threat": "Exploit / Payload Delivery",
        "severity": SeverityLevel.CRITICAL,
        "cve": "",
        "owasp": "A06:2021 – Vulnerable Components",
    },
]

CODE_SIGNATURES: list[dict] = [
    {
        "pattern": re.compile(r"(execute|exec|query)\s*\(\s*['\"].*?\+", re.IGNORECASE | re.DOTALL),
        "threat": "SQL Injection via String Concatenation",
        "severity": SeverityLevel.HIGH,
        "cve": "",
        "owasp": "A03:2021 – Injection",
    },
    {
        "pattern": re.compile(r"(eval\s*\(|exec\s*\()", re.IGNORECASE),
        "threat": "Code Injection via eval/exec",
        "severity": SeverityLevel.CRITICAL,
        "cve": "",
        "owasp": "A03:2021 – Injection",
    },
    {
        "pattern": re.compile(r"subprocess\.(call|Popen|run)\s*\(.*shell\s*=\s*True", re.IGNORECASE | re.DOTALL),
        "threat": "OS Command Injection (shell=True)",
        "severity": SeverityLevel.CRITICAL,
        "cve": "",
        "owasp": "A03:2021 – Injection",
    },
    {
        "pattern": re.compile(r"pickle\.(loads?|Unpickler)", re.IGNORECASE),
        "threat": "Insecure Deserialization (pickle)",
        "severity": SeverityLevel.HIGH,
        "cve": "",
        "owasp": "A08:2021 – Software and Data Integrity Failures",
    },
    {
        "pattern": re.compile(r"(md5|sha1)\s*\(", re.IGNORECASE),
        "threat": "Weak Cryptographic Hash (MD5/SHA-1)",
        "severity": SeverityLevel.MEDIUM,
        "cve": "",
        "owasp": "A02:2021 – Cryptographic Failures",
    },
    {
        "pattern": re.compile(r"open\s*\(.*request\.(args|form|data|json)", re.IGNORECASE),
        "threat": "Path Traversal via User Input",
        "severity": SeverityLevel.HIGH,
        "cve": "",
        "owasp": "A01:2021 – Broken Access Control",
    },
    {
        "pattern": re.compile(r"(requests\.get|urllib.*open)\s*\(.*request\.(args|form)", re.IGNORECASE),
        "threat": "Server-Side Request Forgery (SSRF)",
        "severity": SeverityLevel.HIGH,
        "cve": "",
        "owasp": "A10:2021 – SSRF",
    },
    {
        "pattern": re.compile(r"debug\s*=\s*True", re.IGNORECASE),
        "threat": "Debug Mode Enabled in Production",
        "severity": SeverityLevel.MEDIUM,
        "cve": "",
        "owasp": "A05:2021 – Security Misconfiguration",
    },
]

_SEVERITY_ORDER = [
    SeverityLevel.CRITICAL,
    SeverityLevel.HIGH,
    SeverityLevel.MEDIUM,
    SeverityLevel.LOW,
    SeverityLevel.INFO,
]


class AnalyzerService:
    def __init__(self, llm: Optional[LLMService] = None):
        self.llm = llm or get_llm_service()

    # ── type detection ────────────────────────────────────────────────────────

    @staticmethod
    def detect_type(content: str) -> str:
        """Heuristically determine whether input is log data or source code."""
        code_indicators = [
            r"def\s+\w+\s*\(",
            r"class\s+\w+",
            r"import\s+\w+",
            r"#include\s*<",
            r"public\s+(static\s+)?void\s+main",
            r"function\s+\w+\s*\(",
        ]
        if any(re.search(p, content) for p in code_indicators):
            return "code"
        return "log"

    # ── heuristic scan ────────────────────────────────────────────────────────

    @staticmethod
    def _scan(content: str, signatures: list[dict]) -> list[dict]:
        hits = []
        for sig in signatures:
            if sig["pattern"].search(content):
                hits.append(sig)
        return hits

    # ── main analysis ─────────────────────────────────────────────────────────

    async def analyze(self, content: str, input_type: AnalysisType = AnalysisType.AUTO) -> dict:
        """
        Full analysis pipeline:
        1. Detect input type (log vs code)
        2. Run heuristic signature scan
        3. Enrich each finding with LLM
        4. Return structured result
        """
        # Step 1 — detect type
        resolved_type = (
            self.detect_type(content)
            if input_type == AnalysisType.AUTO
            else input_type.value
        )

        # Step 2 — heuristic scan
        signatures = CODE_SIGNATURES if resolved_type == "code" else LOG_SIGNATURES
        hits = self._scan(content, signatures)

        # Step 3 — LLM enrichment
        threats: list[ThreatDetail] = []
        if hits:
            for hit in hits:
                detail = await self._enrich_with_llm(hit, content, resolved_type)
                threats.append(detail)
        else:
            # No heuristic match — ask LLM to free-form analyse
            detail = await self._free_form_analysis(content, resolved_type)
            if detail:
                threats.append(detail)

        # Step 4 — overall severity
        if threats:
            overall = min(
                threats,
                key=lambda t: _SEVERITY_ORDER.index(t.severity)
            ).severity
        else:
            overall = SeverityLevel.INFO

        summary = self._build_summary(threats, resolved_type)

        return {
            "input_type": resolved_type,
            "threats": [t.model_dump() for t in threats],
            "overall_severity": overall,
            "summary": summary,
            "raw_llm_analysis": threats[0].description if threats else "No threats detected.",
        }

    async def _enrich_with_llm(self, hit: dict, content: str, input_type: str) -> ThreatDetail:
        """Use the LLM to enrich a heuristic hit with expert context."""
        prompt = build_analysis_prompt(
            threat_type=hit["threat"],
            content_snippet=content[:2000],
            input_type=input_type,
        )

        raw = ""
        try:
            raw = await self.llm.generate_response(prompt)
            parsed = _parse_llm_threat_response(raw, hit)
        except Exception as exc:
            logger.warning("LLM enrichment failed: %s", exc)
            parsed = _fallback_threat(hit)

        return parsed

    async def _free_form_analysis(self, content: str, input_type: str) -> Optional[ThreatDetail]:
        """Ask the LLM to analyse content when no signatures matched."""
        prompt = (
            f"You are a cybersecurity expert. Analyse the following {input_type} "
            f"for security threats. If no threats are found, say so clearly.\n\n"
            f"```\n{content[:3000]}\n```\n\n"
            "Respond as JSON with keys: threat_type, severity (critical/high/medium/low/info), "
            "description, attacker_perspective, defender_perspective, mitigation_steps (list), "
            "real_world_commands (list). Only JSON, no extra text."
        )
        try:
            raw = await self.llm.generate_response(prompt)
            data = json.loads(_strip_json_fences(raw))
            return ThreatDetail(
                threat_type=data.get("threat_type", "Unknown"),
                severity=SeverityLevel(data.get("severity", "info")),
                confidence=0.6,
                description=data.get("description", ""),
                attacker_perspective=data.get("attacker_perspective", ""),
                defender_perspective=data.get("defender_perspective", ""),
                mitigation_steps=data.get("mitigation_steps", []),
                real_world_commands=data.get("real_world_commands", []),
            )
        except Exception as exc:
            logger.warning("Free-form LLM analysis failed: %s", exc)
            return None

    @staticmethod
    def _build_summary(threats: list[ThreatDetail], input_type: str) -> str:
        if not threats:
            return f"No security threats detected in the {input_type} input."
        names = ", ".join({t.threat_type for t in threats})
        return (
            f"Detected {len(threats)} threat(s) in {input_type} input: {names}. "
            f"Highest severity: {max(threats, key=lambda t: _SEVERITY_ORDER.index(t.severity) * -1 + 4).severity.value}."
        )


# ── helpers ───────────────────────────────────────────────────────────────────

def _strip_json_fences(text: str) -> str:
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()


def _parse_llm_threat_response(raw: str, hit: dict) -> ThreatDetail:
    try:
        data = json.loads(_strip_json_fences(raw))
        return ThreatDetail(
            threat_type=data.get("threat_type", hit["threat"]),
            severity=SeverityLevel(data.get("severity", hit["severity"].value)),
            confidence=float(data.get("confidence", 0.85)),
            description=data.get("description", ""),
            attacker_perspective=data.get("attacker_perspective", ""),
            defender_perspective=data.get("defender_perspective", ""),
            mitigation_steps=data.get("mitigation_steps", []),
            real_world_commands=data.get("real_world_commands", []),
            cve_references=[hit.get("cve")] if hit.get("cve") else [],
            owasp_category=hit.get("owasp", ""),
        )
    except Exception:
        return _fallback_threat(hit)


def _fallback_threat(hit: dict) -> ThreatDetail:
    return ThreatDetail(
        threat_type=hit["threat"],
        severity=hit["severity"],
        confidence=0.75,
        description=f"Pattern match: {hit['threat']}",
        attacker_perspective="Attacker exploits this pattern to compromise the system.",
        defender_perspective="Apply input validation, sanitisation, and least privilege.",
        mitigation_steps=[
            "Validate and sanitise all user inputs.",
            "Apply the principle of least privilege.",
            "Monitor and alert on anomalous activity.",
        ],
        cve_references=[hit["cve"]] if hit.get("cve") else [],
        owasp_category=hit.get("owasp", ""),
    )


# ── singleton ─────────────────────────────────────────────────────────────────

_analyzer: AnalyzerService | None = None


def get_analyzer_service() -> AnalyzerService:
    global _analyzer
    if _analyzer is None:
        _analyzer = AnalyzerService()
    return _analyzer

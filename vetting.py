"""
vetting.py

Non-LLM Dependency-Free Requirement Coverage Vetting Algorithm.

Splits customer ticket text into individual asks/clauses and checks if each ask
is addressed somewhere in the full evidence trail (diagnosis + actions_taken + final_statement).

Score formula:
    coverage_score = requirements_addressed / total_requirements

Re-bidding threshold rule:
    Re-bidding stopping occurs if coverage_score >= 0.7 (i.e. re-bid if coverage_score < 0.7).
"""

import re


DELIMITERS_PATTERN = r"\b(?:and|but|however|also)\b|[,.;!\n]"

STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "you", "your", "it", "its", "they",
    "them", "a", "an", "the", "is", "am", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "to", "from", "in",
    "on", "at", "for", "with", "about", "against", "between", "into", "of",
    "this", "that", "these", "those", "can", "will", "just", "should", "now",
    "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "s", "t", "don", "shouldn", "now"
}

NON_SUBSTANTIVE_PHRASES = [
    "urgent", "immediately", "losing my patience", "nobody helps me",
    "please help", "please check", "hasn't been addressed", "since 2 days",
    "since 3 days", "thank you", "please fix", "help"
]

DOMAIN_SYNONYMS = {
    "refund": ["refund", "money", "payment", "reimburse", "return", "amount", "charge"],
    "visible": ["visible", "orders", "dashboard", "disappeared", "missing", "show", "profile", "sync"],
    "dashboard": ["dashboard", "orders", "profile", "view", "sync", "sync_status", "visible"],
    "cancel": ["cancel", "cancellation", "subscription", "churn", "retention", "leave"],
    "locked": ["locked", "unlock", "account", "login", "auth", "session", "access"],
    "invoice": ["invoice", "reissue", "missing", "receipt", "billing"],
    "duplicate": ["duplicate", "twice", "billed", "charged"],
}


def split_into_clauses(text: str) -> list[str]:
    """Split text on 'and', 'but', 'however', 'also', ',', '.', ';', '!'."""
    raw_clauses = re.split(DELIMITERS_PATTERN, text, flags=re.IGNORECASE)
    cleaned_clauses = []
    
    for clause in raw_clauses:
        clause_str = clause.strip()
        if not clause_str or len(clause_str) < 4:
            continue
            
        lower_clause = clause_str.lower()
        # Skip non-substantive clauses (pure emotion/urgency without core issue ask)
        if any(ns in lower_clause for ns in NON_SUBSTANTIVE_PHRASES) and not any(
            kw in lower_clause for kw in ["refund", "visible", "dashboard", "cancel", "locked", "money", "orders", "account", "invoice"]
        ):
            continue

        cleaned_clauses.append(clause_str)
        
    return cleaned_clauses if cleaned_clauses else [text.strip()]


def extract_keywords(clause: str) -> list[str]:
    """Extract non-stopwords and domain keywords from a clause."""
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", clause.lower())
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    return keywords


def _extract_evidence_text(evidence: dict) -> str:
    """Extract all searchable text fields from a single evidence dict."""
    parts = []
    parts.append(str(evidence.get("diagnosis", "")))
    parts.append(str(evidence.get("actions_taken") or evidence.get("execution_results") or ""))
    parts.append(str(evidence.get("final_statement") or evidence.get("customer_statement") or ""))
    parts.append(str(evidence.get("state_before_after") or ""))
    collab = evidence.get("collaboration_result")
    if isinstance(collab, dict):
        parts.append(str(collab.get("statement", "")))
        parts.append(str(collab.get("result", "")))
        parts.append(str(collab.get("diagnosis", "")))
        parts.append(str(collab.get("execution_results", "")))
    else:
        parts.append(str(collab or ""))
    parts.append(str(evidence.get("negotiation_transcript") or ""))
    parts.append(str(evidence.get("observations") or ""))
    parts.append(str(evidence.get("verification") or ""))
    return " ".join(parts)


def evaluate_coverage(ticket_text: str, evidence_trail) -> dict:
    """
    Evaluates whether each customer ask in ticket_text is covered somewhere in the full evidence trail.

    evidence_trail can be:
    - A list of result dicts (accumulated across iterations)
    - A single dict containing diagnosis, actions_taken, etc.
    - A combined string.
    """
    if isinstance(evidence_trail, list):
        # Merge all evidence dicts from all iterations into a single corpus
        merged_parts = []
        for item in evidence_trail:
            if isinstance(item, dict):
                merged_parts.append(_extract_evidence_text(item))
            else:
                merged_parts.append(str(item))
        full_trail_text = " ".join(merged_parts).lower()
    elif isinstance(evidence_trail, dict):
        full_trail_text = _extract_evidence_text(evidence_trail).lower()
    else:
        full_trail_text = str(evidence_trail).lower()

    clauses = split_into_clauses(ticket_text)
    total_requirements = len(clauses)
    addressed_count = 0
    checklist = []
    unaddressed_clauses = []

    for clause in clauses:
        keywords = extract_keywords(clause)
        if not keywords:
            addressed_count += 1
            checklist.append({"clause": clause, "addressed": True, "matched_keywords": []})
            continue

        matched_terms = []
        is_covered = False

        for kw in keywords:
            # Direct match
            if kw in full_trail_text:
                is_covered = True
                matched_terms.append(kw)
            else:
                # Check domain synonym list
                for domain, synonyms in DOMAIN_SYNONYMS.items():
                    if kw in synonyms or domain in kw:
                        if any(syn in full_trail_text for syn in synonyms):
                            is_covered = True
                            matched_terms.append(f"{kw}->{domain}")
                            break

        if is_covered:
            addressed_count += 1
            checklist.append({"clause": clause, "addressed": True, "matched_keywords": matched_terms})
        else:
            checklist.append({"clause": clause, "addressed": False, "matched_keywords": []})
            unaddressed_clauses.append(clause)

    coverage_score = round(addressed_count / total_requirements, 4) if total_requirements > 0 else 1.0

    return {
        "coverage_score": coverage_score,
        "total_requirements": total_requirements,
        "addressed_requirements": addressed_count,
        "unaddressed_clauses": unaddressed_clauses,
        "clause_checklist": checklist,
        "is_satisfactory": coverage_score >= 0.7,
    }

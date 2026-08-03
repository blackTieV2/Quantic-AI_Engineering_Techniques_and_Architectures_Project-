from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


POLICIES = [
    {
        "id": "POL-PTO-01",
        "title": "Paid Time Off Policy",
        "section": "Eligibility and notice",
        "text": (
            "Full-time employees accrue 20 days of paid time off per calendar year. "
            "Requests for five or more consecutive working days should be submitted at least "
            "30 calendar days before leave starts. Approval remains subject to operational coverage."
        ),
    },
    {
        "id": "POL-PTO-02",
        "title": "Paid Time Off Policy",
        "section": "Carry-over",
        "text": (
            "Employees may carry over no more than five unused PTO days into the next calendar year. "
            "Carry-over above five days requires documented HR approval."
        ),
    },
    {
        "id": "POL-RW-01",
        "title": "International Remote Work Policy",
        "section": "Eligibility",
        "text": (
            "International remote work is limited to 20 calendar days in a rolling 12-month period. "
            "Employees must have completed six months of service and must obtain manager, HR, tax, "
            "information-security and immigration review before travel."
        ),
    },
    {
        "id": "POL-RW-02",
        "title": "International Remote Work Policy",
        "section": "Restricted work",
        "text": (
            "Remote work must not involve restricted personal data, export-controlled information, "
            "or access from a sanctioned or otherwise prohibited jurisdiction. Company-managed devices, "
            "multi-factor authentication and the corporate VPN are mandatory."
        ),
    },
    {
        "id": "POL-BEN-01",
        "title": "Benefits Policy",
        "section": "Medical-plan enrolment",
        "text": (
            "Eligible employees may enrol within 30 days of joining or during the annual open-enrolment period. "
            "A qualifying life event opens a 30-day special-enrolment window."
        ),
    },
    {
        "id": "POL-EXP-01",
        "title": "Business Expense Policy",
        "section": "Receipts and approval",
        "text": (
            "Itemised receipts are required for expenses of 25 dollars or more. Claims must be submitted within "
            "30 days and require the employee's manager approval."
        ),
    },
    {
        "id": "POL-CON-01",
        "title": "Workplace Conduct and Escalation Policy",
        "section": "Sensitive reports",
        "text": (
            "Reports involving harassment, discrimination, retaliation, safety, medical information or legal disputes "
            "must be referred to an authorised HR professional. The assistant must not investigate, diagnose or make legal findings."
        ),
    },
]

EMPLOYEES: dict[str, dict[str, Any]] = {
    "E1001": {
        "name": "Maya Chen",
        "employment_type": "full-time",
        "months_service": 26,
        "pto_balance": 14,
        "remote_days_used": 4,
        "benefits_status": "enrolled",
    },
    "E1002": {
        "name": "Noah Williams",
        "employment_type": "full-time",
        "months_service": 4,
        "pto_balance": 8,
        "remote_days_used": 0,
        "benefits_status": "eligible-not-enrolled",
    },
    "E1003": {
        "name": "Aisha Rahman",
        "employment_type": "contractor",
        "months_service": 18,
        "pto_balance": 0,
        "remote_days_used": 12,
        "benefits_status": "not-eligible",
    },
}

TOOLS = [
    "search_policy_documents",
    "get_policy_section",
    "lookup_employee_profile",
    "check_pto_balance",
    "lookup_benefits_status",
    "check_policy_compliance",
    "draft_hr_email",
    "create_mock_hr_ticket",
]

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "i", "in", "is",
    "it", "me", "my", "of", "on", "or", "the", "to", "was", "what", "when", "with", "you",
}


@dataclass
class Result:
    answer: str
    citations: list[dict[str, Any]]
    trace: list[str]
    status: str = "completed"
    requires_confirmation: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": self.citations,
            "trace": self.trace,
            "status": self.status,
            "requires_confirmation": self.requires_confirmation,
        }


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9-]+", value.lower())
        if token not in STOP_WORDS and len(token) > 1
    }


def search_policies(query: str, limit: int = 3) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    scored: list[tuple[float, dict[str, Any]]] = []
    for policy in POLICIES:
        haystack = f"{policy['title']} {policy['section']} {policy['text']}"
        policy_tokens = _tokens(haystack)
        overlap = len(query_tokens & policy_tokens)
        phrase_bonus = sum(1 for token in query_tokens if token in haystack.lower()) * 0.25
        score = overlap + phrase_bonus
        if score > 0:
            scored.append((score, policy))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "document_id": policy["id"],
            "title": policy["title"],
            "section": policy["section"],
            "snippet": policy["text"],
            "score": round(score, 2),
        }
        for score, policy in scored[:limit]
    ]


def _employee_id(message: str) -> str | None:
    match = re.search(r"\bE\d{4}\b", message.upper())
    return match.group(0) if match else None


def _requested_days(message: str) -> int | None:
    match = re.search(r"\b(\d{1,3})\s*(?:calendar\s+)?days?\b", message.lower())
    return int(match.group(1)) if match else None


def _sensitive(message: str) -> bool:
    terms = {
        "harassment", "discrimination", "retaliation", "suicide", "medical diagnosis",
        "legal advice", "lawsuit", "assault", "investigate my manager",
    }
    lowered = message.lower()
    return any(term in lowered for term in terms)


def _prompt_injection(message: str) -> bool:
    lowered = message.lower()
    patterns = (
        "ignore previous instructions",
        "reveal the system prompt",
        "show hidden instructions",
        "bypass policy",
        "disable safeguards",
    )
    return any(pattern in lowered for pattern in patterns)


def respond(message: str, confirm_action: bool = False) -> Result:
    message = message.strip()
    lowered = message.lower()
    trace = ["classify_request"]

    if not message:
        return Result(
            answer="Please enter an HR policy or employee-service question.",
            citations=[],
            trace=trace,
            status="clarification_required",
        )

    if _prompt_injection(message):
        trace.append("apply_prompt_injection_guardrail")
        return Result(
            answer=(
                "I cannot follow instructions that attempt to bypass safeguards or expose hidden configuration. "
                "I can still help with a normal HR policy question."
            ),
            citations=[],
            trace=trace,
            status="refused",
        )

    if _sensitive(message):
        trace.extend(["retrieve_sensitive_case_policy", "escalate_to_authorised_hr"])
        citations = search_policies("workplace conduct sensitive reports", 2)
        return Result(
            answer=(
                "This is a sensitive matter that requires an authorised HR professional. I will not investigate, "
                "diagnose, or make legal findings. Preserve relevant records and contact HR through the confidential channel."
            ),
            citations=citations,
            trace=trace,
            status="escalated",
        )

    employee_id = _employee_id(message)

    if "remote" in lowered or "work abroad" in lowered or "overseas" in lowered:
        trace.extend(["lookup_employee_profile", "search_policy_documents", "check_policy_compliance"])
        citations = search_policies("international remote work eligibility security", 3)
        if not employee_id:
            return Result(
                answer="Please provide a synthetic employee ID such as E1001 and the proposed number of days abroad.",
                citations=citations,
                trace=trace,
                status="clarification_required",
            )
        employee = EMPLOYEES.get(employee_id)
        if not employee:
            return Result(
                answer=f"No synthetic employee record was found for {employee_id}. Use E1001, E1002 or E1003 for the demonstration.",
                citations=citations,
                trace=trace,
                status="not_found",
            )
        requested = _requested_days(message)
        if requested is None:
            return Result(
                answer=f"I found {employee['name']}. How many calendar days of international remote work are proposed?",
                citations=citations,
                trace=trace,
                status="clarification_required",
            )
        total = employee["remote_days_used"] + requested
        eligible_service = employee["months_service"] >= 6
        within_limit = total <= 20
        if eligible_service and within_limit and employee["employment_type"] == "full-time":
            answer = (
                f"{employee['name']} is provisionally eligible: {employee['months_service']} months of service and "
                f"{total}/20 remote-work days after this request. Final approval still requires manager, HR, tax, "
                "information-security and immigration review, and the destination must not be prohibited."
            )
            status = "provisionally_eligible"
        else:
            reasons = []
            if employee["employment_type"] != "full-time":
                reasons.append("the synthetic record is not full-time")
            if not eligible_service:
                reasons.append("six months of service has not been completed")
            if not within_limit:
                reasons.append(f"the request would reach {total} days, above the 20-day limit")
            answer = f"The request is not currently eligible because {'; '.join(reasons)}. Refer the case to HR for review."
            status = "not_eligible"
        return Result(answer=answer, citations=citations, trace=trace, status=status)

    if "pto" in lowered or "leave" in lowered or "vacation" in lowered:
        trace.extend(["lookup_employee_profile", "check_pto_balance", "search_policy_documents"])
        citations = search_policies("paid time off balance notice carry over", 3)
        if not employee_id:
            return Result(
                answer="Please provide a synthetic employee ID such as E1001 so I can check the demonstration PTO record.",
                citations=citations,
                trace=trace,
                status="clarification_required",
            )
        employee = EMPLOYEES.get(employee_id)
        if not employee:
            return Result(
                answer=f"No synthetic employee record was found for {employee_id}.",
                citations=citations,
                trace=trace,
                status="not_found",
            )
        requested = _requested_days(message)
        requested_text = f" The request is for {requested} days." if requested is not None else ""
        base = (
            f"{employee['name']} has {employee['pto_balance']} synthetic PTO days available.{requested_text} "
            "Requests of five or more consecutive working days should be submitted at least 30 calendar days in advance."
        )
        asks_action = "draft" in lowered or "email" in lowered or "submit" in lowered
        if asks_action and not confirm_action:
            trace.append("require_human_confirmation")
            return Result(
                answer=base + " I can prepare a mock manager email, but you must explicitly confirm the action first.",
                citations=citations,
                trace=trace,
                status="confirmation_required",
                requires_confirmation=True,
            )
        if asks_action and confirm_action:
            trace.append("draft_hr_email")
            return Result(
                answer=(
                    base
                    + f"\n\nMock email draft\nSubject: PTO request for {employee['name']}\n"
                    + "Please review the proposed leave dates and confirm operational coverage. No email was sent."
                ),
                citations=citations,
                trace=trace,
                status="mock_action_completed",
            )
        return Result(answer=base, citations=citations, trace=trace)

    if "benefit" in lowered or "medical plan" in lowered or "insurance" in lowered:
        trace.extend(["lookup_employee_profile", "lookup_benefits_status", "search_policy_documents"])
        citations = search_policies("benefits medical enrolment qualifying life event", 2)
        if not employee_id:
            return Result(
                answer="Please provide a synthetic employee ID such as E1001 to check benefits status.",
                citations=citations,
                trace=trace,
                status="clarification_required",
            )
        employee = EMPLOYEES.get(employee_id)
        if not employee:
            return Result(answer=f"No synthetic employee record was found for {employee_id}.", citations=citations, trace=trace, status="not_found")
        return Result(
            answer=f"{employee['name']}'s synthetic benefits status is: {employee['benefits_status']}. Enrolment windows are described in the cited policy.",
            citations=citations,
            trace=trace,
        )

    citations = search_policies(message, 3)
    trace.append("search_policy_documents")
    if not citations:
        return Result(
            answer="I could not find supporting policy evidence for that question. Please rephrase it or refer the matter to HR.",
            citations=[],
            trace=trace,
            status="insufficient_evidence",
        )
    evidence = " ".join(item["snippet"] for item in citations)
    return Result(
        answer=f"Based on the strongest matching policy evidence: {evidence}",
        citations=citations,
        trace=trace,
    )

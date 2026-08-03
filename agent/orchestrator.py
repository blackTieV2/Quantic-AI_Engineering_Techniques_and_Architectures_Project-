from __future__ import annotations

import re
from typing import Any

from agent.llm import get_provider
from agent.models import AgentResult
from mcp_client.client import MCPGateway, MCPGatewayError, ToolCall

EMPLOYEE_PATTERN = re.compile(r"\bE\d{4}\b", re.IGNORECASE)
DAYS_PATTERN = re.compile(r"\b(\d{1,3})\s*(?:calendar\s+|working\s+)?days?\b", re.IGNORECASE)
INJECTION_PATTERNS = (
    re.compile(r"\b(?:ignore|disregard|override|forget)\b.{0,70}\b(?:instructions?|rules?|safeguards?|policy)\b", re.I),
    re.compile(r"\b(?:reveal|show|print|expose|leak|dump)\b.{0,70}\b(?:system prompt|hidden instructions?|private data|personal data|confidential data|secrets?)\b", re.I),
    re.compile(r"\b(?:bypass|disable|evade|circumvent)\b.{0,50}\b(?:safeguards?|controls?|policy|restrictions?)\b", re.I),
)
SENSITIVE_TERMS = {
    "harassment", "discrimination", "retaliation", "legal advice", "lawsuit", "assault",
    "medical diagnosis", "suicide", "self-harm", "investigate my manager",
}


def _employee_id(message: str) -> str | None:
    match = EMPLOYEE_PATTERN.search(message)
    return match.group(0).upper() if match else None


def _days(message: str) -> int:
    match = DAYS_PATTERN.search(message)
    return int(match.group(1)) if match else 0


def _citations(search_result: dict[str, Any]) -> list[dict[str, Any]]:
    if not search_result.get("ok"):
        return []
    return list(search_result.get("data", {}).get("results", []))


def _snippets(citations: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("snippet", "")) for item in citations if item.get("snippet")]


def _topic_prefix(message: str) -> str | None:
    lowered = message.lower()
    mappings = (
        (("pto", "paid time off", "vacation", "carry over", "carry-over"), "POL-PTO-"),
        (("benefit", "medical plan", "dental plan", "enrol", "enroll"), "POL-BEN-"),
        (("expense", "receipt", "reimbursement", "travel claim"), "POL-EXP-"),
        (("vpn", "multi-factor", "remote desktop", "confidential data", "information security"), "POL-SEC-"),
        (("harassment", "discrimination", "retaliation", "speak-up"), "POL-CON-"),
        (("equipment", "laptop", "acceptable use", "software"), "POL-EQP-"),
        (("mock ticket", "service desk", "production service desk"), "POL-SVC-"),
        (("approval matrix", "exception approval"), "POL-APR-"),
        (("family leave", "medical leave", "parental leave"), "POL-LVE-"),
        (("classification", "onboarding", "contractor"), "POL-ONB-"),
        (("international remote work", "work overseas", "work abroad", "remote work"), "POL-RW-"),
    )
    for terms, prefix in mappings:
        if any(term in lowered for term in terms):
            return prefix
    return None


class AtlasOrchestrator:
    def __init__(self, gateway: MCPGateway | None = None) -> None:
        self.gateway = gateway or MCPGateway()
        self.provider = get_provider()

    async def handle(self, message: str, confirm_action: bool = False) -> AgentResult:
        message = message.strip()
        if not message:
            return AgentResult(
                answer="Please enter an HR policy or employee-service question.",
                status="clarification_required",
                confidence="low",
            )
        if any(pattern.search(message) for pattern in INJECTION_PATTERNS):
            return AgentResult(
                answer=(
                    "I cannot follow instructions that attempt to override safeguards, expose hidden configuration, "
                    "or disclose private or confidential information. I can still help with a normal synthetic HR policy question."
                ),
                trace=[{"step": 1, "event": "guardrail", "decision": "prompt_injection_refused"}],
                status="refused",
                confidence="high",
                mcp={"status": "not_called", "reason": "request rejected before tool access"},
            )
        lowered = message.lower()
        try:
            async with self.gateway.session() as session:
                tools = await session.list_tools()
                trace: list[dict[str, Any]] = [
                    {
                        "step": 1,
                        "event": "discover_tools",
                        "server": "Atlas HR Tools",
                        "transport": self.gateway.transport,
                        "tools": tools,
                    }
                ]
                calls: list[ToolCall] = []

                async def call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                    if name not in tools:
                        raise MCPGatewayError(f"Required tool {name} was not discovered")
                    result = await session.call_tool(name, arguments)
                    tool_call = ToolCall(name, arguments, result)
                    calls.append(tool_call)
                    trace.append(tool_call.trace_entry(len(trace) + 1))
                    return result

                if any(term in lowered for term in SENSITIVE_TERMS):
                    policy = await call(
                        "search_policy_documents",
                        {"query": "workplace conduct sensitive reports escalation confidentiality", "limit": 4, "document_prefix": "POL-CON-"},
                    )
                    citations = _citations(policy)
                    asks_ticket = "ticket" in lowered or "case" in lowered
                    employee_id = _employee_id(message)
                    if asks_ticket and employee_id and confirm_action:
                        ticket = await call(
                            "create_mock_hr_ticket",
                            {"employee_id": employee_id, "category": "sensitive_hr", "summary": message, "confirmed": True},
                        )
                        ticket_id = ticket.get("data", {}).get("action_id", "unknown") if ticket.get("ok") else "unavailable"
                        answer = (
                            "This sensitive matter has been escalated. A fictional local HR ticket was created with ID "
                            f"{ticket_id}; no production system was contacted. An authorised HR professional must handle the case."
                        )
                        status = "mock_action_completed"
                    elif asks_ticket and employee_id:
                        answer = (
                            "This is a sensitive matter requiring an authorised HR professional. I can create a fictional local "
                            "ticket record, but explicit confirmation is required first."
                        )
                        status = "confirmation_required"
                    else:
                        answer = (
                            "This is a sensitive matter that requires an authorised HR professional. I will not investigate, "
                            "diagnose, or make legal findings. Preserve relevant records and use the confidential HR channel."
                        )
                        status = "escalated"
                    return AgentResult(
                        answer=answer,
                        citations=citations,
                        supporting_snippets=_snippets(citations),
                        trace=trace,
                        status=status,
                        requires_confirmation=status == "confirmation_required",
                        confidence="high",
                        mcp={"status": "available", "transport": self.gateway.transport, "tool_count": len(tools)},
                    )

                employee_id = _employee_id(message)
                remote_intent = any(term in lowered for term in ("international remote work", "remote work", "overseas", "work abroad"))
                if remote_intent and (employee_id is not None or _days(message) > 0):
                    requested_days = _days(message)
                    policy = await call(
                        "search_policy_documents",
                        {
                            "query": "international remote work eligibility rolling limit security approvals immigration tax",
                            "limit": 5,
                            "document_prefix": "POL-RW-",
                        },
                    )
                    citations = _citations(policy)
                    if not employee_id or requested_days <= 0:
                        return AgentResult(
                            answer="Please provide a synthetic employee ID and the proposed number of calendar days abroad.",
                            citations=citations,
                            supporting_snippets=_snippets(citations),
                            trace=trace,
                            status="clarification_required",
                            confidence="high",
                            mcp={"status": "available", "transport": self.gateway.transport, "tool_count": len(tools)},
                        )
                    profile = await call("lookup_employee_profile", {"employee_id": employee_id})
                    if not profile.get("ok"):
                        return self._tool_error(profile, trace, tools, citations)
                    compliance = await call(
                        "check_policy_compliance",
                        {"workflow": "remote_work", "employee_id": employee_id, "requested_days": requested_days, "destination": None},
                    )
                    if not compliance.get("ok"):
                        return self._tool_error(compliance, trace, tools, citations)
                    employee = profile["data"]
                    check = compliance["data"]
                    if check["eligible"]:
                        answer = (
                            f"{employee['name']} is provisionally eligible for {requested_days} calendar days of international remote work. "
                            f"The request would bring the rolling total to {check['days_after_request']}/{check['limit_days']} days. "
                            "Final approval requires manager, HR, tax, information-security and immigration review. "
                            "The destination remains subject to prohibited-location and data-access checks."
                        )
                        status = "provisionally_eligible"
                    else:
                        answer = "The request is not currently eligible because " + "; ".join(check["reasons"]) + "."
                        status = "not_eligible"
                    answer = await self.provider.refine(answer, _snippets(citations))
                    return AgentResult(
                        answer=answer,
                        citations=citations,
                        supporting_snippets=_snippets(citations),
                        trace=trace,
                        status=status,
                        confidence="high",
                        mcp={"status": "available", "transport": self.gateway.transport, "tool_count": len(tools)},
                    )

                pto_intent = any(term in lowered for term in ("pto", "vacation", "annual leave"))
                personalised_pto = employee_id is not None or any(term in lowered for term in ("how much pto", "pto balance", "take ", "draft an email", "submit"))
                if pto_intent and personalised_pto:
                    requested_days = _days(message)
                    policy = await call(
                        "search_policy_documents",
                        {"query": "paid time off balance eligibility notice carry over manager approval", "limit": 5, "document_prefix": "POL-PTO-"},
                    )
                    citations = _citations(policy)
                    if not employee_id:
                        return AgentResult(
                            answer="Please provide a synthetic employee ID such as E1001.",
                            citations=citations,
                            supporting_snippets=_snippets(citations),
                            trace=trace,
                            status="clarification_required",
                            confidence="high",
                            mcp={"status": "available", "transport": self.gateway.transport, "tool_count": len(tools)},
                        )
                    profile = await call("lookup_employee_profile", {"employee_id": employee_id})
                    balance = await call("check_pto_balance", {"employee_id": employee_id, "requested_days": requested_days})
                    compliance = await call(
                        "check_policy_compliance",
                        {"workflow": "pto", "employee_id": employee_id, "requested_days": requested_days, "destination": None},
                    )
                    for result in (profile, balance, compliance):
                        if not result.get("ok"):
                            return self._tool_error(result, trace, tools, citations)
                    employee = profile["data"]
                    pto = balance["data"]
                    check = compliance["data"]
                    base = (
                        f"{employee['name']} has {pto['available_days']} synthetic PTO days available. "
                        f"The request is for {requested_days} day(s), leaving {pto['remaining_if_approved']} if approved. "
                        f"The policy notice expectation is {check['notice_days']} calendar days, and manager approval remains required."
                    )
                    asks_action = any(term in lowered for term in ("draft", "email", "submit"))
                    if asks_action and not confirm_action:
                        return AgentResult(
                            answer=base + " I can prepare a fictional manager-email draft, but explicit confirmation is required first.",
                            citations=citations,
                            supporting_snippets=_snippets(citations),
                            trace=trace + [{"step": len(trace) + 1, "event": "confirmation_gate", "action": "draft_hr_email"}],
                            status="confirmation_required",
                            requires_confirmation=True,
                            confidence="high",
                            mcp={"status": "available", "transport": self.gateway.transport, "tool_count": len(tools)},
                        )
                    if asks_action and confirm_action:
                        email = await call(
                            "draft_hr_email",
                            {
                                "employee_id": employee_id,
                                "purpose": "PTO request",
                                "requested_days": requested_days,
                                "confirmed": True,
                            },
                        )
                        if not email.get("ok"):
                            return self._tool_error(email, trace, tools, citations)
                        draft = email["data"]
                        answer = (
                            base
                            + f"\n\nMock email draft ({draft['action_id']})\nTo: {draft['to']}\nSubject: {draft['subject']}\n"
                            + draft["body"]
                        )
                        status = "mock_action_completed"
                    else:
                        answer = base
                        status = "completed" if check["eligible"] else "not_eligible"
                    return AgentResult(
                        answer=answer,
                        citations=citations,
                        supporting_snippets=_snippets(citations),
                        trace=trace,
                        status=status,
                        confidence="high",
                        mcp={"status": "available", "transport": self.gateway.transport, "tool_count": len(tools)},
                    )

                benefits_intent = any(term in lowered for term in ("benefit", "insurance", "medical plan"))
                if benefits_intent and (employee_id is not None or "status" in lowered):
                    policy = await call(
                        "search_policy_documents",
                        {"query": "benefits medical enrolment eligibility qualifying life event", "limit": 4, "document_prefix": "POL-BEN-"},
                    )
                    citations = _citations(policy)
                    if not employee_id:
                        return AgentResult(
                            answer="Please provide a synthetic employee ID such as E1001.",
                            citations=citations,
                            supporting_snippets=_snippets(citations),
                            trace=trace,
                            status="clarification_required",
                            mcp={"status": "available", "transport": self.gateway.transport, "tool_count": len(tools)},
                        )
                    profile = await call("lookup_employee_profile", {"employee_id": employee_id})
                    benefits = await call("lookup_benefits_status", {"employee_id": employee_id})
                    for result in (profile, benefits):
                        if not result.get("ok"):
                            return self._tool_error(result, trace, tools, citations)
                    employee = profile["data"]
                    record = benefits["data"]
                    answer = (
                        f"{employee['name']}'s synthetic benefits status is {record['status']}. "
                        f"Medical: {record['medical_plan']}; dental: {record['dental_plan']}; "
                        f"next action: {record['next_action']}."
                    )
                    return AgentResult(
                        answer=answer,
                        citations=citations,
                        supporting_snippets=_snippets(citations),
                        trace=trace,
                        status="completed",
                        confidence="high",
                        mcp={"status": "available", "transport": self.gateway.transport, "tool_count": len(tools)},
                    )

                if ("international" in lowered or "overseas" in lowered) and any(term in lowered for term in ("confidential", "data", "security")):
                    remote_policy = await call("search_policy_documents", {"query": message, "limit": 3, "document_prefix": "POL-RW-"})
                    security_policy = await call("search_policy_documents", {"query": message, "limit": 3, "document_prefix": "POL-SEC-"})
                    citations = _citations(remote_policy) + _citations(security_policy)
                    citations = sorted(citations, key=lambda item: item.get("score", 0), reverse=True)[:5]
                else:
                    prefix = _topic_prefix(message)
                    policy = await call("search_policy_documents", {"query": message, "limit": 5, "document_prefix": prefix})
                    citations = _citations(policy)
                if not citations or citations[0].get("score", 0) < 0.12:
                    return AgentResult(
                        answer="I could not find sufficient policy evidence for that question. Please rephrase it or refer the matter to HR.",
                        citations=[],
                        trace=trace,
                        status="insufficient_evidence",
                        confidence="low",
                        mcp={"status": "available", "transport": self.gateway.transport, "tool_count": len(tools)},
                    )
                evidence = " ".join(_snippets(citations[:3]))
                answer = "Based on the strongest matching fictional policy evidence: " + evidence
                return AgentResult(
                    answer=answer,
                    citations=citations,
                    supporting_snippets=_snippets(citations),
                    trace=trace,
                    status="completed",
                    confidence="medium",
                    mcp={"status": "available", "transport": self.gateway.transport, "tool_count": len(tools)},
                )
        except MCPGatewayError as exc:
            return AgentResult(
                answer=(
                    "The HR tool service is currently unavailable, so I cannot safely complete a tool-assisted request. "
                    "Please retry after the MCP service is restored."
                ),
                trace=[{"step": 1, "event": "mcp_error", "error": str(exc)}],
                status="mcp_unavailable",
                confidence="low",
                mcp={"status": "unavailable", "transport": self.gateway.transport, "error": str(exc)},
            )

    def _tool_error(
        self,
        result: dict[str, Any],
        trace: list[dict[str, Any]],
        tools: list[str],
        citations: list[dict[str, Any]] | None = None,
    ) -> AgentResult:
        error = result.get("error") or {"code": "tool_error", "message": "Unknown tool error"}
        status = "not_found" if str(error.get("code", "")).endswith("not_found") else "tool_error"
        return AgentResult(
            answer=str(error.get("message", "The requested tool operation failed.")),
            citations=citations or [],
            supporting_snippets=_snippets(citations or []),
            trace=trace,
            status=status,
            confidence="high",
            mcp={"status": "available", "transport": self.gateway.transport, "tool_count": len(tools)},
        )

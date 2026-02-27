import json
from typing import Any, Dict

from .llm import AnalysisPrompt, LLMClient, build_analysis_prompt
from .models import (
    InboxAnalysisRequest,
    InboxAnalysisResponse,
    InboxAnalysisResult,
    MessageCategory,
    MessageUrgency,
    SafetyFlag,
)


SYSTEM_INSTRUCTIONS = """
You are a clinical inbox assistant helping clinicians manage patient portal messages.

Goals:
- Help clinicians triage and summarize messages efficiently.
- Always prioritize patient safety and err on the side of escalation when in doubt.
- Do NOT provide definitive diagnoses or treatment plans; instead, suggest clinician review.

Steps for each message:
1. Determine urgency: "routine", "soon", or "urgent".
2. Determine one or more categories, such as "clinical", "administrative", "medication_refill", "appointment", or "other".
3. Write a concise summary aimed at a clinician, highlighting key facts and any red flags.
4. Draft a short, patient-friendly reply that is empathetic and clear. Include appropriate disclaimers, e.g., that this does not replace urgent or emergency care.
5. Identify any safety flags such as potential emergency symptoms, self-harm, or high-risk medication issues.
6. Decide whether this should be escalated for urgent clinician review (true/false).

Return JSON ONLY with the following keys:
- "urgency": one of ["routine", "soon", "urgent"]
- "categories": list of one or more of ["clinical", "administrative", "medication_refill", "appointment", "other"]
- "clinician_summary": string
- "draft_patient_reply": string
- "safety_flags": list of zero or more of ["none", "possible_emergency", "self_harm", "high_risk_medication_issue", "unclear_but_concerning"]
- "escalate": boolean

Do not include any additional keys or commentary.
""".strip()


class InboxAnalysisPipeline:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def analyze(self, request: InboxAnalysisRequest) -> InboxAnalysisResponse:
        prompt = build_analysis_prompt(
            AnalysisPrompt(
                system_instructions=SYSTEM_INSTRUCTIONS,
                message_body=request.message.body,
                thread_context=request.message.previous_thread,
            )
        )
        raw_output = await self._llm_client.generate(prompt)
        parsed = self._parse_output(raw_output)
        result = InboxAnalysisResult(
            urgency=parsed["urgency"],
            categories=parsed["categories"],
            clinician_summary=parsed["clinician_summary"],
            draft_patient_reply=parsed["draft_patient_reply"],
            safety_flags=parsed["safety_flags"],
            escalate=parsed["escalate"],
            raw_model_output=raw_output,
        )
        return InboxAnalysisResponse(message_id=request.message.message_id, analysis=result)

    def _parse_output(self, raw_output: str) -> Dict[str, Any]:
        """
        Parse and coerce the LLM's JSON output into our enums and types.

        This is intentionally defensive, since models sometimes return slightly
        malformed JSON or unexpected values.
        """
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            # Best-effort fallback: try to locate a JSON object in the text
            start = raw_output.find("{")
            end = raw_output.rfind("}")
            if start == -1 or end == -1 or start >= end:
                raise ValueError(f"Could not parse JSON from LLM output: {raw_output}")
            data = json.loads(raw_output[start : end + 1])

        urgency_str = str(data.get("urgency", "routine")).lower()
        if urgency_str not in {e.value for e in MessageUrgency}:
            urgency_str = MessageUrgency.routine.value

        categories_raw = data.get("categories") or []
        categories = []
        for cat in categories_raw:
            cat_str = str(cat).lower()
            if cat_str in {e.value for e in MessageCategory}:
                categories.append(MessageCategory(cat_str))
        if not categories:
            categories = [MessageCategory.other]

        safety_raw = data.get("safety_flags") or []
        safety_flags = []
        for flag in safety_raw:
            flag_str = str(flag).lower()
            if flag_str in {e.value for e in SafetyFlag}:
                safety_flags.append(SafetyFlag(flag_str))
        if not safety_flags:
            safety_flags = [SafetyFlag.none]

        escalate = bool(data.get("escalate", False))

        return {
            "urgency": MessageUrgency(urgency_str),
            "categories": categories,
            "clinician_summary": str(data.get("clinician_summary", "")).strip(),
            "draft_patient_reply": str(data.get("draft_patient_reply", "")).strip(),
            "safety_flags": safety_flags,
            "escalate": escalate,
        }


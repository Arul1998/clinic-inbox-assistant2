import asyncio

from clinic_inbox_assistant.llm import LLMClient
from clinic_inbox_assistant.models import InboxAnalysisRequest, InboxMessage
from clinic_inbox_assistant.pipeline import InboxAnalysisPipeline


class StubLLM(LLMClient):
    def __init__(self, output: str) -> None:
        self._output = output

    async def generate(self, prompt: str, **kwargs: object) -> str:  # type: ignore[override]
        return self._output


def test_pipeline_parses_valid_json_output() -> None:
    llm_output = """
    {
      "urgency": "urgent",
      "categories": ["clinical"],
      "clinician_summary": "Patient reports chest pain and shortness of breath for 2 hours.",
      \"draft_patient_reply\": "Thank you for your message. Because chest pain and shortness of breath can be serious, please seek urgent in-person evaluation or call emergency services if symptoms are severe.",
      "safety_flags": ["possible_emergency"],
      "escalate": true
    }
    """
    pipeline = InboxAnalysisPipeline(llm_client=StubLLM(llm_output))
    request = InboxAnalysisRequest(
        message=InboxMessage(
            message_id="msg-1",
            patient_id="patient-1",
            subject="Chest pain",
            body="I have chest pain and shortness of breath.",
        )
    )

    response = asyncio.run(pipeline.analyze(request))

    assert response.message_id == "msg-1"
    assert response.analysis.urgency.value == "urgent"
    assert response.analysis.categories[0].value == "clinical"
    assert "chest pain" in response.analysis.clinician_summary.lower()
    assert response.analysis.escalate is True
    assert "possible_emergency" in {f.value for f in response.analysis.safety_flags}


def test_pipeline_recovers_from_extra_text_around_json() -> None:
    llm_output = """
    Here is the analysis:

    {
      "urgency": "soon",
      "categories": ["administrative"],
      "clinician_summary": "Patient asks about rescheduling an appointment.",
      "draft_patient_reply": "Thanks for reaching out. We can help reschedule your appointment.",
      "safety_flags": ["none"],
      "escalate": false
    }

    Thank you.
    """
    pipeline = InboxAnalysisPipeline(llm_client=StubLLM(llm_output))
    request = InboxAnalysisRequest(
        message=InboxMessage(
            message_id="msg-2",
            patient_id="patient-2",
            subject="Reschedule appointment",
            body="Can I reschedule my appointment?",
        )
    )

    response = asyncio.run(pipeline.analyze(request))

    assert response.analysis.urgency.value == "soon"
    assert response.analysis.categories[0].value == "administrative"
    assert response.analysis.escalate is False


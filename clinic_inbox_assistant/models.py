from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MessageUrgency(str, Enum):
    routine = "routine"
    soon = "soon"
    urgent = "urgent"


class MessageCategory(str, Enum):
    clinical = "clinical"
    administrative = "administrative"
    medication_refill = "medication_refill"
    appointment = "appointment"
    other = "other"


class SafetyFlag(str, Enum):
    none = "none"
    possible_emergency = "possible_emergency"
    self_harm = "self_harm"
    high_risk_medication_issue = "high_risk_medication_issue"
    unclear_but_concerning = "unclear_but_concerning"


class InboxMessage(BaseModel):
    """Single patient message plus optional context."""

    message_id: Optional[str] = Field(
        default=None, description="Identifier from the source inbox system, if available."
    )
    patient_id: Optional[str] = Field(
        default=None, description="Identifier for the patient, if available."
    )
    subject: Optional[str] = Field(default=None, description="Subject line of the thread.")
    body: str = Field(..., description="The patient's message body.")
    previous_thread: Optional[str] = Field(
        default=None,
        description="Optional concatenated previous messages in the thread, for context.",
    )


class InboxAnalysisRequest(BaseModel):
    message: InboxMessage


class InboxAnalysisResult(BaseModel):
    urgency: MessageUrgency
    categories: List[MessageCategory] = Field(default_factory=list)
    clinician_summary: str
    draft_patient_reply: str
    safety_flags: List[SafetyFlag] = Field(default_factory=list)
    escalate: bool = Field(
        default=False,
        description="True if this message should be escalated for urgent review.",
    )
    raw_model_output: Optional[str] = Field(
        default=None,
        description="Optional raw text from the model for debugging and research purposes.",
    )


class InboxAnalysisResponse(BaseModel):
    message_id: Optional[str]
    analysis: InboxAnalysisResult


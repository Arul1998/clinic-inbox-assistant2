## Clinic Inbox Assistant

An experimental clinic inbox assistant inspired by the MedGemma Impact Challenge writeup. The goal of this project is to help clinicians manage patient portal messages by:

- Classifying messages by urgency and type
- Summarizing threads for clinician review
- Drafting safe, patient-friendly replies
- Surfacing red-flag content and escalation needs

This repository focuses on a local/self-hostable backend that can integrate with open medical models such as MedGemma, while keeping a clear human-in-the-loop workflow.

### Features (MVP)

- FastAPI backend exposing an `/analyze_message` endpoint
- Pluggable LLM client (start with any OpenAI-compatible model; later plug in MedGemma)
- Message analysis pipeline:
  - Urgency classification
  - Category tagging (clinical vs admin, refills, questions, etc.)
  - Clinician-facing summary
  - Draft patient reply
  - Safety flags and escalation recommendation

### Tech Stack

- Python
- FastAPI
- Pydantic
- HTTPX (for calling model APIs)

### Getting Started

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables for your LLM provider (for example, an OpenAI-compatible endpoint).
4. Run the API locally:

   ```bash
   uvicorn main:app --reload
   ```

5. Open the interactive docs at `http://127.0.0.1:8000/docs`.

### Configuration

The backend expects an OpenAI-compatible chat completion endpoint. You can point it to:

- A hosted provider such as OpenAI, or
- Your own deployment of an open model (for example, MedGemma served via an OpenAI-style server).

Environment variables:

- `LLM_API_KEY` (or `OPENAI_API_KEY`): API key for the model server (required).
- `LLM_BASE_URL` (or `OPENAI_BASE_URL`): Base URL of the API, e.g. `https://api.openai.com` or your own server.
- `LLM_MODEL` (or `OPENAI_MODEL`): Model name, e.g. `gpt-4o-mini` or your MedGemma deployment name.

Example (PowerShell):

```powershell
$env:LLM_API_KEY = "your-key-here"
$env:LLM_BASE_URL = "https://api.openai.com"
$env:LLM_MODEL = "gpt-4o-mini"
```

Then open `http://127.0.0.1:8000/docs` and try `POST /analyze_message`.

### Example `analyze_message` request

```json
{
  "message": {
    "message_id": "msg-123",
    "patient_id": "patient-42",
    "subject": "Chest pain today",
    "body": "Hi doctor, I have had chest pain and shortness of breath for 2 hours...",
    "previous_thread": null
  }
}
```

The response includes:

- `urgency`: `"routine" | "soon" | "urgent"`
- `categories`: list of message categories
- `clinician_summary`: concise summary for the clinician
- `draft_patient_reply`: patient-facing draft reply
- `safety_flags`: list of safety flags
- `escalate`: whether urgent clinician review is recommended

### MedGemma integration (conceptual)

To use MedGemma, you would:

1. Deploy a MedGemma model behind an OpenAI-compatible API (for example, using a gateway or serving framework).
2. Point `LLM_BASE_URL` to that deployment.
3. Set `LLM_MODEL` to the deployed model name.

No code changes in this repository should be needed; the `OpenAICompatibleClient` will send prompts to the configured endpoint.

### Status

This is an early prototype. The focus is on:

- Clear architecture for the inbox analysis pipeline
- Safety-oriented outputs and structured JSON responses
- Making it easy to later swap in MedGemma or other medical models without changing the API surface.


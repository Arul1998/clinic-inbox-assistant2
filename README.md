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

### Status

This is an early prototype. The focus is on:

- Clear architecture for the inbox analysis pipeline
- Safety-oriented outputs and structured JSON responses
- Making it easy to later swap in MedGemma or other medical models without changing the API surface.


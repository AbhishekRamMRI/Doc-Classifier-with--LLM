# doc-classifier

CLI tool that classifies uploaded business-document PDFs (invoices, insurance
certificates, contracts, etc.) and extracts key fields as structured JSON, using
an LLM.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in OPENAI_API_KEY
```

## Usage

```bash
python cli.py upload file1.pdf file2.pdf --contractor-id CN-4821 --output results.json
```

- Prints a one-line summary per file (filename, detected type, confidence %).
- Writes the full JSON array to `--output` if given, otherwise prints it to stdout.
- One bad file (corrupt/scanned PDF, API failure, invalid LLM output) does not
  stop the rest of the batch; it's recorded as an error result instead.

## Web UI (FastAPI + React/TypeScript)

A browser UI is also available: upload one or more PDFs and click **Classify**
to run the same pipeline as the CLI and see the results in the page.

### Quickest way to run it

```bash
./run.sh
```

This starts the FastAPI backend (http://127.0.0.1:8001) and the Vite dev
server (http://localhost:5173) together, installing frontend dependencies on
first run. Press `Ctrl+C` to stop both.

### Running the two servers manually

**1. Start the API backend** (from the project root, with the venv set up as above):

```bash
source .venv/bin/activate
uvicorn api:app --host 127.0.0.1 --port 8001
```

**2. Start the frontend** (in another terminal):

```bash
cd web
npm install   # first time only
npm run dev
```

Open the URL Vite prints (typically http://localhost:5173). The dev server
proxies `/api/*` requests to the backend on port 8001 (see `web/vite.config.ts`
if you need to change the port).

To build the frontend for production: `cd web && npm run build` (outputs to
`web/dist`).

## Architecture

All business logic (PDF extraction, LLM call, validation) lives in the
`doc_classifier/` package and has no CLI/web dependencies:

- `doc_classifier/pdf_extract.py` — extract text from a PDF
- `doc_classifier/llm.py` — system prompt + OpenAI call
- `doc_classifier/schema.py` — `DocumentResult` Pydantic model
- `doc_classifier/processor.py` — orchestrates extraction → LLM → validation,
  with a single retry on invalid JSON/validation failure

`cli.py` is a thin entry point built on `click` that only calls
`doc_classifier.processor.process_files`. `api.py` is a thin FastAPI wrapper
that exposes `process_files` over HTTP (`POST /api/classify`, multipart file
upload) for the `web/` React/TypeScript front-end — both entry points reuse
the same `doc_classifier` package with no duplicated logic.

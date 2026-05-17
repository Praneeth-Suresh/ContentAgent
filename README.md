# ContentAgent

ContentAgent is a local Marketing Agent application. It accepts a software source, either a GitHub repository URL or a website URL, and generates a monetization-focused marketing plan with market research, campaign orchestration, editable plan text, and content briefs.

The current implementation runs locally with a deterministic model adapter, so it does not require live OpenAI or Gemini credentials to start.

## Requirements

- Python 3.10 or newer
- A shell that can run the repository scripts

No Python package installation is required for the current local app. It uses the Python standard library.

## API Keys

The project brief names OpenAI API and Gemini API as future external model providers. The current code keeps provider access behind the `ModelAdapter` boundary and uses `DeterministicModelAdapter` by default, so API keys are not required for local development.

If provider-backed adapters are added later, keep credentials out of the repository and set them as environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
```

Do not commit `.env` files, real keys, or provider logs containing secrets.

## Run Locally

From the repository root:

```bash
python3 -m web_app.server
```

Then open:

```text
http://127.0.0.1:8000
```

The app serves the Web Interface and exposes the API endpoint:

```text
POST /api/marketing-plan
```

Example API request:

```bash
curl -s http://127.0.0.1:8000/api/marketing-plan \
  -H "Content-Type: application/json" \
  -d '{
    "software_source": "https://github.com/acme/revenue-dashboard",
    "user_interventions": [
      {
        "stage_name": "Market Research",
        "feedback": "Prioritize finance teams with budget authority."
      }
    ]
  }'
```

## Run Checks

Run the full deterministic gate:

```bash
./scripts/check.sh
```

Run only the Python behavior tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'
```

## Project Structure

- `src/marketing_agent/__init__.py`: Marketing Agent bounded context and public Python interface.
- `web_app/server.py`: thin HTTP adapter for the Web Interface.
- `web/static/`: browser UI assets.
- `tests/`: behavior tests for the core agent and web adapter.
- `agent/`: design, architecture, testing, and ADR documentation.

## Current Provider Behavior

Generated plans are produced locally by deterministic logic. This keeps development and tests stable while preserving the adapter boundary needed for future OpenAI or Gemini integrations.

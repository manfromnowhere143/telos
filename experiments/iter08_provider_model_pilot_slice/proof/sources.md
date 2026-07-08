# Iteration 08 Sources

## Official Model Sources

- OpenAI developer docs, `latest-model.md`, fetched through the OpenAI developer-docs MCP on
  2026-07-08. The page identifies `gpt-5.5` as the latest OpenAI model and recommends it for
  complex, tool-heavy coding workflows.
  <https://developers.openai.com/api/docs/guides/latest-model.md>
- Google Cloud Gemini model catalog, opened on 2026-07-08. The catalog lists Gemini 3.1 Pro as a
  preview model and lists Gemini 3.5 Flash as a featured fast agentic model.
  <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/google-models>
- Google Cloud Gemini 3.1 Pro model page, opened on 2026-07-08. The page documents model ID
  `gemini-3.1-pro-preview` and the custom-tools endpoint
  `gemini-3.1-pro-preview-customtools`, with the page last updated 2026-07-07 UTC.
  <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-1-pro>

## Harness Sources

- Pinned CodeClash commit: `381cdfa05a35e8acd35853b9fc7e13005121b127`.
- Local inspection of that pinned commit found:
  - `pyproject.toml` includes `litellm`,
  - `codeclash/agents/minisweagent.py` resolves models through Mini-SWE-Agent `get_model`,
  - `configs/pvp/*` includes provider-backed examples using `model_class: portkey`,
  - existing BattleSnake provider examples use Google, OpenAI, Anthropic, and other model names.

## Secret-Safe Preflight Commands

The preflight checked only presence and service names:

```bash
gh secret list --repo manfromnowhere143/telos
gcloud config get-value project >/dev/null
gcloud auth list --filter=status:ACTIVE --format='value(account)' >/dev/null
gcloud services list --enabled --filter='name:(aiplatform.googleapis.com OR generativelanguage.googleapis.com)' --format='value(name)'
```

No token, API key, credential JSON, or Google Cloud project identifier is committed in the proof
bundle.

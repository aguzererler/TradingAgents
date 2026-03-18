# Technology Stack & Dependencies

## Core Dependencies

| Package | Purpose | Notes |
|---------|---------|-------|
| `langgraph` | Agent workflow orchestration | Fan-out/fan-in, state management, conditional routing |
| `langchain-core` | LLM abstractions, tools | `@tool` decorator, `ToolNode`, `ChatPromptTemplate` |
| `langchain-openai` | OpenAI/OpenRouter provider | `ChatOpenAI` with configurable `base_url` |
| `langchain-google-genai` | Google Gemini provider | `ChatGoogleGenerativeAI` |
| `langchain-anthropic` | Anthropic Claude provider | `ChatAnthropic` |
| `langchain-xai` | xAI Grok provider | `ChatXAI` |
| `langchain-ollama` | Ollama local models | `ChatOllama` with configurable host |
| `yfinance` | Primary market data | OHLCV, fundamentals, sector/industry, screener |
| `python-dotenv` | Environment configuration | `load_dotenv()` at module level in `default_config.py` |
| `typer` | CLI framework | `cli/main.py` |
| `stockstats` | Technical indicators | Local computation from yfinance OHLCV — no vendor dependency |

## External APIs

| Service | Auth | Rate Limit | Primary Use |
|---------|------|-----------|-------------|
| OpenAI | `OPENAI_API_KEY` | Per-plan | Default LLM provider |
| OpenRouter | `OPENROUTER_API_KEY` | Per-plan | Multi-model routing |
| Alpha Vantage | `ALPHA_VANTAGE_API_KEY` | 75/min (free) | News sentiment, market movers |
| Finnhub | `FINNHUB_API_KEY` | 60/min (free) | Earnings calendar, economic calendar, insider transactions |
| Ollama | None (local) | Unlimited | Local model inference |

## LLM Provider Support

| Provider | Config Value | Models Tested |
|----------|-------------|---------------|
| OpenAI | `"openai"` | gpt-5-mini, gpt-5.2, gpt-5.4 |
| Google | `"google"` | gemini-3-pro, gemini-3.1-pro |
| Anthropic | `"anthropic"` | claude-4.x, claude-4.5, claude-4.6 |
| xAI | `"xai"` | grok-4.x |
| OpenRouter | `"openrouter"` | Any model via routing |
| Ollama | `"ollama"` | qwen, deepseek, llama (local) |

## Python Version

- Requires Python 3.13+ (as specified in conda setup)

## Development Tools

| Tool | Purpose |
|------|---------|
| `pytest` | Test framework |
| `conda` | Environment management |
| `pip` / `uv` | Package management (uv.lock present) |


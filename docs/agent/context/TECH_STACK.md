# Technology Stack & Dependencies

## Core Dependencies

| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `langchain-core` | >=0.3.81 | LLM abstractions, tools | `@tool` decorator, `ToolNode`, `ChatPromptTemplate` |
| `langchain-openai` | >=0.3.23 | OpenAI/OpenRouter provider | `ChatOpenAI` with configurable `base_url` |
| `langchain-google-genai` | >=2.1.5 | Google Gemini provider | `ChatGoogleGenerativeAI` |
| `langchain-anthropic` | >=0.3.15 | Anthropic Claude provider | `ChatAnthropic` |
| `langchain-experimental` | >=0.3.4 | Experimental LangChain features | |
| `langgraph` | >=0.4.8 | Agent workflow orchestration | Fan-out/fan-in, state management, conditional routing |
| `yfinance` | >=0.2.63 | Primary market data | OHLCV, fundamentals, sector/industry, screener |
| `pandas` | >=2.3.0 | Data processing | DataFrame manipulation throughout dataflows |
| `stockstats` | >=0.6.5 | Technical indicators | Local computation from yfinance OHLCV — no vendor dependency |
| `python-dotenv` | >=1.0.0 | Environment configuration | `load_dotenv()` at module level in `default_config.py` |
| `typer` | >=0.21.0 | CLI framework | `cli/main.py` |
| `rich` | >=14.0.0 | CLI formatting | Tables, Panels, Markdown, Live display, Layout |
| `questionary` | >=2.1.0 | Interactive CLI prompts | Analyst selection in `cli/main.py` |
| `requests` | >=2.32.4 | HTTP client | Alpha Vantage and Finnhub API calls |
| `redis` | >=6.2.0 | Cache / message broker | Optional caching layer |
| `backtrader` | >=1.9.78.123 | Backtesting engine | Strategy backtesting |
| `chainlit` | >=2.5.5 | Chat UI framework | Web-based chat interface |
| `parsel` | >=1.10.0 | HTML/XML parsing | Web scraping utilities |
| `rank-bm25` | >=0.2.2 | BM25 text ranking | Document relevance scoring |
| `tqdm` | >=4.67.1 | Progress bars | Long-running operations |
| `pytz` | >=2025.2 | Timezone handling | Date/time operations |
| `setuptools` | >=80.9.0 | Build system | Package setup |
| `typing-extensions` | >=4.14.0 | Type hint backports | `Literal`, `TypedDict` support |

## External APIs

| Service | Auth Env Var | Rate Limit | Primary Use |
|---------|-------------|-----------|-------------|
| OpenAI | `OPENAI_API_KEY` | Per-plan | Default LLM provider |
| OpenRouter | `OPENROUTER_API_KEY` | Per-plan | Multi-model routing |
| Alpha Vantage | `ALPHA_VANTAGE_API_KEY` | 75/min (free) | News sentiment, market movers |
| Finnhub | `FINNHUB_API_KEY` | 60/min (free) | Earnings calendar, economic calendar, insider transactions |
| Google AI | `GOOGLE_API_KEY` | Per-plan | Gemini LLM provider |
| Anthropic | `ANTHROPIC_API_KEY` | Per-plan | Claude LLM provider |
| xAI | `XAI_API_KEY` | Per-plan | Grok LLM provider |
| Ollama | None (local) | Unlimited | Local model inference |

## LLM Provider Support

| Provider | Config Value | Client Class | Models Tested |
|----------|-------------|-------------|---------------|
| OpenAI | `"openai"` | `OpenAIClient` | gpt-5-mini, gpt-5.2 |
| Google | `"google"` | `GoogleClient` | gemini-3-pro |
| Anthropic | `"anthropic"` | `AnthropicClient` | claude-4.x |
| xAI | `"xai"` | `OpenAIClient` (xAI endpoint) | grok-4.x |
| OpenRouter | `"openrouter"` | `OpenAIClient` (OR endpoint) | Any model via routing |
| Ollama | `"ollama"` | `OpenAIClient` (local endpoint) | qwen, deepseek, llama |

## Python Version

- Requires Python >=3.10 (as specified in `pyproject.toml` `requires-python`)

## Project Metadata

- **Package name**: `tradingagents`
- **Version**: 0.2.1
- **Entry point**: `tradingagents = "cli.main:app"`

## Development Tools

| Tool | Purpose |
|------|---------|
| `pytest` (>=9.0.2) | Test framework (dev dependency) |
| `conda` | Environment management |
| `pip` / `uv` | Package management (`uv.lock` present) |

<!-- Last verified: 2026-03-18 -->

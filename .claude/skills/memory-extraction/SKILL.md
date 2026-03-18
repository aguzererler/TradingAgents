---
name: Memory Extraction & Builder
description: >
  Extracts structured repository knowledge from source code, git history, ADRs, and
  conversations, then writes it into the layered memory system under docs/agent/context/.
  Use this skill when asked to "build memory", "update memory", "extract knowledge",
  "refresh context files", or "rebuild repository docs". This skill defines the exact
  format, extraction rules, and quality criteria for each memory file.
version: 2.0.0
---

# Memory Extraction & Builder Skill

## Purpose

Systematically extract, structure, and persist repository knowledge into a layered
memory system. The output files serve as the primary context for all future agent
sessions — they must be accurate, current, and complete enough that an agent with
no prior context can understand the project and make correct decisions.

## Memory Layer Model

The memory system has **4 layers**, from most-volatile to most-stable:

```
docs/agent/
├── CURRENT_STATE.md              # Layer 1: Live State (changes every session)
├── context/                      # Layer 2: Structured Knowledge (changes per milestone)
│   ├── ARCHITECTURE.md           #   System design, workflows, data flow, pipeline
│   ├── CONVENTIONS.md            #   Coding patterns, rules, gotchas
│   ├── COMPONENTS.md             #   File map, extension points, test org
│   ├── TECH_STACK.md             #   Dependencies, APIs, providers, versions
│   └── GLOSSARY.md               #   Term definitions, acronyms, data classes
├── decisions/                    # Layer 3: Decisions (append-only, rarely edited)
│   └── NNN-short-name.md         #   ADRs with YAML frontmatter
├── plans/                        # Layer 4: Plans (created/completed per task)
│   └── NNN-plan-name.md          #   Implementation checklists
├── logs/                         # Optional: session logs
└── templates/                    # Templates for ADRs, commits, PRs
```

## Extraction Rules

### Source Priority (highest to lowest)

1. **Source code** — the single source of truth for structure, patterns, and behavior
2. **Existing ADRs** (`docs/agent/decisions/`) — binding architectural constraints
3. **Test files** — reveal actual contracts, edge cases, and expected behavior
4. **Git history** (`git log`, PR descriptions) — reveal evolution and rationale
5. **Configuration files** (config modules, `pyproject.toml`, `.env.example`) — settings and deps
6. **README.md** — user-facing docs (may be outdated; cross-check with code)

### Source Discovery (dynamic — never hardcode file lists)

The skill and builder agent must **discover** sources at runtime, not rely on static
file lists. Use these patterns:

```bash
# Discover all Python source modules
find tradingagents -name "*.py" -type f | sort

# Discover configuration and build files
ls pyproject.toml requirements*.txt .env.example 2>/dev/null

# Discover CLI entry points and supporting modules
find cli -name "*.py" -type f | sort

# Discover test files
ls tests/

# Discover ADRs
ls docs/agent/decisions/

# Discover all classes in the codebase
grep -rn "^class " tradingagents/ cli/ --include="*.py"

# Discover dataclasses and key data structures
grep -rn "@dataclass" tradingagents/ cli/ --include="*.py"

# Recent git history
git log --oneline -20
```

**High-signal file patterns** (prioritize these when reading discovered files):
- `default_config.py` — all configuration with env var overrides
- `interface.py` — vendor routing, `VENDOR_METHODS`, `FALLBACK_ALLOWED`
- `*_common.py` — vendor base infrastructure (rate limiters, exceptions)
- `*_graph.py`, `*_setup.py` — workflow orchestration
- `*_states.py` — LangGraph state definitions with reducers
- `__init__.py` — module exports and public API
- `tool_runner.py` — inline tool execution for scanners
- `*_tools.py` — LangChain tool definitions
- `macro_bridge.py` — pipeline data classes and orchestration
- `cli/main.py` — CLI commands, MessageBuffer, UI layout
- `cli/models.py`, `cli/config.py`, `cli/utils.py` — CLI supporting modules
- `llm_clients/factory.py` — multi-provider LLM factory

### What to Extract per File

#### CURRENT_STATE.md
- **Source**: git log (last 5-10 meaningful commits), open PRs, TODO comments in code
- **Format**: 3 sections only — `# Current Milestone`, `# Recent Progress` (bullet list),
  `# Active Blockers` (bullet list)
- **Rule**: Never include historical information older than the last milestone
- **Rule**: Keep under 30 lines

#### ARCHITECTURE.md
- **Source**: Discover graph/workflow files (`*_graph.py`, `*_setup.py`), agent factory
  files, dataflow interface modules, config modules, pipeline modules, and CLI modules
  via filesystem traversal
- **Extract**:
  - System description (1 paragraph)
  - Core patterns (agent factory, LLM tiers, vendor routing, graph workflows)
  - Workflow diagrams (ASCII art) for **both** trading graph and scanner graph
  - **Pipeline architecture** — how scanner output bridges to per-ticker analysis
    via `MacroBridge`, including data classes (`MacroContext`, `StockCandidate`,
    `TickerResult`) and the parse → filter → analyze → report flow
  - **CLI architecture** — command structure, `MessageBuffer` for real-time UI,
    `StatsCallbackHandler` for metrics, Rich layout system
  - **LLM client factory** — multi-provider support, `create_llm_client()` dispatch
  - Key source file table (file → purpose, max 20 entries)
- **Rule**: No code snippets longer than 3 lines. Reference files instead.
- **Rule**: Every claim must be verifiable by reading the referenced file.
- **Rule**: Include the pipeline flow (scanner → bridge → trading) as a diagram.

#### CONVENTIONS.md
- **Source**: ADR actionable rules, code patterns observed in 3+ files, test patterns
- **Extract**:
  - Configuration conventions (env vars, fallbacks, per-tier overrides)
  - Agent creation pattern (factory closures)
  - Tool execution pattern (ToolNode vs run_tool_loop, with constants)
  - Vendor routing rules (category-level vs tool-level, FALLBACK_ALLOWED)
  - yfinance-specific gotchas
  - LangGraph state rules (reducers, MessagesState)
  - Threading/rate limiting rules (with actual rate values)
  - Testing conventions (markers, mocking patterns, env isolation)
  - Error handling patterns (exception hierarchies, fail-fast)
  - **CLI conventions** — Rich formatting, MessageBuffer patterns, stats tracking
  - **Pipeline conventions** — conviction ranking, JSON parsing, macro context
- **Rule**: Each convention must cite at least one ADR or source file
- **Rule**: Use imperative mood ("Use X", "Never do Y", "Always check Z")
- **Rule**: Include exact constant values (e.g., `MIN_REPORT_LENGTH = 2000`)

#### COMPONENTS.md
- **Source**: `find` command output for directory tree, `__init__.py` files for module
  exports, `ls tests/` for test organization, `grep class` for class inventory
- **Extract**:
  - Full directory tree (indented, with one-line purpose per file/dir) covering:
    - `tradingagents/` — all packages and modules
    - `cli/` — all CLI modules
    - `tests/` — all test files
  - **Class inventory** table (class → file → purpose) for all important classes
  - Extension point guides (how to add: analyst, scanner, vendor, config key, LLM provider)
  - CLI command table with entry points
  - Test organization table with type, notes, and marker info
- **Rule**: Directory tree must match actual filesystem. Run `find` to verify.
- **Rule**: Extension guides must list every file that needs modification.
- **Rule**: Include all `@dataclass` classes from pipeline and dataflows.

#### TECH_STACK.md
- **Source**: `pyproject.toml`, any `requirements*.txt` files, `.env.example`, LLM client
  modules discovered via filesystem traversal
- **Extract**:
  - Core dependency table (package → version constraint → purpose → notes)
  - External API table (service → auth env var → rate limit → primary use)
  - LLM provider table (provider → config value → client class → models tested)
  - Python version requirement (from `requires-python` in `pyproject.toml`)
  - Development tools table (tool → purpose)
- **Rule**: Version constraints from `pyproject.toml` only — use exact `>=X.Y.Z` format
- **Rule**: Rate limits must match values in rate limiter source code docstrings
- **Rule**: Include ALL dependencies from pyproject.toml, not just "important" ones

#### GLOSSARY.md
- **Source**: All other context files, ADRs, source code identifiers, class definitions
- **Extract**:
  - Every project-specific term, acronym, or identifier used in 2+ files
  - Grouped by domain: Agents & Workflows, Data Layer, Configuration, Vendor-Specific,
    State & Data Classes, Pipeline, CLI, File Conventions
  - For data classes (`@dataclass`): include the source file and key fields
  - For constants: include the source file and actual value
- **Rule**: Definitions must be under 25 words each
- **Rule**: Include the authoritative source file for each term

## Formatting Rules

### General
- Use GitHub-Flavored Markdown (GFM)
- Use `#` for file title, `##` for sections, `###` for subsections — no deeper nesting
- Tables for structured data (3+ items with same schema)
- Bullet lists for unstructured items
- Code blocks with language annotation (```python, ```bash, ```env)
- No HTML tags except freshness marker comments
- No emoji in headings
- Max line length: 100 characters (soft limit; tables may exceed)

### Cross-References
- Reference ADRs as `(ADR NNN)` — e.g., `(ADR 011)`
- Reference source files as backtick paths — e.g., `tradingagents/dataflows/interface.py`
- Reference other context files as relative links — e.g., `[CONVENTIONS.md](CONVENTIONS.md)`

### Freshness Markers
- Each file MUST have a comment at the bottom: `<!-- Last verified: YYYY-MM-DD -->`
- During extraction, verify every factual claim against source code before writing

## Quality Criteria

A memory file is **good** if it satisfies ALL of:

1. **Accurate** — Every statement is verifiable in current source code or ADRs
2. **Current** — Reflects the latest code on the working branch, not stale history
3. **Complete** — Covers all major subsystems: agents, dataflows, graphs, pipeline, CLI,
   LLM clients, config, and tests
4. **Concise** — No redundancy across files; each fact lives in exactly one file
5. **Navigable** — A reader can find any specific fact within 2 clicks/scrolls
6. **Actionable** — Conventions use imperative mood; extension guides list exact files
7. **Quantified** — Constants, counts, and limits include actual values from source code
8. **Cross-referenced** — Every convention cites a source; every term links to its file

## Builder Workflow

When invoked to build or refresh memory:

1. **Audit current files**: Read all files in `docs/agent/context/` and note what exists
2. **Discover sources**: Run discovery commands above; prioritize high-signal files
3. **Gather data**: Read key source files per the extraction rules; collect class names,
   constants, config keys, CLI commands, test files, and dependency versions
4. **Cross-reference**: Verify claims against actual code; discard stale information
5. **Write files**: Create/update each context file following the formatting rules
6. **Add freshness markers**: Append `<!-- Last verified: YYYY-MM-DD -->` to each file
7. **Self-check**: Re-read each file and verify:
   - No contradictions between files
   - Every factual claim maps to a real file
   - Directory trees match `find` output
   - Glossary covers every term used in other context files
   - All subsystems documented: agents, dataflows, graphs, pipeline, CLI, LLM clients

## Anti-Patterns to Avoid

- ❌ Copying entire code blocks into memory files (reference the file instead)
- ❌ Including aspirational/planned features as current facts
- ❌ Duplicating ADR content in CONVENTIONS.md (summarize and cite instead)
- ❌ Mixing volatile state (current progress) with stable knowledge (architecture)
- ❌ Writing vague descriptions ("various tools") instead of specific names
- ❌ Leaving stale information after a refactor
- ❌ Omitting the CLI subsystem (`cli/`) from documentation
- ❌ Omitting the pipeline subsystem (`tradingagents/pipeline/`) from documentation
- ❌ Listing dependencies without version constraints from pyproject.toml
- ❌ Omitting data classes (`MacroContext`, `StockCandidate`, `TickerResult`) from glossary
- ❌ Using round numbers for constants instead of exact values from source code

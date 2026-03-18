---
name: Memory Extraction & Builder
description: >
  Extracts structured repository knowledge from source code, git history, ADRs, and
  conversations, then writes it into the layered memory system under docs/agent/context/.
  Use this skill when asked to "build memory", "update memory", "extract knowledge",
  "refresh context files", or "rebuild repository docs". This skill defines the exact
  format, extraction rules, and quality criteria for each memory file.
version: 1.0.0
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
│   ├── ARCHITECTURE.md           #   System design, workflows, data flow
│   ├── CONVENTIONS.md            #   Coding patterns, rules, gotchas
│   ├── COMPONENTS.md             #   File map, extension points, test org
│   ├── TECH_STACK.md             #   Dependencies, APIs, providers
│   └── GLOSSARY.md               #   Term definitions, acronyms
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
5. **Configuration files** (`default_config.py`, `pyproject.toml`, `.env.example`) — reveal settings and dependencies
6. **README.md** — user-facing docs (may be outdated; cross-check with code)

### What to Extract per File

#### CURRENT_STATE.md
- **Source**: git log (last 5-10 meaningful commits), open PRs, TODO comments in code
- **Format**: 3 sections only — `# Current Milestone`, `# Recent Progress` (bullet list), `# Active Blockers` (bullet list)
- **Rule**: Never include historical information older than the last milestone. Keep under 30 lines.

#### ARCHITECTURE.md
- **Source**: Graph setup files, agent factory files, dataflow interface, config
- **Extract**:
  - System description (1 paragraph)
  - Core patterns (agent factory, LLM tiers, vendor routing, graph workflows)
  - Workflow diagrams (ASCII art, not images)
  - Key source file table (file → purpose, max 15 entries)
- **Rule**: No code snippets longer than 3 lines. Reference files instead.
- **Rule**: Every claim must be verifiable by reading the referenced file.

#### CONVENTIONS.md
- **Source**: ADR actionable rules, code patterns observed in 3+ files, test patterns
- **Extract**:
  - Configuration conventions (env vars, fallbacks)
  - Agent creation pattern
  - Tool execution pattern
  - Vendor routing rules
  - yfinance-specific gotchas
  - LangGraph state rules
  - Threading/rate limiting rules
  - Testing conventions
  - Error handling patterns
- **Rule**: Each convention must cite at least one ADR or source file.
- **Rule**: Use imperative mood ("Use X", "Never do Y", "Always check Z").

#### COMPONENTS.md
- **Source**: Directory listing, imports in `__init__.py` files, test file organization
- **Extract**:
  - Full directory tree (indented, with one-line purpose per file/dir)
  - Extension point guides (how to add: analyst, scanner, vendor, config key)
  - CLI command table
  - Test organization table
- **Rule**: Directory tree must match actual filesystem. Run `find` to verify.
- **Rule**: Extension guides must list every file that needs modification.

#### TECH_STACK.md
- **Source**: `pyproject.toml`, `requirements.txt`, `.env.example`, LLM client files
- **Extract**:
  - Core dependency table (package → purpose → notes)
  - External API table (service → auth → rate limit → primary use)
  - LLM provider table (provider → config value → models tested)
  - Python version requirement
- **Rule**: Version numbers from `pyproject.toml` or `requirements.txt` only.
- **Rule**: Rate limits must match values in rate limiter source code.

#### GLOSSARY.md
- **Source**: All other context files, ADRs, source code identifiers
- **Extract**:
  - Every project-specific term, acronym, or identifier used in 2+ files
  - Grouped by domain (Agents, Data Layer, Configuration, Vendor, State, Files)
- **Rule**: Definitions must be under 20 words each.
- **Rule**: Include the authoritative source location for each term.

## Formatting Rules

### General
- Use GitHub-Flavored Markdown (GFM)
- Use `#` for file title, `##` for sections, `###` for subsections — no deeper nesting
- Tables for structured data (3+ items with same schema)
- Bullet lists for unstructured items
- Code blocks with language annotation (```python, ```bash, ```env)
- No HTML tags
- No emoji in headings
- Max line length: 100 characters (soft limit; tables may exceed)

### Cross-References
- Reference ADRs as `(ADR NNN)` — e.g., `(ADR 011)`
- Reference source files as backtick paths — e.g., `tradingagents/dataflows/interface.py`
- Reference other context files as relative links — e.g., `[CONVENTIONS.md](CONVENTIONS.md)`

### Freshness Markers
- Each file SHOULD have a comment at the bottom: `<!-- Last verified: YYYY-MM-DD -->`
- During extraction, verify every factual claim against source code before writing

## Quality Criteria

A memory file is **good** if it satisfies ALL of:

1. **Accurate** — Every statement is verifiable in current source code or ADRs
2. **Current** — Reflects the latest code on the working branch, not stale history
3. **Complete** — Covers all major components, patterns, and extension points
4. **Concise** — No redundancy across files; each fact lives in exactly one file
5. **Navigable** — A reader can find any specific fact within 2 clicks/scrolls
6. **Actionable** — Conventions use imperative mood; extension guides list exact files

## Builder Workflow

When invoked to build or refresh memory:

1. **Audit current files**: Read all files in `docs/agent/context/` and note what exists
2. **Gather sources**: Read key source files per the extraction rules above
3. **Cross-reference**: Verify claims against actual code; discard stale information
4. **Write files**: Create/update each context file following the formatting rules
5. **Add freshness markers**: Append `<!-- Last verified: YYYY-MM-DD -->` to each file
6. **Self-check**: Re-read each file and verify no contradictions exist between files

## Anti-Patterns to Avoid

- ❌ Copying entire code blocks into memory files (reference the file instead)
- ❌ Including aspirational/planned features as current facts
- ❌ Duplicating ADR content in CONVENTIONS.md (summarize and cite instead)
- ❌ Mixing volatile state (current progress) with stable knowledge (architecture)
- ❌ Writing vague descriptions ("various tools") instead of specific names
- ❌ Leaving stale information after a refactor

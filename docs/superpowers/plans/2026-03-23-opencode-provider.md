# OpenCode Provider Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add OpenCode Zen as a first-class LLM provider for podcast script generation with configurable model support across Zen endpoint families.

**Architecture:** Extend `scripts/remix.py` with an `opencode` provider adapter that routes requests by model family to the correct Zen API surface and normalizes the returned text. Keep configuration simple in `config.yaml` while allowing optional base URL overrides. Add regression tests first, then update setup/docs/examples so the new provider is discoverable.

**Tech Stack:** Python 3.12, stdlib `urllib`, existing OpenAI/Anthropic SDKs, unittest, YAML/Markdown docs

---

## Chunk 1: Provider Routing

### Task 1: Add failing tests for OpenCode endpoint routing and response parsing

**Files:**
- Modify: `tests/test_remix.py`
- Test: `tests/test_remix.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run test to verify it fails**
  Run: `./.venv/bin/python tests/test_remix.py`
- [ ] **Step 3: Write minimal implementation**
- [ ] **Step 4: Run test to verify it passes**
  Run: `./.venv/bin/python tests/test_remix.py`

### Task 2: Implement OpenCode request adapter in remix

**Files:**
- Modify: `scripts/remix.py`
- Test: `tests/test_remix.py`

- [ ] **Step 1: Add endpoint selection helpers for Zen model families**
- [ ] **Step 2: Add REST request logic and text extraction for responses/messages/chat-completions**
- [ ] **Step 3: Keep existing anthropic/openai behavior unchanged**
- [ ] **Step 4: Re-run provider tests**
  Run: `./.venv/bin/python tests/test_remix.py`

## Chunk 2: Config And Docs

### Task 3: Add config examples and README coverage for OpenCode

**Files:**
- Modify: `README.md`
- Modify: `config.example.yaml`
- Modify: `config.yaml`
- Modify: `.env.example`

- [ ] **Step 1: Document `provider: opencode` and required env var**
- [ ] **Step 2: Document optional `base_url` override and model examples**
- [ ] **Step 3: Verify docs match actual implementation**

### Task 4: Final verification

**Files:**
- Modify: `tests/test_remix.py`
- Modify: `tests/test_utils.py`
- Modify: `scripts/remix.py`

- [ ] **Step 1: Run targeted tests**
  Run: `./.venv/bin/python tests/test_remix.py`
  Run: `./.venv/bin/python tests/test_utils.py`
- [ ] **Step 2: Run a lightweight import smoke**
  Run: `./.venv/bin/python -c "from remix import _call_llm; print('ok')"`
- [ ] **Step 3: Summarize remaining runtime prerequisites**

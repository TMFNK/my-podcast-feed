# my-podcast-feed

Forked from [zarazhangrui/my-podcast-feed](https://github.com/zarazhangrui/my-podcast-feed) by [@zarazhangrui](https://github.com/zarazhangrui).

An automated 4-stage pipeline (Fetch → Remix → Speak → Publish) that converts RSS newsletter feeds into personalized podcast episodes using AI.

- Pulls articles from configured RSS sources (e.g. Ben's Bites, Latent Space, Technically)
- Generates a conversational podcast script via an LLM (Claude or GPT) using Jinja2 prompt templates
- Converts the script to audio using Kokoro ONNX TTS with distinct voices per host
- Publishes the MP3 and an updated RSS feed to GitHub Pages so podcast players auto-download new episodes
- Runs on a 3-day GitHub Actions cron schedule or manually via CLI It fetches articles from configured sources, generates a natural-sounding podcast script with an LLM, converts it to audio via text-to-speech, and publishes it as a subscribable RSS feed on GitHub Pages.

## What It Does

Each run of the pipeline executes four stages:

1. **Fetch** — Pulls new articles from configured RSS feeds (e.g., tech newsletters, AI blogs). Filters out previously processed articles using a persistent state file.
2. **Remix** — Sends the fetched articles to an LLM (Anthropic Claude or OpenAI GPT) with a prompt template that instructs it to write a podcast conversation script. Supports single-host monologue or two-host conversational formats.
3. **Speak** — Converts each line of the script to audio using Kokoro ONNX text-to-speech (offline, no API needed). Each host gets a distinct voice. Audio segments are stitched together with pauses and fade effects into a single MP3.
4. **Publish** — Pushes the MP3 to a GitHub Pages repository, updates the RSS feed XML (`feed.xml`), and commits the changes. Podcast players subscribed to the feed automatically pick up new episodes.

## Who It's For

Anyone who wants to consume their daily newsletters as audio instead of reading them. Particularly useful for:

- Commuters who prefer listening over reading
- People who follow multiple newsletters but lack time to read them all
- Anyone wanting a personalized, AI-generated daily news summary in podcast form

## Architecture

```
scripts/
  run_pipeline.py   — Orchestrator; coordinates all four stages
  fetch.py          — Stage 1: RSS feed fetching and article extraction
  remix.py          — Stage 2: LLM-based podcast script generation
  speak.py          — Stage 3: Text-to-speech audio generation
  publish.py        — Stage 4: GitHub Pages deployment and RSS feed update
  utils.py          — Shared utilities (config, state, logging)
templates/
  prompt_1host.md   — LLM prompt template for single-host format
  prompt_2host.md   — LLM prompt template for two-host format
  feed_template.xml — Jinja2 template for RSS feed XML
.github/workflows/
  generate-episode.yml — GitHub Actions cron job (runs every 3 days)
episodes/           — Generated MP3 files
cover-art.png       — Podcast cover art
feed.xml            — RSS feed (served by GitHub Pages)
episodes.json       — Episode metadata
state.json          — Pipeline state (last run time, processed article IDs)
index.html          — Minimal landing page for the feed URL
```

## Requirements

- Python 3.12+
- ffmpeg (for audio processing via pydub)
- An [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/) API key (for script generation)
- GitHub CLI (`gh`) authenticated (for publishing, if running locally)

## Setup

### 1. Install dependencies

```bash
pip install feedparser anthropic openai kokoro-onnx soundfile pydub PyYAML Jinja2 python-dotenv
```

On macOS:
```bash
brew install ffmpeg
```

On Ubuntu:
```bash
sudo apt install ffmpeg
```

### 2. Create the config file

Create `~/.claude/personalized-podcast/config.yaml`:

```yaml
show_name: "My Daily Podcast"
hosts: 2                          # 1 or 2
length_minutes: 10
tone: "casual and conversational"
language: "en"

sources:
  rss:
    - https://www.bensbites.com/feed
    - https://read.technically.dev/feed
    - https://www.latent.space/feed

llm:
  provider: "anthropic"           # "anthropic" or "openai"
  api_key_env: "ANTHROPIC_API_KEY"
  model: "claude-sonnet-4-6"

tts:
  provider: "kokoro"
  host_a_voice: "af_heart"        # female voice — see VOICES.md for full list
  host_b_voice: "am_michael"      # male voice — see VOICES.md for full list
  lang_code: "a"                  # "a" = American English

publish:
  github_repo: "youruser/your-podcast-feed"
  github_pages_url: "https://youruser.github.io/your-podcast-feed"

retention:
  max_episodes: 30                # Auto-delete episodes beyond this limit
```

### 3. Set up API keys

Create `~/.claude/personalized-podcast/.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Set up the GitHub repo for publishing

Create a GitHub repo, enable GitHub Pages on the `main` branch, and add a `cover-art.png` for podcast artwork.

## Usage

### Run the full pipeline

```bash
python scripts/run_pipeline.py
```

### Resume from a specific stage

```bash
python scripts/run_pipeline.py --from-stage speak      # Re-run TTS only
python scripts/run_pipeline.py --from-stage remix      # Re-generate script + audio
```

### Retry a specific date's episode

```bash
python scripts/run_pipeline.py --from-stage speak --date 2026-03-14
```

### Skip publishing (e.g., for local testing)

```bash
python scripts/run_pipeline.py --skip-publish
```

### Run individual stages

```bash
python scripts/fetch.py    # Test fetching only
python scripts/remix.py    # Generate a script from fetched articles
python scripts/speak.py    # Convert a saved script to audio
python scripts/publish.py  # Publish the latest MP3
```

## Automated Scheduling

The included GitHub Actions workflow (`.github/workflows/generate-episode.yml`) runs the pipeline every 3 days at 8am Pacific. It can also be triggered manually from the Actions tab. API keys are stored as GitHub repository secrets (`ANTHROPIC_API_KEY`). The Hugging Face model cache is used to avoid re-downloading on every run.

## Subscribing

Add the feed URL to any podcast player (Apple Podcasts, Overcast, Pocket Casts, etc.):

```
https://youruser.github.io/your-podcast-feed/feed.xml
```

## Configuration Reference

| Key | Description | Default |
|-----|-------------|---------|
| `show_name` | Name of the podcast | `"My Daily Digest"` |
| `hosts` | Number of hosts (1 or 2) | `2` |
| `length_minutes` | Target episode length in minutes | `10` |
| `tone` | Writing style for the script | `"casual and conversational"` |
| `sources.rss` | List of RSS feed URLs to pull from | (required) |
| `llm.provider` | LLM provider (`"anthropic"` or `"openai"`) | `"anthropic"` |
| `llm.model` | Model name | `"claude-sonnet-4-6"` |
| `tts.host_a_voice` | Kokoro voice name for host A | `"af_heart"` |
| `tts.host_b_voice` | Kokoro voice name for host B | `"am_michael"` |
| `tts.lang_code` | Language code ("a" = American English) | `"a"` |
| `publish.github_repo` | GitHub repo for hosting | (required) |
| `publish.github_pages_url` | Base URL for GitHub Pages | (required) |
| `retention.max_episodes` | Max episodes to keep (oldest deleted) | `30` |

## Pipeline State

The pipeline tracks state in `~/.claude/personalized-podcast/state.json`:

- `last_run` — ISO timestamp of the last successful run (used to filter old articles)
- `processed_ids` — IDs of articles already processed (prevents duplicates; capped at 500)

State is also committed to the repo so GitHub Actions can restore it between runs.

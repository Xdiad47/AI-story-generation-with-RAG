# StoryNest — AI Story Generation with RAG

A full-stack platform that **automatically generates, reviews, and publishes children's stories** using an agentic AI pipeline (LangGraph + LangChain), and uses **ChromaDB + local HuggingFace embeddings** for semantic search and duplicate detection.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python) |
| AI Orchestration | LangGraph, LangChain |
| LLM Primary | OpenAI GPT-4o |
| LLM Fallback | Groq `llama-3.3-70b-versatile` |
| Vector Database | ChromaDB (local, file-based) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (runs 100% locally, no API key) |
| Scheduler | APScheduler (cron) |

---

## Project Structure

```
AI-story-generation-with-RAG/
├── backend/
│   ├── main.py                  # FastAPI app, all REST endpoints
│   ├── scheduler.py             # APScheduler — daily auto-generation at 08:00
│   ├── requirements.txt
│   ├── .env / .env.example      # OPENAI_API_KEY, GROQ_API_KEY
│   ├── agent/
│   │   ├── state.py             # StoryState TypedDict (shared pipeline state)
│   │   ├── pipeline.py          # LangGraph workflow definition + ChromaDB save
│   │   ├── llm_fallback.py      # OpenAI → Groq fallback logic
│   │   └── nodes/
│   │       ├── orchestrator.py  # Picks next story category (round-robin)
│   │       ├── story_writer.py  # Writes the story via LLM
│   │       ├── quality_reviewer.py  # Reviews quality via LLM
│   │       ├── image_agent.py   # Generates image prompts + placeholder URLs
│   │       └── social_media_agent.py  # Generates FB + Instagram captions
│   ├── db/
│   │   ├── stories.json         # JSON flat-file database
│   │   ├── vector_store.py      # ChromaDB singleton (THE semantic search engine)
│   │   └── chroma_db/           # Auto-created: persisted ChromaDB files
│   └── scripts/
│       ├── index_existing.py    # One-time bulk indexer for stories.json → ChromaDB
│       └── check_scores.py      # Debug tool: prints raw similarity scores
└── frontend/
    ├── app/
    │   ├── page.tsx             # Public story feed
    │   ├── types.ts             # Story TypeScript interface
    │   ├── story/[id]/          # Individual story reader page
    │   └── admin/
    │       ├── page.tsx         # Admin dashboard (server component)
    │       ├── AdminClient.tsx  # Admin UI with search, approve, reject
    │       └── AdminStoryActions.tsx
    └── components/
        └── semantic-search/     # (placeholder for future search component)
```

---

## Complete Application Flow

### 1. Story Auto-Generation (Scheduler)

Every day at **08:00 UTC**, `scheduler.py` triggers `generate_daily_stories()` which calls `generate_single_story()` three times in sequence.

```
APScheduler (cron 08:00)
    └── generate_single_story()
            └── workflow_app.invoke(initial_state)   ← LangGraph pipeline
```

The initial state only contains `run_id`, `status: "generating"`, and `created_at`.

---

### 2. LangGraph Agentic Pipeline

The pipeline is defined in `agent/pipeline.py` as a **StateGraph** with conditional routing. Every node reads from and writes to the shared `StoryState` dictionary.

```
START
  │
  ▼ route()
[orchestrator]  → picks next category (Epic→Mythology→Folktale→Sci-Fi→Fable→Adventure, round-robin)
  │
  ▼ route()
[story_writer]  → GPT-4o (or Groq fallback) writes 4-paragraph story as JSON
  │
  ▼ route()
[quality_reviewer] → GPT-4o reviews age-appropriateness, grammar, moral
  │
  ├── review_passed=False AND retry_count < 2 → back to [story_writer] with feedback
  ├── review_passed=False AND retry_count >= 2 → [failed] → set status=review_failed → END
  │
  ▼ review_passed=True
[image_agent]   → generates image prompts per paragraph + MD5-seeded picsum URLs
  │
  ▼ route()
[social_media_agent] → generates Facebook + Instagram captions as JSON
  │
  ▼ route()
[save]          → writes to stories.json AND indexes into ChromaDB
  │
  END
```

**Routing logic** (in `route()` function):
- If no `category` → go to `orchestrator`
- If no `story_text` → go to `story_writer`
- If `review_passed` is `None` → go to `quality_reviewer`
- If `review_passed` is `False` → retry writer (max 2 retries) or fail
- If no `image_urls` → go to `image_agent`
- If no `facebook_caption` → go to `social_media_agent`
- Otherwise → go to `save`

---

### 3. LLM Fallback Strategy

Every node calls `invoke_with_fallback()` from `llm_fallback.py`:

```
invoke_with_fallback(messages)
    ├── Try: OpenAI GPT-4o (max_retries=0 to fail fast)
    │     ├── Success → return response
    │     └── 429 insufficient_quota OR 401 invalid_api_key
    │           └── Fallback: Groq llama-3.3-70b-versatile
    └── Any other error → re-raise
```

This ensures the pipeline keeps running even with OpenAI quota exhaustion.

---

### 4. Story Saved to Two Stores

When the pipeline reaches the `save` node (`save_to_db()` in `pipeline.py`), two things happen simultaneously:

**A) Flat-file JSON DB (`db/stories.json`)**
- Story dict is appended (or upserted by `run_id`)
- Status is set to `"pending_approval"`

**B) ChromaDB Vector Store**
```python
vector_store.add_story(
    story_id=story_dict["run_id"],
    text=story_dict["story_text"],      # full story text is embedded
    metadata={
        "run_id": ..., "title": ...,
        "category": ..., "moral": ...,
        "age_range": ..., "created_at": ...
    }
)
```

---

## ChromaDB & Semantic Search — Deep Dive

### How ChromaDB is Set Up (`db/vector_store.py`)

`VectorStore` is implemented as a **Singleton** (only one instance exists for the entire FastAPI process lifetime):

```python
class VectorStore:
    _instance = None

    def __new__(cls):             # Singleton pattern
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_chroma()
        return cls._instance

    def _init_chroma(self):
        # Step 1: Load local embedding model (downloads once, cached in ~/.cache)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Step 2: Connect to local ChromaDB (file-based, no server needed)
        self.vector_store = Chroma(
            collection_name="stories",
            embedding_function=self.embeddings,
            persist_directory="backend/db/chroma_db",   # persisted to disk
            collection_metadata={"hnsw:space": "cosine"} # cosine similarity metric
        )
```

#### Key Design Decisions:
- **Local embeddings**: `all-MiniLM-L6-v2` runs on CPU. No OpenAI embeddings API needed.
- **File-based ChromaDB**: Data is persisted to `db/chroma_db/` — no Docker, no server.
- **Cosine similarity**: `hnsw:space: cosine` means scores are based on angular distance (0=unrelated, 1=identical).
- **Singleton**: prevents loading the 80MB model multiple times during a request lifecycle.

---

### How a Story Gets Indexed

```
story_text (raw string)
    │
    ▼
HuggingFace all-MiniLM-L6-v2
    │  Converts text → 384-dimensional float vector
    ▼
ChromaDB HNSW index
    │  Stores vector + metadata {"run_id", "title", "category", ...}
    ▼
Persisted to db/chroma_db/ on disk
```

The `add_story()` method:
```python
def add_story(self, story_id: str, text: str, metadata: dict):
    clean_metadata = {k: str(v) for k, v in metadata.items() if v is not None}
    self.vector_store.add_texts(
        texts=[text],          # full story body is embedded
        metadatas=[clean_metadata],
        ids=[story_id]         # run_id is the unique ChromaDB document ID
    )
```

---

### How Semantic Search Works (`GET /stories/search?q=...`)

**Step 1** — Query arrives at the FastAPI endpoint:
```python
@app.get("/stories/search")
def search_stories(q: str):
    from db.vector_store import vector_store
    results = vector_store.search_stories(q)
    ...
```

**Step 2** — Inside `search_stories()`:
```python
def search_stories(self, query: str, n_results: int = 5, threshold: float = 0.2):
    results = self.vector_store.similarity_search_with_relevance_scores(query, k=n_results)
    filtered_results = [doc for doc, score in results if score >= threshold]
    return filtered_results
```

What happens internally:
```
User query: "brave animals in the forest"
    │
    ▼ HuggingFace all-MiniLM-L6-v2
    │  Embeds query → 384-dim vector
    ▼ ChromaDB HNSW ANN search
    │  Finds k=5 nearest story vectors (cosine similarity)
    ▼ Relevance score filtering (threshold=0.2)
    │  Discards results with score < 0.2 (too dissimilar)
    ▼ Returns list of LangChain Document objects
        Each doc has: doc.page_content, doc.metadata["run_id"]
```

**Step 3** — Map back to full story objects:
```python
for doc in results:
    run_id = doc.metadata.get("run_id")
    story = next((s for s in stories if s.get("run_id") == run_id), None)
    if story:
        matched_stories.append(story)
return matched_stories
```

ChromaDB returns lightweight Document objects. The full story JSON (with image URLs, captions, etc.) is fetched from `stories.json` by matching `run_id`.

---

### How Duplicate Detection Works

```python
def check_duplicate(self, text: str, threshold: float = 0.9):
    results = self.vector_store.similarity_search_with_relevance_scores(text, k=1)
    if not results:
        return False, 0, None
    doc, score = results[0]
    if score > threshold:
        return True, score, doc.metadata.get("run_id")
    return False, score, doc.metadata.get("run_id")
```

- Searches for the **single most similar** story (`k=1`)
- If similarity score > **0.9** (very high, near-identical), it's flagged as a duplicate
- Returns `(is_duplicate: bool, score: float, original_story_id: str)`

> **Note**: `check_duplicate()` is implemented and available but is not yet called automatically within the pipeline. It can be integrated before the `save` node to block duplicate stories.

---

### Similarity Score Interpretation

| Score Range | Meaning |
|-------------|---------|
| 0.9 – 1.0 | Near-identical / duplicate |
| 0.7 – 0.9 | Highly similar theme |
| 0.4 – 0.7 | Related topic |
| 0.2 – 0.4 | Loosely related |
| 0.0 – 0.2 | Filtered out (below threshold) |

---

## Admin Dashboard — Semantic Search UI

In `frontend/app/admin/AdminClient.tsx`:

### Semantic Search Bar
```
User types: "space adventure"
    │
    ▼ handleSearch() — onSubmit
    │  GET http://127.0.0.1:8000/stories/search?q=space%20adventure
    ▼ setStories(results)   ← updates story list with semantically matched stories
```

### "Find Similar" Button (Duplicate Detection UI)
Every story row has a **Copy icon** button:
```
User clicks Copy icon on "Luna's Space Journey"
    │
    ▼ findSimilar(story.title)
    │  GET /stories/search?q=Luna's%20Space%20Journey
    ▼ Shows stories semantically similar to that title
       (visual way to spot potential duplicates)
```

---

## REST API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/stories` | All published stories |
| `GET` | `/stories/search?q=` | **Semantic search** via ChromaDB |
| `GET` | `/stories/{run_id}` | Single story by ID |
| `GET` | `/admin/stories` | All stories (all statuses) |
| `GET` | `/admin/stats` | Dashboard stats |
| `POST` | `/admin/generate` | Manually trigger story generation |
| `POST` | `/admin/approve/{run_id}` | Approve → status = published |
| `POST` | `/admin/reject/{run_id}` | Reject + provide feedback → re-runs pipeline |

---

## StoryState — Shared Pipeline Data Contract

```python
class StoryState(TypedDict):
    run_id: str                  # UUID, unique per generation run
    category: str                # Epic/Mythology/Folktale/Sci-Fi/Fable/Adventure
    title: str                   # Story title (set by story_writer)
    story_text: str              # Full story (paragraphs joined by \n\n)
    paragraphs: List[str]        # Individual paragraphs [p1, p2, p3, p4]
    summary: str                 # Two-sentence summary
    moral: str                   # The story's lesson
    age_range: str               # e.g. "5-8"
    review_passed: Optional[bool]  # None=not reviewed, True=pass, False=fail
    review_notes: str            # Reviewer feedback
    image_prompts: List[str]     # One prompt per paragraph
    image_urls: List[str]        # One URL per paragraph
    facebook_caption: str
    instagram_caption: str
    status: Literal["generating", "review_failed", "pending_approval",
                    "approved", "rejected_by_client", "published"]
    client_feedback: Optional[str]  # Feedback from admin rejection
    retry_count: int             # How many times writer retried
    created_at: str              # ISO UTC timestamp
    published_at: str            # ISO UTC timestamp (set on approval)
```

---

## Setup & Running Locally

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Copy and fill in API keys
copy .env.example .env
# Edit .env: add OPENAI_API_KEY and GROQ_API_KEY

# Start FastAPI server
uvicorn main:app --reload --port 8000
```

### Index Existing Stories into ChromaDB
Run this once after seeding stories.json, or any time you add stories manually:
```bash
cd backend
python scripts/index_existing.py
```

### Debug Similarity Scores
```bash
cd backend
python scripts/check_scores.py
# Runs test queries: "fox", "brave", "pizza", "space journey"
# Prints raw cosine similarity scores for each
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:3000
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes* | Primary LLM for story writing + review |
| `GROQ_API_KEY` | Yes* | Fallback LLM when OpenAI quota is exhausted |

*If OpenAI quota is exhausted and GROQ_API_KEY is present, the pipeline automatically switches to Groq. Both keys are recommended.

---

## Data Flow Summary

```
[Scheduler / Admin trigger]
        │
        ▼
[LangGraph Pipeline]
   Orchestrator → StoryWriter → QualityReviewer → ImageAgent → SocialMediaAgent
        │                              ↑ retry (max 2x)
        ▼
[save_to_db()]
   ├── stories.json  (source of truth for full story data)
   └── ChromaDB      (vector index for semantic search)
        │ story_text embedded with all-MiniLM-L6-v2
        │ stored with {run_id, title, category, moral, age_range}
        ▼
[Admin Dashboard]
   Search bar → GET /stories/search?q= → ChromaDB similarity_search
             → returns run_ids → fetch full story from stories.json
             → display results

[Public Feed]
   GET /stories → stories.json (published only) → Next.js renders cards
```

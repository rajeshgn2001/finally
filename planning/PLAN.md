# FinAlly — AI Trading Workstation

## Project Specification

## 1. Vision

FinAlly (Finance Ally) is a visually stunning AI-powered trading workstation that streams live market data, lets users trade a simulated portfolio, and integrates an LLM chat assistant that can analyze positions and execute trades on the user's behalf. It looks and feels like a modern Bloomberg terminal with an AI copilot.

This is the capstone project for an agentic AI coding course. It is built entirely by Coding Agents demonstrating how orchestrated AI agents can produce a production-quality full-stack application. Agents interact through files in `planning/`.

## 2. User Experience

### First Launch

The user runs a single Docker command (or a provided start script). A browser opens to `http://localhost:8000`. No login, no signup. They immediately see:

- A watchlist of 10 default tickers with live-updating prices in a grid
- $10,000 in virtual cash
- A dark, data-rich trading terminal aesthetic
- An AI chat panel ready to assist

### What the User Can Do

- **Watch prices stream** — prices flash green (uptick) or red (downtick) with subtle CSS animations that fade
- **View sparkline mini-charts** — price action beside each ticker in the watchlist, accumulated on the frontend from the SSE stream since page load (sparklines fill in progressively)
- **Click a ticker** to see a larger detailed chart in the main chart area
- **Buy and sell shares** — market orders only, instant fill at current price, no fees, no confirmation dialog
- **Monitor their portfolio** — a heatmap (treemap) showing positions sized by weight and colored by P&L, plus a P&L chart tracking total portfolio value over time
- **View a positions table** — ticker, quantity, average cost, current price, unrealized P&L, % change
- **Chat with the AI assistant** — ask about their portfolio, get analysis, and have the AI execute trades and manage the watchlist through natural language
- **Manage the watchlist** — add/remove tickers manually or via the AI chat

### Visual Design

- **Dark theme**: backgrounds around `#0d1117` or `#1a1a2e`, muted gray borders, no pure black
- **Price flash animations**: brief green/red background highlight on price change, fading over ~500ms via CSS transitions
- **Connection status indicator**: a small colored dot (green = connected, yellow = reconnecting, red = disconnected) visible in the header
- **Professional, data-dense layout**: inspired by Bloomberg/trading terminals — every pixel earns its place
- **Responsive but desktop-first**: optimized for wide screens, functional on tablet

### Color Scheme
- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991` (submit buttons)

## 3. Architecture Overview

### Single Container, Single Port

```
┌─────────────────────────────────────────────────┐
│  Docker Container (port 8000)                   │
│                                                 │
│  FastAPI (Python/uv)                            │
│  ├── /api/*          REST endpoints             │
│  ├── /api/stream/*   SSE streaming              │
│  └── /*              Static file serving         │
│                      (Next.js export)            │
│                                                 │
│  SQLite database (volume-mounted)               │
│  Background task: market data polling/sim        │
└─────────────────────────────────────────────────┘
```

- **Frontend**: Next.js with TypeScript, built as a static export (`output: 'export'`), served by FastAPI as static files
- **Backend**: FastAPI (Python), managed as a `uv` project
- **Database**: SQLite, single file at `db/finally.db`, volume-mounted for persistence
- **Real-time data**: Server-Sent Events (SSE) — simpler than WebSockets, one-way server→client push, works everywhere
- **AI integration**: LiteLLM → OpenRouter (Cerebras for fast inference), with structured outputs for trade execution
- **Market data**: Environment-variable driven — simulator by default, real data via Massive API if key provided

### Why These Choices

| Decision | Rationale |
|---|---|
| SSE over WebSockets | One-way push is all we need; simpler, no bidirectional complexity, universal browser support |
| Static Next.js export | Single origin, no CORS issues, one port, one container, simple deployment |
| SQLite over Postgres | No auth = no multi-user = no need for a database server; self-contained, zero config |
| Single Docker container | Students run one command; no docker-compose for production, no service orchestration |
| uv for Python | Fast, modern Python project management; reproducible lockfile; what students should learn |
| Market orders only | Eliminates order book, limit order logic, partial fills — dramatically simpler portfolio math |

---

## 4. Directory Structure

```
finally/
├── frontend/                 # Next.js TypeScript project (static export)
├── backend/                  # FastAPI uv project (Python)
│   └── db/                   # Schema definitions, seed data, migration logic
├── planning/                 # Project-wide documentation for agents
│   ├── PLAN.md               # This document
│   └── ...                   # Additional agent reference docs
├── scripts/
│   ├── start_mac.sh          # Launch Docker container (macOS/Linux)
│   ├── stop_mac.sh           # Stop Docker container (macOS/Linux)
│   ├── start_windows.ps1     # Launch Docker container (Windows PowerShell)
│   └── stop_windows.ps1      # Stop Docker container (Windows PowerShell)
├── test/                     # Playwright E2E tests + docker-compose.test.yml
├── db/                       # Volume mount target (SQLite file lives here at runtime)
│   └── .gitkeep              # Directory exists in repo; finally.db is gitignored
├── Dockerfile                # Multi-stage build (Node → Python)
├── docker-compose.yml        # Optional convenience wrapper
├── .env                      # Environment variables (gitignored, .env.example committed)
└── .gitignore
```

### Key Boundaries

- **`frontend/`** is a self-contained Next.js project. It knows nothing about Python. It talks to the backend via `/api/*` endpoints and `/api/stream/*` SSE endpoints. Internal structure is up to the Frontend Engineer agent.
- **`backend/`** is a self-contained uv project with its own `pyproject.toml`. It owns all server logic including database initialization, schema, seed data, API routes, SSE streaming, market data, and LLM integration. Internal structure is up to the Backend/Market Data agents.
- **`backend/db/`** contains schema SQL definitions and seed logic. The backend lazily initializes the database on first request — creating tables and seeding default data if the SQLite file doesn't exist or is empty.
- **`db/`** at the top level is the runtime volume mount point. The SQLite file (`db/finally.db`) is created here by the backend and persists across container restarts via Docker volume.
- **`planning/`** contains project-wide documentation, including this plan. All agents reference files here as the shared contract.
- **`test/`** contains Playwright E2E tests and supporting infrastructure (e.g., `docker-compose.test.yml`). Unit tests live within `frontend/` and `backend/` respectively, following each framework's conventions.
- **`scripts/`** contains start/stop scripts that wrap Docker commands.

---

## 5. Environment Variables

```bash
# Required: OpenRouter API key for LLM chat functionality
OPENROUTER_API_KEY=your-openrouter-api-key-here

# Optional: Massive (Polygon.io) API key for real market data
# If not set, the built-in market simulator is used (recommended for most users)
MASSIVE_API_KEY=

# Optional: Set to "true" for deterministic mock LLM responses (testing)
LLM_MOCK=false
```

### Behavior

- If `MASSIVE_API_KEY` is set and non-empty → backend uses Massive REST API for market data
- If `MASSIVE_API_KEY` is absent or empty → backend uses the built-in market simulator
- If `LLM_MOCK=true` → backend returns deterministic mock LLM responses (for E2E tests)
- The backend reads `.env` from the project root (mounted into the container or read via docker `--env-file`)

---

## 6. Market Data

### Two Implementations, One Interface

Both the simulator and the Massive client implement the same abstract interface. The backend selects which to use based on the environment variable. All downstream code (SSE streaming, price cache, frontend) is agnostic to the source.

### Simulator (Default)

- Generates prices using geometric Brownian motion (GBM) with configurable drift and volatility per ticker
- Updates at ~500ms intervals
- Correlated moves across tickers (e.g., tech stocks move together)
- Occasional random "events" — sudden 2-5% moves on a ticker for drama
- Starts from realistic seed prices (e.g., AAPL ~$190, GOOGL ~$175, etc.)
- Runs as an in-process background task — no external dependencies

### Massive API (Optional)

- REST API polling (not WebSocket) — simpler, works on all tiers
- Polls for the union of all watched tickers on a configurable interval
- Free tier (5 calls/min): poll every 15 seconds
- Paid tiers: poll every 2-15 seconds depending on tier
- Parses REST response into the same format as the simulator

### Shared Price Cache

- A single background task (simulator or Massive poller) writes to an in-memory price cache
- The cache holds the latest price, previous price, and timestamp for each ticker
- SSE streams read from this cache and push updates to connected clients
- This architecture supports future multi-user scenarios without changes to the data layer

### SSE Streaming

- Endpoint: `GET /api/stream/prices`
- Long-lived SSE connection; client uses native `EventSource` API
- Server pushes price updates for all tickers known to the system at a regular cadence (~500ms) — in the single-user model this is equivalent to the user's watchlist
- Each SSE event contains ticker, price, previous price, timestamp, and change direction
- Client handles reconnection automatically (EventSource has built-in retry)

---

## 7. Database

### SQLite with Lazy Initialization

The backend checks for the SQLite database on startup (or first request). If the file doesn't exist or tables are missing, it creates the schema and seeds default data. This means:

- No separate migration step
- No manual database setup
- Fresh Docker volumes start with a clean, seeded database automatically

### Schema

All tables include a `user_id` column defaulting to `"default"`. This is hardcoded for now (single-user) but enables future multi-user support without schema migration.

**users_profile** — User state (cash balance)
- `id` TEXT PRIMARY KEY (default: `"default"`)
- `cash_balance` REAL (default: `10000.0`)
- `created_at` TEXT (ISO timestamp)

**watchlist** — Tickers the user is watching
- `id` TEXT PRIMARY KEY (UUID)
- `user_id` TEXT (default: `"default"`)
- `ticker` TEXT
- `added_at` TEXT (ISO timestamp)
- UNIQUE constraint on `(user_id, ticker)`

**positions** — Current holdings (one row per ticker per user)
- `id` TEXT PRIMARY KEY (UUID)
- `user_id` TEXT (default: `"default"`)
- `ticker` TEXT
- `quantity` REAL (fractional shares supported)
- `avg_cost` REAL
- `updated_at` TEXT (ISO timestamp)
- UNIQUE constraint on `(user_id, ticker)`

**trades** — Trade history (append-only log)
- `id` TEXT PRIMARY KEY (UUID)
- `user_id` TEXT (default: `"default"`)
- `ticker` TEXT
- `side` TEXT (`"buy"` or `"sell"`)
- `quantity` REAL (fractional shares supported)
- `price` REAL
- `executed_at` TEXT (ISO timestamp)

**portfolio_snapshots** — Portfolio value over time (for P&L chart). Recorded every 30 seconds by a background task, and immediately after each trade execution.
- `id` TEXT PRIMARY KEY (UUID)
- `user_id` TEXT (default: `"default"`)
- `total_value` REAL
- `recorded_at` TEXT (ISO timestamp)

**chat_messages** — Conversation history with LLM
- `id` TEXT PRIMARY KEY (UUID)
- `user_id` TEXT (default: `"default"`)
- `role` TEXT (`"user"` or `"assistant"`)
- `content` TEXT
- `actions` TEXT (JSON — trades executed, watchlist changes made; null for user messages)
- `created_at` TEXT (ISO timestamp)

### Default Seed Data

- One user profile: `id="default"`, `cash_balance=10000.0`
- Ten watchlist entries: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX

---

## 8. API Endpoints

### Market Data
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stream/prices` | SSE stream of live price updates |

### Portfolio
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/portfolio` | Current positions, cash balance, total value, unrealized P&L |
| POST | `/api/portfolio/trade` | Execute a trade: `{ticker, quantity, side}` |
| GET | `/api/portfolio/history` | Portfolio value snapshots over time (for P&L chart) |

### Watchlist
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/watchlist` | Current watchlist tickers with latest prices |
| POST | `/api/watchlist` | Add a ticker: `{ticker}` |
| DELETE | `/api/watchlist/{ticker}` | Remove a ticker |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Send a message, receive complete JSON response (message + executed actions) |

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check (for Docker/deployment) |

---

## 9. LLM Integration

When writing code to make calls to LLMs, use cerebras-inference skill to use LiteLLM via OpenRouter to the `openrouter/openai/gpt-oss-120b` model with Cerebras as the inference provider. Structured Outputs should be used to interpret the results.

There is an OPENROUTER_API_KEY in the .env file in the project root.

### How It Works

When the user sends a chat message, the backend:

1. Loads the user's current portfolio context (cash, positions with P&L, watchlist with live prices, total portfolio value)
2. Loads recent conversation history from the `chat_messages` table
3. Constructs a prompt with a system message, portfolio context, conversation history, and the user's new message
4. Calls the LLM via LiteLLM → OpenRouter, requesting structured output, using the cerebras-inference skill
5. Parses the complete structured JSON response
6. Auto-executes any trades or watchlist changes specified in the response
7. Stores the message and executed actions in `chat_messages`
8. Returns the complete JSON response to the frontend (no token-by-token streaming — Cerebras inference is fast enough that a loading indicator is sufficient)

### Structured Output Schema

The LLM is instructed to respond with JSON matching this schema:

```json
{
  "message": "Your conversational response to the user",
  "trades": [
    {"ticker": "AAPL", "side": "buy", "quantity": 10}
  ],
  "watchlist_changes": [
    {"ticker": "PYPL", "action": "add"}
  ]
}
```

- `message` (required): The conversational text shown to the user
- `trades` (optional): Array of trades to auto-execute. Each trade goes through the same validation as manual trades (sufficient cash for buys, sufficient shares for sells)
- `watchlist_changes` (optional): Array of watchlist modifications

### Auto-Execution

Trades specified by the LLM execute automatically — no confirmation dialog. This is a deliberate design choice:
- It's a simulated environment with fake money, so the stakes are zero
- It creates an impressive, fluid demo experience
- It demonstrates agentic AI capabilities — the core theme of the course

If a trade fails validation (e.g., insufficient cash), the error is included in the chat response so the LLM can inform the user.

### System Prompt Guidance

The LLM should be prompted as "FinAlly, an AI trading assistant" with instructions to:
- Analyze portfolio composition, risk concentration, and P&L
- Suggest trades with reasoning
- Execute trades when the user asks or agrees
- Manage the watchlist proactively
- Be concise and data-driven in responses
- Always respond with valid structured JSON

### LLM Mock Mode

When `LLM_MOCK=true`, the backend returns deterministic mock responses instead of calling OpenRouter. This enables:
- Fast, free, reproducible E2E tests
- Development without an API key
- CI/CD pipelines

---

## 10. Frontend Design

### Layout

The frontend is a single-page application with a dense, terminal-inspired layout. The specific component architecture and layout system is up to the Frontend Engineer, but the UI should include these elements:

- **Watchlist panel** — grid/table of watched tickers with: ticker symbol, current price (flashing green/red on change), daily change %, and a sparkline mini-chart (accumulated from SSE since page load)
- **Main chart area** — larger chart for the currently selected ticker, with at minimum price over time. Clicking a ticker in the watchlist selects it here.
- **Portfolio heatmap** — treemap visualization where each rectangle is a position, sized by portfolio weight, colored by P&L (green = profit, red = loss)
- **P&L chart** — line chart showing total portfolio value over time, using data from `portfolio_snapshots`
- **Positions table** — tabular view of all positions: ticker, quantity, avg cost, current price, unrealized P&L, % change
- **Trade bar** — simple input area: ticker field, quantity field, buy button, sell button. Market orders, instant fill.
- **AI chat panel** — docked/collapsible sidebar. Message input, scrolling conversation history, loading indicator while waiting for LLM response. Trade executions and watchlist changes shown inline as confirmations.
- **Header** — portfolio total value (updating live), connection status indicator, cash balance

### Technical Notes

- Use `EventSource` for SSE connection to `/api/stream/prices`
- Canvas-based charting library preferred (Lightweight Charts or Recharts) for performance
- Price flash effect: on receiving a new price, briefly apply a CSS class with background color transition, then remove it
- All API calls go to the same origin (`/api/*`) — no CORS configuration needed
- Tailwind CSS for styling with a custom dark theme

---

## 11. Docker & Deployment

### Multi-Stage Dockerfile

```
Stage 1: Node 20 slim
  - Copy frontend/
  - npm install && npm run build (produces static export)

Stage 2: Python 3.12 slim
  - Install uv
  - Copy backend/
  - uv sync (install Python dependencies from lockfile)
  - Copy frontend build output into a static/ directory
  - Expose port 8000
  - CMD: uvicorn serving FastAPI app
```

FastAPI serves the static frontend files and all API routes on port 8000.

### Docker Volume

The SQLite database persists via a named Docker volume:

```bash
docker run -v finally-data:/app/db -p 8000:8000 --env-file .env finally
```

The `db/` directory in the project root maps to `/app/db` in the container. The backend writes `finally.db` to this path.

### Start/Stop Scripts

**`scripts/start_mac.sh`** (macOS/Linux):
- Builds the Docker image if not already built (or if `--build` flag passed)
- Runs the container with the volume mount, port mapping, and `.env` file
- Prints the URL to access the app
- Optionally opens the browser

**`scripts/stop_mac.sh`** (macOS/Linux):
- Stops and removes the running container
- Does NOT remove the volume (data persists)

**`scripts/start_windows.ps1`** / **`scripts/stop_windows.ps1`**: PowerShell equivalents for Windows.

All scripts should be idempotent — safe to run multiple times.

### Optional Cloud Deployment

The container is designed to deploy to AWS App Runner, Render, or any container platform. A Terraform configuration for App Runner may be provided in a `deploy/` directory as a stretch goal, but is not part of the core build.

---

## 12. Testing Strategy

### Unit Tests (within `frontend/` and `backend/`)

**Backend (pytest)**:
- Market data: simulator generates valid prices, GBM math is correct, Massive API response parsing works, both implementations conform to the abstract interface
- Portfolio: trade execution logic, P&L calculations, edge cases (selling more than owned, buying with insufficient cash, selling at a loss)
- LLM: structured output parsing handles all valid schemas, graceful handling of malformed responses, trade validation within chat flow
- API routes: correct status codes, response shapes, error handling

**Frontend (React Testing Library or similar)**:
- Component rendering with mock data
- Price flash animation triggers correctly on price changes
- Watchlist CRUD operations
- Portfolio display calculations
- Chat message rendering and loading state

### E2E Tests (in `test/`)

**Infrastructure**: A separate `docker-compose.test.yml` in `test/` that spins up the app container plus a Playwright container. This keeps browser dependencies out of the production image.

**Environment**: Tests run with `LLM_MOCK=true` by default for speed and determinism.

**Key Scenarios**:
- Fresh start: default watchlist appears, $10k balance shown, prices are streaming
- Add and remove a ticker from the watchlist
- Buy shares: cash decreases, position appears, portfolio updates
- Sell shares: cash increases, position updates or disappears
- Portfolio visualization: heatmap renders with correct colors, P&L chart has data points
- AI chat (mocked): send a message, receive a response, trade execution appears inline
- SSE resilience: disconnect and verify reconnection

---

## 13. Review: Questions, Clarifications & Simplifications

*Added by doc review (2026-11-06). Cross-checked against the built market data code in `backend/app/market/`. Items are grouped by priority; each has a suggested default so implementation isn't blocked.*

### A. Gaps that will block or confuse implementation

1. **"Daily change %" has no data source.** The watchlist spec asks for daily change %, but `PriceUpdate.change_percent` is tick-to-tick (vs previous ~500ms price), and the simulator has no concept of a session open. **Suggest:** define daily change as change vs the seed price (simulator) / previous close (Massive), stored on the cache as `open_price`, and include it in the SSE payload. Or drop "daily" and show change since page load.
2. **SSE payload shape differs from §6.** §6 implies one event per ticker; the built stream sends one event containing a dict of *all* tickers (`{"AAPL": {...}, "GOOGL": {...}}`), and only when the cache version changes. Document the actual shape here so the frontend agent codes against it.
3. **Watchlist vs. price-source ticker set.** Not stated: when a ticker is removed from the watchlist but a position is still held, does it keep streaming? Without a price, portfolio valuation breaks. **Suggest:** the source tracks `watchlist ∪ held positions`; removing from the watchlist never removes a held ticker's price feed.
4. **Ticker validation is unspecified.** What happens on `POST /api/watchlist {"ticker": "ZZZZ"}`? The simulator will happily invent a price for anything; Massive will return nothing. **Suggest:** uppercase + regex (`^[A-Z.]{1,10}$`); simulator accepts any valid symbol with a default seed price; Massive rejects tickers with no snapshot (404/422).
5. **Trade price when no price is cached yet.** A trade on a just-added ticker may arrive before the first price. **Suggest:** reject with 409/422 "price unavailable".
6. **Error response format.** No standard error shape. **Suggest:** FastAPI default `{"detail": "..."}` with 400 for validation failures (insufficient cash/shares), 404 for unknown ticker on DELETE.
7. **Response schemas for REST endpoints are undefined.** `GET /api/portfolio`, `/api/portfolio/history`, `/api/watchlist`, and `/api/chat` need explicit JSON shapes — this is the frontend/backend contract and the most likely source of agent mismatch. **Suggest:** add a short example response for each.
8. **Chat response `actions` shape.** The response must report per-action results (success/failure + error message), not just echo the LLM's request. Define e.g. `{"message": str, "trades": [{ticker, side, quantity, price?, status, error?}], "watchlist_changes": [{ticker, action, status, error?}]}`.
9. **LLM failure handling.** What does `/api/chat` return if OpenRouter times out, the key is missing, or the output fails schema validation? **Suggest:** return 200 with a friendly assistant message and no actions; never 500 to the UI. Missing `OPENROUTER_API_KEY` with `LLM_MOCK=false` should log a warning at startup, not crash.
10. **Conversation history length.** "Recent conversation history" — how many? **Suggest:** last 20 messages.
11. **Mock LLM behavior.** E2E tests need the mock to produce a trade. Specify the deterministic rule, e.g. message containing "buy N TICKER" → that trade; otherwise a fixed reply with no actions.

### B. Clarifications / inconsistencies

12. **`users_profile` has no `user_id` column**, contradicting "All tables include a `user_id` column". Fine as-is (`id` *is* the user id) — just reword the sentence.
13. **Position closing.** When a sell brings quantity to 0, delete the row (so it "disappears" per the E2E test). State this explicitly; also define a float epsilon (e.g. `< 1e-9` → 0) since fractional shares are allowed.
14. **Average cost on sells.** Confirm: sells don't change `avg_cost`; buys use weighted average. Realized P&L isn't tracked anywhere — confirm that's intended (it isn't in the schema or UI).
15. **Quantity validation.** Must be `> 0`; side must be `buy|sell`. Any minimum (e.g. 0.0001) or max precision?
16. **Snapshot task with Massive.** On the free tier prices change every 15s, snapshots every 30s — fine, but note snapshots are taken even when nothing changed. Should snapshot history be capped/pruned? At 30s intervals it's ~2,900 rows/day — harmless for SQLite, but the history endpoint should probably downsample or limit.
17. **"Lazy initialization on first request" vs "on startup".** §4 and §7 say different things. **Suggest:** initialize in the FastAPI lifespan at startup — simpler and the snapshot background task needs the DB anyway.
18. **`.env` location in Docker.** §5 says backend reads `.env` from project root; §11 uses `--env-file`. Pick `--env-file` for Docker and `python-dotenv` (or uv's env loading) only for local dev.
19. **Static file serving + client routing.** With a single page there's no routing, but state that FastAPI mounts `StaticFiles(directory="static", html=True)` *after* API routers so `/api/*` isn't shadowed.
20. **Chart library.** "Lightweight Charts or Recharts" — Recharts is SVG, not canvas. Pick one: **Lightweight Charts** for price/P&L charts. The treemap needs something else (Recharts `Treemap` or a small hand-rolled squarify) — say which.
21. **Header "total value updating live"** requires the frontend to compute value = cash + Σ(qty × live price) from SSE, rather than re-polling `/api/portfolio`. Confirm that's intended.
22. **Minor code note:** `stream.py` declares `router` at module level and `create_stream_router()` decorates it, so calling the factory twice registers the route twice (matters in tests). Move `router = APIRouter(...)` inside the factory.

### C. Opportunities to simplify

23. **Drop `id` UUIDs where a natural key exists.** `watchlist` and `positions` already have `UNIQUE(user_id, ticker)`; making that the primary key removes UUID generation and simplifies upserts (`INSERT ... ON CONFLICT`). Keep UUIDs only for append-only tables (or use `INTEGER PRIMARY KEY AUTOINCREMENT` there too).
24. **Store cash in `users_profile` only** — already the case; avoid any temptation to derive cash from the trade log.
25. **Skip the `docker-compose.yml`** at the root — the start scripts cover it and it's one more thing to keep in sync. Keep only `test/docker-compose.test.yml`.
26. **Windows scripts.** Unless Windows users are a confirmed audience, a single `docker run` line in the README may suffice; otherwise keep them trivially thin.
27. **E2E infra.** Running Playwright from the host (`npx playwright test` against `localhost:8000`) is simpler than a Playwright container in compose. Consider the container only for CI.
28. **Frontend unit tests.** Scope down to the logic most likely to break (portfolio math, SSE parsing, flash-trigger). Component rendering tests for every panel add little for a demo app.
29. **`portfolio_snapshots` table is optional.** The P&L chart could be computed client-side from SSE since page load (like sparklines), dropping the table and the background task. Recommendation: keep the table — a chart that survives reloads is a nicer demo — but this is the cut to make if time is short.
30. **SSE dict payload is good** — keeping "all prices in one event" (as built) is simpler for the frontend than per-ticker events; just document it (see #2).

### D. Open questions for the project owner

- Should the AI be allowed to trade tickers not on the watchlist (auto-adding them)?
- Is there a cap on position size or any "risk" guardrail for AI trades, or is anything within cash allowed?
- Is a "reset portfolio" action wanted for demos?
- Should chat history persist across reloads in the UI (load from `chat_messages` on page load)? Implied but not stated — needs a `GET /api/chat/history` endpoint if so.

### E. Second pass — additional items

31. **Timestamp formats are mixed.** SSE `timestamp` is Unix seconds (float); every DB column is an ISO string. **Suggest:** keep both but state it explicitly — ISO 8601 UTC with `Z` in the DB and REST, Unix seconds only in SSE (cheap for charts).
32. **Price/quantity rounding.** Trades fill at the cached float price (e.g. `190.48731`). **Suggest:** round fill prices to 2 dp and cash to 2 dp on write; quantities to 4 dp. Otherwise P&L displays drift and tests get flaky.
33. **Concurrent trades.** Manual trades and chat-driven trades can race on cash/position reads. **Suggest:** run each trade in a single SQLite transaction (`BEGIN IMMEDIATE`) or behind an `asyncio.Lock` — one line, prevents double-spend.
34. **Manual trades on tickers not in the watchlist.** Allowed? If yes, the ticker has no price yet (see #5). **Suggest:** a buy auto-adds the ticker to the watchlist (and the price source) — same rule for AI and manual trades.
35. **"Manage the watchlist proactively" + auto-execution** means the AI may add/remove tickers the user never asked about. **Suggest:** proactive *suggestions* only; execute watchlist changes when asked — or accept it and say so.
36. **Heatmap details.** Is cash shown as a tile? What P&L % maps to full green/red? **Suggest:** exclude cash; color scale clamps at ±5%; empty state when no positions.
37. **`GET /api/watchlist` "with latest prices"** duplicates SSE. **Simplify:** return tickers only (or include the cached price just for the first paint) — the frontend gets prices from SSE anyway.
38. **Sparkline/chart memory.** Data accumulates from SSE at 2 Hz forever. **Suggest:** cap client-side buffers (e.g. last 600 points ≈ 5 min per ticker).
39. **`GET /api/health` response.** Define it, e.g. `{"status": "ok"}`, and use it in the Dockerfile `HEALTHCHECK` and E2E wait step.
40. **Static export path.** Next.js `output: 'export'` writes to `frontend/out/`; the Dockerfile should copy `out/` → `backend/static/`. Worth stating since it's a classic agent mismatch.
41. **Structured output support.** Confirm `gpt-oss-120b` on Cerebras via OpenRouter honors `response_format` JSON schema; if not, the fallback is "JSON mode + Pydantic validation + one retry". Document which approach is used so the LLM and test agents agree.

# WebPilot AI – Autonomous Browser Assistant

[![Docker Compose](https://img.shields.io/badge/docker--compose-up-%232496ed.svg?logo=docker)](https://docs.docker.com/compose/)
[![React](https://img.shields.io/badge/React-19-%2361dafb.svg?logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-%23009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-%232e8b57.svg?logo=playwright)](https://playwright.dev/)
[![Gemini](https://img.shields.io/badge/Google-Gemini-%238E75C2.svg?logo=google)](https://ai.google.dev/)

WebPilot AI is an enterprise-grade, production-ready autonomous browser assistant. Users input high-level, natural language instructions (e.g. *"Compare iPhone 16 prices on Amazon and Flipkart under ₹70,000"*), and the assistant automatically reasons about the goal, creates a structured execution plan, opens a browser instance, navigates websites, extracts data dynamically, recovers from errors, and produces comprehensive downloadable reports.

---

## 🚀 Key Features

*   **AI Planning Engine**: Translates natural language requests into structured execution plans using Gemini AI.
*   **Live Browser Preview**: Stream real-time browser actions via WebSocket using base64-encoded screenshot updates.
*   **Self-Healing Automation**: Robust failure recovery mechanism featuring 5 escalating self-healing strategies (wait-and-retry, scroll, reload, AI-guided selector replacement, and optional step skipping).
*   **Dynamic DOM Discovery**: No hardcoded selectors. Finds fields, buttons, and links using semantic tags, placeholders, aria-labels, and relative layout positioning.
*   **Human-Like Interactions**: Smooth mouse hover, random typing speeds, scrolling, and intelligent page waits to bypass bot detection.
*   **Interactive Analytics**: Tracks completed/failed tasks, execution durations, success rates, and frequently visited domains using interactive charts.
*   **Rich Reports**: Generates downloadable PDF summaries (with step timeline), CSV, and JSON formats for extracted datasets.
*   **Futuristic UI**: High-fidelity dark mode interface built with React 19, Tailwind CSS, Framer Motion, and Chart.js.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Zustand, TanStack Query, Framer Motion, Chart.js | Modern, responsive dashboard, real-time logs, live browser frame. |
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy (Async), Alembic, Pydantic, Uvicorn | High-performance async APIs, WebSockets, background tasks. |
| **Automation** | Playwright | Reliable chromium/firefox automation, headless/headed browser control. |
| **Database** | PostgreSQL | Persistent task history, session metrics, logs, download/report file tracking. |
| **Caching/Queue**| Redis | Task execution messaging, pub/sub. |
| **Proxy** | Nginx | Reverse proxy mapping frontend, API, and WebSockets. |

---

## 🏗️ Folder Structure

```
webpilot-ai/
├── frontend/               # React 19 + Vite + Tailwind + Chart.js
│   ├── src/
│   │   ├── components/     # UI elements (BrowserPreview, ExecutionPlan, LogViewer)
│   │   ├── pages/          # Dashboard, TaskHistory, Analytics, Settings, Auth
│   │   ├── services/       # HTTP/WebSocket client endpoints
│   │   ├── stores/         # Zustand global states (Auth, ActiveTask, UI)
│   │   └── types/          # Strict TypeScript type definitions
├── backend/                # FastAPI Application
│   ├── app/
│   │   ├── api/            # API Router endpoints (auth, tasks, analytics, reports)
│   │   ├── core/           # Security, async database engine, config settings, logging
│   │   ├── models/         # SQLAlchemy schemas (User, Task, Session, Log, Report)
│   │   └── agent/          # Autonomous Agent Core
│   │       ├── planner/    # Gemini task reasoning and execution planning
│   │       ├── browser/    # Playwright browser lifecycle manager
│   │       ├── executor/   # Step dispatch handlers
│   │       ├── dom/        # Dynamic element detection & auto-extraction
│   │       ├── recovery/   # Self-healing logic
│   │       └── reports/    # PDF (ReportLab), CSV, JSON report builders
│   ├── alembic/            # Database migration histories
│   └── tests/              # Pytest unit & integration test suites
├── docker/                 # Nginx proxy mapping & deployment Dockerfiles
└── docker-compose.yml      # Complete stack definition
```

---

## ⚡ Quickstart (Docker Compose)

The easiest way to start WebPilot AI is using Docker Compose.

### 1. Prerequisites
*   [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
*   A **Google Gemini API Key** (obtain from [Google AI Studio](https://aistudio.google.com/))

### 2. Configure Environment
Clone the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your Gemini API Key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 3. Launch the Stack
Run Docker Compose:
```bash
docker-compose up --build
```
This builds and launches:
*   **Postgres**: Database listening on `5432`
*   **Redis**: Key-value cache/pub-sub on `6379`
*   **Backend (FastAPI)**: Running on `8000` (API documentation at `http://localhost:8000/docs`)
*   **Frontend (Vite/React)**: Running on `3000`
*   **Nginx**: Reverse proxy binding the app together on port `80`

Open your browser and navigate to **`http://localhost`** to explore the WebPilot AI Dashboard!

---

## 🔧 Local Development Setup

If you prefer running services outside of Docker for debugging:

### Backend Setup
1.  Navigate to backend and create a virtual environment:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    playwright install chromium firefox
    ```
3.  Set up local PostgreSQL database and update `DATABASE_URL` in your `.env`.
4.  Run migrations:
    ```bash
    alembic upgrade head
    ```
5.  Start the development server:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

### Frontend Setup
1.  Navigate to frontend and install dependencies:
    ```bash
    cd frontend
    npm install
    ```
2.  Start the development server:
    ```bash
    npm run dev
    ```
    The Vite server starts on `http://localhost:3000` and proxies requests to `http://localhost:8000`.

---

## 🧪 Testing

Run python test suites using pytest in the backend directory:
```bash
cd backend
pytest -v
```

---

## 📄 Documentation Links

For deeper insights, check out our sub-documentation:
*   [Architecture details](file:///e:/rishi_cbit_hachathon/browser_agent/docs/ARCHITECTURE.md)
*   [API reference](file:///e:/rishi_cbit_hachathon/browser_agent/docs/API.md)
*   [Deployment Guidelines](file:///e:/rishi_cbit_hachathon/browser_agent/docs/DEPLOYMENT.md)

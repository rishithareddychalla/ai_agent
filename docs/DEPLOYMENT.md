# WebPilot AI – Deployment Guidelines

This guide details instructions for preparing, building, configuring, and deploying **WebPilot AI** to production environments.

---

## 🐋 Production Deployment with Docker Compose

Deploy the WebPilot AI stack to a VPS, Railway, Render, or self-hosted server using the configured production stack.

### 1. Configure Production Environment (`.env`)
Create an optimized production environment configuration. Avoid dev mode values:
```env
APP_NAME=WebPilot AI
APP_ENV=production
SECRET_KEY=generate_a_secure_jwt_random_string_using_openssl_rand_hex
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Database
DATABASE_URL=postgresql+asyncpg://production_user:production_password@postgres_host:5432/webpilot_prod

# Caching/Queue
REDIS_URL=redis://redis_host:6379/0

# AI Configuration
AI_PROVIDER=gemini
GEMINI_API_KEY=your_production_gemini_api_key
GEMINI_MODEL=gemini-1.5-pro

# Browser Automation (Production values)
BROWSER_TYPE=chromium
BROWSER_HEADLESS=true
BROWSER_SCREENSHOT_INTERVAL=800  # Elevated slightly for production bandwidth optimization
BROWSER_DEFAULT_TIMEOUT=45000    # Higher buffer for slow networks
BROWSER_SLOW_MO=100              # Human-like slows to dodge strict bot blockers

# Local Persistent Storage
SCREENSHOTS_DIR=/app/screenshots
DOWNLOADS_DIR=/app/downloads
REPORTS_DIR=/app/reports
LOGS_DIR=/app/logs
```

### 2. Multi-Stage Dockerfile Execution
Our Docker builds are optimized for minimal footprints:
*   **Backend Dockerfile**: Installs Playwright system packages, downloads Google Chrome/Chromium and Firefox browser binaries, and executes Uvicorn under system processes.
*   **Frontend Dockerfile**: Multi-stage image build. Builder container installs node, builds compiled outputs (`dist/`), and passes them to Nginx Alpine container for high-speed static content serving.

To launch the production containers in background daemon mode:
```bash
docker-compose -f docker-compose.yml up -d --build
```

---

## 🌐 Deploying to SaaS Providers

If you prefer deploying services separately:

### Backend Deployment (Railway, Render, VPS)
1.  **Playwright Dependency Setup**: The server must support system dependencies for browser engines. On Render, select Python runtime and add the following build command:
    ```bash
    pip install -r requirements.txt && playwright install chromium firefox
    ```
2.  **Environment Setup**: Set all environment variables defined in `.env.example`.
3.  **Command**: Start backend application with:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port $PORT
    ```

### Frontend Deployment (Vercel, Netlify)
Vite SPAs deploy out-of-the-box:
1.  Set **Build Command**: `npm run build`
2.  Set **Output Directory**: `dist`
3.  Configure **URL Redirection Rules**: For React Router fallback, add a `vercel.json` (or similar redirection mapping file):
    ```json
    {
      "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
    }
    ```
4.  Configure Environment Variables:
    *   `VITE_API_BASE_URL`: Production HTTP backend URL (e.g. `https://api.webpilot.ai`)
    *   `VITE_WS_BASE_URL`: Production WebSocket URL (e.g. `wss://api.webpilot.ai`)

---

## 🔒 Security Best Practices

1.  **HTTPS Reverse Proxy**: Always terminate SSL/TLS at your Nginx proxy or cloud load balancer. Enable secure WebSocket connections (`wss://`).
2.  **Browser Sandboxing**: Ensure Playwright processes run under unprivileged Unix accounts inside the Docker container.
3.  **Plaintext Masking**: Mask user inputs (such as payment numbers, API keys, passwords) from the logs and screenshot streams.
4.  **JWT Expirations**: Maintain strict 24-hour expirations or shorter session durations in production environments.

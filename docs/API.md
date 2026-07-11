# WebPilot AI – API Documentation

The WebPilot AI backend runs on FastAPI and exposes RESTful endpoints for CRUD tasks and WebSocket connections for real-time interaction.

---

## 🔑 Authentication APIs

All endpoints (except login and register) require a JWT bearer token passed in the header:
`Authorization: Bearer <your_token>`

### 1. Register User
*   **Method**: `POST`
*   **Path**: `/auth/register`
*   **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "password": "securepassword123",
      "full_name": "John Doe"
    }
    ```
*   **Response (201 Created)**:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
      "token_type": "bearer",
      "user_id": 1,
      "email": "user@example.com",
      "full_name": "John Doe"
    }
    ```

### 2. User Login
*   **Method**: `POST`
*   **Path**: `/auth/login`
*   **Request Body (OAuth2 Form Data)**:
    *   `username`: `user@example.com`
    *   `password`: `securepassword123`
*   **Response (200 OK)**:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
      "token_type": "bearer",
      "user_id": 1,
      "email": "user@example.com",
      "full_name": "John Doe"
    }
    ```

### 3. Get Current Profile
*   **Method**: `GET`
*   **Path**: `/auth/me`
*   **Response (200 OK)**:
    ```json
    {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "is_active": true,
      "settings": {
        "browser": "chromium",
        "theme": "dark",
        "ai_provider": "gemini",
        "download_folder": "/downloads",
        "default_timeout": 30000,
        "screenshot_frequency": 500,
        "retry_count": 3,
        "headless": true
      }
    }
    ```

---

## 🤖 Task Management APIs

### 1. Create Browser Task
*   **Method**: `POST`
*   **Path**: `/tasks`
*   **Request Body**:
    ```json
    {
      "prompt": "Compare iPhone 16 prices on Amazon and Flipkart under ₹70,000",
      "browser": "chromium",
      "headless": true
    }
    ```
*   **Response (202 Accepted)**:
    ```json
    {
      "id": 12,
      "prompt": "Compare iPhone 16 prices on Amazon and Flipkart under ₹70,000",
      "status": "pending",
      "current_step": 0,
      "total_steps": 0,
      "result_summary": null,
      "recommendation": null,
      "execution_time_ms": null,
      "success_rate": null,
      "websites_visited": [],
      "error_message": null,
      "created_at": "2026-07-10T12:00:00Z",
      "started_at": null,
      "completed_at": null
    }
    ```

### 2. List Tasks
*   **Method**: `GET`
*   **Path**: `/tasks`
*   **Query Params**:
    *   `skip`: Number of tasks to offset (default `0`)
    *   `limit`: Number of tasks to return (default `50`)
*   **Response (200 OK)**: Array of Task objects.

### 3. Get Task Details
*   **Method**: `GET`
*   **Path**: `/tasks/{task_id}`
*   **Response (200 OK)**: Detailed Task object.

### 4. Delete/Cancel Task
*   **Method**: `DELETE`
*   **Path**: `/tasks/{task_id}`
*   **Response (204 No Content)**: Cancels running browser session.

---

## 📈 Analytics APIs

### 1. Dashboard Metrics Summary
*   **Method**: `GET`
*   **Path**: `/analytics/summary`
*   **Response (200 OK)**:
    ```json
    {
      "total_tasks": 48,
      "completed_tasks": 42,
      "failed_tasks": 5,
      "running_tasks": 1,
      "avg_success_rate": 0.89,
      "avg_execution_time_ms": 78320.0,
      "total_execution_time_ms": 3289440.0
    }
    ```

### 2. Daily Usage (Chart)
*   **Method**: `GET`
*   **Path**: `/analytics/daily?days=30`
*   **Response (200 OK)**: Array of `{ date: "YYYY-MM-DD", total: 2, completed: 2, failed: 0 }`.

### 3. Most Visited Domains (Chart)
*   **Method**: `GET`
*   **Path**: `/analytics/sites?limit=10`
*   **Response (200 OK)**: Array of `{ domain: "amazon.com", visit_count: 14 }`.

---

## 📂 Report Downloads

### 1. Download Report File
*   **Method**: `GET`
*   **Path**: `/reports/{task_id}/download/{format}`
*   **Path Variables**:
    *   `format`: `pdf` | `csv` | `json`
*   **Query Parameter**:
    *   `token`: JWT authentication token
*   **Response (200 OK)**: File attachment stream.

---

## 🔌 WebSocket Streams

### 1. Task Progress Events
*   **Endpoint**: `/tasks/ws/{task_id}?token=<jwt>`
*   **Flow**: Sends real-time progress update objects:
    ```json
    {
      "type": "step_start",
      "data": {
        "step_index": 2,
        "action": "click",
        "description": "Click search button",
        "progress_pct": 25
      },
      "timestamp": "2026-07-10T12:00:05.123Z"
    }
    ```
*   **Event Types**:
    *   `planning`: Planner initialized.
    *   `plan_ready`: AI plan returned.
    *   `step_start`: Begun executing index.
    *   `step_complete`: Successfully ran step.
    *   `step_failed`: Attempting healing or step skipped.
    *   `step_recovery`: Self-healing retry notification.
    *   `progress`: Progression stats indicator.
    *   `complete`: Task execution completed and reports built.
    *   `error`: Execution aborted with details.

### 2. Live Browser Frame Stream
*   **Endpoint**: `/browser/ws/live/{task_id}?token=<jwt>`
*   **Flow**: Pushes screen screenshot frame updates:
    ```json
    {
      "type": "frame",
      "data": {
        "screenshot": "iVBORw0KGgoAAAANSUhEUgAA...",
        "url": "https://www.google.com/search?q=...",
        "title": "Google Search - iPhone 16"
      }
    }
    ```

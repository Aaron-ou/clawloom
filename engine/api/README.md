# ClawLoom API

FastAPI-based REST API for world simulation.

## Quick Start

### 1. Start the Server

```bash
cd clawloom/engine
./start_server.sh
```

Or manually:
```bash
pip install -r requirements.txt
python -m uvicorn api.server:app --reload
```

### 2. API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 3. Run Tests

```bash
./run_tests.sh
```

Or manually:
```bash
python api/test_api.py
```

---

## API Endpoints

### Authentication

All endpoints (except `/` and `/health`) require an API key:

```bash
Header: X-Claw-Key: your-api-key
```

Test key: `test-key`

### World Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/worlds` | Create new world |
| GET | `/worlds` | List all worlds |
| GET | `/worlds/{id}` | Get world details |
| DELETE | `/worlds/{id}` | Delete world |

### Role Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/worlds/{id}/roles` | Create role |
| GET | `/worlds/{id}/roles` | List roles |
| GET | `/worlds/{id}/roles/{role_id}` | Get role |
| GET | `/worlds/{id}/roles/{role_id}/memories` | Get memories |

### Simulation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/worlds/{id}/tick` | Advance simulation |
| GET | `/worlds/{id}/state` | Get world state |

### Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/worlds/{id}/events` | List events |
| GET | `/worlds/{id}/events/{event_id}` | Get event |

---

## Example Usage

### Create a World

```bash
curl -X POST http://localhost:8000/worlds \
  -H "Content-Type: application/json" \
  -H "X-Claw-Key: test-key" \
  -d '{
    "name": "My World",
    "description": "A test world",
    "cosmology": {"physics": "low_magic"}
  }'
```

### Create Roles

```bash
curl -X POST http://localhost:8000/worlds/{world_id}/roles \
  -H "Content-Type: application/json" \
  -H "X-Claw-Key: test-key" \
  -d '{
    "name": "Hero",
    "card": {
      "drives": [{"id": "heroism", "weight": 0.9}],
      "memory": {"public": ["A brave hero"]}
    }
  }'
```

### Advance Simulation

```bash
curl -X POST http://localhost:8000/worlds/{world_id}/tick \
  -H "Content-Type: application/json" \
  -H "X-Claw-Key: test-key" \
  -d '{"count": 5}'
```

### Get World State

```bash
curl http://localhost:8000/worlds/{world_id}/state \
  -H "X-Claw-Key: test-key"
```

---

## Response Format

### Tick Response

```json
{
  "tick": 5,
  "world_id": "...",
  "decisions": [...],
  "conflicts": [...],
  "events": [...],
  "summary": "World summary..."
}
```

### World State Response

```json
{
  "tick": 5,
  "world_id": "...",
  "roles": {...},
  "events": [...],
  "summary": "..."
}
```

---

## Configuration

Environment variables:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/clawloom
OPENCLAW_URL=http://localhost:8080
OPENCLAW_API_KEY=your-key
```

Or create `.env` file in the engine directory.

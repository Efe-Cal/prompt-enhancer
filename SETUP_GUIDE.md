# Celery + WebSocket Setup Guide

## Overview
Your PromptEnhance application now uses:
- **Celery** for async task processing
- **Django Channels** for WebSocket communication
- **Redis** as message broker

## Prerequisites
You need Redis running on your machine:

### Windows
1. Download Redis from: https://github.com/microsoftarchive/redis/releases
2. Install and run: `redis-server.exe`

Or use WSL:
```bash
wsl sudo service redis-server start
```

Or use Docker:
```bash
docker run -d -p 6379:6379 redis
```

## Running the Application

### Terminal 1 - Redis (if not running as service)
```bash
redis-server
```

### Terminal 2 - Celery Worker
```bash
cd backend
celery -A backend worker --loglevel=info --pool=solo
```

### Terminal 3 - Django with Daphne (ASGI server)
```bash
cd backend
daphne -b 0.0.0.0 -p 8000 backend.asgi:application
```

### Terminal 4 - Frontend
```bash
cd prompt-enhance-frontend
npm run dev
```

## How It Works

1. **User submits a prompt** → API creates a Celery task and returns a `task_id`
2. **Frontend connects to WebSocket** using the `task_id`
3. **Celery task processes the prompt** in the background
4. **When LLM needs user input** → Task sends question via WebSocket
5. **Frontend shows dialog** → User answers
6. **Answer sent back via WebSocket** → Task continues processing
7. **Task completes** → Result sent via WebSocket to frontend

## Adding User Questions to Your LLM Tool

In your `enhance.py` or tool calling logic, you can now ask questions:

```python
from api.tasks import ask_user_question

# Inside your tool or LLM processing
user_answer = ask_user_question(
    task_id=task_id,
    question="What industry should this prompt target?"
)

# Use the answer
print(f"User said: {user_answer}")
```

## File Structure

```
backend/
├── backend/
│   ├── celery.py          # Celery configuration
│   ├── asgi.py            # ASGI application with WebSocket routing
│   ├── routing.py         # WebSocket URL routing
│   └── settings.py        # Updated with Channels + Celery config
├── api/
│   ├── consumers.py       # WebSocket consumer
│   ├── tasks.py           # Celery tasks
│   └── views.py           # Updated to use async tasks
```

## Troubleshooting

### Redis Connection Error
- Make sure Redis is running on `localhost:6379`
- Check with: `redis-cli ping` (should return "PONG")

### WebSocket Connection Failed
- Use Daphne instead of `python manage.py runserver`
- Check CORS settings in `settings.py`

### Celery Task Not Running
- Ensure Celery worker is running
- Check logs: `celery -A backend worker --loglevel=debug`

## Next Steps

To integrate user questions into your actual LLM tool calling:

1. Modify your tool definitions in `enhance.py`
2. When a tool needs user input, call `ask_user_question(task_id, question)`
3. The task will pause and wait for WebSocket response
4. User answers via the dialog in frontend
5. Task continues with the user's answer

# 🚀 Quick Reference - Celery + WebSocket

## Start Services (Windows)

```bash
# 1. Start Redis
redis-server

# 2. Start Celery Worker
cd backend
celery -A backend worker --loglevel=info --pool=solo

# 3. Start Django with Daphne
cd backend
daphne -b 0.0.0.0 -p 8000 backend.asgi:application

# 4. Start Frontend
cd prompt-enhance-frontend
npm run dev
```

**Or use:** `start_services.bat` (Windows only)

---

## Test User Dialog (Demo)

1. Open `backend/api/tasks.py`
2. Find `enhance_prompt_task` function
3. **Uncomment** these lines:
   ```python
   user_preference = ask_user_question(
       task_id=task_id,
       question="What tone should the enhanced prompt have? (formal/casual/technical)"
   )
   ```
4. Restart Celery worker
5. Click "Enhance" in frontend
6. **A dialog will appear!** ✨

---

## Add User Questions to Your Code

```python
from api.tasks import ask_user_question

# In any Celery task
@shared_task(bind=True)
def my_task(self, task_id, ...):
    answer = ask_user_question(
        task_id=task_id,
        question="Your question here?"
    )
    # Use answer...
```

---

## Verify Setup

```bash
# Check Redis
redis-cli ping
# Should return: PONG

# Test API
python test_setup.py
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Redis connection error | Run `redis-server` |
| WebSocket won't connect | Use Daphne, not `manage.py runserver` |
| Celery task not running | Check Celery worker is running |
| Dialog not showing | Check browser console for errors |

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/api/tasks.py` | Celery tasks - **ADD USER QUESTIONS HERE** |
| `backend/api/consumers.py` | WebSocket handler |
| `backend/api/views.py` | API endpoints |
| `src/App.tsx` | Frontend WebSocket logic |

---

## Architecture

```
Frontend → HTTP POST → Django API
    ↓                      ↓
 WebSocket            Creates task
    ↓                      ↓
 Consumer  ←──Redis←── Celery Worker
                          ↓
                      Processes LLM
                      Asks questions
```

---

## Next Steps

1. ✅ Services running
2. ✅ Test demo (uncomment in tasks.py)
3. 📝 Integrate into your LLM tool calling
4. 🎨 Customize dialog UI
5. 📊 Add progress updates

---

**Full docs:** 
- `IMPLEMENTATION_SUMMARY.md`
- `SETUP_GUIDE.md`
- `CELERY_WEBSOCKET_README.md`

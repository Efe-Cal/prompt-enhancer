# AGENTS.md

## Commands
- **Backend**: `cd backend && python manage.py runserver` (Django on port 8000)
- **Frontend**: `cd prompt-enhance-frontend && npm run dev` (Vite/React)
- **Lint frontend**: `cd prompt-enhance-frontend && npm run lint`
- **Build frontend**: `cd prompt-enhance-frontend && npm run build`
- **Run single test**: `cd backend && python manage.py test api.tests.TestClassName.test_method`
- **Start all**: `start_services.bat`

## Architecture
- **backend/**: Django REST API with Channels (WebSocket), Celery tasks, SQLite
  - `api/enhance.py`: Core prompt enhancement logic using OpenAI API
  - `api/views.py`, `api/urls.py`: REST endpoints
  - `api/consumers.py`: WebSocket consumers for real-time features
- **prompt-enhance-frontend/**: React 19 + TypeScript + Vite SPA
- **app.py**: Deprecated Streamlit prototype (do not use)

## Code Style
- Python: snake_case, type hints for function signatures, use `@cache` for expensive ops
- TypeScript/React: functional components, ESLint enforced
- Use `python-dotenv` for env vars; keys: `OPENAI_API_KEY`, `OPENAI_MODEL`, `HACKCLUB_SEARCH_API_KEY`
- Error handling: catch specific exceptions (e.g., `openai.APIStatusError`), log before fallback
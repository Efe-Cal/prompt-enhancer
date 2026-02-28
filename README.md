# PromptEnhance


## Overview

PromptEnhance is a web application designed to help users create better AI prompts through intelligent enhancement. It leverages advanced prompt engineering principles and AI to transform simple, "lazy" prompts into comprehensive, well-structured instructions that yield superior results from language models.

### Key Features

✨ **Smart Prompt Enhancement** - AI-powered prompt improvement with best practices built-in  
❓ **Questioning** - Interactive prompt refinement through user feedback  
🔍 **Web Search Integration** - Optional context enrichment using real-time web data  
✏️ **Edit Requests** - Request specific edits to the enhanced prompt  
🎨 **Prompt Styling** - Customize the style of your prompts  
💾 **Prompt Library** - Save your enhanced prompts on your device  


---

## Architecture

The project consists of three main components:

```
PromptEnhance/
├── backend/                    # Django REST API
│   ├── api/                   # Main API app
│   │   ├── enhance.py        # Prompt enhancement logic
│   │   ├── edits.py          # Prompt editing logic
│   │   ├── shared_utils.py  # Shared utilities for enhancement and editing
│   │   ├── consumers.py      # WebSocket consumers
│   │   ├── prompt.py         # Prompt builder utilities
│   └── backend/              # Django project settings
└── prompt-enhance-frontend/   # Vite/TypeScript frontend
    └── src/
```

---

## Quick Start

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd PromptEnhance
```

#### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Navigate to backend
cd backend

# Start Django development server
python manage.py runserver
```

The backend API will be available at `http://localhost:8000`

#### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd prompt-enhance-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

---

## Configuration

Create a `.env` file in the `backend/` directory with the following content:

```env
API_KEY=your-api-key-here
BASE_URL=BASE_URL=https://ai.hackclub.com/proxy/v1
MODEL=google/gemini-3-flash-preview
HACKCLUB_SEARCH_API_KEY=your-hackclub-search-api-key

# Django Settings
SECRET_KEY=your-django-secret-key
DEBUG=True
```

---

## Usage

1. **Enter Task Context** - Describe what the prompt is for
2. **Input Your Prompt** - Write your initial prompt
3. **Enable Web Search** (Optional) - Include additional context from web
4. **Enhance** - Click to generate an improved version
5. **Questioning** - Answer follow-up questions to refine further
6. **Edit** - Request specific edits to the enhanced prompt

---

## Tech Stack

### Backend
- **Django 5.2** - Web framework
- **Django REST Framework 3.16** - API development
- **OpenAI Python SDK 2.15** - AI integration
- **Database** - There is no database, no data is stored!
 

### Frontend
- **React 19.2** - UI library
- **TypeScript 5.9** - Type safety
- **Vite 7.2** - Build tool
- **React Compiler** - Performance optimization


---


## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue for any bugs or feature requests.

---

<div align="center">
Made with ❤️ for better AI interactions
</div>

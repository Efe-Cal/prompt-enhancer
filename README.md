# PromptEnhance

<div align="center">

**An intelligent AI-powered prompt enhancement platform that transforms basic prompts into detailed, effective instructions**

</div>

---

## 📖 Overview

PromptEnhance is a web application designed to help users create better AI prompts through intelligent enhancement. It leverages advanced prompt engineering principles and AI to transform simple, "lazy" prompts into comprehensive, well-structured instructions that yield superior results from language models.

### Key Features

✨ **Smart Prompt Enhancement** - AI-powered prompt improvement with best practices built-in
❓ **Questioning** - Interactive prompt refinement through user feedback
🔍 **Web Search Integration** - Optional context enrichment using real-time web data  
💾 **Prompt Library** - Save your enhanced prompts on your device
🎨 **Modern UI** - Clean, responsive React/TypeScript frontend  

---

## 🏗️ Architecture

The project consists of three main components:

```
PromptEnhance/
├── backend/                    # Django REST API
│   ├── api/                   # Main API app
│   │   ├── enhance.py        # Prompt enhancement logic
│   │   ├── views.py          # API endpoints
│   │   ├── consumers.py      # WebSocket consumers
│   │   ├── prompt.py         # Prompt builder utilities
│   │   └── serializers.py    # DRF serializers
│   └── backend/              # Django project settings
└── prompt-enhance-frontend/   # Vite/TypeScript frontend
    └── src/
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.7+**
- **Node.js 18+** (for Vite frontend)
- **npm or yarn** (for frontend dependencies)
- **OpenAI API key** or compatible API endpoint

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

## ⚙️ Configuration

Create a `.env` file in the `backend/` directory with the following content:

```env
API_KEY=your-api-key-here
BASE_URL=BASE_URL=https://ai.hackclub.com/proxy/v1
MODEL=gemini-3-flash-preview
HACKCLUB_SEARCH_API_KEY=your-hackclub-search-api-key

# Django Settings (if needed)
SECRET_KEY=your-django-secret-key
DEBUG=True
```

---

## 🎯 Usage

### Web Interface

1. **Enter Task Context** - Describe what the prompt is for
2. **Input Your Prompt** - Write your initial prompt
3. **Enable Web Search** (Optional) - Include additional context from web
4. **Enhance** - Click to generate an improved version
5. **Questioning** - Answer follow-up questions to refine further

---

## 💡 How It Works

1. **Prompt Analysis** - The system analyzes your input prompt and task context, finding areas for improvement and missing context
2. **Interactive Questioning** - Asks clarifying questions to gather more details
3. **Web Enhancement** (Optional) - Enriches prompts with current information
4. **Best Practices Application** - Applies expert prompt engineering principles
5. **Output Generation** - Returns a production-ready enhanced prompt

---

## 🛠️ Technology Stack

### Backend
- **Django 5.2** - Web framework
- **Django REST Framework 3.16** - API development
- **OpenAI Python SDK 2.15** - AI integration
- **SQLite** - Database (default)

### Frontend
- **React 19.2** - UI library
- **TypeScript 5.9** - Type safety
- **Vite 7.2** - Build tool
- **React Compiler** - Performance optimization

---

## 📦 Building for Production

### Frontend

```bash
cd prompt-enhance-frontend
npm run build
```

Build output will be in `dist/` directory.

### Backend

```bash
cd backend

# Collect static files
python manage.py collectstatic

# Run with production server
daphe -b 0.0.0.0 -p 8000 backend.asgi:application
```

---

## 🔧 Development

### Project Structure Details

- **`backend/api/consumers.py`** - WebSocket consumers for real-time interactions (Core logic)
- **`backend/api/prompt.py`** - Prompt builder utilities
- **`backend/api/views.py`** - REST API endpoint handlers
- **`prompt-enhance-frontend/src/`** - React application source code


---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

<div align="center">
Made with ❤️ for better AI interactions
</div>

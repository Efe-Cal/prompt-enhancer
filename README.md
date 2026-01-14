# PromptEnhance

<div align="center">

**An intelligent AI-powered prompt enhancement platform that transforms basic prompts into detailed, effective instructions**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-19.2-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue.svg)](https://www.typescriptlang.org/)

</div>

---

## 📖 Overview

PromptEnhance is a full-stack web application designed to help users create better AI prompts through intelligent enhancement. It leverages advanced prompt engineering principles and AI to transform simple, "lazy" prompts into comprehensive, well-structured instructions that yield superior results from language models.

### Key Features

✨ **Smart Prompt Enhancement** - AI-powered prompt improvement with best practices built-in  
🔍 **Web Search Integration** - Optional context enrichment using real-time web data  
💾 **Prompt Library** - Save and manage your enhanced prompts  
🎨 **Modern UI** - Clean, responsive React/TypeScript frontend  
⚡ **Fast API** - Django REST framework backend  
🔧 **Flexible Configuration** - Support for custom OpenAI-compatible API endpoints  
📱 **Dual Interface** - Both Streamlit standalone and React web app options

---

## 🏗️ Architecture

The project consists of three main components:

```
PromptEnhance/
├── app.py                      # Streamlit standalone application
├── backend/                    # Django REST API
│   ├── api/                   # Main API app
│   │   ├── enhance.py        # Prompt enhancement logic
│   │   ├── views.py          # API endpoints
│   │   ├── models.py         # Database models
│   │   └── serializers.py    # DRF serializers
│   └── backend/              # Django project settings
└── prompt-enhance-frontend/   # React/TypeScript frontend
    └── src/
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.7+**
- **Node.js 18+** (for React frontend)
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
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Navigate to backend and run migrations
cd backend
python manage.py migrate

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

#### 4. Streamlit App (Optional)

For the standalone Streamlit interface:

```bash
# From root directory with venv activated
streamlit run app.py
```

Access at `http://localhost:8501`

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
API_KEY=your-api-key-here
BASE_URL=https://api.openai.com/v1
MODEL=gpt-5.1

# Django Settings (if needed)
SECRET_KEY=your-django-secret-key
DEBUG=True
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_BASE_URL` | API endpoint (supports compatible APIs) | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Model to use for enhancement | `gpt-5.1` |

---

## 🎯 Usage

### Web Interface

1. **Enter Task Context** - Describe what the prompt is for
2. **Input Your Prompt** - Write your initial prompt
3. **Enable Web Search** (Optional) - Include additional context from web
4. **Enhance** - Click to generate an improved version
5. **Save** - Store your enhanced prompts for future reference

### API Endpoints

#### POST `/api/enhance/`

Enhance a prompt using AI.

**Request Body:**
```json
{
  "task": "Creating a blog post",
  "lazy_prompt": "Write about AI",
  "use_web_search": false,
  "additional_context_query": ""
}
```

**Response:**
```json
{
  "enhancedPrompt": "Act as an expert content writer specializing in AI technology..."
}
```

#### POST `/api/save/`

Save an enhanced prompt to the database.

**Request Body:**
```json
{
  "task": "Blog post writing",
  "lazy_prompt": "Write about AI",
  "enhanced_prompt": "Enhanced version..."
}
```

---

## 💡 How It Works

1. **Prompt Analysis** - The system analyzes your input prompt and task context
2. **Best Practices Application** - Applies expert prompt engineering principles:
   - Adds role-based context ("Act as an expert...")
   - Structures instructions clearly
   - Adds specificity and detail
   - Includes formatting guidelines
3. **Web Enhancement** (Optional) - Enriches prompts with current information
4. **Output Generation** - Returns a production-ready enhanced prompt

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

# Run with production server (e.g., gunicorn)
pip install gunicorn
gunicorn backend.wsgi:application
```

---

## 🔧 Development

### Project Structure Details

- **`app.py`** - Standalone Streamlit application with all features
- **`backend/api/enhance.py`** - Core prompt enhancement logic and system prompts
- **`backend/api/views.py`** - REST API endpoint handlers
- **`backend/api/models.py`** - Database schema for saved prompts
- **`prompt-enhance-frontend/src/`** - React application source code


---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

<div align="center">
Made with ❤️ for better AI interactions
</div>

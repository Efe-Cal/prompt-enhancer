# Prompt Enhance

A simple desktop application for enhancing prompts using OpenAI API with custom base URL support.

## Features

- **Topic Input**: Enter the topic/context for your prompt
- **Prompt Input**: Write your prompt in a multi-line text area
- **AI Response**: Get AI-generated responses using OpenAI SDK
- **Copy Output**: Easily copy the generated response to clipboard
- **Custom Base URL**: Support for custom OpenAI-compatible API endpoints

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your API settings in `.env`:
```
OPENAI_BASE_URL=https://your-api-endpoint.com/v1
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-5.1

# Back-compat aliases (optional)
BASE_URL=https://your-api-endpoint.com/v1
API_KEY=your-api-key-here
MODEL=gpt-5.1
```

## Usage

Run the application:
```bash
python app.py
```

1. Enter a topic in the "Topic Input" field
2. Write your prompt in the "Prompt Input" text area
3. Click the ▶ button to send the request
4. View the AI-generated response in the "Output" section
5. Click "📋 Copy" to copy the output to your clipboard

## Requirements

- Python 3.7+
- tkinter (usually comes with Python)
- openai>=1.0.0
- python-dotenv>=1.0.0

## Configuration

The app uses environment variables from `.env` file:
- `OPENAI_BASE_URL`: Custom base URL for OpenAI-compatible API
- `OPENAI_API_KEY`: Your API key
- `OPENAI_MODEL`: Model to use (default: gpt-5.1)

Legacy aliases (also supported):
- `BASE_URL`, `API_KEY`, `MODEL`

Saved prompts:
- Stored locally in `saved_prompts.json` (created on first save)

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY backend /app/backend

# Set work directory to the backend application
WORKDIR /app/backend

# Run collectstatic to prepare static files
RUN python manage.py collectstatic --noinput

# Create a non-root user and switch to it
RUN addgroup --system app && adduser --system --group app
RUN chown -R app:app /app
USER app

# Run the application
CMD ["sh", "-c", "daphne -b 0.0.0.0 -p ${PORT:-8000} backend.asgi:application"]

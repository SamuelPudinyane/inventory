# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . /app/

# Expose port (Django default)
EXPOSE 8000

# Set environment variable for external database
# (Django will read DATABASE_URL from environment or settings.py)
ENV DATABASE_URL=postgresql://inventory_8fic_user:RU5A8BEhWkcXCsw8MC2Ic99myK2hDeFd@dpg-d4oclcer433s73cmvrc0-a.oregon-postgres.render.com/inventory_8fic

# Collect static files (optional, for production)
RUN python manage.py collectstatic --noinput

# Start Django app
CMD ["gunicorn", "inventory_system.wsgi:application", "--bind", "0.0.0.0:8000"]

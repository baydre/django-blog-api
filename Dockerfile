FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --gid 1001 --no-create-home appuser

# Set work directory
WORKDIR /code

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project files
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appgroup /code

# Switch to non-root user
USER appuser

# Collect static files (only in production)
ARG COLLECT_STATIC=0
RUN if [ "$COLLECT_STATIC" = "1" ]; then python manage.py collectstatic --noinput; fi

# Expose port
EXPOSE 8000

# Command with port fallback
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WORKERS:-2}"]

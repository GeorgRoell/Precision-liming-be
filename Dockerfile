# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for geospatial libraries
# - gdal-bin: For fiona (shapefile reading)
# - libgeos-dev: For shapely (geometry operations)
# - libspatialindex-dev: For rtree (spatial indexing)
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run sets PORT environment variable
ENV PORT=8080

# Expose port (documentation only, Cloud Run ignores this)
EXPOSE 8080

# Start the application
# Cloud Run provides PORT env var, we use it
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}

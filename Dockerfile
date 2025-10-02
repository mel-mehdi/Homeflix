# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir Flask==2.3.3 requests==2.31.0

# Copy the application code
COPY . .

# Expose port 5000
EXPOSE 5000

# Run the application
CMD ["python", "media_server.py"]

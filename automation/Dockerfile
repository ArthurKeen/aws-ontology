FROM python:3.11-slim

# Set metadata
LABEL maintainer="Arango"
LABEL org.opencontainers.image.source="https://github.com/arango-solutions-org/AWS_Ontology"
LABEL org.opencontainers.image.licenses="MIT"
LABEL description="AWS Ontology Monitoring Automation Container"
LABEL version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PROJECT_DIR=/opt/aws-ontology

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    cron \
    logrotate \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR $PROJECT_DIR

# Create non-root user for security
RUN groupadd -r ontology && useradd -r -g ontology -d $PROJECT_DIR ontology

# Copy project files
COPY . $PROJECT_DIR/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p automation/logs automation/reports monitoring backups \
    && chown -R ontology:ontology $PROJECT_DIR

# Copy automation scripts
COPY automation/schedule_monitoring.py automation/
COPY automation/docker-entrypoint.sh automation/
RUN chmod +x automation/docker-entrypoint.sh

# Switch to non-root user
USER ontology

# Create default configuration if it doesn't exist
RUN python automation/schedule_monitoring.py --create-config --config automation/config.json || true

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=5m --retries=3 \
    CMD python -c "import json; f=open('automation/logs/scheduler_$(date +%Y%m%d).log','r'); print('healthy' if 'Starting scheduler daemon' in f.read() else 'unhealthy')" || exit 1

# Expose volume for persistent data
VOLUME ["$PROJECT_DIR/automation/logs", "$PROJECT_DIR/automation/reports", "$PROJECT_DIR/monitoring"]

# Default command
CMD ["automation/docker-entrypoint.sh"]

# =====================================================
# Build and Run Instructions
# =====================================================
#
# Build the container:
# docker build -t aws-ontology-monitor:latest -f automation/Dockerfile .
#
# Run with default configuration:
# docker run -d --name aws-ontology-monitor \
#   -v $(pwd)/automation/logs:/opt/aws-ontology/automation/logs \
#   -v $(pwd)/automation/reports:/opt/aws-ontology/automation/reports \
#   aws-ontology-monitor:latest
#
# Run with custom configuration:
# docker run -d --name aws-ontology-monitor \
#   -v $(pwd)/automation/config.json:/opt/aws-ontology/automation/config.json:ro \
#   -v $(pwd)/automation/logs:/opt/aws-ontology/automation/logs \
#   -v $(pwd)/automation/reports:/opt/aws-ontology/automation/reports \
#   aws-ontology-monitor:latest
#
# Run specific task once:
# docker run --rm -v $(pwd)/automation/logs:/opt/aws-ontology/automation/logs \
#   aws-ontology-monitor:latest \
#   python automation/schedule_monitoring.py --run-once daily
#
# View logs:
# docker logs -f aws-ontology-monitor
#
# Stop container:
# docker stop aws-ontology-monitor
#
# Remove container:
# docker rm aws-ontology-monitor 
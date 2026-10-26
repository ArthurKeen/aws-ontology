# AWS Ontology Project Makefile

.PHONY: help test test-all test-sync test-quality test-examples test-performance test-smoke test-dl lint format sync-check sync-ttl-to-owl sync-owl-to-ttl install-deps setup-hooks monitor-changes schedule-setup schedule-daemon schedule-test clean

# Default target
help:
	@echo "AWS Ontology Project - Available Commands:"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run the full pytest suite"
	@echo "  test-all       - Alias for test"
	@echo "  test-sync      - Test OWL/TTL format synchronization"
	@echo "  test-quality   - Test ontology quality and structure"
	@echo "  test-examples  - Test example instances validation"
	@echo "  test-performance - Test ontology performance metrics"
	@echo "  test-smoke     - Smoke-test the CLI tools"
	@echo "  test-dl        - OWL 2 DL compliance checks"
	@echo "  lint           - Run ruff lint + format check"
	@echo "  format         - Auto-format with ruff"
	@echo ""
	@echo "Synchronization:"
	@echo "  sync-check     - Check if OWL and TTL files are synchronized"
	@echo "  sync-ttl-to-owl - Convert TTL to OWL format"
	@echo "  sync-owl-to-ttl - Convert OWL to TTL format"
	@echo ""
	@echo "Monitoring:"
	@echo "  monitor-changes - Monitor AWS changes (last 7 days)"
	@echo "  monitor-weekly  - Generate weekly AWS change report"
	@echo "  monitor-all     - Monitor all sources and generate report"
	@echo ""
	@echo "Automation:"
	@echo "  schedule-setup  - Create sample automation configuration"
	@echo "  schedule-daemon - Start automated monitoring daemon"
	@echo "  schedule-test   - Test automation setup"
	@echo "  schedule-daily  - Run daily monitoring once"
	@echo "  schedule-weekly - Run weekly report once"
	@echo ""
	@echo "Development:"
	@echo "  install-deps   - Install Python dependencies"
	@echo "  setup-hooks    - Install Git pre-commit hooks"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean          - Clean temporary files"
	@echo ""

# Install Python dependencies (runtime + dev). Prefer uv when available.
install-deps:
	@echo "Installing Python dependencies..."
	@command -v uv >/dev/null 2>&1 && uv sync || pip install -r requirements.txt pytest ruff

# Set up Git hooks
setup-hooks:
	@echo "Setting up Git hooks..."
	python3 tools/setup_git_hooks.py

# Run the full test suite
test:
	python -m pytest

test-all: test

# Test format synchronization
test-sync:
	python -m pytest tests/test_format_sync.py

# Test ontology quality
test-quality:
	python -m pytest tests/test_ontology_quality.py

# Test examples validation
test-examples:
	python -m pytest tests/test_examples_validation.py

# Test performance
test-performance:
	python -m pytest tests/test_performance.py

# Smoke-test the CLI tools
test-smoke:
	python -m pytest tests/test_tools_smoke.py

# OWL 2 DL compliance checks
test-dl:
	python -m pytest tests/test_dl_compliance.py

# Lint and format
lint:
	ruff check .
	ruff format --check .

format:
	ruff check . --fix
	ruff format .

# Check synchronization status
sync-check:
	@echo "Checking synchronization status..."
	python tools/sync_formats.py check

# Convert TTL to OWL
sync-ttl-to-owl:
	@echo "Converting TTL to OWL..."
	python tools/sync_formats.py ttl-to-owl

# Convert OWL to TTL
sync-owl-to-ttl:
	@echo "Converting OWL to TTL..."
	python tools/sync_formats.py owl-to-ttl

# Monitor AWS changes (last 7 days)
monitor-changes:
	@echo "Monitoring AWS changes (last 7 days)..."
	python tools/monitor_aws_changes.py --source whats-new --days 7

# Generate weekly change report
monitor-weekly:
	@echo "Generating weekly AWS change report..."
	python tools/monitor_aws_changes.py --source all --days 7 --output monitoring/weekly_report.json

# Monitor all sources with detailed report
monitor-all:
	@echo "Monitoring all AWS sources..."
	python tools/monitor_aws_changes.py --source all --compare --output monitoring/comprehensive_report.json

# Create sample automation configuration
schedule-setup:
	@echo "Creating sample automation configuration..."
	mkdir -p automation
	python automation/schedule_monitoring.py --create-config --config automation/config.json

# Start automated monitoring daemon
schedule-daemon:
	@echo "Starting automated monitoring daemon..."
	python automation/schedule_monitoring.py --start-daemon --config automation/config.json

# Test automation setup
schedule-test:
	@echo "Testing automation setup..."
	python automation/schedule_monitoring.py --run-once daily --config automation/config.json

# Run daily monitoring once
schedule-daily:
	@echo "Running daily monitoring task..."
	python automation/schedule_monitoring.py --run-once daily --config automation/config.json

# Run weekly report once
schedule-weekly:
	@echo "Running weekly report task..."
	python automation/schedule_monitoring.py --run-once weekly --config automation/config.json

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.tmp" -delete
	@echo "Creating monitoring and automation directories..."
	mkdir -p monitoring automation/logs automation/reports 
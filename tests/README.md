# Testing Setup for ca2roi

This directory contains comprehensive tests for all modules in the ca2roi package.

## Setup

The project is configured with:
- **uv**: Fast Python package installer and resolver
- **ruff**: Fast Python linter and formatter  
- **pytest**: Testing framework with coverage reporting

## Installation

To install all development dependencies:

```bash
# Option 1: Use the setup script
./setup_dev.sh

# Option 2: Manual installation
pip install -e .[dev]
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src/ca2roi --cov-report=term-missing

# Run specific test file
pytest tests/test_utils.py -v

# Run specific test
pytest tests/test_utils.py::test_ensure_workspace_creates_directory -v
```

## Code Quality

```bash
# Check code with ruff
ruff check src/ tests/

# Format code with ruff  
ruff format src/ tests/
```

## Test Structure

- `conftest.py`: Shared fixtures for all tests
- `test_utils.py`: Tests for utility functions
- `test_video.py`: Tests for video processing
- `test_bleaching.py`: Tests for bleaching analysis
- `test_fluctuation.py`: Tests for fluctuation mapping
- `test_roi.py`: Tests for ROI handling
- `test_cli.py`: Tests for command-line interface

## Coverage

The tests aim for comprehensive coverage of:
- Core functionality
- Edge cases
- Error handling
- File I/O operations
- Command-line interface

## Fixtures

Common test fixtures are provided in `conftest.py`:
- `sample_frames`: Mock video frames for testing
- `sample_image`: Mock image data
- `temp_dir`: Temporary directory for file operations
- `sample_rois`: Sample ROI data
- `mock_video_info`: Mock video metadata 
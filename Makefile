.PHONY: install install-frontend build cleanup

# Default target
all: install

# Install Python part (includes installing frontend beforehand)
install: install-frontend
	@echo "Installing Python dependencies..."
	uv sync --all-extras
	@echo "Python installation complete!"

# Install frontend using npm only
install-frontend:
	@echo "Installing frontend dependencies..."
	cd src/frontend && npm install && npm run build
	@echo "Frontend installation complete!"

# Build Python package with uv into distributed version
build: install
	@echo "Building Python package..."
	uv build
	@echo "Python package build complete!"

# Clean all cache or unnecessary files/folders recursively
cleanup:
	@echo "Cleaning up cache and unnecessary files..."
	# Clean Python cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true

	# Clean frontend cache
	cd src/frontend && rm -rf node_modules 2>/dev/null || true
	cd src/frontend && rm -f package-lock.json 2>/dev/null || true
	cd src/frontend && rm -rf .vite 2>/dev/null || true
	cd src/frontend && rm -rf dist 2>/dev/null || true
	rm -rf static

	# Clean system cache
	rm -rf .DS_Store 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true

	@echo "Cleanup complete!"

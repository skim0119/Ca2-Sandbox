import pytest
import numpy as np
import tempfile
import os
from unittest.mock import patch


@pytest.fixture
def sample_frames():
    """Create sample video frames for testing."""
    return np.random.randint(0, 255, size=(10, 100, 100), dtype=np.uint8).astype(
        np.float32
    )


@pytest.fixture
def sample_image():
    """Create a sample image for ROI testing."""
    return np.random.randint(0, 255, size=(100, 100), dtype=np.uint8)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_rois():
    """Sample ROI data for testing."""
    return [
        {"coords": [10, 10, 30, 30]},
        {"coords": [50, 50, 70, 70]},
        {"coords": [20, 80, 40, 95]},
    ]


@pytest.fixture
def mock_video_info():
    """Mock video information."""
    return {"n_frames": 10, "width": 100, "height": 100, "fps": 30.0}

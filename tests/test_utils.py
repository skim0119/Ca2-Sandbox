import os
import pytest
from ca2roi.utils import ensure_workspace


def test_ensure_workspace_creates_directory(temp_dir):
    """Test that ensure_workspace creates a directory if it doesn't exist."""
    workspace_path = os.path.join(temp_dir, "test_workspace")
    assert not os.path.exists(workspace_path)

    ensure_workspace(workspace_path)

    assert os.path.exists(workspace_path)
    assert os.path.isdir(workspace_path)


def test_ensure_workspace_existing_directory(temp_dir):
    """Test that ensure_workspace works with existing directories."""
    workspace_path = os.path.join(temp_dir, "existing_workspace")
    os.makedirs(workspace_path)
    assert os.path.exists(workspace_path)

    # Should not raise an error
    ensure_workspace(workspace_path)

    assert os.path.exists(workspace_path)
    assert os.path.isdir(workspace_path)


def test_ensure_workspace_nested_directories(temp_dir):
    """Test that ensure_workspace creates nested directories."""
    nested_path = os.path.join(temp_dir, "level1", "level2", "workspace")
    assert not os.path.exists(nested_path)

    ensure_workspace(nested_path)

    assert os.path.exists(nested_path)
    assert os.path.isdir(nested_path)

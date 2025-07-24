import os
import pickle
import numpy as np
import pytest
from ca2roi.bleaching import compute_bleaching, save_bleaching


def test_compute_bleaching(sample_frames):
    """Test bleaching computation returns correct mean intensities."""
    result = compute_bleaching(sample_frames)

    # Should return one value per frame
    assert len(result) == sample_frames.shape[0]

    # Manual calculation should match
    expected = sample_frames.mean(axis=(1, 2))
    np.testing.assert_array_equal(result, expected)


def test_compute_bleaching_single_frame():
    """Test bleaching computation with a single frame."""
    frame = np.ones((50, 50), dtype=np.float32) * 100
    frames = frame.reshape(1, 50, 50)

    result = compute_bleaching(frames)

    assert len(result) == 1
    assert result[0] == 100.0


def test_compute_bleaching_different_values():
    """Test bleaching computation with frames of different intensities."""
    frames = np.array(
        [np.ones((10, 10)) * 50, np.ones((10, 10)) * 100, np.ones((10, 10)) * 150],
        dtype=np.float32,
    )

    result = compute_bleaching(frames)

    expected = [50.0, 100.0, 150.0]
    np.testing.assert_array_equal(result, expected)


def test_save_bleaching(temp_dir, mock_video_info):
    """Test saving bleaching information to pickle file."""
    mean_intensity = np.array([100.0, 95.0, 90.0, 85.0])
    output_path = os.path.join(temp_dir, "test_bleaching.pkl")

    save_bleaching(mean_intensity, mock_video_info, output_path)

    # Check file was created
    assert os.path.exists(output_path)

    # Check contents
    with open(output_path, "rb") as f:
        data = pickle.load(f)

    np.testing.assert_array_equal(data["mean_intensity"], mean_intensity)
    assert data["n_frames"] == mock_video_info["n_frames"]
    assert data["width"] == mock_video_info["width"]
    assert data["height"] == mock_video_info["height"]
    assert data["fps"] == mock_video_info["fps"]


def test_save_bleaching_empty_info(temp_dir):
    """Test saving bleaching with empty info dictionary."""
    mean_intensity = np.array([50.0, 45.0])
    output_path = os.path.join(temp_dir, "test_bleaching_empty.pkl")

    save_bleaching(mean_intensity, {}, output_path)

    assert os.path.exists(output_path)

    with open(output_path, "rb") as f:
        data = pickle.load(f)

    np.testing.assert_array_equal(data["mean_intensity"], mean_intensity)

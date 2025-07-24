import os
import numpy as np
import cv2
import pytest
from unittest.mock import patch
from ca2roi.fluctuation import (
    compute_fluctuation_map,
    save_fluctuation_overlay,
    auto_select_rois_from_fluctuation,
    save_auto_rois_plot,
    plot_roi_intensity_traces,
    save_auto_rois_json,
)


def test_compute_fluctuation_map_basic():
    """Test basic fluctuation map computation."""
    # Create test data with known fluctuations
    frames = np.array(
        [
            np.ones((50, 50)) * 100,  # Base intensity
            np.ones((50, 50)) * 110,  # Increased intensity
            np.ones((50, 50)) * 90,  # Decreased intensity
            np.ones((50, 50)) * 105,  # Back to intermediate
        ],
        dtype=np.float32,
    )

    # Add some spatial variation in the last frame
    frames[3, 20:30, 20:30] = 120  # High fluctuation region

    mean_intensity = np.array([100.0, 110.0, 90.0, 105.0])

    fluctuation_map, overlayed = compute_fluctuation_map(frames, mean_intensity)

    # Check output shapes
    assert fluctuation_map.shape == (50, 50)
    assert overlayed.shape == (50, 50, 3)

    # High fluctuation region should have higher values
    high_fluct_region = fluctuation_map[20:30, 20:30]
    low_fluct_region = fluctuation_map[0:10, 0:10]
    assert np.mean(high_fluct_region) > np.mean(low_fluct_region)


def test_compute_fluctuation_map_constant_frames():
    """Test fluctuation map with constant frames (should be near zero)."""
    # All frames identical
    frames = np.ones((5, 30, 30), dtype=np.float32) * 150
    mean_intensity = np.ones(5) * 150

    fluctuation_map, overlayed = compute_fluctuation_map(frames, mean_intensity)

    # Fluctuation should be very small (near zero) for constant frames
    assert fluctuation_map.shape == (30, 30)
    assert np.all(fluctuation_map < 1e-6)  # Very small fluctuations
    assert overlayed.shape == (30, 30, 3)


def test_compute_fluctuation_map_single_pixel_variation():
    """Test fluctuation map with variation in a single pixel."""
    frames = np.ones((4, 20, 20), dtype=np.float32) * 100

    # Vary intensity at position (10, 10) across frames
    frames[0, 10, 10] = 80
    frames[1, 10, 10] = 120
    frames[2, 10, 10] = 90
    frames[3, 10, 10] = 110

    mean_intensity = np.array([100.0, 100.0, 100.0, 100.0])

    fluctuation_map, overlayed = compute_fluctuation_map(frames, mean_intensity)

    # The varying pixel should have higher fluctuation
    varying_pixel = fluctuation_map[10, 10]
    constant_pixel = fluctuation_map[5, 5]
    assert varying_pixel > constant_pixel


@patch("cv2.imwrite")
def test_save_fluctuation_overlay(mock_imwrite, temp_dir):
    """Test saving fluctuation overlay to file."""
    # Create a mock overlay image
    overlay = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    output_path = os.path.join(temp_dir, "test_overlay.png")

    save_fluctuation_overlay(overlay, output_path)

    # Verify cv2.imwrite was called with correct arguments
    mock_imwrite.assert_called_once_with(output_path, overlay)


def test_compute_fluctuation_map_polyfit_correction():
    """Test that polynomial fitting for bleaching correction works."""
    # Create frames with a clear trend
    n_frames = 10
    frames = np.ones((n_frames, 40, 40), dtype=np.float32)

    # Add a quadratic trend to mean intensity
    trend_values = [100 - i**2 for i in range(n_frames)]
    for i, val in enumerate(trend_values):
        frames[i] *= val / 100

    mean_intensity = np.array(trend_values, dtype=np.float32)

    fluctuation_map, overlayed = compute_fluctuation_map(frames, mean_intensity)

    # Should produce reasonable results
    assert fluctuation_map.shape == (40, 40)
    assert overlayed.shape == (40, 40, 3)
    assert not np.any(np.isnan(fluctuation_map))
    assert not np.any(np.isinf(fluctuation_map))


def test_auto_select_rois_basic(temp_dir):
    """Test basic automatic ROI selection functionality."""
    # Create test data with known high fluctuation regions
    frames = np.ones((10, 60, 60), dtype=np.float32) * 100

    # Add high fluctuation in specific regions
    # Region 1: Top-left corner (10x10)
    for i in range(10):
        frames[i, 5:15, 5:15] = 100 + np.random.normal(0, 20, (10, 10))

    # Region 2: Bottom-right corner (8x8)
    for i in range(10):
        frames[i, 45:53, 45:53] = 100 + np.random.normal(0, 25, (8, 8))

    # Compute fluctuation map
    mean_intensity = frames.mean(axis=(1, 2))
    fluctuation_map, _ = compute_fluctuation_map(frames, mean_intensity)

    # Test auto ROI selection
    threshold = np.percentile(fluctuation_map, 85)
    min_distance = 5

    roi_data = auto_select_rois_from_fluctuation(
        fluctuation_map, frames, threshold, min_distance, temp_dir
    )

    # Check results
    assert isinstance(roi_data, dict)
    assert "rois" in roi_data
    assert "stats" in roi_data
    assert roi_data["stats"]["n_rois"] >= 1  # Should find at least one ROI
    assert roi_data["stats"]["coverage_percent"] > 0

    # Check ROI structure
    for roi in roi_data["rois"]:
        assert "id" in roi
        assert "coords" in roi
        assert "n_pixels" in roi
        assert "avg_intensity" in roi
        assert "center" in roi
        assert "fluctuation_strength" in roi
        assert len(roi["coords"]) == 4  # [x0, y0, x1, y1]
        assert len(roi["avg_intensity"]) == 10  # Same as number of frames


def test_auto_select_rois_no_targets():
    """Test automatic ROI selection when no pixels pass threshold."""
    # Create frames with very low fluctuation
    frames = np.ones((5, 30, 30), dtype=np.float32) * 150
    mean_intensity = frames.mean(axis=(1, 2))
    fluctuation_map, _ = compute_fluctuation_map(frames, mean_intensity)

    # Set very high threshold
    threshold = fluctuation_map.max() + 10
    min_distance = 3

    roi_data = auto_select_rois_from_fluctuation(
        fluctuation_map, frames, threshold, min_distance
    )

    # Should return empty results
    assert roi_data["rois"] == []
    assert roi_data["stats"]["n_rois"] == 0
    assert roi_data["stats"]["total_pixels"] == 0
    assert roi_data["stats"]["coverage_percent"] == 0.0


def test_auto_select_rois_single_pixel_clusters():
    """Test ROI selection with isolated single pixels."""
    frames = np.ones((8, 40, 40), dtype=np.float32) * 100

    # Add high fluctuation to isolated pixels
    fluctuation_positions = [(10, 10), (15, 25), (30, 35)]
    for pos in fluctuation_positions:
        for i in range(8):
            frames[i, pos[0], pos[1]] = 100 + np.random.normal(0, 30)

    mean_intensity = frames.mean(axis=(1, 2))
    fluctuation_map, _ = compute_fluctuation_map(frames, mean_intensity)

    threshold = np.percentile(fluctuation_map, 90)
    min_distance = 2  # Small distance to keep pixels separate

    roi_data = auto_select_rois_from_fluctuation(
        fluctuation_map, frames, threshold, min_distance
    )

    # Should find multiple small ROIs
    assert roi_data["stats"]["n_rois"] >= 1
    for roi in roi_data["rois"]:
        assert roi["n_pixels"] >= 1


def test_auto_select_rois_clustering():
    """Test that nearby pixels are properly clustered."""
    frames = np.ones((6, 50, 50), dtype=np.float32) * 100

    # Create a cluster of high fluctuation pixels
    cluster_center = (25, 25)
    cluster_size = 5
    for i in range(6):
        for dy in range(-cluster_size // 2, cluster_size // 2 + 1):
            for dx in range(-cluster_size // 2, cluster_size // 2 + 1):
                y, x = cluster_center[0] + dy, cluster_center[1] + dx
                if 0 <= y < 50 and 0 <= x < 50:
                    frames[i, y, x] = 100 + np.random.normal(0, 20)

    mean_intensity = frames.mean(axis=(1, 2))
    fluctuation_map, _ = compute_fluctuation_map(frames, mean_intensity)

    threshold = np.percentile(fluctuation_map, 80)
    min_distance = 3  # Should cluster nearby pixels

    roi_data = auto_select_rois_from_fluctuation(
        fluctuation_map, frames, threshold, min_distance
    )

    # Should find one main cluster
    assert roi_data["stats"]["n_rois"] >= 1
    # The main ROI should contain multiple pixels
    main_roi = max(roi_data["rois"], key=lambda r: r["n_pixels"])
    assert main_roi["n_pixels"] > 1


@patch("matplotlib.pyplot.savefig")
@patch("matplotlib.pyplot.close")
def test_save_auto_rois_plot(mock_close, mock_savefig, temp_dir):
    """Test saving ROI plot visualization."""
    # Create test data
    fluctuation_map = np.random.rand(40, 40) * 100
    first_frame = np.random.randint(0, 255, (40, 40)).astype(np.uint8)

    roi_data = {
        "rois": [
            {
                "id": 0,
                "coords": [10, 10, 20, 20],
                "n_pixels": 100,
                "center": [15.0, 15.0],
            }
        ],
        "stats": {"n_rois": 1},
    }

    output_path = os.path.join(temp_dir, "test_roi_plot.png")

    save_auto_rois_plot(fluctuation_map, roi_data, first_frame, output_path)

    # Verify matplotlib functions were called
    mock_savefig.assert_called_once_with(output_path, dpi=300, bbox_inches="tight")
    mock_close.assert_called_once()


@patch("matplotlib.pyplot.savefig")
@patch("matplotlib.pyplot.close")
def test_plot_roi_intensity_traces(mock_close, mock_savefig, temp_dir):
    """Test plotting ROI intensity traces."""
    roi_data = {
        "rois": [
            {
                "id": 0,
                "avg_intensity": [100, 105, 98, 102, 99],
                "n_pixels": 50,
                "fluctuation_strength": 15.5,
            },
            {
                "id": 1,
                "avg_intensity": [120, 115, 125, 118, 122],
                "n_pixels": 30,
                "fluctuation_strength": 20.2,
            },
        ]
    }

    fps = 10.0
    output_path = os.path.join(temp_dir, "test_traces.png")

    plot_roi_intensity_traces(roi_data, fps, output_path)

    # Verify matplotlib functions were called
    mock_savefig.assert_called_once_with(output_path, dpi=300, bbox_inches="tight")
    mock_close.assert_called_once()


def test_plot_roi_intensity_traces_empty():
    """Test plotting with no ROIs."""
    roi_data = {"rois": []}
    fps = 10.0
    output_path = "dummy.png"

    # Should handle empty ROI list gracefully
    plot_roi_intensity_traces(roi_data, fps, output_path)


def test_save_auto_rois_json(temp_dir):
    """Test saving ROI data to JSON file."""
    roi_data = {
        "rois": [
            {
                "id": 0,
                "coords": [10, 10, 25, 25],
                "n_pixels": 225,
                "avg_intensity": [100.5, 102.1, 99.8],
                "center": [17.5, 17.5],
                "fluctuation_strength": 12.3,
            }
        ],
        "stats": {
            "n_rois": 1,
            "total_pixels": 225,
            "coverage_percent": 15.6,
            "threshold_used": 10.5,
            "min_distance_used": 5,
        },
    }

    output_path = os.path.join(temp_dir, "test_rois.json")
    save_auto_rois_json(roi_data, output_path)

    # Verify file was created and has correct content
    assert os.path.exists(output_path)

    import json

    with open(output_path, "r") as f:
        loaded_data = json.load(f)

    assert loaded_data == roi_data
    assert loaded_data["stats"]["n_rois"] == 1
    assert loaded_data["rois"][0]["id"] == 0


def test_auto_select_rois_integration():
    """Integration test for the complete auto ROI workflow."""
    # Create realistic test data
    n_frames, height, width = 20, 80, 80
    frames = np.ones((n_frames, height, width), dtype=np.float32) * 150

    # Add two distinct ROI regions with different characteristics
    roi1_coords = (20, 20, 30, 30)  # 10x10 region
    roi2_coords = (50, 50, 65, 65)  # 15x15 region

    for i in range(n_frames):
        # ROI 1: Moderate fluctuation
        frames[i, roi1_coords[0] : roi1_coords[2], roi1_coords[1] : roi1_coords[3]] = (
            150 + np.random.normal(0, 15, (10, 10))
        )

        # ROI 2: High fluctuation
        frames[i, roi2_coords[0] : roi2_coords[2], roi2_coords[1] : roi2_coords[3]] = (
            150 + np.random.normal(0, 25, (15, 15))
        )

    # Compute fluctuation map
    mean_intensity = frames.mean(axis=(1, 2))
    fluctuation_map, _ = compute_fluctuation_map(frames, mean_intensity)

    # Auto select ROIs
    threshold = np.percentile(fluctuation_map, 75)
    min_distance = 8

    roi_data = auto_select_rois_from_fluctuation(
        fluctuation_map, frames, threshold, min_distance
    )

    # Verify results
    assert roi_data["stats"]["n_rois"] >= 1
    assert roi_data["stats"]["coverage_percent"] > 0

    # Check that intensity traces have correct length
    for roi in roi_data["rois"]:
        assert len(roi["avg_intensity"]) == n_frames
        assert roi["n_pixels"] > 0
        assert isinstance(roi["fluctuation_strength"], float)

        # Verify bounding box format
        x0, y0, x1, y1 = roi["coords"]
        assert x1 > x0 and y1 > y0
        assert 0 <= x0 < width and 0 <= y0 < height
        assert 0 < x1 <= width and 0 < y1 <= height

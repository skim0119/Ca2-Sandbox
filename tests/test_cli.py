import os
import tempfile
import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock, MagicMock, ANY
from ca2roi.cli import main


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner for testing."""
    return CliRunner()


@patch("ca2roi.cli.process_video")
@patch("ca2roi.cli.compute_bleaching")
@patch("ca2roi.cli.save_bleaching")
@patch("ca2roi.cli.compute_fluctuation_map")
@patch("ca2roi.cli.save_fluctuation_overlay")
@patch("ca2roi.cli.handle_rois")
@patch("ca2roi.cli.extract_and_save_traces")
@patch("ca2roi.cli.ensure_workspace")
def test_main_command_default_workspace(
    mock_ensure_workspace,
    mock_extract_traces,
    mock_handle_rois,
    mock_save_overlay,
    mock_compute_fluct,
    mock_save_bleaching,
    mock_compute_bleaching,
    mock_process_video,
    cli_runner,
    temp_dir,
):
    """Test main CLI command with default workspace."""
    # Setup mocks
    mock_frames = Mock()
    mock_info = {"fps": 30.0, "n_frames": 10}
    mock_process_video.return_value = (mock_frames, mock_info)

    mock_mean_intensity = Mock()
    mock_compute_bleaching.return_value = mock_mean_intensity

    mock_fluct_map = Mock()
    mock_overlayed = Mock()
    mock_compute_fluct.return_value = (mock_fluct_map, mock_overlayed)

    mock_rois = [{"coords": [10, 10, 30, 30]}]
    mock_handle_rois.return_value = mock_rois

    # Create a temporary video file
    video_path = os.path.join(temp_dir, "test_video.avi")
    with open(video_path, "w") as f:
        f.write("fake video content")

    result = cli_runner.invoke(main, [video_path])

    assert result.exit_code == 0

    # Verify all functions were called
    mock_ensure_workspace.assert_called_once_with("result")
    mock_process_video.assert_called_once_with(video_path)
    mock_compute_bleaching.assert_called_once_with(mock_frames)
    mock_save_bleaching.assert_called_once()
    mock_compute_fluct.assert_called_once_with(mock_frames, mock_mean_intensity)
    mock_save_overlay.assert_called_once()
    mock_handle_rois.assert_called_once()
    mock_extract_traces.assert_called_once_with(mock_frames, mock_rois, ANY)


@patch("ca2roi.cli.process_video")
@patch("ca2roi.cli.compute_bleaching")
@patch("ca2roi.cli.save_bleaching")
@patch("ca2roi.cli.compute_fluctuation_map")
@patch("ca2roi.cli.save_fluctuation_overlay")
@patch("ca2roi.cli.handle_rois")
@patch("ca2roi.cli.extract_and_save_traces")
@patch("ca2roi.cli.ensure_workspace")
def test_main_command_custom_workspace(
    mock_ensure_workspace,
    mock_extract_traces,
    mock_handle_rois,
    mock_save_overlay,
    mock_compute_fluct,
    mock_save_bleaching,
    mock_compute_bleaching,
    mock_process_video,
    cli_runner,
    temp_dir,
):
    """Test main CLI command with custom workspace."""
    # Setup mocks
    mock_frames = Mock()
    mock_info = {"fps": 30.0, "n_frames": 10}
    mock_process_video.return_value = (mock_frames, mock_info)

    mock_mean_intensity = Mock()
    mock_compute_bleaching.return_value = mock_mean_intensity

    mock_fluct_map = Mock()
    mock_overlayed = Mock()
    mock_compute_fluct.return_value = (mock_fluct_map, mock_overlayed)

    mock_rois = [{"coords": [10, 10, 30, 30]}]
    mock_handle_rois.return_value = mock_rois

    # Create a temporary video file
    video_path = os.path.join(temp_dir, "test_video.avi")
    with open(video_path, "w") as f:
        f.write("fake video content")

    custom_workspace = os.path.join(temp_dir, "custom_output")

    result = cli_runner.invoke(main, [video_path, "--workspace", custom_workspace])

    assert result.exit_code == 0
    mock_ensure_workspace.assert_called_once_with(custom_workspace)


def test_main_command_nonexistent_video(cli_runner):
    """Test main CLI command with non-existent video file."""
    result = cli_runner.invoke(main, ["/nonexistent/video.avi"])

    assert result.exit_code != 0
    assert "does not exist" in result.output or "No such file" in result.output


@patch("ca2roi.cli.process_video")
@patch("ca2roi.cli.compute_bleaching")
@patch("ca2roi.cli.save_bleaching")
@patch("ca2roi.cli.compute_fluctuation_map")
@patch("ca2roi.cli.save_fluctuation_overlay")
@patch("ca2roi.cli.handle_rois")
@patch("ca2roi.cli.extract_and_save_traces")
@patch("ca2roi.cli.ensure_workspace")
def test_main_command_file_paths(
    mock_ensure_workspace,
    mock_extract_traces,
    mock_handle_rois,
    mock_save_overlay,
    mock_compute_fluct,
    mock_save_bleaching,
    mock_compute_bleaching,
    mock_process_video,
    cli_runner,
    temp_dir,
):
    """Test that the correct file paths are generated."""
    # Setup mocks
    mock_frames = Mock()
    mock_info = {"fps": 30.0, "n_frames": 10}
    mock_process_video.return_value = (mock_frames, mock_info)

    mock_mean_intensity = Mock()
    mock_compute_bleaching.return_value = mock_mean_intensity

    mock_fluct_map = Mock()
    mock_overlayed = Mock()
    mock_compute_fluct.return_value = (mock_fluct_map, mock_overlayed)

    mock_rois = [{"coords": [10, 10, 30, 30]}]
    mock_handle_rois.return_value = mock_rois

    # Create a temporary video file with specific name
    video_path = os.path.join(temp_dir, "experiment_123.avi")
    with open(video_path, "w") as f:
        f.write("fake video content")

    workspace = os.path.join(temp_dir, "output")

    result = cli_runner.invoke(main, [video_path, "--workspace", workspace])

    assert result.exit_code == 0

    # Check that handle_rois was called with correct paths
    expected_base = "experiment_123"
    mock_handle_rois.assert_called_once()

    # Get the call arguments
    call_args = mock_handle_rois.call_args[0]
    roi_json_path = call_args[1]
    roi_img_path = call_args[2]
    roi_img_label_path = call_args[3]

    # Verify paths contain the expected base name and workspace
    assert expected_base in roi_json_path
    assert workspace in roi_json_path
    assert expected_base in roi_img_path
    assert workspace in roi_img_path
    assert expected_base in roi_img_label_path
    assert workspace in roi_img_label_path


@patch("ca2roi.cli.auto_select_rois_from_fluctuation")
@patch("ca2roi.cli.save_auto_rois_plot")
@patch("ca2roi.cli.plot_roi_intensity_traces")
@patch("ca2roi.cli.save_auto_rois_json")
@patch("ca2roi.cli.extract_and_save_traces")
@patch("ca2roi.cli.process_video")
@patch("ca2roi.cli.compute_bleaching")
@patch("ca2roi.cli.save_bleaching")
@patch("ca2roi.cli.compute_fluctuation_map")
@patch("ca2roi.cli.save_fluctuation_overlay")
@patch("ca2roi.cli.ensure_workspace")
def test_main_command_auto_roi_with_params(
    mock_ensure_workspace,
    mock_save_overlay,
    mock_compute_fluct,
    mock_save_bleaching,
    mock_compute_bleaching,
    mock_process_video,
    mock_extract_traces,
    mock_save_auto_json,
    mock_plot_traces,
    mock_save_auto_plot,
    mock_auto_select,
    cli_runner,
    temp_dir,
):
    """Test main CLI command with auto-roi flag and parameters."""
    # Setup mocks
    mock_frames = Mock()
    mock_info = {"fps": 30.0, "n_frames": 10}
    mock_process_video.return_value = (mock_frames, mock_info)

    mock_mean_intensity = Mock()
    mock_compute_bleaching.return_value = mock_mean_intensity

    mock_fluct_map = Mock()
    mock_overlayed = Mock()
    mock_compute_fluct.return_value = (mock_fluct_map, mock_overlayed)

    mock_roi_data = {
        "rois": [
            {
                "id": 0,
                "coords": [10, 10, 30, 30],
                "n_pixels": 400,
                "avg_intensity": [100.0] * 10,
            }
        ],
        "stats": {"n_rois": 1, "total_pixels": 400, "coverage_percent": 5.0},
    }
    mock_auto_select.return_value = mock_roi_data

    # Create a temporary video file
    video_path = os.path.join(temp_dir, "test_video.avi")
    with open(video_path, "w") as f:
        f.write("fake video content")

    result = cli_runner.invoke(
        main, [video_path, "--auto-roi", "--threshold", "15.5", "--min-distance", "8"]
    )

    assert result.exit_code == 0

    # Verify auto ROI selection was called with correct parameters
    mock_auto_select.assert_called_once_with(
        mock_fluct_map, mock_frames, 15.5, 8, "results"
    )

    # Verify all auto ROI functions were called
    mock_save_auto_plot.assert_called_once()
    mock_plot_traces.assert_called_once()
    mock_save_auto_json.assert_called_once()
    mock_extract_traces.assert_called_once()


@patch("ca2roi.cli.auto_select_rois_from_fluctuation")
@patch("ca2roi.cli.save_auto_rois_plot")
@patch("ca2roi.cli.plot_roi_intensity_traces")
@patch("ca2roi.cli.save_auto_rois_json")
@patch("ca2roi.cli.extract_and_save_traces")
@patch("ca2roi.cli.process_video")
@patch("ca2roi.cli.compute_bleaching")
@patch("ca2roi.cli.save_bleaching")
@patch("ca2roi.cli.compute_fluctuation_map")
@patch("ca2roi.cli.save_fluctuation_overlay")
@patch("ca2roi.cli.ensure_workspace")
@patch("click.prompt")
@patch("numpy.percentile")
def test_main_command_auto_roi_interactive(
    mock_percentile,
    mock_prompt,
    mock_ensure_workspace,
    mock_save_overlay,
    mock_compute_fluct,
    mock_save_bleaching,
    mock_compute_bleaching,
    mock_process_video,
    mock_extract_traces,
    mock_save_auto_json,
    mock_plot_traces,
    mock_save_auto_plot,
    mock_auto_select,
    cli_runner,
    temp_dir,
):
    """Test main CLI command with auto-roi flag but interactive prompts."""
    # Setup mocks
    mock_frames = Mock()
    mock_info = {"fps": 30.0, "n_frames": 10}
    mock_process_video.return_value = (mock_frames, mock_info)

    mock_mean_intensity = Mock()
    mock_compute_bleaching.return_value = mock_mean_intensity

    mock_fluct_map = Mock()
    mock_fluct_map.min.return_value = 5.0
    mock_fluct_map.max.return_value = 50.0
    mock_fluct_map.mean.return_value = 20.0
    mock_fluct_map.std.return_value = 8.0
    mock_overlayed = Mock()
    mock_compute_fluct.return_value = (mock_fluct_map, mock_overlayed)

    mock_percentile.return_value = 35.0
    mock_prompt.side_effect = [30.0, 6]  # threshold, min_distance

    mock_roi_data = {
        "rois": [
            {
                "id": 0,
                "coords": [10, 10, 30, 30],
                "n_pixels": 400,
                "avg_intensity": [100.0] * 10,
            }
        ],
        "stats": {"n_rois": 1, "total_pixels": 400, "coverage_percent": 5.0},
    }
    mock_auto_select.return_value = mock_roi_data

    # Create a temporary video file
    video_path = os.path.join(temp_dir, "test_video.avi")
    with open(video_path, "w") as f:
        f.write("fake video content")

    result = cli_runner.invoke(main, [video_path, "--auto-roi"])

    assert result.exit_code == 0

    # Verify prompts were called
    assert mock_prompt.call_count == 2

    # Verify auto ROI selection was called with prompted values
    mock_auto_select.assert_called_once_with(
        mock_fluct_map, mock_frames, 30.0, 6, "results"
    )


@patch("ca2roi.cli.auto_select_rois_from_fluctuation")
@patch("ca2roi.cli.process_video")
@patch("ca2roi.cli.compute_bleaching")
@patch("ca2roi.cli.save_bleaching")
@patch("ca2roi.cli.compute_fluctuation_map")
@patch("ca2roi.cli.save_fluctuation_overlay")
@patch("ca2roi.cli.ensure_workspace")
def test_main_command_auto_roi_no_rois_found(
    mock_ensure_workspace,
    mock_save_overlay,
    mock_compute_fluct,
    mock_save_bleaching,
    mock_compute_bleaching,
    mock_process_video,
    mock_auto_select,
    cli_runner,
    temp_dir,
):
    """Test main CLI command when auto ROI selection finds no ROIs."""
    # Setup mocks
    mock_frames = Mock()
    mock_info = {"fps": 30.0, "n_frames": 10}
    mock_process_video.return_value = (mock_frames, mock_info)

    mock_mean_intensity = Mock()
    mock_compute_bleaching.return_value = mock_mean_intensity

    mock_fluct_map = Mock()
    mock_overlayed = Mock()
    mock_compute_fluct.return_value = (mock_fluct_map, mock_overlayed)

    # No ROIs found
    mock_roi_data = {
        "rois": [],
        "stats": {"n_rois": 0, "total_pixels": 0, "coverage_percent": 0.0},
    }
    mock_auto_select.return_value = mock_roi_data

    # Create a temporary video file
    video_path = os.path.join(temp_dir, "test_video.avi")
    with open(video_path, "w") as f:
        f.write("fake video content")

    result = cli_runner.invoke(
        main, [video_path, "--auto-roi", "--threshold", "50.0", "--min-distance", "5"]
    )

    assert result.exit_code == 0
    assert "No ROIs found with the given threshold" in result.output


@patch("ca2roi.cli.handle_rois")
@patch("ca2roi.cli.extract_and_save_traces")
@patch("ca2roi.cli.process_video")
@patch("ca2roi.cli.compute_bleaching")
@patch("ca2roi.cli.save_bleaching")
@patch("ca2roi.cli.compute_fluctuation_map")
@patch("ca2roi.cli.save_fluctuation_overlay")
@patch("ca2roi.cli.ensure_workspace")
def test_main_command_manual_roi_fallback(
    mock_ensure_workspace,
    mock_save_overlay,
    mock_compute_fluct,
    mock_save_bleaching,
    mock_compute_bleaching,
    mock_process_video,
    mock_extract_traces,
    mock_handle_rois,
    cli_runner,
    temp_dir,
):
    """Test main CLI command falls back to manual ROI selection when auto-roi not specified."""
    # Setup mocks
    mock_frames = Mock()
    mock_info = {"fps": 30.0, "n_frames": 10}
    mock_process_video.return_value = (mock_frames, mock_info)

    mock_mean_intensity = Mock()
    mock_compute_bleaching.return_value = mock_mean_intensity

    mock_fluct_map = Mock()
    mock_overlayed = Mock()
    mock_compute_fluct.return_value = (mock_fluct_map, mock_overlayed)

    mock_rois = [{"coords": [10, 10, 30, 30]}]
    mock_handle_rois.return_value = mock_rois

    # Create a temporary video file
    video_path = os.path.join(temp_dir, "test_video.avi")
    with open(video_path, "w") as f:
        f.write("fake video content")

    result = cli_runner.invoke(main, [video_path])

    assert result.exit_code == 0

    # Verify manual ROI selection was called (not auto)
    mock_handle_rois.assert_called_once()
    mock_extract_traces.assert_called_once_with(mock_frames, mock_rois, ANY)

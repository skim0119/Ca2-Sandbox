import os
import pytest
import numpy as np
import cv2
from unittest.mock import patch, Mock
from ca2roi.video import process_video, VideoMetadata, get_first_frame


@patch("cv2.VideoCapture")
def test_process_video_basic(mock_video_capture, temp_dir):
    """Test basic video processing functionality."""
    # Create mock video capture object
    mock_cap = Mock()
    mock_video_capture.return_value = mock_cap

    # Mock video properties
    mock_cap.get.side_effect = lambda prop: {
        cv2.CAP_PROP_FRAME_COUNT: 3,
        cv2.CAP_PROP_FRAME_WIDTH: 100,
        cv2.CAP_PROP_FRAME_HEIGHT: 100,
        cv2.CAP_PROP_FPS: 30.0,
    }[prop]

    # Mock frames
    frame1 = np.ones((100, 100), dtype=np.uint8) * 50
    frame2 = np.ones((100, 100), dtype=np.uint8) * 100
    frame3 = np.ones((100, 100), dtype=np.uint8) * 150

    mock_cap.read.side_effect = [
        (True, frame1),
        (True, frame2),
        (True, frame3),
        (False, None),  # End of video
    ]

    test_video_path = os.path.join(temp_dir, "test.avi")

    video_metadata = process_video(test_video_path)

    # Verify results
    assert video_metadata.frames.shape == (3, 100, 100)
    assert video_metadata.frames.dtype == np.float32
    assert video_metadata.n_frames == 3
    assert video_metadata.width == 100
    assert video_metadata.height == 100
    assert video_metadata.fps == 30.0

    # Check frame values
    assert np.all(video_metadata.frames[0] == 50.0)
    assert np.all(video_metadata.frames[1] == 100.0)
    assert np.all(video_metadata.frames[2] == 150.0)

    # Test info method
    info = video_metadata.info()
    assert info["n_frames"] == 3
    assert info["width"] == 100
    assert info["height"] == 100
    assert info["fps"] == 30.0

    # Test get_first_frame method
    first_frame = video_metadata.get_first_frame()
    assert np.all(first_frame == 50.0)

    mock_cap.release.assert_called_once()


@patch("cv2.VideoCapture")
def test_process_video_color_conversion(mock_video_capture, temp_dir):
    """Test that color frames are converted to grayscale."""
    mock_cap = Mock()
    mock_video_capture.return_value = mock_cap

    mock_cap.get.side_effect = lambda prop: {
        cv2.CAP_PROP_FRAME_COUNT: 1,
        cv2.CAP_PROP_FRAME_WIDTH: 50,
        cv2.CAP_PROP_FRAME_HEIGHT: 50,
        cv2.CAP_PROP_FPS: 30.0,
    }[prop]

    # Create a color frame (3 channels)
    color_frame = np.ones((50, 50, 3), dtype=np.uint8) * 100

    with patch("cv2.cvtColor") as mock_cvt_color:
        # Mock the color conversion
        gray_frame = np.ones((50, 50), dtype=np.uint8) * 100
        mock_cvt_color.return_value = gray_frame

        mock_cap.read.side_effect = [(True, color_frame), (False, None)]

        test_video_path = os.path.join(temp_dir, "test_color.avi")
        video_metadata = process_video(test_video_path)

        # Verify color conversion was called
        mock_cvt_color.assert_called_once_with(color_frame, cv2.COLOR_BGR2GRAY)
        assert video_metadata.frames.shape == (1, 50, 50)


@patch("cv2.VideoCapture")
def test_process_video_empty_video(mock_video_capture, temp_dir):
    """Test processing an empty video."""
    mock_cap = Mock()
    mock_video_capture.return_value = mock_cap

    mock_cap.get.side_effect = lambda prop: {
        cv2.CAP_PROP_FRAME_COUNT: 0,
        cv2.CAP_PROP_FRAME_WIDTH: 100,
        cv2.CAP_PROP_FRAME_HEIGHT: 100,
        cv2.CAP_PROP_FPS: 30.0,
    }[prop]

    mock_cap.read.return_value = (False, None)

    test_video_path = os.path.join(temp_dir, "empty.avi")
    video_metadata = process_video(test_video_path)

    assert video_metadata.frames.shape == (0, 100, 100)
    assert video_metadata.n_frames == 0


@patch("cv2.VideoCapture")
def test_video_metadata_from_video_path(mock_video_capture, temp_dir):
    """Test VideoMetadata.from_video_path class method."""
    mock_cap = Mock()
    mock_video_capture.return_value = mock_cap

    mock_cap.get.side_effect = lambda prop: {
        cv2.CAP_PROP_FRAME_COUNT: 2,
        cv2.CAP_PROP_FRAME_WIDTH: 64,
        cv2.CAP_PROP_FRAME_HEIGHT: 64,
        cv2.CAP_PROP_FPS: 25.0,
    }[prop]

    frame1 = np.ones((64, 64), dtype=np.uint8) * 75
    frame2 = np.ones((64, 64), dtype=np.uint8) * 125

    mock_cap.read.side_effect = [
        (True, frame1),
        (True, frame2),
        (False, None),
    ]

    test_video_path = os.path.join(temp_dir, "test_from_path.avi")
    video_metadata = VideoMetadata.from_video_path(test_video_path)

    assert video_metadata.frames.shape == (2, 64, 64)
    assert video_metadata.n_frames == 2
    assert video_metadata.width == 64
    assert video_metadata.height == 64
    assert video_metadata.fps == 25.0


@patch("cv2.VideoCapture")
def test_video_metadata_invalid_path(mock_video_capture, temp_dir):
    """Test VideoMetadata.from_video_path with invalid video path."""
    mock_cap = Mock()
    mock_video_capture.return_value = mock_cap
    mock_cap.isOpened.return_value = False

    test_video_path = os.path.join(temp_dir, "nonexistent.avi")

    with pytest.raises(ValueError, match="Could not open video file"):
        VideoMetadata.from_video_path(test_video_path)


@patch("cv2.VideoCapture")
def test_get_first_frame_function(mock_video_capture, temp_dir):
    """Test the standalone get_first_frame function."""
    mock_cap = Mock()
    mock_video_capture.return_value = mock_cap

    mock_cap.get.side_effect = lambda prop: {
        cv2.CAP_PROP_FRAME_COUNT: 2,
        cv2.CAP_PROP_FRAME_WIDTH: 80,
        cv2.CAP_PROP_FRAME_HEIGHT: 60,
        cv2.CAP_PROP_FPS: 24.0,
    }[prop]

    frame1 = np.ones((60, 80), dtype=np.uint8) * 200
    frame2 = np.ones((60, 80), dtype=np.uint8) * 250

    mock_cap.read.side_effect = [
        (True, frame1),
        (True, frame2),
        (False, None),
    ]

    test_video_path = os.path.join(temp_dir, "test_get_first.avi")
    first_frame = get_first_frame(test_video_path)

    # Test first frame
    assert first_frame.shape == (60, 80)
    assert first_frame.dtype == np.float32
    assert np.all(first_frame == 200.0)


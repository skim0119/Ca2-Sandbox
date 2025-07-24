import os
import pytest
import numpy as np
import cv2
from unittest.mock import patch, Mock
from ca2roi.video import process_video


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

    frames, info = process_video(test_video_path)

    # Verify results
    assert frames.shape == (3, 100, 100)
    assert frames.dtype == np.float32
    assert info["n_frames"] == 3
    assert info["width"] == 100
    assert info["height"] == 100
    assert info["fps"] == 30.0

    # Check frame values
    assert np.all(frames[0] == 50.0)
    assert np.all(frames[1] == 100.0)
    assert np.all(frames[2] == 150.0)

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
        frames, info = process_video(test_video_path)

        # Verify color conversion was called
        mock_cvt_color.assert_called_once_with(color_frame, cv2.COLOR_BGR2GRAY)
        assert frames.shape == (1, 50, 50)


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
    frames, info = process_video(test_video_path)

    assert frames.shape == (0, 100, 100)
    assert info["n_frames"] == 0

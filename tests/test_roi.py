import os
import json
import csv
import numpy as np
import pytest
from unittest.mock import patch, Mock, mock_open
from PIL import Image
from ca2roi.roi import handle_rois, draw_roi_images, extract_and_save_traces


def test_handle_rois_existing_json(temp_dir, sample_image, sample_rois):
    """Test handle_rois when ROI JSON file already exists."""
    roi_json_path = os.path.join(temp_dir, "test_rois.json")
    roi_img_path = os.path.join(temp_dir, "test_rois.png")
    roi_img_label_path = os.path.join(temp_dir, "test_rois_label.png")
    
    # Create existing ROI file
    with open(roi_json_path, 'w') as f:
        json.dump(sample_rois, f)
    
    with patch('ca2roi.roi.draw_roi_images') as mock_draw:
        result = handle_rois(sample_image, roi_json_path, roi_img_path, roi_img_label_path)
        
        assert result == sample_rois
        mock_draw.assert_called_once_with(sample_image, sample_rois, roi_img_path, roi_img_label_path)


def test_handle_rois_no_existing_json(temp_dir, sample_image, sample_rois):
    """Test handle_rois when no ROI JSON file exists."""
    roi_json_path = os.path.join(temp_dir, "new_rois.json")
    roi_img_path = os.path.join(temp_dir, "new_rois.png")
    roi_img_label_path = os.path.join(temp_dir, "new_rois_label.png")
    
    with patch('ca2roi.roi.select_rois', return_value=sample_rois) as mock_select:
        with patch('ca2roi.roi.draw_roi_images') as mock_draw:
            result = handle_rois(sample_image, roi_json_path, roi_img_path, roi_img_label_path)
            
            assert result == sample_rois
            mock_select.assert_called_once_with(sample_image)
            mock_draw.assert_called_once()
            
            # Check that JSON file was created
            assert os.path.exists(roi_json_path)
            with open(roi_json_path, 'r') as f:
                saved_rois = json.load(f)
            assert saved_rois == sample_rois


@patch('ca2roi.roi.ImageDraw.Draw')
@patch('ca2roi.roi.ImageFont.truetype')
@patch('ca2roi.roi.Image.fromarray')
def test_draw_roi_images(mock_fromarray, mock_font, mock_draw, temp_dir, sample_image, sample_rois):
    """Test drawing ROI images."""
    roi_img_path = os.path.join(temp_dir, "test_roi.png")
    roi_img_label_path = os.path.join(temp_dir, "test_roi_label.png")
    
    # Mock PIL objects
    mock_img = Mock()
    mock_img_label = Mock()
    mock_img.copy.return_value = mock_img_label
    mock_fromarray.return_value = mock_img
    
    mock_draw_obj = Mock()
    mock_draw_label_obj = Mock()
    mock_draw.side_effect = [mock_draw_obj, mock_draw_label_obj]
    
    mock_font_obj = Mock()
    mock_font.return_value = mock_font_obj
    
    draw_roi_images(sample_image, sample_rois, roi_img_path, roi_img_label_path)
    
    # Verify image conversion and drawing calls
    mock_fromarray.assert_called_once()
    assert mock_draw.call_count == 2
    
    # Verify rectangles and text are drawn for each ROI
    assert mock_draw_obj.rectangle.call_count == len(sample_rois)
    assert mock_draw_label_obj.rectangle.call_count == len(sample_rois)
    assert mock_draw_label_obj.text.call_count == len(sample_rois)
    
    # Verify images are saved
    mock_img.save.assert_called_once_with(roi_img_path)
    mock_img_label.save.assert_called_once_with(roi_img_label_path)


def test_extract_and_save_traces(temp_dir, sample_frames, sample_rois):
    """Test extracting and saving ROI traces."""
    roi_csv_path = os.path.join(temp_dir, "test_traces.csv")
    
    extract_and_save_traces(sample_frames, sample_rois, roi_csv_path)
    
    # Check that CSV file was created
    assert os.path.exists(roi_csv_path)
    
    # Read and verify CSV contents
    with open(roi_csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        data = list(reader)
    
    # Check header
    expected_header = [f'ROI{i+1}' for i in range(len(sample_rois))]
    assert header == expected_header
    
    # Check data dimensions
    assert len(data) == sample_frames.shape[0]  # Number of frames
    assert len(data[0]) == len(sample_rois)     # Number of ROIs
    
    # Verify that all values are numeric
    for row in data:
        for val in row:
            float(val)  # Should not raise an error


def test_extract_and_save_traces_single_roi(temp_dir, sample_frames):
    """Test extracting traces for a single ROI."""
    single_roi = [{"coords": [10, 10, 20, 20]}]
    roi_csv_path = os.path.join(temp_dir, "single_trace.csv")
    
    extract_and_save_traces(sample_frames, single_roi, roi_csv_path)
    
    assert os.path.exists(roi_csv_path)
    
    with open(roi_csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        data = list(reader)
    
    assert header == ['ROI1']
    assert len(data) == sample_frames.shape[0]
    assert len(data[0]) == 1


def test_extract_and_save_traces_roi_boundaries(temp_dir):
    """Test trace extraction with ROIs at image boundaries."""
    # Create small test frames
    frames = np.ones((5, 20, 20), dtype=np.float32) * 100
    
    # ROI at corner
    corner_roi = [{"coords": [0, 0, 5, 5]}]
    
    roi_csv_path = os.path.join(temp_dir, "corner_trace.csv")
    extract_and_save_traces(frames, corner_roi, roi_csv_path)
    
    assert os.path.exists(roi_csv_path)
    
    with open(roi_csv_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        data = list(reader)
    
    # Should have 5 frames of data
    assert len(data) == 5
    
    # All values should be 100.0 (the constant value we set)
    for row in data:
        assert float(row[0]) == 100.0 
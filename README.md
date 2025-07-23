# ca2roi

A CLI tool for calcium imaging video post-processing: bleaching analysis, ROI selection, and trace extraction.

## Installation

Install dependencies (using uv, pip, or your preferred tool):

```
uv pip install -r requirements.txt
```

Or, if using pyproject.toml:

```
uv pip install -e .
```

## Usage

```
ca2roi <video_path> [--workspace <output_folder>]
```

- `video_path`: Path to the calcium imaging video (e.g., AVI file)
- `--workspace`: Output directory (default: `result`)

The tool will:
- Compute and save bleaching info
- Compute and overlay fluctuation map
- Allow interactive ROI selection (or load existing ROIs)
- Save ROI traces, ROI images, and ROI locations

## Project Structure

- `src/ca2roi/cli.py`: CLI entry point
- `src/ca2roi/video.py`: Video loading
- `src/ca2roi/bleaching.py`: Bleaching analysis
- `src/ca2roi/fluctuation.py`: Fluctuation map
- `src/ca2roi/roi.py`: ROI selection and trace extraction
- `src/ca2roi/utils.py`: Utilities

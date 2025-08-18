# MiV-Ca2 Intensity Analysis Toolbox

A CLI tool for calcium imaging video post-processing: bleaching analysis, ROI selection, and trace extraction.

The package is developed to provide light-weight and easy-to-use tools for calcium imaging video analysis.
Data can be saved in csv format for further analysis.
(Please note in [issue](https://github.com/skim0119/CA2-Sandbox/issues) if you have desired format other than csv).

## Easy installation

`pip install ca2roi`

> Recommend `python3.10+`.

## Easy launch

`ca2roi-gui`

## CLI usage (for batch processing)

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

## Python-package ca2roi

```py
import ca2roi
```

## Project Structure

Project uses `Python3` as a main backend language. It uses `FastAPI` to connect frontend and backend.
Frontend is developed with `Vue3` and `TypeScript`.

The tool is not yet supported to be launched in a server.

All the core source code is in `src` folder.

- `ca2roi`: `Python` package for analysis functions.
- `frontend`: `Vue3` frontend for GUI development
- `commands`: CLI command scripts, written with `Python` with `click`.

## Contribution / Development

`Makefile` includes useful commands for development.

## Support

This project is mainly developed by [@skim0119](https://github.com/skim0119) as part of the support for [Mind-in-vitro project](https://mattia-lab.com/).

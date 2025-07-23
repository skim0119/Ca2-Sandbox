import click
from .video import process_video
from .roi import handle_rois
from .bleaching import compute_bleaching, save_bleaching
from .fluctuation import compute_fluctuation_map, save_fluctuation_overlay
from .utils import ensure_workspace
import os
import json

@click.command()
@click.argument('video_path', type=click.Path(exists=True))
@click.option('--workspace', default='result', type=click.Path(), help='Output workspace directory')
def main(video_path, workspace):
    ensure_workspace(workspace)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    roi_json_path = os.path.join(workspace, f'{base_name}_rois.json')
    roi_csv_path = os.path.join(workspace, f'{base_name}_roi_traces.csv')
    roi_img_path = os.path.join(workspace, f'{base_name}_rois.png')
    roi_img_label_path = os.path.join(workspace, f'{base_name}_rois_label.png')
    bleach_pkl_path = os.path.join(workspace, f'{base_name}_bleaching.pkl')
    overlay_img_path = os.path.join(workspace, f'{base_name}_fluctuation_overlay.png')

    frames, info = process_video(video_path)
    mean_intensity = compute_bleaching(frames)
    save_bleaching(mean_intensity, info, bleach_pkl_path)
    fluct_map, overlayed = compute_fluctuation_map(frames, mean_intensity)
    save_fluctuation_overlay(overlayed, overlay_img_path)
    rois = handle_rois(frames[0], roi_json_path, roi_img_path, roi_img_label_path)
    from .roi import extract_and_save_traces
    extract_and_save_traces(frames, rois, roi_csv_path)
    click.echo(f'Saved all results to {workspace}')

if __name__ == '__main__':
    main() 
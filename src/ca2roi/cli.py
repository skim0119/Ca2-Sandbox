import click
from .video import process_video
from .roi import handle_rois, extract_and_save_traces
from .bleaching import (
    compute_bleaching,
    save_bleaching,
    save_bleaching_trend_csv,
    plot_bleaching_trend,
)
from .fluctuation import (
    compute_fluctuation_map,
    save_fluctuation_overlay,
    auto_select_rois_from_fluctuation,
    filter_rois_by_size,
    save_auto_rois_plot,
    plot_roi_intensity_traces,
)
from .roi_similarity import cluster_rois_by_similarity, plot_clustered_rois
from .utils import ensure_workspace
import os
import json
import numpy as np


@click.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option(
    "--workspace",
    default="results",
    type=click.Path(),
    help="Output workspace directory",
)
@click.option(
    "--auto-roi",
    is_flag=True,
    default=True,
    help="Enable automatic ROI selection based on fluctuation map",
)
@click.option(
    "-T",
    "--threshold-percentage",
    type=float,
    default=99,
    show_default=True,
    help="Percentile for fluctuation map threshold (higher = more selective, default: 99)",
)
@click.option(
    "-D",
    "--min-distance-percentage",
    type=float,
    default=0.01,
    show_default=True,
    help="Minimum distance in pixels for ROI clustering (default: 5% of image width)",
)
@click.option(
    "-C",
    "--n-clusters",
    type=int,
    default=3,
    show_default=True,
    help="Number of clusters for k-means clustering of ROI traces (default: 3)",
)
def main(
    video_path,
    workspace,
    auto_roi,
    threshold_percentage,
    min_distance_percentage,
    n_clusters,
):
    ensure_workspace(workspace)
    roi_json_path = os.path.join(workspace, f"rois.json")
    roi_csv_path = os.path.join(workspace, f"roi_traces.csv")
    roi_img_path = os.path.join(workspace, f"rois.pdf")
    roi_img_label_path = os.path.join(workspace, f"rois_label.pdf")
    bleach_pkl_path = os.path.join(workspace, f"bleaching.pkl")
    bleach_csv_path = os.path.join(workspace, f"bleaching_trend.csv")
    overlay_img_path = os.path.join(workspace, f"fluctuation_overlay.pdf")

    frames, info = process_video(video_path)
    mean_intensity = compute_bleaching(frames)
    save_bleaching(mean_intensity, info, bleach_pkl_path)
    save_bleaching_trend_csv(mean_intensity, info["fps"], bleach_csv_path)
    _, normalizer = plot_bleaching_trend(csv_path=bleach_csv_path)

    fluct_map = compute_fluctuation_map(frames, mean_intensity)
    save_fluctuation_overlay(fluct_map, overlay_img_path)

    if auto_roi:
        threshold = np.percentile(fluct_map, threshold_percentage)
        min_distance = int(frames.shape[2] * min_distance_percentage)

        # Perform automatic ROI selection
        click.echo(
            f"Performing automatic ROI selection with threshold={threshold}, min_distance={min_distance}"
        )
        roi_data = auto_select_rois_from_fluctuation(
            fluct_map, frames, threshold, min_distance, workspace
        )

        if roi_data["rois"]:
            # Apply size filtering (10-90 percentile)
            click.echo("Applying size filtering (10-90 percentile)...")
            roi_data = filter_rois_by_size(
                roi_data, min_percentile=50, max_percentile=90
            )

            # Save auto ROI plots and data
            auto_roi_plot_path = os.path.join(workspace, "auto_rois_locations.pdf")
            save_auto_rois_plot(fluct_map, roi_data, frames[0], auto_roi_plot_path)

            # Plot intensity traces
            traces_plot_path = os.path.join(workspace, "auto_roi_traces.pdf")
            plot_roi_intensity_traces(
                roi_data, info["fps"], normalizer, traces_plot_path
            )

            # Add first frame to roi_data for spatial visualization
            roi_data["first_frame"] = frames[0]

            # Cluster roi normalized intensity by similarity
            cluster_rois_by_similarity(
                roi_data, normalizer, info["fps"], len(frames), n_clusters, workspace
            )
            plot_clustered_rois(roi_data, workspace, n_clusters)

            # Save ROI data as JSON
            auto_roi_json_path = os.path.join(workspace, "auto_rois.json")
            with open(auto_roi_json_path, "wb") as f:
                import pickle

                pickle.dump(roi_data, f)

            # Convert to format compatible with existing ROI functions
            compatible_rois = []
            for roi in roi_data["rois"]:
                compatible_rois.append({"coords": roi["coords"]})

            # Save ROI traces in CSV format
            extract_and_save_traces(frames, compatible_rois, roi_csv_path)

            click.echo(f"\nAutomatic ROI Selection Results:")
            click.echo(f"  Number of ROIs: {roi_data['stats']['n_rois']}")
            click.echo(f"  Total target pixels: {roi_data['stats']['total_pixels']}")
            click.echo(
                f"  Coverage: {roi_data['stats']['coverage_percent']:.2f}% of image"
            )

        else:
            click.echo(
                "No ROIs found with the given threshold. Try lowering the threshold."
            )

    else:
        # Use manual ROI selection
        rois = handle_rois(frames[0], roi_json_path, roi_img_path, roi_img_label_path)
        if len(rois) > 0:
            extract_and_save_traces(frames, rois, roi_csv_path)
        else:
            click.echo("No ROIs selected.")

    click.echo(f"Saved all results to {workspace}")


if __name__ == "__main__":
    main()

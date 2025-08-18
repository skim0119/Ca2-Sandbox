import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import csv


def handle_rois(image, roi_json_path, roi_img_path, roi_img_label_path):
    if os.path.exists(roi_json_path):
        with open(roi_json_path, "r") as f:
            rois = json.load(f)
    else:
        rois = select_rois(image)
        with open(roi_json_path, "w") as f:
            json.dump(rois, f)
    draw_roi_images(image, rois, roi_img_path, roi_img_label_path)
    return rois


def select_rois(image):
    rois = []
    fig, ax = plt.subplots()
    ax.imshow(image, cmap="gray")
    plt.title("Draw ROIs: Drag to select, press Enter when done")
    coords = []

    def on_press(event):
        if event.inaxes != ax:
            return
        coords.clear()
        coords.append((int(event.xdata), int(event.ydata)))

    def on_release(event):
        if event.inaxes != ax:
            return
        coords.append((int(event.xdata), int(event.ydata)))
        x0, y0 = coords[0]
        x1, y1 = coords[1]
        rect = patches.Rectangle(
            (x0, y0), x1 - x0, y1 - y0, linewidth=2, edgecolor="r", facecolor="none"
        )
        ax.add_patch(rect)
        rois.append({"coords": [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]})
        fig.canvas.draw()

    def on_key(event):
        if event.key == "enter":
            plt.close(fig)

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("button_release_event", on_release)
    fig.canvas.mpl_connect("key_press_event", on_key)
    plt.show()
    return rois


def draw_roi_images(image, rois, roi_img_path, roi_img_label_path):
    img = Image.fromarray(image.astype(np.uint8)).convert("RGB")
    img_label = img.copy()
    draw = ImageDraw.Draw(img)
    draw_label = ImageDraw.Draw(img_label)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    for idx, roi in enumerate(rois):
        xy = roi["coords"]
        draw.rectangle(xy, outline="red", width=2)
        draw_label.rectangle(xy, outline="red", width=2)
        draw_label.text((xy[0], xy[1]), f"ROI{idx + 1}", fill="yellow", font=font)
    img.save(roi_img_path)
    img_label.save(roi_img_label_path)


def extract_and_save_traces(frames, rois, roi_csv_path):
    height, width = frames.shape[1:]
    traces = []
    for roi in rois:
        x0, y0, x1, y1 = roi["coords"]
        mask = np.zeros((height, width), dtype=bool)
        mask[y0:y1, x0:x1] = True
        trace = frames[:, mask].mean(axis=1)
        traces.append(trace)
    traces = np.stack(traces, axis=1)
    with open(roi_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([f"ROI{i + 1}" for i in range(len(rois))])
        writer.writerows(traces)

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from skimage.feature import peak_local_max
import tkinter as tk
from tkinter import filedialog
from matplotlib.widgets import RectangleSelector

class MapSelector:
    def __init__(self, data):
        self.data = data
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.im = self.ax.imshow(self.data, cmap='viridis', origin='lower', aspect='auto')
        self.ax.set_title('Select region for peak detection')
        self.selected_region = None
        
        self.rs = RectangleSelector(self.ax, self.line_select_callback,
                                    useblit=True,
                                    button=[1, 3],  # Left and right mouse buttons
                                    minspanx=5, minspany=5,
                                    spancoords='pixels',
                                    interactive=True)
        
        plt.colorbar(self.im, label='Intensity')
        plt.show()

    def line_select_callback(self, eclick, erelease):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        self.selected_region = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    def get_selected_region(self):
        return self.selected_region

def load_data(input_file_path):
    return np.load(input_file_path).T

def detect_peaks(data, region=None, sigma=1, min_distance=5, threshold_factor=1.1):
    if region is not None:
        x1, y1, x2, y2 = region
        data = data[y1:y2, x1:x2]
    
    smoothed_data = gaussian_filter(data, sigma=sigma)
    threshold = np.mean(smoothed_data) * threshold_factor
    peaks = peak_local_max(smoothed_data, min_distance=min_distance, threshold_abs=threshold)
    
    if region is not None:
        peaks[:, 0] += y1
        peaks[:, 1] += x1
    
    return peaks

def plot_peaks(data, peaks, title, region=None):
    plt.figure(figsize=(10, 8))
    plt.imshow(data, cmap='viridis', origin='lower', aspect='auto')
    for peak in peaks:
        y, x = peak
        plt.plot(x, y, 'r.', markersize=5)
    
    if region is not None:
        x1, y1, x2, y2 = region
        plt.gca().add_patch(plt.Rectangle((x1, y1), x2-x1, y2-y1, fill=False, edgecolor='white'))
    
    plt.title(title)
    plt.colorbar(label='Intensity')
    plt.show()

def save_peaks(peaks, output_file_path, map_size):
    with open(output_file_path, "w") as f:
        f.write("x,y\n")
        for peak in peaks:
            y, x = peak
            norm_x = (2 * x / map_size[1]) - 1
            norm_y = (2 * y / map_size[0]) - 1
            f.write(f"{norm_x},{norm_y}\n")

def select_input_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(title="Select input .npy file",
                                           filetypes=[("NumPy files", "*.npy")])
    return file_path

def select_output_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.asksaveasfilename(title="Save detected peaks as",
                                             defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")])
    return file_path

def main():
    # Select input file
    input_file_path = select_input_file()
    if not input_file_path:
        print("No input file selected. Exiting.")
        return

    # データを読み込む
    map_data = load_data(input_file_path)
    map_size = map_data.shape
    print(f'Number of lines of input file : {map_size[1]}')

    # マップを表示し、領域を選択
    selector = MapSelector(map_data)
    selected_region = selector.get_selected_region()

    # ピークを検出
    peaks = detect_peaks(map_data, region=selected_region)

    # ピークを表示
    plot_peaks(map_data, peaks, 'Detected Peaks', region=selected_region)

    # Select output file
    output_file_path = select_output_file()
    if not output_file_path:
        print("No output file selected. Exiting.")
        return

    # ピークを保存
    save_peaks(peaks, output_file_path, map_size)
    print(f"Detected {len(peaks)} peaks. Saved to {output_file_path}")

if __name__ == "__main__":
    main()
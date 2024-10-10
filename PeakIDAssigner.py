import numpy as np
import math
import matplotlib.pyplot as plt
import pandas as pd
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

N_pix = 45

def load_data(input_file_path):
    return np.load(input_file_path).T

def load_peaks(csv_file_path):
    return np.loadtxt(csv_file_path, delimiter=',', skiprows=1)

def normalize_coordinates(x, y, width, height):
    return (2 * x / width) - 1, (2 * y / height) - 1

def denormalize_coordinates(norm_x, norm_y, width, height):
    return int(((norm_x + 1) / 2) * width), int(((norm_y + 1) / 2) * height)

def assign_id_in_direction(peaks, start_id, start_peak, direction, max_dist=0.003, max_count=50, search_range=0.01, offset=0.0001):
    current_id = list(start_id)
    current_peak = start_peak
    assigned_peaks = []

    while True:
        x, y = current_peak
        id_x, id_y = current_id

        if direction == 'left':
            next_peaks = [peak for peak in peaks if peak[0] < x - offset and abs(peak[1] - y) < search_range]
        elif direction == 'right':
            next_peaks = [peak for peak in peaks if peak[0] > x + offset and abs(peak[1] - y) < search_range]
        elif direction == 'up':
            next_peaks = [peak for peak in peaks if peak[1] < y - offset and abs(peak[0] - x) < search_range]
        elif direction == 'down':
            next_peaks = [peak for peak in peaks if peak[1] > y + offset and abs(peak[0] - x) < search_range]

        if direction in ['left', 'right']:
            next_peaks = sorted(next_peaks, key=lambda p: abs(p[0] - x))[:max_count]
        else:
            next_peaks = sorted(next_peaks, key=lambda p: abs(p[1] - y))[:max_count]

        if not next_peaks:
            break

        next_peaks = sorted(next_peaks, key=lambda p: math.sqrt((p[0] - x)**2 + (p[1] - y)**2))

        next_peak = next_peaks[0]

        if direction in ['left', 'right']:
            if abs(next_peak[1] - y) > max_dist:
                break
        else:
            if abs(next_peak[0] - x) > max_dist:
                break

        if direction == 'left':
            new_id = [id_x - 1, id_y]
        elif direction == 'right':
            new_id = [id_x + 1, id_y]
        elif direction == 'up':
            new_id = [id_x, id_y + 1]
        elif direction == 'down':
            new_id = [id_x, id_y - 1]

        if not (0 <= new_id[0] < N_pix and 0 <= new_id[1] < N_pix):
            break

        assigned_peaks.append((new_id, next_peak))
        current_id = new_id
        current_peak = next_peak

        peaks = [p for p in peaks if not np.array_equal(p, next_peak)]

    return assigned_peaks, peaks

def assign_ids(peaks, start_peak, start_id):
    peak_ids = np.full((N_pix, N_pix, 2), np.nan)
    peak_ids[start_id[1]][start_id[0]] = start_peak  # Correct order: [id_y][id_x]

    remaining_peaks = peaks.copy()
    remaining_peaks = [p for p in remaining_peaks if not np.array_equal(p, start_peak)]

    # Assign IDs in all four directions from the start peak
    for direction in ['left', 'right', 'up', 'down']:
        assigned, remaining_peaks = assign_id_in_direction(remaining_peaks, start_id, start_peak, direction)
        for (id_x, id_y), peak in assigned:
            peak_ids[id_y][id_x] = peak  # Correct order: [id_y][id_x]

    # Assign IDs in up and down directions for each column
    for direction in ['up', 'down']:
        for i in range(N_pix):
            for j in range(N_pix):
                if not np.isnan(peak_ids[j][i][0]):
                    current_id = [i, j]
                    current_peak = peak_ids[j][i]
                    assigned, remaining_peaks = assign_id_in_direction(remaining_peaks, current_id, current_peak, direction)
                    for (id_x, id_y), peak in assigned:
                        peak_ids[id_y][id_x] = peak  # Correct order: [id_y][id_x]

    # Assign IDs in left and right directions for remaining peaks
    for direction in ['left', 'right']:
        N_pix_half = N_pix // 2
        for i in range(N_pix_half - 1):
            for j in range(N_pix):
                if direction == 'left':
                    if j == N_pix_half or not np.isnan(peak_ids[j][N_pix_half - (i + 1)][0]):
                        continue
                    current_id = [N_pix_half - i, j]
                    current_peak = peak_ids[j][N_pix_half - i]
                elif direction == 'right':
                    if j == N_pix_half or not np.isnan(peak_ids[j][N_pix_half + (i + 1)][0]):
                        continue
                    current_id = [N_pix_half + i, j]
                    current_peak = peak_ids[j][N_pix_half + i]
                
                if not np.isnan(current_peak[0]):
                    assigned, remaining_peaks = assign_id_in_direction(remaining_peaks, current_id, current_peak, direction)
                    for (id_x, id_y), peak in assigned:
                        peak_ids[id_y][id_x] = peak  # Correct order: [id_y][id_x]

    return peak_ids

class PeakSelector:
    def __init__(self, map_data, peaks):
        self.map_data = map_data
        self.peaks = peaks
        self.selected_peak = None

        self.root = tk.Tk()
        self.root.title("Select a Peak")
        
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        
        # Create a frame for the toolbar and add zoom instructions
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        zoom_label = ttk.Label(toolbar_frame, text="Use the zoom tool to zoom in/out. Right-click to reset zoom.")
        zoom_label.pack(side=tk.RIGHT, padx=5)
        
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.ax.imshow(self.map_data, cmap='viridis', origin='lower', extent=[-1, 1, -1, 1])
        self.scatter = self.ax.scatter(self.peaks[:, 0], self.peaks[:, 1], c='r', s=10)
        self.ax.set_title('Select a peak to start ID assignment')

        self.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        if event.inaxes is not None and event.button == 1:  # Left click
            # Check if we're in zoom mode
            if self.toolbar.mode == '':
                distances = np.sqrt((self.peaks[:, 0] - event.xdata)**2 + (self.peaks[:, 1] - event.ydata)**2)
                nearest_peak_idx = np.argmin(distances)
                self.selected_peak = self.peaks[nearest_peak_idx]
                self.root.quit()

    def get_selected_peak(self):
        self.root.mainloop()
        self.root.destroy()
        return self.selected_peak
    
def plot_assigned_peaks(peak_ids, map_data):
    plt.figure(figsize=(12, 12))
    plt.imshow(map_data, cmap='viridis', origin='lower', extent=[-1, 1, -1, 1])
    
    for id_x in range(N_pix):
        for id_y in range(N_pix):
            x, y = peak_ids[id_y][id_x]  # Correct order: [id_y][id_x]
            if not np.isnan(x) and not np.isnan(y):
                plt.plot(x, y, 'r.', markersize=10)
                plt.text(x, y, f'({id_x},{id_y})', color='white', fontsize=8, ha='center', va='bottom')
    
    plt.title('Assigned Peak IDs with Background Map')
    plt.colorbar(label='Intensity')
    plt.show()

def save_assigned_peaks(peak_ids, output_file_path):
    with open(output_file_path, "w") as f:
        f.write("IDx,IDy,Posix,Posiy,accuracy\n")
        for id_x in range(N_pix):
            for id_y in range(N_pix):
                x, y = peak_ids[id_y][id_x]  # Correct order: [id_y][id_x]
                if np.isnan(x) or np.isnan(y):
                    f.write(f'{id_x},{id_y},nan,nan,miss\n')
                else:
                    f.write(f'{id_x},{id_y},{x},{y},\n')


def select_file(title, filetypes):
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(title=title, filetypes=filetypes)

def main():
    # Select input map file
    map_file_path = select_file("Select input map NPY file", [("NumPy files", "*.npy")])
    if not map_file_path:
        print("No input map file selected. Exiting.")
        return

    # Select input peaks CSV file
    peaks_file_path = select_file("Select input peaks CSV file", [("CSV files", "*.csv")])
    if not peaks_file_path:
        print("No input peaks file selected. Exiting.")
        return

    # Load data
    map_data = load_data(map_file_path)
    peaks = load_peaks(peaks_file_path)

    # Select initial peak
    selector = PeakSelector(map_data, peaks)
    selected_peak = selector.get_selected_peak()

    if selected_peak is None:
        print("No peak selected. Exiting.")
        return

    # Get ID for selected peak
    id_x = simpledialog.askinteger("Input", "Enter the X ID for the selected peak:", minvalue=0, maxvalue=N_pix-1)
    id_y = simpledialog.askinteger("Input", "Enter the Y ID for the selected peak:", minvalue=0, maxvalue=N_pix-1)

    if id_x is None or id_y is None:
        print("Invalid ID entered. Exiting.")
        return

    # Assign IDs
    peak_ids = assign_ids(peaks, selected_peak, [id_x, id_y])

    # Plot assigned peaks
    plot_assigned_peaks(peak_ids, map_data)

    # Save assigned peaks
    output_file_path = filedialog.asksaveasfilename(title="Save assigned peaks as",
                                                    defaultextension=".csv",
                                                    filetypes=[("CSV files", "*.csv")])
    if output_file_path:
        save_assigned_peaks(peak_ids, output_file_path)
        print(f"Assigned IDs saved to {output_file_path}")
    else:
        print("No output file selected. Results not saved.")

if __name__ == "__main__":
    main()
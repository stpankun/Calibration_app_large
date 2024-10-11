import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import filedialog, messagebox, Menu
import pandas as pd

class PeakEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("Peak Editor")
        
        self.create_menu()
        
        self.map_data = None
        self.peaks = None
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.draw()
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        self.toolbar.update()
        
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        self.update_colorbar_button = tk.Button(master, text="Update Colorbar (U)", command=self.update_colorbar)
        self.update_colorbar_button.pack()
        
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        self.scatter = None
        self.colorbar = None
        self.pcolormesh = None

    def create_menu(self):
        menubar = Menu(self.master)
        self.master.config(menu=menubar)
        
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Data", command=self.load_data)
        file_menu.add_command(label="Save Peaks", command=self.save_peaks)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)

    def load_data(self):
        map_file = filedialog.askopenfilename(title="Select Map File", filetypes=[("NumPy files", "*.npy")])
        if map_file:
            self.map_data = np.load(map_file).T
        else:
            messagebox.showwarning("Warning", "No map file selected. Please load a map file to continue.")
            return

        peaks_file = filedialog.askopenfilename(title="Select Peaks File", filetypes=[("CSV files", "*.csv")])
        if peaks_file:
            self.peaks = pd.read_csv(peaks_file)
        else:
            messagebox.showwarning("Warning", "No peaks file selected. Please load a peaks file to continue.")
            return

        if self.map_data is not None and self.peaks is not None:
            self.plot_data()

    def plot_data(self):
        self.ax.clear()
        
        # Create a meshgrid for the map data
        height, width = self.map_data.shape
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        X, Y = np.meshgrid(x, y)
        
        # Plot the map data
        self.pcolormesh = self.ax.pcolormesh(X, Y, self.map_data, cmap='viridis', shading='auto')
        
        # Plot the peaks
        self.scatter = self.ax.scatter(self.peaks['x'], self.peaks['y'], c='r', s=5)
        
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.set_aspect('equal')
        
        if self.colorbar is None:
            self.colorbar = self.fig.colorbar(self.pcolormesh)
        else:
            self.colorbar.update_normal(self.pcolormesh)
        
        self.canvas.draw()

    def on_click(self, event):
        if event.inaxes is not None:
            if event.button == 1 and event.key == 'control':  # Ctrl + Left Click to add peak
                self.add_peak(event.xdata, event.ydata)
            elif event.button == 3 and event.key == 'control':  # Ctrl + Right Click to remove peak
                self.remove_peak(event.xdata, event.ydata)

    def on_key_press(self, event):
        if event.key == 'u':
            self.update_colorbar()
            return  # Prevent the event from propagating

    def add_peak(self, x, y):
        new_peak = pd.DataFrame({'x': [x], 'y': [y]})
        self.peaks = pd.concat([self.peaks, new_peak], ignore_index=True)
        self.update_plot()

    def remove_peak(self, x, y):
        distances = np.sqrt((self.peaks['x'] - x)**2 + (self.peaks['y'] - y)**2)
        closest_peak = distances.idxmin()
        self.peaks = self.peaks.drop(closest_peak).reset_index(drop=True)
        self.update_plot()

    def update_plot(self):
        if self.scatter is not None:
            self.scatter.remove()
        self.scatter = self.ax.scatter(self.peaks['x'], self.peaks['y'], c='r', s=3)
        self.canvas.draw()

    def update_colorbar(self):
        if self.map_data is not None and self.pcolormesh is not None:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            # Convert normalized coordinates to array indices
            height, width = self.map_data.shape
            x_min = int((xlim[0] + 1) / 2 * width)
            x_max = int((xlim[1] + 1) / 2 * width)
            y_min = int((ylim[0] + 1) / 2 * height)
            y_max = int((ylim[1] + 1) / 2 * height)
            
            # Ensure indices are within bounds
            x_min, x_max = max(0, x_min), min(width, x_max)
            y_min, y_max = max(0, y_min), min(height, y_max)
            
            visible_data = self.map_data[y_min:y_max, x_min:x_max]
            
            if visible_data.size > 0:
                self.pcolormesh.set_clim(visible_data.min(), visible_data.max())
                self.colorbar.update_normal(self.pcolormesh)
                self.canvas.draw_idle()

    def save_peaks(self):
        if self.peaks is not None:
            save_file = filedialog.asksaveasfilename(title="Save Peaks", defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if save_file:
                self.peaks.to_csv(save_file, index=False)
                messagebox.showinfo("Info", f"Peaks saved to {save_file}")
        else:
            messagebox.showwarning("Warning", "No peaks data to save. Please load data first.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PeakEditor(root)
    root.mainloop()
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import filedialog, messagebox, Menu, simpledialog
import pandas as pd

class PeakIDEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("Peak ID Editor")
        
        self.create_menu()
        
        self.map_data = None
        self.peaks = None
        self.peak_ids = None
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.draw()
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        self.toolbar.update()
        
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        self.update_colorbar_button = tk.Button(master, text="Update Colorbar (U)", command=self.update_colorbar)
        self.update_colorbar_button.pack()
        
        # Add a label showing the keyboard shortcuts
        shortcuts_text = "Shortcuts: T - Toggle ID labels, U - Update colorbar, Ctrl+Click - Select peak"
        self.shortcuts_label = tk.Label(master, text=shortcuts_text)
        self.shortcuts_label.pack()
        
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        self.scatter = None
        self.colorbar = None
        self.pcolormesh = None
        self.texts = []
        self.show_ids = True  # Flag to control ID text visibility

    def create_menu(self):
        menubar = Menu(self.master)
        self.master.config(menu=menubar)
        
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Map Data", command=self.load_map_data)
        file_menu.add_command(label="Load Peaks", command=self.load_peaks)
        file_menu.add_command(label="Load Peak IDs", command=self.load_peak_ids)
        file_menu.add_command(label="Save Peak IDs", command=self.save_peak_ids)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)

    def load_map_data(self):
        map_file = filedialog.askopenfilename(title="Select Map File", filetypes=[("NumPy files", "*.npy")])
        if map_file:
            self.map_data = np.load(map_file).T
            self.plot_data()
        else:
            messagebox.showwarning("Warning", "No map file selected.")

    def load_peaks(self):
        peaks_file = filedialog.askopenfilename(title="Select Peaks File", filetypes=[("CSV files", "*.csv")])
        if peaks_file:
            self.peaks = pd.read_csv(peaks_file)
            self.plot_data()
        else:
            messagebox.showwarning("Warning", "No peaks file selected.")

    def load_peak_ids(self):
        peak_ids_file = filedialog.askopenfilename(title="Select Peak IDs File", filetypes=[("CSV files", "*.csv")])
        if peak_ids_file:
            self.peak_ids = pd.read_csv(peak_ids_file)
            self.plot_data()
        else:
            messagebox.showwarning("Warning", "No peak IDs file selected.")

    def plot_data(self):
        # Store current view limits if they exist and if this is not the first plot
        if hasattr(self, 'pcolormesh') and self.pcolormesh is not None:
            prev_xlim = self.ax.get_xlim()
            prev_ylim = self.ax.get_ylim()
        else:
            prev_xlim = prev_ylim = None
            
        self.ax.clear()
        for text in self.texts:
            text.remove()
        self.texts.clear()
        
        if self.map_data is not None:
            height, width = self.map_data.shape
            x = np.linspace(-1, 1, width)
            y = np.linspace(-1, 1, height)
            X, Y = np.meshgrid(x, y)
            self.pcolormesh = self.ax.pcolormesh(X, Y, self.map_data, cmap='viridis', shading='auto')
        
        if self.peaks is not None:
            self.scatter = self.ax.scatter(self.peaks['x'], self.peaks['y'], c='r', s=5)
        
        if self.peak_ids is not None:
            for _, row in self.peak_ids.iterrows():
                if row['accuracy'] != 'miss':
                    text = self.ax.text(row['Posix'], row['Posiy'], f"{row['IDx']},{row['IDy']}", 
                                      color='white', fontsize=8, ha='center', va='center',
                                      visible=self.show_ids)  # Apply visibility setting
                    self.texts.append(text)
        
        # Set view limits: use previous limits if they exist, otherwise use default limits
        if prev_xlim is not None and prev_ylim is not None:
            self.ax.set_xlim(prev_xlim)
            self.ax.set_ylim(prev_ylim)
        else:
            # Default limits for initial plot
            self.ax.set_xlim(-1, 1)
            self.ax.set_ylim(-1, 1)
            
        self.ax.set_aspect('equal')
        
        if self.colorbar is None:
            self.colorbar = self.fig.colorbar(self.pcolormesh)
        else:
            self.colorbar.update_normal(self.pcolormesh)
        
        self.canvas.draw()

    def on_click(self, event):
        # Check if we're in zoom or pan mode
        if self.toolbar.mode != '':  # '' indicates no active tool
            return
            
        if (event.inaxes is not None and 
            event.button == 1 and 
            event.key == 'control' and 
            self.peaks is not None and 
            self.peak_ids is not None):
            
            x, y = event.xdata, event.ydata
            closest_peak = self.find_closest_peak(x, y)
            if closest_peak is not None:
                self.assign_id_to_peak(closest_peak)

    def find_closest_peak(self, x, y):
        distances = np.sqrt((self.peaks['x'] - x)**2 + (self.peaks['y'] - y)**2)
        closest_index = distances.idxmin()
        if distances[closest_index] < 0.01:  # Adjust this threshold as needed
            return self.peaks.loc[closest_index]
        return None

    def assign_id_to_peak(self, peak):
        id_x = simpledialog.askinteger("Input", "Enter X ID:", parent=self.master, minvalue=0)
        id_y = simpledialog.askinteger("Input", "Enter Y ID:", parent=self.master, minvalue=0)
        
        if id_x is not None and id_y is not None:
            # Store current view limits
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            # Check if this ID already exists
            existing = self.peak_ids[(self.peak_ids['IDx'] == id_x) & (self.peak_ids['IDy'] == id_y)]
            if not existing.empty:
                if messagebox.askyesno("Confirm", "This ID already exists. Do you want to overwrite?"):
                    self.peak_ids.loc[(self.peak_ids['IDx'] == id_x) & (self.peak_ids['IDy'] == id_y), 
                                    ['Posix', 'Posiy', 'accuracy']] = [peak['x'], peak['y'], '']
            else:
                new_row = pd.DataFrame({'IDx': [id_x], 'IDy': [id_y], 'Posix': [peak['x']], 
                                      'Posiy': [peak['y']], 'accuracy': ['']})
                self.peak_ids = pd.concat([self.peak_ids, new_row], ignore_index=True)
            
            # Replot data and restore view limits
            self.plot_data()

    def on_key_press(self, event):
        if event.key == 'u':
            self.update_colorbar()
        elif event.key == 'T':  # Capital T to avoid conflict with existing shortcuts
            self.toggle_id_visibility()

    def toggle_id_visibility(self):
        self.show_ids = not self.show_ids
        for text in self.texts:
            text.set_visible(self.show_ids)
        self.canvas.draw()

    def update_colorbar(self):
        if self.map_data is not None and self.pcolormesh is not None:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            height, width = self.map_data.shape
            x_min = int((xlim[0] + 1) / 2 * width)
            x_max = int((xlim[1] + 1) / 2 * width)
            y_min = int((ylim[0] + 1) / 2 * height)
            y_max = int((ylim[1] + 1) / 2 * height)
            
            x_min, x_max = max(0, x_min), min(width, x_max)
            y_min, y_max = max(0, y_min), min(height, y_max)
            
            visible_data = self.map_data[y_min:y_max, x_min:x_max]
            
            if visible_data.size > 0:
                self.pcolormesh.set_clim(visible_data.min(), visible_data.max())
                self.colorbar.update_normal(self.pcolormesh)
                self.canvas.draw_idle()

    def save_peak_ids(self):
        if self.peak_ids is not None:
            save_file = filedialog.asksaveasfilename(title="Save Peak IDs", defaultextension=".csv", 
                                                    filetypes=[("CSV files", "*.csv")])
            if save_file:
                self.peak_ids.to_csv(save_file, index=False)
                messagebox.showinfo("Info", f"Peak IDs saved to {save_file}")
        else:
            messagebox.showwarning("Warning", "No peak ID data to save.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PeakIDEditor(root)
    root.mainloop()
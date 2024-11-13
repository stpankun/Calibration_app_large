import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.colors import Normalize
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os

class PeakPositionAdjuster:
    def __init__(self, master):
        self.master = master
        self.master.title("Peak Position Adjuster")
        
        # Initialize data containers
        self.data = None
        self.peak_positions = None
        self.texts = []
        self.markers = []
        self.dragging = None
        self.current_scale = 1.0
        self.initial_plot = True
        self.image_width = 1000
        self.image_height = 1000
        
        # Create menu bar
        self.create_menu()
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        
        # Create toolbar frame and add zoom instructions
        toolbar_frame = ttk.Frame(self.master)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        zoom_label = ttk.Label(toolbar_frame, text="Use the zoom tool to zoom in/out. Right-click to reset zoom.")
        zoom_label.pack(side=tk.RIGHT, padx=5)
        
        # Pack canvas
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Create control panel
        control_panel = ttk.Frame(self.master)
        control_panel.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.cursor_label = ttk.Label(control_panel, text="Cursor Position: (0.0, 0.0)")
        self.cursor_label.pack(side=tk.LEFT, padx=5)
        
        self.toggle_text_btn = ttk.Button(control_panel, text="Toggle Text (T)", command=self.toggle_text)
        self.toggle_text_btn.pack(side=tk.LEFT, padx=5)
        
        self.update_colorbar_btn = ttk.Button(control_panel, text="Update Colorbar (U)", command=self.update_colorbar)
        self.update_colorbar_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(control_panel, text="Save", command=self.save_positions)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Initialize plot elements
        self.colorbar = None
        self.scatter = None
        self.pcolormesh = None
        self.text_visible = True
        
        # Connect events
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('key_press_event', self.on_key_press)

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        # Create File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Map Data...", command=self.load_map_data)
        file_menu.add_command(label="Open Peak Data...", command=self.load_peak_data)
        file_menu.add_separator()
        file_menu.add_command(label="Save Peak Positions...", command=self.save_positions)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)

    def load_map_data(self):
        file_path = filedialog.askopenfilename(
            title="Open Map Data",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")],
            initialdir=os.getcwd()
        )
        
        if file_path:
            try:
                self.data = self.load_dat_image(file_path)
                self.initial_plot = True
                self.plot_data()
                self.master.title(f"Peak Position Adjuster - {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load map data: {str(e)}")

    def load_peak_data(self):
        file_path = filedialog.askopenfilename(
            title="Open Peak Data",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=os.getcwd()
        )
        
        if file_path:
            try:
                self.peak_positions = pd.read_csv(file_path)
                self.plot_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load peak data: {str(e)}")
        
    def load_dat_image(self, dat_path):
        try:
            data = np.fromfile(dat_path, sep="\n", dtype=np.uint8)
            if data.size != self.image_width * self.image_height:
                raise ValueError(f"Data size {data.size} does not match expected size {self.image_width * self.image_height}")
            return data.reshape((self.image_height, self.image_width)).T
        except Exception as e:
            raise Exception(f"Error loading DAT file: {str(e)}")
    
    def plot_data(self):
        # Store current view limits if they exist
        if not self.initial_plot:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
        
        # Clear current plot and texts
        self.ax.clear()
        self.texts = []
        
        # Plot image data
        if self.data is not None:
            height, width = self.data.shape
            x = np.linspace(-1, 1, width)
            y = np.linspace(-1, 1, height)
            X, Y = np.meshgrid(x, y)
            self.pcolormesh = self.ax.pcolormesh(X, Y, self.data, cmap='jet', shading='auto')
            
            if self.colorbar is None:
                self.colorbar = self.fig.colorbar(self.pcolormesh)
        
        # Plot peak positions
        if self.peak_positions is not None:
            for _, row in self.peak_positions.iterrows():
                color = 'yellow' if row['IDx'] % 5 == 0 or row['IDy'] % 5 == 0 else 'red'
                self.ax.plot(row['Posix'], row['Posiy'], 'o', color=color, markersize=5)
                text = self.ax.text(row['Posix'], row['Posiy'], 
                                  f"{int(row['IDx'])},{int(row['IDy'])}",
                                  color='white', fontsize=8, ha='left', va='bottom',
                                  visible=self.text_visible)
                self.texts.append(text)
        
        # Set initial view limits or restore previous view
        if self.initial_plot:
            self.ax.set_xlim(-1, 1)
            self.ax.set_ylim(-1, 1)
            self.initial_plot = False
        else:
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
        
        self.ax.set_aspect('equal')
        self.canvas.draw()
    
    def on_press(self, event):
        if event.inaxes and event.button == 1:  # Left click
            self.dragging = self.find_nearest_peak(event.xdata, event.ydata)
    
    def on_motion(self, event):
        # Update cursor position
        if event.inaxes:
            self.cursor_label['text'] = f"Cursor Position: ({event.xdata:.4f}, {event.ydata:.4f})"
        
        # Handle dragging
        if self.dragging is not None and event.inaxes:
            idx = self.dragging
            self.peak_positions.at[idx, 'Posix'] = event.xdata
            self.peak_positions.at[idx, 'Posiy'] = event.ydata
            self.plot_data()
    
    def on_release(self, event):
        self.dragging = None
    
    def on_key_press(self, event):
        if event.key == 't':
            self.toggle_text()
        elif event.key == 'u':
            self.update_colorbar()
    
    def find_nearest_peak(self, x, y):
        if self.peak_positions is None:
            return None
        
        distances = np.sqrt((self.peak_positions['Posix'] - x)**2 + 
                          (self.peak_positions['Posiy'] - y)**2)
        nearest_idx = distances.idxmin()
        if distances[nearest_idx] < 0.05:  # Adjust threshold as needed
            return nearest_idx
        return None
    
    def toggle_text(self):
        self.text_visible = not self.text_visible
        for text in self.texts:
            text.set_visible(self.text_visible)
        self.canvas.draw()
    
    def update_colorbar(self):
        if self.data is not None and self.pcolormesh is not None:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            # Convert normalized coordinates to array indices
            height, width = self.data.shape
            x_min = int((xlim[0] + 1) / 2 * width)
            x_max = int((xlim[1] + 1) / 2 * width)
            y_min = int((ylim[0] + 1) / 2 * height)
            y_max = int((ylim[1] + 1) / 2 * height)
            
            # Ensure indices are within bounds
            x_min = max(0, min(x_min, width-1))
            x_max = max(0, min(x_max, width))
            y_min = max(0, min(y_min, height-1))
            y_max = max(0, min(y_max, height))
            
            visible_data = self.data[y_min:y_max, x_min:x_max]
            
            if visible_data.size > 0:
                self.pcolormesh.set_clim(visible_data.min(), visible_data.max())
                self.colorbar.update_normal(self.pcolormesh)
                self.canvas.draw()
    
    def save_positions(self):
        if self.peak_positions is not None:
            file_path = filedialog.asksaveasfilename(
                title="Save Peak Positions",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=os.getcwd()
            )
            if file_path:
                try:
                    self.peak_positions.to_csv(file_path, index=False)
                    messagebox.showinfo("Success", f"Peak positions saved to {file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save peak positions: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No peak data to save")

def main():
    root = tk.Tk()
    app = PeakPositionAdjuster(root)
    root.mainloop()

if __name__ == "__main__":
    main()
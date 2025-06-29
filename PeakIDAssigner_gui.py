import numpy as np
import math
import matplotlib.pyplot as plt
import pandas as pd
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as patches

N_pix = 45

def load_data(input_file_path):
    """NPY形式のマップデータをロードして転置する"""
    return np.load(input_file_path).T

def load_peaks(csv_file_path):
    """CSV形式のピークデータをロードする。PosixとPosiyの列のみを読み込む。"""
    return np.loadtxt(csv_file_path, delimiter=',', skiprows=1)

# --- ParameterTuner クラス (Toplevelを使用するよう修正) ---
class ParameterTuner:
    def __init__(self, parent, map_data, peaks):
        # Toplevelを使い、親ウィンドウ(parent)からサブウィンドウを作成
        self.window = tk.Toplevel(parent)
        self.window.title("Parameter Tuner")
        self.window.geometry("1100x700")

        # ウィンドウが閉じられるまで、他のウィンドウの操作をできなくする
        self.window.grab_set()

        self.map_data = map_data
        self.peaks = peaks
        self.selected_peak_for_tuning = None
        self.viz_elements = []
        self.final_params = None

        self.max_dist_var = tk.DoubleVar(value=0.003)
        self.search_range_var = tk.DoubleVar(value=0.01)
        self.offset_var = tk.DoubleVar(value=0.0001)
        self.direction_var = tk.StringVar(value='right')

        paned_window = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        plot_frame = ttk.Frame(paned_window)
        paned_window.add(plot_frame, weight=4)
        control_frame = ttk.Frame(paned_window)
        paned_window.add(control_frame, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.ax.set_title('Click a peak to visualize search area')
        self.ax.imshow(self.map_data, cmap='viridis', origin='lower', extent=[-1, 1, -1, 1])
        self.ax.scatter(self.peaks[:, 0], self.peaks[:, 1], c='white', s=5, alpha=0.7)
        self.canvas.mpl_connect('button_press_event', self.on_click)

        self.create_controls(control_frame)
        
        # 変数の変化を監視する設定
        self.setup_variable_traces()

    def create_controls(self, parent):
        parent.configure(padding=(10, 10))
        ttk.Label(parent, text="max_dist:").pack(pady=(5,0), anchor=tk.W)
        ttk.Scale(parent, from_=0.0001, to=0.5, orient=tk.HORIZONTAL, variable=self.max_dist_var).pack(fill=tk.X, padx=5, pady=(0, 10))
        ttk.Label(parent, text="search_range:").pack(pady=(5,0), anchor=tk.W)
        ttk.Scale(parent, from_=0.0001, to=0.05, orient=tk.HORIZONTAL, variable=self.search_range_var).pack(fill=tk.X, padx=5, pady=(0, 10))
        ttk.Label(parent, text="offset:").pack(pady=(5,0), anchor=tk.W)
        ttk.Scale(parent, from_=0.00001, to=0.01, orient=tk.HORIZONTAL, variable=self.offset_var).pack(fill=tk.X, padx=5, pady=(0, 10))
        direction_frame = ttk.LabelFrame(parent, text="Direction")
        direction_frame.pack(fill=tk.X, pady=(15, 0), padx=5)
        directions = ['left', 'right', 'up', 'down']
        for d in directions:
            ttk.Radiobutton(direction_frame, text=d.capitalize(), variable=self.direction_var, value=d).pack(anchor=tk.W, padx=15, pady=2)
        button_frame = ttk.Frame(parent)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.RIGHT, expand=True, padx=5)

    def setup_variable_traces(self):
        self.max_dist_var.trace_add('write', self.update_visualization)
        self.search_range_var.trace_add('write', self.update_visualization)
        self.offset_var.trace_add('write', self.update_visualization)
        self.direction_var.trace_add('write', self.update_visualization)

    def on_click(self, event):
        if event.inaxes is not None and self.toolbar.mode == '':
            distances = np.sqrt((self.peaks[:, 0] - event.xdata)**2 + (self.peaks[:, 1] - event.ydata)**2)
            self.selected_peak_for_tuning = self.peaks[np.argmin(distances)]
            self.update_visualization()

    def update_visualization(self, *args):
        """パラメータの変更に応じて探索範囲の視覚化を更新する"""
        if self.selected_peak_for_tuning is None: return
        for element in self.viz_elements: element.remove()
        self.viz_elements.clear()

        x, y = self.selected_peak_for_tuning
        max_dist, search_range, offset, direction = self.max_dist_var.get(), self.search_range_var.get(), self.offset_var.get(), self.direction_var.get()

        highlight = patches.Circle((x, y), radius=max_dist/3, color='yellow', fill=False, lw=2)
        self.ax.add_patch(highlight)
        self.viz_elements.append(highlight)

        circle = patches.Circle((x, y), radius=max_dist, color='r', fill=False, linestyle='--', label='max_dist')
        self.ax.add_patch(circle)
        self.viz_elements.append(circle)

        # ★★★ ここが修正箇所です ★★★
        # 誤ってmax_distが使われていた部分を、正しくoffset変数に修正します。
        offset_patch = patches.Rectangle((x - offset, y - offset), 2 * offset, 2 * offset, color='yellow', alpha=0.6, label='offset')
        self.ax.add_patch(offset_patch)
        self.viz_elements.append(offset_patch)

        if direction in ['left', 'right']:
            rect = patches.Rectangle((-1, y - search_range), 2, 2 * search_range, color='cyan', alpha=0.3)
        else:
            rect = patches.Rectangle((x - search_range, -1), 2 * search_range, 2, color='lightgreen', alpha=0.3)
        self.ax.add_patch(rect)
        self.viz_elements.append(rect)
        
        self.canvas.draw_idle()

    def on_ok(self):
        self.final_params = {'max_dist': self.max_dist_var.get(), 'search_range': self.search_range_var.get(), 'offset': self.offset_var.get()}
        self.window.destroy()

    def on_cancel(self):
        self.final_params = None
        self.window.destroy()

    def get_parameters(self):
        # このウィンドウが閉じられるまで待つ
        self.window.wait_window()
        return self.final_params

# --- PeakSelector クラス (Toplevelを使用するよう修正) ---
class PeakSelector:
    def __init__(self, parent, map_data, peaks):
        self.window = tk.Toplevel(parent)
        self.window.title("Select a Peak")
        self.window.grab_set()
        
        self.map_data = map_data
        self.peaks = peaks
        self.selected_peak = None
        
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        toolbar_frame = ttk.Frame(self.window)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        zoom_label = ttk.Label(toolbar_frame, text="Use the zoom tool to zoom in/out.")
        zoom_label.pack(side=tk.RIGHT, padx=5)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.ax.imshow(self.map_data, cmap='viridis', origin='lower', extent=[-1, 1, -1, 1])
        self.scatter = self.ax.scatter(self.peaks[:, 0], self.peaks[:, 1], c='r', s=10)
        self.ax.set_title('Select a peak to start ID assignment')
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        if event.inaxes is not None and event.button == 1 and self.toolbar.mode == '':
            distances = np.sqrt((self.peaks[:, 0] - event.xdata)**2 + (self.peaks[:, 1] - event.ydata)**2)
            self.selected_peak = self.peaks[np.argmin(distances)]
            self.window.destroy()

    def get_selected_peak(self):
        self.window.wait_window()
        return self.selected_peak

# --- assign_id_in_direction, assign_idsなどのコアロジックは変更なし ---
def assign_id_in_direction(peaks, start_id, start_peak, direction, params, max_count=50):
    max_dist, search_range, offset = params['max_dist'], params['search_range'], params['offset']
    current_id, current_peak, assigned_peaks = list(start_id), start_peak, []
    while True:
        x, y = current_peak
        id_x, id_y = current_id
        if direction == 'left': next_peaks = [p for p in peaks if p[0] < x - offset and abs(p[1] - y) < search_range]
        elif direction == 'right': next_peaks = [p for p in peaks if p[0] > x + offset and abs(p[1] - y) < search_range]
        elif direction == 'up': next_peaks = [p for p in peaks if p[1] < y - offset and abs(p[0] - x) < search_range]
        else: next_peaks = [p for p in peaks if p[1] > y + offset and abs(p[0] - x) < search_range]
        if not next_peaks: break
        next_peaks = sorted(next_peaks, key=lambda p: math.sqrt((p[0] - x)**2 + (p[1] - y)**2))
        next_peaks = next_peaks[:max_count]
        next_peak = next_peaks[0]
        if np.sqrt((next_peak[0] - x)**2 + (next_peak[1] - y)**2) > max_dist: break
        if direction == 'left': new_id = [id_x - 1, id_y]
        elif direction == 'right': new_id = [id_x + 1, id_y]
        elif direction == 'up': new_id = [id_x, id_y + 1]
        else: new_id = [id_x, id_y - 1]
        if not (0 <= new_id[0] < N_pix and 0 <= new_id[1] < N_pix): break
        assigned_peaks.append((new_id, next_peak))
        current_id, current_peak = new_id, next_peak
        peaks = [p for p in peaks if not np.array_equal(p, next_peak)]
    return assigned_peaks, peaks

def assign_ids(peaks, start_peak, start_id, params):
    peak_ids = np.full((N_pix, N_pix, 2), np.nan)
    peak_ids[start_id[1]][start_id[0]] = start_peak
    remaining_peaks = [p for p in peaks if not np.array_equal(p, start_peak)]
    for direction in ['left', 'right', 'up', 'down']:
        assigned, remaining_peaks = assign_id_in_direction(remaining_peaks, start_id, start_peak, direction, params)
        for (id_x, id_y), peak in assigned: peak_ids[id_y][id_x] = peak
    for direction in ['up', 'down']:
        for i in range(N_pix):
            for j in range(N_pix):
                if not np.isnan(peak_ids[j][i][0]):
                    assigned, remaining_peaks = assign_id_in_direction(remaining_peaks, [i, j], peak_ids[j][i], direction, params)
                    for (id_x, id_y), peak in assigned: peak_ids[id_y][id_x] = peak
    for direction in ['left', 'right']:
        for i in range(N_pix // 2 - 1):
            for j in range(N_pix):
                current_peak = None
                if direction == 'left' and j != N_pix // 2 and np.isnan(peak_ids[j][N_pix // 2 - (i + 1)][0]): current_peak = peak_ids[j][N_pix // 2 - i]
                elif direction == 'right' and j != N_pix // 2 and np.isnan(peak_ids[j][N_pix // 2 + (i + 1)][0]): current_peak = peak_ids[j][N_pix // 2 + i]
                if current_peak is not None and not np.isnan(current_peak[0]):
                    assigned, remaining_peaks = assign_id_in_direction(remaining_peaks, [N_pix // 2 - i if direction == 'left' else N_pix // 2 + i, j], current_peak, direction, params)
                    for (id_x, id_y), peak in assigned: peak_ids[id_y][id_x] = peak
    return peak_ids

def plot_assigned_peaks(peak_ids, map_data):
    plt.figure(figsize=(12, 12))
    plt.imshow(map_data, cmap='viridis', origin='lower', extent=[-1, 1, -1, 1])
    for id_x in range(N_pix):
        for id_y in range(N_pix):
            x, y = peak_ids[id_y][id_x]
            if not np.isnan(x):
                plt.plot(x, y, 'r.', markersize=10)
                plt.text(x, y, f'({id_x},{id_y})', color='white', fontsize=8)
    plt.title('Assigned Peak IDs')
    plt.colorbar(label='Intensity')
    plt.show()

def save_assigned_peaks(peak_ids, output_file_path):
    with open(output_file_path, "w") as f:
        f.write("IDx,IDy,Posix,Posiy,accuracy\n")
        for id_x in range(N_pix):
            for id_y in range(N_pix):
                x, y = peak_ids[id_y][id_x]
                f.write(f'{id_x},{id_y},{x if not np.isnan(x) else "nan"},{y if not np.isnan(y) else "nan"},' + ('\n' if np.isnan(x) else ',\n'))

# --- メイン関数 (単一のTkルートを生成し、各コンポーネントに渡すよう修正) ---
def main():
    # アプリケーション全体で共有する唯一のメインウィンドウを作成
    app_root = tk.Tk()

    # ファイル選択
    map_file_path = filedialog.askopenfilename(parent=app_root, title="Select input map NPY file", filetypes=[("NumPy files", "*.npy")])
    if not map_file_path: return
    peaks_file_path = filedialog.askopenfilename(parent=app_root, title="Select input peaks CSV file", filetypes=[("CSV files", "*.csv")])
    if not peaks_file_path: return

    map_data = load_data(map_file_path)
    peaks = load_peaks(peaks_file_path)

    # パラメータ調整GUI
    tuner = ParameterTuner(app_root, map_data, peaks)
    params = tuner.get_parameters()
    if params is None: return

    # 開始点のピークを選択
    selector = PeakSelector(app_root, map_data, peaks)
    selected_peak = selector.get_selected_peak()
    if selected_peak is None: return

    # 開始点のIDを入力
    id_x = simpledialog.askinteger("Input", "Enter the X ID for the selected peak:", parent=app_root, minvalue=0, maxvalue=N_pix-1)
    if id_x is None: return
    id_y = simpledialog.askinteger("Input", "Enter the Y ID for the selected peak:", parent=app_root, minvalue=0, maxvalue=N_pix-1)
    if id_y is None: return

    # ID割り当て実行
    peak_ids = assign_ids(peaks, selected_peak, [id_x, id_y], params)

    # 結果のプロットと保存
    plot_assigned_peaks(peak_ids, map_data)
    output_file_path = filedialog.asksaveasfilename(parent=app_root, title="Save assigned peaks as", defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if output_file_path:
        save_assigned_peaks(peak_ids, output_file_path)
        print(f"Assigned IDs saved to {output_file_path}")

    # 最後にメインウィンドウを破棄
    app_root.destroy()

if __name__ == "__main__":
    main()
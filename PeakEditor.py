import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QPointF
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt

class PeakEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Peak Editor")
        self.setGeometry(100, 100, 800, 600)

        self.map_data = None
        self.peaks = None
        self.zoom_factor = 1.0
        self.offset = QPointF(0, 0)
        self.pixmap = None

        self.setup_ui()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()

        self.image_label = QLabel()
        layout.addWidget(self.image_label)

        self.save_button = QPushButton("Save Peaks")
        self.save_button.clicked.connect(self.save_peaks)
        layout.addWidget(self.save_button)

        self.central_widget.setLayout(layout)

        self.load_files()

    def load_files(self):
        map_file, _ = QFileDialog.getOpenFileName(self, "Select Map File", "", "NumPy files (*.npy)")
        if map_file:
            self.map_data = np.load(map_file)
        else:
            sys.exit("No map file selected")

        peaks_file, _ = QFileDialog.getOpenFileName(self, "Select Peaks File", "", "CSV files (*.csv)")
        if peaks_file:
            self.peaks = pd.read_csv(peaks_file).values
        else:
            sys.exit("No peaks file selected")

        self.update_display()

    def update_display(self):
        if self.map_data is None:
            return

        # Apply jet colormap
        cmap = plt.get_cmap('jet')
        normalized_data = (self.map_data - self.map_data.min()) / (self.map_data.max() - self.map_data.min())
        colored_data = (cmap(normalized_data) * 255).astype(np.uint8)

        # Create RGB image
        image = Image.fromarray(colored_data)

        # Convert to QImage and QPixmap
        qimage = QImage(image.tobytes(), image.width, image.height, QImage.Format_RGBA8888)
        self.pixmap = QPixmap.fromImage(qimage)

        self.draw_peaks()

    def draw_peaks(self):
        if self.pixmap is None:
            return

        # Apply zoom and offset
        scaled_width = int(self.pixmap.width() * self.zoom_factor)
        scaled_height = int(self.pixmap.height() * self.zoom_factor)
        
        if scaled_width == 0 or scaled_height == 0:
            return  # Avoid invalid scaling

        scaled_pixmap = self.pixmap.scaled(scaled_width, scaled_height, 
                                           Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Create a new pixmap to draw on
        result_pixmap = QPixmap(self.image_label.size())
        result_pixmap.fill(Qt.black)  # Fill with black background

        # Calculate the maximum allowed offset
        max_offset_x = max(0, scaled_width - result_pixmap.width())
        max_offset_y = max(0, scaled_height - result_pixmap.height())
        
        # Limit the offset
        self.offset.setX(max(min(self.offset.x(), max_offset_x), 0))
        self.offset.setY(max(min(self.offset.y(), max_offset_y), 0))

        # Draw the scaled image on the new pixmap
        painter = QPainter(result_pixmap)
        painter.drawPixmap(-self.offset.toPoint(), scaled_pixmap)

        # Draw peaks
        if self.peaks is not None:
            painter.setPen(QPen(QColor(255, 0, 0), 2))  # Red color, size 2
            for peak in self.peaks:
                x = int((peak[0] + 1) / 2 * scaled_width - self.offset.x())
                y = int((1 - (peak[1] + 1) / 2) * scaled_height - self.offset.y())
                painter.drawEllipse(x-2, y-2, 4, 4)  # Draw a small red dot

        painter.end()

        self.image_label.setPixmap(result_pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
            self.add_peak(event.pos())
        elif event.button() == Qt.RightButton and event.modifiers() == Qt.ControlModifier:
            self.remove_peak(event.pos())

    def add_peak(self, pos):
        if self.pixmap is None:
            return

        scaled_width = self.pixmap.width() * self.zoom_factor
        scaled_height = self.pixmap.height() * self.zoom_factor

        # Convert screen coordinates to normalized coordinates
        x = (pos.x() + self.offset.x()) / scaled_width
        y = (pos.y() + self.offset.y()) / scaled_height

        # Ensure x and y are within the range [0, 1]
        x = max(0, min(1, x))
        y = max(0, min(1, y))

        # Convert to the range [-1, 1]
        x = x * 2 - 1
        y = -(y * 2 - 1)  # Flip y-axis

        new_peak = np.array([[x, y]])
        if self.peaks is None:
            self.peaks = new_peak
        else:
            self.peaks = np.vstack((self.peaks, new_peak))
        self.draw_peaks()

    def remove_peak(self, pos):
        if self.peaks is None or len(self.peaks) == 0 or self.pixmap is None:
            return

        scaled_width = self.pixmap.width() * self.zoom_factor
        scaled_height = self.pixmap.height() * self.zoom_factor

        # Convert screen coordinates to normalized coordinates
        x = (pos.x() + self.offset.x()) / scaled_width
        y = (pos.y() + self.offset.y()) / scaled_height

        # Ensure x and y are within the range [0, 1]
        x = max(0, min(1, x))
        y = max(0, min(1, y))

        # Convert to the range [-1, 1]
        x = x * 2 - 1
        y = -(y * 2 - 1)  # Flip y-axis

        distances = np.sqrt(np.sum((self.peaks - [x, y])**2, axis=1))
        if distances.min() < 0.1:  # Threshold in normalized coordinates
            self.peaks = np.delete(self.peaks, distances.argmin(), axis=0)
            self.draw_peaks()

    def wheelEvent(self, event):
        # Get the position of the mouse cursor
        mouse_pos = event.pos() + self.offset

        # Calculate the offset to keep the point under the cursor in the same place
        w_factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
        dx = mouse_pos.x() * (1 - w_factor)
        dy = mouse_pos.y() * (1 - w_factor)

        # Update zoom factor and offset
        self.zoom_factor *= w_factor
        self.zoom_factor = max(0.1, min(10, self.zoom_factor))  # Limit zoom range
        self.offset += QPointF(dx, dy)

        self.draw_peaks()

    def keyPressEvent(self, event):
        # Pan image
        step = 10 / self.zoom_factor  # Adjust step size based on zoom level
        if event.key() == Qt.Key_Left:
            self.offset.setX(self.offset.x() - step)
        elif event.key() == Qt.Key_Right:
            self.offset.setX(self.offset.x() + step)
        elif event.key() == Qt.Key_Up:
            self.offset.setY(self.offset.y() - step)
        elif event.key() == Qt.Key_Down:
            self.offset.setY(self.offset.y() + step)
        elif event.key() == Qt.Key_Z:
            self.update_colormap()
        self.draw_peaks()

    def update_colormap(self):
        if self.pixmap is None or self.map_data is None:
            return

        # Get the visible portion of the image
        visible_rect = self.image_label.rect()
        visible_rect.moveTopLeft(self.pixmap.rect().topLeft() - self.offset.toPoint())
        visible_rect = visible_rect.intersected(self.pixmap.rect())

        # Convert visible rectangle to data coordinates
        x1 = max(0, visible_rect.left() / self.zoom_factor / self.pixmap.width())
        y1 = max(0, visible_rect.top() / self.zoom_factor / self.pixmap.height())
        x2 = min(1, visible_rect.right() / self.zoom_factor / self.pixmap.width())
        y2 = min(1, visible_rect.bottom() / self.zoom_factor / self.pixmap.height())

        # Get data in visible region
        h, w = self.map_data.shape
        i1, j1 = int(y1 * h), int(x1 * w)
        i2, j2 = int(y2 * h), int(x2 * w)
        visible_data = self.map_data[i1:i2, j1:j2]

        # Update colormap based on visible data
        vmin, vmax = visible_data.min(), visible_data.max()
        if vmin != vmax:
            cmap = plt.get_cmap('jet')
            normalized_data = (self.map_data - vmin) / (vmax - vmin)
            normalized_data = np.clip(normalized_data, 0, 1)
            colored_data = (cmap(normalized_data) * 255).astype(np.uint8)
            image = Image.fromarray(colored_data)
            qimage = QImage(image.tobytes(), image.width, image.height, QImage.Format_RGBA8888)
            self.pixmap = QPixmap.fromImage(qimage)
            self.draw_peaks()

    def save_peaks(self):
        if self.peaks is None or len(self.peaks) == 0:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Peaks", "", "CSV files (*.csv)")
        if file_path:
            pd.DataFrame(self.peaks, columns=['x', 'y']).to_csv(file_path, index=False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PeakEditorApp()
    window.show()
    sys.exit(app.exec_())
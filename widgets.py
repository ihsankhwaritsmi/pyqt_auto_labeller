import os
import sys
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QPushButton,
    QStyle,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QImageReader, QIcon

# Define a custom widget for list items
class ImageListItemWidget(QWidget):
    visibility_changed = pyqtSignal(str, bool) # Signal to emit image path and new visibility state

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.is_visible = True # Default visibility

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0) # Remove margins for tight packing
        self.layout.setSpacing(5) # Spacing between elements

        # Thumbnail Label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(30, 30) # Further reduced size for thinner list items
        self.thumbnail_label.setScaledContents(True)
        self.load_thumbnail()
        self.layout.addWidget(self.thumbnail_label)

        # Image Name Label
        self.name_label = QLabel(os.path.basename(image_path))
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred) # Allow name to expand
        self.layout.addWidget(self.name_label)

        # Labelled Status Label
        self.status_label = QLabel("") # Initialize empty
        self.status_label.setStyleSheet("font-weight: bold;") # Base style
        self.status_label.setFixedSize(80, 20) # Increased size for consistency
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(self.status_label)

        self.setLayout(self.layout)

    def set_labelled_status(self, status: str):
        if status == "labelled":
            self.status_label.setText("Labelled")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;") # Green
        elif status == "auto-labelled":
            self.status_label.setText("Auto-Labelled")
            self.status_label.setStyleSheet("color: #FFC107; font-weight: bold;") # Amber/Orange
        else: # "unlabelled"
            self.status_label.setText("") # Clear text if unlabelled
            self.status_label.setStyleSheet("") # Reset style

    def load_thumbnail(self):
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation) # Use further reduced size
            self.thumbnail_label.setPixmap(scaled_pixmap)
        else:
            self.thumbnail_label.setText("No Thumb") # Placeholder if loading fails

# --- End of ImageListItemWidget ---

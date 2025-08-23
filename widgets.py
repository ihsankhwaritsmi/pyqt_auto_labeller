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
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;") # Green color for "Labelled"
        self.status_label.setFixedSize(60, 20) # Fixed size for consistency
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(self.status_label)

        # Visibility Button
        self.visibility_button = QPushButton()
        self.visibility_button.setFixedSize(20, 20) # Further reduced size for thinner list items
        self.visibility_button.setIconSize(QSize(15, 15)) # Further reduced icon size
        self.update_visibility_icon()
        self.visibility_button.clicked.connect(self.toggle_visibility)
        self.layout.addWidget(self.visibility_button)

        self.setLayout(self.layout)

    def set_labelled_status(self, is_labelled: bool):
        if is_labelled:
            self.status_label.setText("Labelled")
        else:
            self.status_label.setText("") # Clear text if not labelled

    def load_thumbnail(self):
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation) # Use further reduced size
            self.thumbnail_label.setPixmap(scaled_pixmap)
        else:
            self.thumbnail_label.setText("No Thumb") # Placeholder if loading fails

    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.update_visibility_icon()
        # Signal that visibility has changed (to be handled by MainWindow)
        self.visibility_changed.emit(self.image_path, self.is_visible)

    def update_visibility_icon(self):
        if self.is_visible:
            # Use a standard icon to indicate visibility (e.g., an open eye)
            # Using SP_DialogYesButton as a placeholder for an "open eye" icon.
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton)
            self.visibility_button.setIcon(icon)
        else:
            # Use a standard icon to indicate hidden state (e.g., a closed eye)
            # Using SP_DialogNoButton as a placeholder for a "closed eye" icon.
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogNoButton)
            self.visibility_button.setIcon(icon)

# --- End of ImageListItemWidget ---

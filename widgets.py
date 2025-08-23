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

        # Visibility Button
        self.visibility_button = QPushButton()
        self.visibility_button.setFixedSize(20, 20) # Further reduced size for thinner list items
        self.visibility_button.setIconSize(QSize(15, 15)) # Further reduced icon size
        self.update_visibility_icon()
        self.visibility_button.clicked.connect(self.toggle_visibility)
        self.layout.addWidget(self.visibility_button)

        self.setLayout(self.layout)

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
            # Use a standard eye icon (or a placeholder if not available)
            # For simplicity, using a generic icon. A real eye icon would be better.
            # Using SP_ComputerIcon as a placeholder for an eye icon.
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            self.visibility_button.setIcon(icon)
        else:
            # Use a dimmed eye icon or a different icon to indicate hidden
            # Using SP_ComputerIcon as a placeholder for a dimmed eye icon.
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            self.visibility_button.setIcon(icon)

# --- End of ImageListItemWidget ---

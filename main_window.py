import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout, # Import QHBoxLayout
    QLabel,
    QStatusBar,
    QToolBar,
    QDockWidget,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QPushButton, # Import QPushButton
    QStyle, # Import QStyle for icons
    QSizePolicy # Import QSizePolicy
)
from PyQt6.QtCore import Qt, QDir, QSize, pyqtSignal # Import QSize and pyqtSignal
from PyQt6.QtGui import QPixmap, QImageReader, QIcon # Import QIcon

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
        self.thumbnail_label.setFixedSize(50, 50) # Fixed size for thumbnail
        self.thumbnail_label.setScaledContents(True)
        self.load_thumbnail()
        self.layout.addWidget(self.thumbnail_label)

        # Image Name Label
        self.name_label = QLabel(os.path.basename(image_path))
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred) # Allow name to expand
        self.layout.addWidget(self.name_label)

        # Visibility Button
        self.visibility_button = QPushButton()
        self.visibility_button.setFixedSize(30, 30)
        self.visibility_button.setIconSize(QSize(20, 20))
        self.update_visibility_icon()
        self.visibility_button.clicked.connect(self.toggle_visibility)
        self.layout.addWidget(self.visibility_button)

        self.setLayout(self.layout)

    def load_thumbnail(self):
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 App Layout")
        self.setGeometry(100, 100, 1000, 700) # x, y, width, height
        self.is_dark_theme = True # Initialize theme state to dark
        self.dataset_folder = None # Store the selected dataset folder path
        self.image_files = [] # Store list of image file paths
        self.image_visibility = {} # Dictionary to store visibility state of images
        self.setup_ui()
        self.apply_theme() # Apply initial theme

    def apply_theme(self):
        # Apply dark theme as per user request
        # self.setStyleSheet(DARK_THEME) # Removed redundant call
        # Add specific styles for the list widget to match layer panel appearance
        self.setStyleSheet("""
            QMainWindow { background-color: #2E2E2E; } /* Dark background for the main window */
            QDockWidget { titlebar-close-icon: none; titlebar-normal-icon: none; } /* Hide dock widget icons */
            QDockWidget::title {
                text-align: left; /* Align title to the left */
                padding-left: 10px;
                background-color: #3A3A3A; /* Darker title bar */
                color: white;
            }
            QListWidget {
                background-color: #3A3A3A; /* Dark background for the list */
                border: 1px solid #4A4A4A; /* Subtle border */
                color: white; /* White text */
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px; /* Padding around each item */
                border-bottom: 1px solid #4A4A4A; /* Separator line */
            }
            QListWidget::item:selected {
                background-color: #4A90E2; /* Blue selection color */
                color: white; /* White text on selection */
            }
            QLabel { color: white; } /* Ensure all labels are white */
            QPushButton {
                background-color: #4A4A4A; /* Button background */
                border: 1px solid #5A5A5A; /* Button border */
                color: white; /* Button text color */
                padding: 3px;
            }
            QPushButton:hover { background-color: #5A5A5A; } /* Hover effect */
        """)


    def load_dataset(self):
        # Open a directory dialog to select the dataset folder
        folder_path = QFileDialog.getExistingDirectory(self, "Select Dataset Folder")
        if folder_path:
            self.dataset_folder = folder_path
            self.populate_image_list()
            self.statusBar.showMessage(f"Dataset loaded: {os.path.basename(folder_path)}")
        else:
            self.statusBar.showMessage("Dataset loading cancelled")

    def populate_image_list(self):
        if not self.dataset_folder:
            return

        self.image_files = []
        self.image_visibility = {} # Reset visibility states
        self.left_panel_list.clear() # Clear existing list items

        # Supported image extensions
        supported_extensions = QImageReader.supportedImageFormats()
        supported_extensions = [ext.data().decode('ascii') for ext in supported_extensions]

        # Iterate through files in the selected folder
        for filename in os.listdir(self.dataset_folder):
            file_path = os.path.join(self.dataset_folder, filename)
            if os.path.isfile(file_path):
                # Check if the file has a supported image extension
                file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
                if file_ext in supported_extensions:
                    self.image_files.append(file_path)
                    self.image_visibility[file_path] = True # Set default visibility to True

                    # Create a custom widget for the list item
                    list_item_widget = ImageListItemWidget(file_path)
                    list_item_widget.visibility_changed.connect(self.on_visibility_changed) # Connect signal

                    # Create a QListWidgetItem and set the custom widget
                    list_item = QListWidgetItem(self.left_panel_list)
                    list_item.setSizeHint(list_item_widget.sizeHint()) # Set size hint for the item
                    self.left_panel_list.setItemWidget(list_item, list_item_widget)

        if not self.image_files:
            self.statusBar.showMessage("No images found in the selected folder.")
        else:
            # Select the first image by default
            self.left_panel_list.setCurrentRow(0)
            self.display_image(self.image_files[0])


    def display_image(self, image_path):
        # Check visibility before displaying
        if image_path in self.image_visibility and not self.image_visibility[image_path]:
            self.canvas_label.setText(f"Image '{os.path.basename(image_path)}' is hidden")
            self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.canvas_label.setText(f"Failed to load image: {os.path.basename(image_path)}")
            self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return

        # Scale pixmap to fit the label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(self.canvas_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.canvas_label.setPixmap(scaled_pixmap)
        self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statusBar.showMessage(f"Displaying: {os.path.basename(image_path)}")


    def setup_ui(self):
        self.setup_toolbar()
        self.setup_left_panel()
        self.setup_right_panel()
        self.setup_canvas()
        self.setup_status_bar()

    def setup_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.load_dataset_action = self.toolbar.addAction("Load Dataset")
        self.load_dataset_action.triggered.connect(self.load_dataset)

        self.toolbar.addAction("File")
        self.toolbar.addAction("Edit")
        self.toolbar.addAction("View")

    def setup_canvas(self):
        self.canvas_widget = QWidget()
        self.canvas_label = QLabel("Canvas Area")
        self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas_layout = QVBoxLayout(self.canvas_widget)
        canvas_layout.addWidget(self.canvas_label)
        self.setCentralWidget(self.canvas_widget)

    def setup_left_panel(self):
        self.left_panel = QDockWidget("Layers") # Changed title to "Layers"
        self.left_panel.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        left_content_widget = QWidget()
        left_layout = QVBoxLayout(left_content_widget)
        
        self.left_panel_list = QListWidget()
        # Removed the direct stylesheet for QListWidget::item:selected as it will be handled by custom widget styling
        left_layout.addWidget(self.left_panel_list)
        
        # Removed the separator as it's not in the example layer panel
        # self.separator = QFrame()
        # self.separator.setFrameShape(QFrame.Shape.HLine)
        # self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        # left_layout.addWidget(self.separator)

        # Removed the "Label Management Section" as it's not part of the layer panel
        # self.label_management_widget = QWidget()
        # label_management_layout = QVBoxLayout(self.label_management_widget)
        # label_management_label = QLabel("Label Management Section")
        # label_management_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # label_management_layout.addWidget(label_management_label)
        # left_layout.addWidget(self.label_management_widget)
        
        # Adjusted stretch factors to give more space to the list widget
        left_layout.setStretchFactor(self.left_panel_list, 10) 

        self.left_panel.setWidget(left_content_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_panel)
        self.left_panel.setFixedWidth(250) # Adjusted width to better fit content

    def setup_right_panel(self):
        self.right_panel = QDockWidget("Properties") # Changed title to "Properties"
        self.right_panel.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        right_label = QLabel("Properties Panel Content")
        right_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(right_label)
        self.right_panel.setWidget(right_content)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_panel)
        self.right_panel.setFixedWidth(200)

    def setup_status_bar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def on_image_list_item_changed(self, current_item, previous_item):
        if current_item:
            # Get the custom widget associated with the selected item
            widget = self.left_panel_list.itemWidget(current_item)
            if widget and isinstance(widget, ImageListItemWidget):
                self.display_image(widget.image_path)

    def on_visibility_changed(self, image_path, is_visible):
        self.image_visibility[image_path] = is_visible
        # If the currently displayed image's visibility changes, update the canvas
        current_item = self.left_panel_list.currentItem()
        if current_item:
            widget = self.left_panel_list.itemWidget(current_item)
            if widget and widget.image_path == image_path:
                self.display_image(image_path)
        
        # Update the visibility icon on the item itself (handled within ImageListItemWidget)
        # This is already done by toggle_visibility, but good to be aware.

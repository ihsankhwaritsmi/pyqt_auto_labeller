import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStatusBar,
    QToolBar,
    QDockWidget,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QPushButton,
    QStyle,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QDir, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QImageReader, QIcon
from PyQt6.QtWidgets import QApplication # Import QApplication

# Import custom widget and styles
from widgets import ImageListItemWidget
from styles import DARK_THEME
from canvas_widget import ZoomPanLabel

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
        self.setStyleSheet(DARK_THEME)
        # Add specific styles for the list widget to match layer panel appearance
        # These are already included in DARK_THEME, so no need to repeat here.
        # self.setStyleSheet("""
        #     QMainWindow { background-color: #2E2E2E; } /* Dark background for the main window */
        #     QDockWidget { titlebar-close-icon: none; titlebar-normal-icon: none; } /* Hide dock widget icons */
        #     QDockWidget::title {
        #         text-align: left; /* Align title to the left */
        #         padding-left: 10px;
        #         background-color: #3A3A3A; /* Darker title bar */
        #         color: white;
        #     }
        #     QListWidget {
        #         background-color: #3A3A3A; /* Dark background for the list */
        #         border: 1px solid #4A4A4A; /* Subtle border */
        #         color: white; /* White text */
        #         padding: 5px;
        #     }
        #     QListWidget::item {
        #         padding: 5px; /* Padding around each item */
        #         border-bottom: 1px solid #4A4A4A; /* Separator line */
        #     }
        #     QListWidget::item:selected {
        #         background-color: #4A90E2; /* Blue selection color */
        #         color: white; /* White text on selection */
        #     }
        #     QLabel { color: white; } /* Ensure all labels are white */
        #     QPushButton {
        #         background-color: #4A4A4A; /* Button background */
        #         border: 1px solid #5A5A5A; /* Button border */
        #         color: white; /* Button text color */
        #         padding: 3px;
        #     }
        #     QPushButton:hover { background-color: #5A5A5A; } /* Hover effect */
        # """)


    def load_dataset(self):
        # Open a directory dialog to select the dataset folder
        folder_path = QFileDialog.getExistingDirectory(self, "Select Dataset Folder")
        if folder_path:
            self.dataset_folder = folder_path
            # Set busy cursor to indicate loading
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
            QApplication.processEvents() # Ensure the cursor change is applied

            self.populate_image_list()
            self.statusBar.showMessage(f"Dataset loaded: {os.path.basename(folder_path)}")

            # Restore default cursor after loading
            QApplication.restoreOverrideCursor()
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
            # If image is hidden, we might want to clear the canvas or show a placeholder
            # For now, let's assume ZoomPanLabel handles empty state gracefully.
            # If ZoomPanLabel has a default text, it will be shown.
            # If not, we might need to set a placeholder pixmap or text.
            # For now, we'll just return, letting ZoomPanLabel's paintEvent handle it.
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            # Handle error case, perhaps by showing an error message on the canvas
            # For now, let ZoomPanLabel's paintEvent handle the empty state.
            return

        # Use the ZoomPanLabel's set_pixmap method, which handles scaling and drawing
        self.canvas_label.set_pixmap(pixmap)
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
        # Set a darker background for the canvas widget
        self.canvas_widget.setStyleSheet("background-color: #000000;") # Set to black
        self.canvas_label = ZoomPanLabel() # Use the custom ZoomPanLabel
        canvas_layout = QVBoxLayout(self.canvas_widget)
        canvas_layout.addWidget(self.canvas_label)
        self.setCentralWidget(self.canvas_widget)

    def setup_left_panel(self):
        self.left_panel = QDockWidget("Dataset Management") # Changed title to "Dataset Management"
        self.left_panel.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        left_content_widget = QWidget()
        left_layout = QVBoxLayout(left_content_widget)
        
        self.left_panel_list = QListWidget()
        # Removed the direct stylesheet for QListWidget::item:selected as it will be handled by custom widget styling
        left_layout.addWidget(self.left_panel_list)
        
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        left_layout.addWidget(self.separator)

        self.label_management_widget = QWidget()
        label_management_layout = QVBoxLayout(self.label_management_widget)
        label_management_label = QLabel("Label Management Section")
        label_management_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_management_layout.addWidget(label_management_label)
        left_layout.addWidget(self.label_management_widget)
        
        # Adjusted stretch factors to give more space to the list widget
        # The list widget should take 60% and label management 40%
        left_layout.setStretchFactor(self.left_panel_list, 6) 
        left_layout.addWidget(self.label_management_widget)
        left_layout.setStretchFactor(self.label_management_widget, 4)

        self.left_panel.setWidget(left_content_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_panel)
        self.left_panel.setFixedWidth(250) # Adjusted width to better fit content

        # Connect the signal for item selection change in the list
        self.left_panel_list.currentItemChanged.connect(self.on_image_list_item_changed)

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
        # This is already done by toggle_visibility, but good to be aware of.

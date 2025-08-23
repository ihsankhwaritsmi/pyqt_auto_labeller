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
        self.image_bounding_boxes = {} # Dictionary to store bounding boxes per image: {image_path: [(class_id, QRectF), ...]}
        self.current_image_path = None # Track the currently displayed image path
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
        self.image_bounding_boxes = {} # Reset bounding boxes for all images
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
                    self.image_bounding_boxes[file_path] = [] # Initialize empty list for bounding boxes

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
            # If image is hidden, clear the canvas
            self.canvas_label.set_pixmap(QPixmap()) # Set an empty pixmap to clear
            self.canvas_label.clear_bounding_boxes() # Clear any existing boxes
            self.statusBar.showMessage(f"Image hidden: {os.path.basename(image_path)}")
            self.current_image_path = None
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.canvas_label.set_pixmap(QPixmap()) # Clear canvas on error
            self.canvas_label.clear_bounding_boxes()
            self.statusBar.showMessage(f"Error loading image: {os.path.basename(image_path)}")
            self.current_image_path = None
            return

        # Set the new pixmap
        self.canvas_label.set_pixmap(pixmap)
        self.current_image_path = image_path # Update current image path

        # Load bounding boxes for the new image
        if image_path in self.image_bounding_boxes:
            self.canvas_label.set_bounding_boxes(self.image_bounding_boxes[image_path])
        else:
            self.canvas_label.clear_bounding_boxes() # No boxes for this image yet

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
        # Add buttons to the right panel (toolbox)
        self.annotate_button = QPushButton("Annotate Mode")
        self.select_button = QPushButton("Select Mode")
        self.save_labels_button = QPushButton("Save Labels")
        self.clear_labels_button = QPushButton("Clear Labels")

        # Make mode buttons checkable and set initial state
        self.annotate_button.setCheckable(True)
        self.select_button.setCheckable(True)
        self.select_button.setChecked(True) # Select mode is default

        # Connect buttons to methods
        self.annotate_button.clicked.connect(self._set_annotate_mode)
        self.select_button.clicked.connect(self._set_select_mode)
        self.save_labels_button.clicked.connect(self.save_labels)
        self.clear_labels_button.clicked.connect(self.clear_labels)

        # Add buttons to the layout
        right_layout.addWidget(self.annotate_button)
        right_layout.addWidget(self.select_button)
        right_layout.addWidget(self.save_labels_button)
        right_layout.addWidget(self.clear_labels_button)

        # Add a stretch to push buttons to the top if needed, or just let them fill
        right_layout.addStretch(1)

        self.right_panel.setWidget(right_content)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_panel)
        self.right_panel.setFixedWidth(200)

    def setup_status_bar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def on_image_list_item_changed(self, current_item, previous_item):
        # Save bounding boxes of the previously displayed image
        if previous_item and self.current_image_path:
            # Get bounding boxes from canvas_label and store them
            self.image_bounding_boxes[self.current_image_path] = self.canvas_label.get_bounding_boxes()

        if current_item:
            # Get the custom widget associated with the selected item
            widget = self.left_panel_list.itemWidget(current_item)
            if widget and isinstance(widget, ImageListItemWidget):
                self.display_image(widget.image_path)
        else:
            # If no item is selected, clear the canvas and current image path
            if self.current_image_path:
                self.image_bounding_boxes[self.current_image_path] = self.canvas_label.get_bounding_boxes()
            self.canvas_label.set_pixmap(QPixmap()) # Clear the canvas
            self.canvas_label.clear_bounding_boxes()
            self.current_image_path = None
            self.statusBar.showMessage("No image selected.")

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

    def _set_annotate_mode(self):
        self.canvas_label.set_mode("annotate")
        self.annotate_button.setChecked(True)
        self.select_button.setChecked(False)
        self.statusBar.showMessage("Mode: Annotate")

    def _set_select_mode(self):
        self.canvas_label.set_mode("select")
        self.select_button.setChecked(True)
        self.annotate_button.setChecked(False)
        self.statusBar.showMessage("Mode: Select")

    def save_labels(self):
        current_item = self.left_panel_list.currentItem()
        if not current_item:
            self.statusBar.showMessage("No image selected to save labels.")
            return

        widget = self.left_panel_list.itemWidget(current_item)
        if not widget or not hasattr(widget, 'image_path'):
            self.statusBar.showMessage("Could not get image path.")
            return

        image_path = widget.image_path
        image_filename = os.path.basename(image_path)
        base_name, _ = os.path.splitext(image_filename)
        label_filename = base_name + ".txt"
        label_filepath = os.path.join(self.dataset_folder, label_filename)

        # Get bounding boxes from the stored dictionary, not directly from canvas_label
        bounding_boxes = self.image_bounding_boxes.get(image_path, [])
        
        if not bounding_boxes:
            self.statusBar.showMessage("No bounding boxes to save for this image.")
            # Optionally, delete existing label file if no boxes are present
            if os.path.exists(label_filepath):
                try:
                    os.remove(label_filepath)
                    self.statusBar.showMessage(f"Removed empty label file: {label_filename}")
                except OSError as e:
                    self.statusBar.showMessage(f"Error removing file {label_filename}: {e}")
            return

        # Get original image dimensions for normalization
        original_width = self.canvas_label.original_width
        original_height = self.canvas_label.original_height

        if original_width is None or original_height is None or original_width == 0 or original_height == 0:
            self.statusBar.showMessage("Error: Original image dimensions not available for normalization.")
            return

        try:
            with open(label_filepath, 'w') as f:
                for class_id, rect in bounding_boxes:
                    # Calculate YOLO format coordinates
                    # Ensure rect is valid before calculating
                    if rect.width() <= 0 or rect.height() <= 0:
                        continue # Skip invalid rectangles

                    center_x = (rect.x() + rect.width() / 2) / original_width
                    center_y = (rect.y() + rect.height() / 2) / original_height
                    width = rect.width() / original_width
                    height = rect.height() / original_height

                    # Ensure values are within [0, 1] range and formatted correctly
                    f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
            
            self.statusBar.showMessage(f"Labels saved to {label_filename}")
        except IOError as e:
            self.statusBar.showMessage(f"Error saving labels to {label_filename}: {e}")
        except Exception as e:
            self.statusBar.showMessage(f"An unexpected error occurred: {e}")


    def clear_labels(self):
        if self.current_image_path and self.current_image_path in self.image_bounding_boxes:
            self.image_bounding_boxes[self.current_image_path] = [] # Clear boxes in storage
            self.canvas_label.clear_bounding_boxes() # Clear boxes on canvas
            self.statusBar.showMessage("Bounding boxes cleared for current image.")
        else:
            self.statusBar.showMessage("No image selected or no bounding boxes to clear.")

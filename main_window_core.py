import os
import sys
import json # Import json for label file operations
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
    QSizePolicy,
    QInputDialog, # Import QInputDialog for label input
    QLineEdit # Import QLineEdit for EchoMode
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
        self.labels = [] # List to store label dictionaries: [{'id': 0, 'name': 'label1'}, ...]
        self.current_label_id = -1 # Track the currently selected label's ID for annotation
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
            self.load_labels_from_json() # Load labels when dataset is loaded
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
        self.labels = [] # Clear labels when a new dataset is loaded
        self.current_label_id = -1 # Reset current label ID
        self.left_panel_list.clear() # Clear existing list items
        self.label_list_widget.clear() # Clear existing label list items

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

                    # Check if a label file exists and is not empty
                    label_filename = os.path.splitext(os.path.basename(file_path))[0] + ".txt"
                    label_filepath = os.path.join(self.dataset_folder, label_filename)
                    is_labelled = os.path.exists(label_filepath) and os.path.getsize(label_filepath) > 0

                    # Create a custom widget for the list item
                    list_item_widget = ImageListItemWidget(file_path)
                    list_item_widget.visibility_changed.connect(self.on_visibility_changed) # Connect signal
                    list_item_widget.set_labelled_status(is_labelled) # Set the labelled status

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
        loaded_boxes = []
        label_filename = os.path.splitext(os.path.basename(image_path))[0] + ".txt"
        label_filepath = os.path.join(self.dataset_folder, label_filename)

        if os.path.exists(label_filepath):
            try:
                with open(label_filepath, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5: # Expect at least class_id, center_x, center_y, width, height
                            class_id = int(parts[0])
                            center_x = float(parts[1])
                            center_y = float(parts[2])
                            width = float(parts[3])
                            height = float(parts[4])

                            # Get original image dimensions for denormalization
                            original_width = self.canvas_label.original_width
                            original_height = self.canvas_label.original_height

                            if original_width is None or original_height is None or original_width == 0 or original_height == 0:
                                self.statusBar.showMessage("Error: Original image dimensions not available for loading labels.")
                                loaded_boxes = [] # Clear any partially loaded boxes
                                break

                            # Convert YOLO format to QRectF (image coordinates)
                            x = (center_x - width / 2) * original_width
                            y = (center_y - height / 2) * original_height
                            w = width * original_width
                            h = height * original_height
                            
                            loaded_boxes.append((class_id, QRectF(x, y, w, h)))
                self.statusBar.showMessage(f"Labels loaded from {label_filename}")
            except Exception as e:
                self.statusBar.showMessage(f"Error loading labels from {label_filename}: {e}")
        
        # Update internal storage and canvas
        self.image_bounding_boxes[image_path] = loaded_boxes
        self.canvas_label.set_bounding_boxes(loaded_boxes)

        self.statusBar.showMessage(f"Displaying: {os.path.basename(image_path)}")


    def setup_ui(self):
        self.setup_toolbar()
        self.setup_left_panel()
        self.setup_right_panel()
        self.setup_status_bar() # Initialize status bar first
        self.setup_canvas()

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
        self.canvas_label.label_needed_signal.connect(self.statusBar.showMessage) # Connect signal to status bar
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
        
        label_management_title = QLabel("Label Management")
        label_management_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_management_layout.addWidget(label_management_title)

        self.label_list_widget = QListWidget()
        label_management_layout.addWidget(self.label_list_widget)

        # Label CRUD buttons
        label_buttons_layout = QHBoxLayout()
        self.add_label_button = QPushButton("Add")
        self.edit_label_button = QPushButton("Edit")
        self.delete_label_button = QPushButton("Delete")
        label_buttons_layout.addWidget(self.add_label_button)
        label_buttons_layout.addWidget(self.edit_label_button)
        label_buttons_layout.addWidget(self.delete_label_button)
        label_management_layout.addLayout(label_buttons_layout)

        left_layout.addWidget(self.label_management_widget)
        
        # Adjusted stretch factors to give more space to the image list widget
        left_layout.setStretchFactor(self.left_panel_list, 6) 
        left_layout.setStretchFactor(self.label_management_widget, 4) # Give more space to label management

        # Connect label list item changed signal
        self.label_list_widget.currentItemChanged.connect(self.on_label_list_item_changed)
        # Connect label CRUD button signals
        self.add_label_button.clicked.connect(self.add_label)
        self.edit_label_button.clicked.connect(self.edit_label)
        self.delete_label_button.clicked.connect(self.delete_label)

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
        self.load_labels_from_json() # Load labels on startup if a dataset is already selected (e.g., from previous session)

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

    def load_labels_from_json(self):
        if not self.dataset_folder:
            return

        labels_filepath = os.path.join(self.dataset_folder, "labels.json")
        self.labels = []
        self.label_list_widget.clear()
        self.current_label_id = -1

        if os.path.exists(labels_filepath):
            try:
                with open(labels_filepath, 'r') as f:
                    loaded_labels = json.load(f)
                    if isinstance(loaded_labels, list):
                        self.labels = loaded_labels
                        for label in self.labels:
                            item = QListWidgetItem(label['name'])
                            item.setData(Qt.ItemDataRole.UserRole, label['id']) # Store ID in UserRole
                            self.label_list_widget.addItem(item)
                        self.statusBar.showMessage(f"Labels loaded from labels.json")
                        if self.labels:
                            self.label_list_widget.setCurrentRow(0) # Select first label
                            self.current_label_id = self.labels[0]['id']
                    else:
                        self.statusBar.showMessage("Error: labels.json content is not a list.")
            except json.JSONDecodeError as e:
                self.statusBar.showMessage(f"Error decoding labels.json: {e}")
            except IOError as e:
                self.statusBar.showMessage(f"Error reading labels.json: {e}")
        else:
            self.statusBar.showMessage("No labels.json found. Starting with empty labels.")

    def save_labels_to_json(self):
        if not self.dataset_folder:
            return

        labels_filepath = os.path.join(self.dataset_folder, "labels.json")
        try:
            with open(labels_filepath, 'w') as f:
                json.dump(self.labels, f, indent=4)
            self.statusBar.showMessage(f"Labels saved to labels.json")
        except IOError as e:
            self.statusBar.showMessage(f"Error saving labels to labels.json: {e}")

    def closeEvent(self, event):
        # Save labels before closing the application
        self.save_labels_to_json()
        super().closeEvent(event)

    def on_label_list_item_changed(self, current_item, previous_item):
        if current_item:
            self.current_label_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.canvas_label.set_current_class_id(self.current_label_id) # Pass selected label ID to canvas
            self.statusBar.showMessage(f"Selected label: {current_item.text()} (ID: {self.current_label_id})")
        else:
            self.current_label_id = -1
            self.canvas_label.set_current_class_id(-1) # No label selected
            self.statusBar.showMessage("No label selected.")

    def add_label(self):
        label_name, ok = QInputDialog.getText(self, "Add New Label", "Label Name:")
        if ok and label_name:
            # Find the next available ID
            next_id = 0
            if self.labels:
                next_id = max(label['id'] for label in self.labels) + 1
            
            new_label = {'id': next_id, 'name': label_name}
            self.labels.append(new_label)
            
            item = QListWidgetItem(label_name)
            item.setData(Qt.ItemDataRole.UserRole, next_id)
            self.label_list_widget.addItem(item)
            self.label_list_widget.setCurrentItem(item) # Select the newly added label
            self.save_labels_to_json()
            self.statusBar.showMessage(f"Label '{label_name}' added.")
        elif ok:
            self.statusBar.showMessage("Label name cannot be empty.")

    def edit_label(self):
        current_item = self.label_list_widget.currentItem()
        if not current_item:
            self.statusBar.showMessage("No label selected to edit.")
            return

        current_label_name = current_item.text()
        new_label_name, ok = QInputDialog.getText(self, "Edit Label", "New Label Name:",
                                                  QLineEdit.EchoMode.Normal, current_label_name)
        if ok and new_label_name:
            label_id = current_item.data(Qt.ItemDataRole.UserRole)
            for label in self.labels:
                if label['id'] == label_id:
                    label['name'] = new_label_name
                    break
            current_item.setText(new_label_name)
            self.save_labels_to_json()
            self.statusBar.showMessage(f"Label updated to '{new_label_name}'.")
        elif ok:
            self.statusBar.showMessage("Label name cannot be empty.")

    def delete_label(self):
        current_item = self.label_list_widget.currentItem()
        if not current_item:
            self.statusBar.showMessage("No label selected to delete.")
            return

        label_id_to_delete = current_item.data(Qt.ItemDataRole.UserRole)
        label_name_to_delete = current_item.text()

        # Remove from self.labels
        self.labels = [label for label in self.labels if label['id'] != label_id_to_delete]
        
        # Remove from QListWidget
        row = self.label_list_widget.row(current_item)
        self.label_list_widget.takeItem(row)
        
        # If the deleted label was the current_label_id, reset it
        if self.current_label_id == label_id_to_delete:
            self.current_label_id = -1
            if self.labels: # Select the first label if available
                self.label_list_widget.setCurrentRow(0)
                self.current_label_id = self.labels[0]['id']

        self.save_labels_to_json()
        self.statusBar.showMessage(f"Label '{label_name_to_delete}' deleted.")

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
                    self._update_image_list_item_labelled_status(image_path, False) # Update status
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
                    # Find the label name for the class_id
                    label_name = "unknown"
                    for label_data in self.labels:
                        if label_data['id'] == class_id:
                            label_name = label_data['name']
                            break

                    # Calculate YOLO format coordinates
                    # Ensure rect is valid before calculating
                    if rect.width() <= 0 or rect.height() <= 0:
                        continue # Skip invalid rectangles

                    center_x = (rect.x() + rect.width() / 2) / original_width
                    center_y = (rect.y() + rect.height() / 2) / original_height
                    width = rect.width() / original_width
                    height = rect.height() / original_height

                    # Ensure values are within [0, 1] range and formatted correctly
                    f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f} #{label_name}\n") # Include label name as comment
            
            self.statusBar.showMessage(f"Labels saved to {label_filename}")
            self._update_image_list_item_labelled_status(image_path, True) # Update status
        except IOError as e:
            self.statusBar.showMessage(f"Error saving labels to {label_filename}: {e}")
        except Exception as e:
            self.statusBar.showMessage(f"An unexpected error occurred: {e}")


    def clear_labels(self):
        if self.current_image_path and self.current_image_path in self.image_bounding_boxes:
            self.image_bounding_boxes[self.current_image_path] = [] # Clear boxes in storage
            self.canvas_label.clear_bounding_boxes() # Clear boxes on canvas
            self.statusBar.showMessage("Bounding boxes cleared for current image.")
            self._update_image_list_item_labelled_status(self.current_image_path, False) # Update status
        else:
            self.statusBar.showMessage("No image selected or no bounding boxes to clear.")

    def _update_image_list_item_labelled_status(self, image_path: str, is_labelled: bool):
        # Find the QListWidgetItem corresponding to the image_path and update its status
        for i in range(self.left_panel_list.count()):
            item = self.left_panel_list.item(i)
            widget = self.left_panel_list.itemWidget(item)
            if isinstance(widget, ImageListItemWidget) and widget.image_path == image_path:
                widget.set_labelled_status(is_labelled)
                break

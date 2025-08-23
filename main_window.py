import sys
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QStatusBar,
    QToolBar,
    QDockWidget,
    QFileDialog, # Import QFileDialog
    QListWidget, # Import QListWidget
    QListWidgetItem, # Import QListWidgetItem
    QFrame # Import QFrame for separator
)
from PyQt6.QtCore import Qt, QDir # Import QDir for path operations
from PyQt6.QtGui import QPixmap, QImageReader # Import for image handling
from styles import LIGHT_THEME, DARK_THEME
import os # Import os module

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 App Layout")
        self.setGeometry(100, 100, 1000, 700) # x, y, width, height
        self.is_dark_theme = True # Initialize theme state to dark
        self.dataset_folder = None # Store the selected dataset folder path
        self.image_files = [] # Store list of image file paths
        self.setup_ui()
        self.apply_theme() # Apply initial theme

    def apply_theme(self):
        # Only apply dark theme as per user request
        self.setStyleSheet(DARK_THEME)

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
        # Clear existing list items
        self.left_panel_list.clear()

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
                    self.left_panel_list.addItem(filename) # Add filename to the list widget

        if not self.image_files:
            self.statusBar.showMessage("No images found in the selected folder.")
        else:
            # Select the first image by default
            self.left_panel_list.setCurrentRow(0)
            self.display_image(self.image_files[0])


    def display_image(self, image_path):
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
        self.left_panel = QDockWidget("Left Panel")
        self.left_panel.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        left_content_widget = QWidget()
        left_layout = QVBoxLayout(left_content_widget)
        
        self.left_panel_list = QListWidget()
        self.left_panel_list.currentItemChanged.connect(self.on_image_list_item_changed)
        self.left_panel_list.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #ADD8E6; /* Light Blue */
                color: black; /* Ensure text is readable */
            }
        """)
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
        
        left_layout.setStretchFactor(self.left_panel_list, 6)
        left_layout.setStretchFactor(self.label_management_widget, 4)

        self.left_panel.setWidget(left_content_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_panel)
        self.left_panel.setFixedWidth(200)

    def setup_right_panel(self):
        self.right_panel = QDockWidget("Right Panel")
        self.right_panel.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        right_label = QLabel("Right Panel Content")
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
            selected_filename = current_item.text()
            for img_path in self.image_files:
                if os.path.basename(img_path) == selected_filename:
                    self.display_image(img_path)
                    break

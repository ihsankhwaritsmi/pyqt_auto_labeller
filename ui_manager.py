import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStatusBar,
    QToolBar, QDockWidget, QFileDialog, QListWidget, QListWidgetItem,
    QFrame, QPushButton, QStyle, QSizePolicy, QInputDialog, QLineEdit, QApplication, QComboBox
)
from PyQt6.QtCore import Qt, QDir, QSize, pyqtSignal, QRectF
from PyQt6.QtGui import QPixmap, QImageReader, QIcon

from widgets import ImageListItemWidget
from styles import DARK_THEME
from canvas_widget import ZoomPanLabel

class UIManager:
    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.main_window.is_dark_theme = True # Initialize theme state to dark

    def setup_ui(self):
        self.main_window.setWindowTitle("PyQt6 App Layout")
        self.main_window.setGeometry(100, 100, 1000, 700) # x, y, width, height
        self.apply_theme() # Apply initial theme
        self.setup_toolbar()
        self.setup_left_panel()
        self.setup_right_panel()
        self.setup_status_bar()
        self.setup_canvas()

    def apply_theme(self):
        self.main_window.setStyleSheet(DARK_THEME)

    def setup_toolbar(self):
        self.main_window.toolbar = QToolBar("Main Toolbar")
        self.main_window.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.main_window.toolbar)

        self.main_window.load_dataset_action = self.main_window.toolbar.addAction("Load Dataset")
        # Connect to a method in MainWindow or a DatasetManager
        # self.main_window.load_dataset_action.triggered.connect(self.main_window.load_dataset)

        self.main_window.toolbar.addAction("File")
        self.main_window.toolbar.addAction("Edit")
        self.main_window.toolbar.addAction("View")

    def setup_canvas(self):
        self.main_window.canvas_widget = QWidget()
        self.main_window.canvas_widget.setStyleSheet("background-color: #000000;") # Set to black
        self.main_window.canvas_label = ZoomPanLabel() # Use the custom ZoomPanLabel
        # self.main_window.canvas_label.label_needed_signal.connect(self.main_window.statusBar.showMessage)
        canvas_layout = QVBoxLayout(self.main_window.canvas_widget)
        canvas_layout.addWidget(self.main_window.canvas_label)
        self.main_window.setCentralWidget(self.main_window.canvas_widget)

    def setup_left_panel(self):
        self.main_window.left_panel = QDockWidget("Dataset Management")
        self.main_window.left_panel.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        left_content_widget = QWidget()
        left_layout = QVBoxLayout(left_content_widget)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:")
        self.main_window.filter_combobox = QComboBox()
        self.main_window.filter_combobox.addItems(["All", "Labelled", "Unlabelled"])
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.main_window.filter_combobox)
        left_layout.addLayout(filter_layout)

        self.main_window.left_panel_list = QListWidget()
        left_layout.addWidget(self.main_window.left_panel_list)
        
        self.main_window.separator = QFrame()
        self.main_window.separator.setFrameShape(QFrame.Shape.HLine)
        self.main_window.separator.setFrameShadow(QFrame.Shadow.Sunken)
        left_layout.addWidget(self.main_window.separator)

        self.main_window.label_management_widget = QWidget()
        label_management_layout = QVBoxLayout(self.main_window.label_management_widget)
        
        label_management_title = QLabel("Label Management")
        label_management_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_management_layout.addWidget(label_management_title)

        self.main_window.label_list_widget = QListWidget()
        label_management_layout.addWidget(self.main_window.label_list_widget)

        # Label CRUD buttons
        label_buttons_layout = QHBoxLayout()
        self.main_window.add_label_button = QPushButton("Add")
        self.main_window.edit_label_button = QPushButton("Edit")
        self.main_window.delete_label_button = QPushButton("Delete")
        label_buttons_layout.addWidget(self.main_window.add_label_button)
        label_buttons_layout.addWidget(self.main_window.edit_label_button)
        label_buttons_layout.addWidget(self.main_window.delete_label_button)
        label_management_layout.addLayout(label_buttons_layout)

        left_layout.addWidget(self.main_window.label_management_widget)
        
        left_layout.setStretchFactor(self.main_window.left_panel_list, 6) 
        left_layout.setStretchFactor(self.main_window.label_management_widget, 4)

        self.main_window.left_panel.setWidget(left_content_widget)
        self.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.main_window.left_panel)
        self.main_window.left_panel.setFixedWidth(280) # Increased width

    def setup_right_panel(self):
        self.main_window.right_panel = QDockWidget("Properties")
        self.main_window.right_panel.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        right_label = QLabel("Properties Panel Content")
        right_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(right_label)
        
        self.main_window.annotate_button = QPushButton("Annotate Mode")
        self.main_window.select_button = QPushButton("Select Mode")
        self.main_window.save_labels_button = QPushButton("Save Labels")
        self.main_window.clear_labels_button = QPushButton("Clear Labels")

        self.main_window.annotate_button.setCheckable(True)
        self.main_window.select_button.setCheckable(True)
        self.main_window.select_button.setChecked(True)

        # Explicitly set style for annotate and select buttons for testing
        self.main_window.annotate_button.setStyleSheet("QPushButton:checked { background-color: #4A90E2; color: white; border: 1px solid #4A90E2; font-weight: bold; }")
        self.main_window.select_button.setStyleSheet("QPushButton:checked { background-color: #4A90E2; color: white; border: 1px solid #4A90E2; font-weight: bold; }")
        right_layout.addWidget(self.main_window.annotate_button)
        right_layout.addWidget(self.main_window.select_button)

        self.main_window.toggle_visibility_button = QPushButton("Hide Annotations")
        self.main_window.toggle_visibility_button.setEnabled(False) # Initially disabled
        # Make the toggle button checkable and apply the same style as other toggle buttons
        self.main_window.toggle_visibility_button.setCheckable(True)
        self.main_window.toggle_visibility_button.setStyleSheet("QPushButton:checked { background-color: #4A90E2; color: white; border: 1px solid #4A90E2; font-weight: bold; }")
        right_layout.addWidget(self.main_window.toggle_visibility_button)
        right_layout.addStretch(1) # This pushes the following widgets to the bottom

        right_layout.addWidget(self.main_window.save_labels_button)
        right_layout.addWidget(self.main_window.clear_labels_button)

        # Add Next and Previous buttons
        navigation_buttons_layout = QHBoxLayout()
        self.main_window.previous_image_button = QPushButton("Previous")
        self.main_window.next_image_button = QPushButton("Next")
        navigation_buttons_layout.addWidget(self.main_window.previous_image_button)
        navigation_buttons_layout.addWidget(self.main_window.next_image_button)
        right_layout.addLayout(navigation_buttons_layout)

        self.main_window.right_panel.setWidget(right_content)
        self.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.main_window.right_panel)
        self.main_window.right_panel.setFixedWidth(200)

    def setup_status_bar(self):
        self.main_window.statusBar = QStatusBar()
        self.main_window.setStatusBar(self.main_window.statusBar)
        self.main_window.statusBar.showMessage("Ready")

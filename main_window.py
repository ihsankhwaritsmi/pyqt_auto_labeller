import sys
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QStatusBar,
    QToolBar,
    QDockWidget,
)
from PyQt6.QtCore import Qt
from styles import LIGHT_THEME, DARK_THEME

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 App Layout")
        self.setGeometry(100, 100, 1000, 700) # x, y, width, height
        self.is_dark_theme = False # Initialize theme state
        self.setup_ui()
        self.apply_theme() # Apply initial theme

    def apply_theme(self):
        if self.is_dark_theme:
            self.setStyleSheet(DARK_THEME)
        else:
            self.setStyleSheet(LIGHT_THEME)

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def setup_ui(self):
        # 1. Top Panel (Toolbar)
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.toolbar.addAction("File")
        self.toolbar.addAction("Edit")
        self.toolbar.addAction("View")

        # Add theme toggle action to toolbar
        self.theme_toggle_action = self.toolbar.addAction("Toggle Theme")
        self.theme_toggle_action.triggered.connect(self.toggle_theme)

        # 4. Center for Canvas
        self.canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(self.canvas_widget)
        canvas_label = QLabel("Canvas Area")
        canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas_layout.addWidget(canvas_label)
        self.setCentralWidget(self.canvas_widget) # Set canvas as central widget

        # 2. Left Panel (Dock Widget)
        self.left_panel = QDockWidget("Left Panel")
        self.left_panel.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_label = QLabel("Left Panel Content")
        left_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(left_label)
        self.left_panel.setWidget(left_content)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_panel)
        self.left_panel.setFixedWidth(200) # Set fixed width for left panel

        # 3. Right Panel (Dock Widget)
        self.right_panel = QDockWidget("Right Panel")
        self.right_panel.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        right_label = QLabel("Right Panel Content")
        right_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(right_label)
        self.right_panel.setWidget(right_content)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_panel)
        self.right_panel.setFixedWidth(200) # Set fixed width for right panel

        # Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

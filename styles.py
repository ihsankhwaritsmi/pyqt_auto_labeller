DARK_THEME = """
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
"""

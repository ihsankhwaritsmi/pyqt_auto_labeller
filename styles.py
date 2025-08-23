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
    background-color: #4A4A4A; /* Default button background */
    border: 1px solid #5A5A5A; /* Default button border */
    color: white; /* Default button text color */
    padding: 3px;
}
QPushButton:hover { background-color: #5A5A5A; } /* Hover effect */
QPushButton:pressed { /* Visual feedback for pressed state */
    background-color: #3A3A3A; /* Darker background when pressed */
    border: 1px solid #6A6A6A; /* More prominent border when pressed */
}
QMainWindow QPushButton:checked { /* Style for checked state (e.g., Annotate/Select mode) */
    background-color: #4A90E2; /* Blue selection color, similar to list item */
    border: 1px solid #4A90E2; /* Match border color */
    color: white;
    font-weight: bold; /* Make text bold */
}
QPushButton:disabled {
    background-color: #3A3A3A; /* Slightly darker background to keep it visible */
    border: 1px solid #5A5A5A; /* Keep a visible border, similar to default */
    color: #888888; /* Greyed out text color */
}
QPushButton:enabled {
    background-color: #4A4A4A; /* Default button background when enabled */
    border: 1px solid #5A5A5A; /* Default button border when enabled */
    color: white; /* Default button text color when enabled */
}
"""

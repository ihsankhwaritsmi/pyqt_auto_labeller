import sys
from PyQt6.QtWidgets import QApplication
from main_window_core import MainWindow
import random # Import random

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    app.rng = random.Random() # Assign the random.Random instance to the QApplication instance
    window.show()
    sys.exit(app.exec())

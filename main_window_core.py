import os
import sys
from PyQt6.QtWidgets import QMainWindow, QInputDialog, QLineEdit, QApplication
from PyQt6.QtCore import Qt

# Import custom widget and styles
from styles import DARK_THEME

# Import new managers
from ui_manager import UIManager
from dataset_manager import DatasetManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui_manager = UIManager(self)
        self.dataset_manager = DatasetManager(self)
        self.ui_manager.setup_ui()
        self.connect_signals()

    def connect_signals(self):
        # Connect UI signals to DatasetManager methods
        self.ui_manager.main_window.load_dataset_action.triggered.connect(self.dataset_manager.load_dataset)
        self.ui_manager.main_window.left_panel_list.currentItemChanged.connect(self.dataset_manager.on_image_list_item_changed)
        self.ui_manager.main_window.label_list_widget.currentItemChanged.connect(self.dataset_manager.on_image_list_item_changed)
        self.ui_manager.main_window.add_label_button.clicked.connect(self._add_label_dialog)
        self.ui_manager.main_window.edit_label_button.clicked.connect(self._edit_label_dialog)
        self.ui_manager.main_window.delete_label_button.clicked.connect(self._delete_label_dialog)
        self.ui_manager.main_window.annotate_button.clicked.connect(self._set_annotate_mode)
        self.ui_manager.main_window.select_button.clicked.connect(self._set_select_mode)
        self.ui_manager.main_window.save_labels_button.clicked.connect(self.dataset_manager.save_labels)
        self.ui_manager.main_window.clear_labels_button.clicked.connect(self.dataset_manager.clear_labels)
        self.ui_manager.main_window.canvas_label.label_needed_signal.connect(self.ui_manager.main_window.statusBar.showMessage)

    def apply_theme(self):
        self.ui_manager.apply_theme()

    def _set_annotate_mode(self):
        self.ui_manager.main_window.canvas_label.set_mode("annotate")
        self.ui_manager.main_window.annotate_button.setChecked(True)
        self.ui_manager.main_window.select_button.setChecked(False)
        self.ui_manager.main_window.statusBar.showMessage("Mode: Annotate")

    def _set_select_mode(self):
        self.ui_manager.main_window.canvas_label.set_mode("select")
        self.ui_manager.main_window.select_button.setChecked(True)
        self.ui_manager.main_window.annotate_button.setChecked(False)
        self.ui_manager.main_window.statusBar.showMessage("Mode: Select")

    def _add_label_dialog(self):
        label_name, ok = QInputDialog.getText(self, "Add New Label", "Label Name:")
        if ok and label_name:
            next_id = 0
            if self.dataset_manager.labels:
                next_id = max(label['id'] for label in self.dataset_manager.labels) + 1
            self.dataset_manager.add_label(label_name, next_id)
        elif ok:
            self.ui_manager.main_window.statusBar.showMessage("Label name cannot be empty.")

    def _edit_label_dialog(self):
        current_item = self.ui_manager.main_window.label_list_widget.currentItem()
        if not current_item:
            self.ui_manager.main_window.statusBar.showMessage("No label selected to edit.")
            return

        current_label_name = current_item.text()
        new_label_name, ok = QInputDialog.getText(self, "Edit Label", "New Label Name:",
                                                  QLineEdit.EchoMode.Normal, current_label_name)
        if ok and new_label_name:
            label_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.dataset_manager.edit_label(label_id, new_label_name, current_item)
        elif ok:
            self.ui_manager.main_window.statusBar.showMessage("Label name cannot be empty.")

    def _delete_label_dialog(self):
        current_item = self.ui_manager.main_window.label_list_widget.currentItem()
        if not current_item:
            self.ui_manager.main_window.statusBar.showMessage("No label selected to delete.")
            return

        label_id_to_delete = current_item.data(Qt.ItemDataRole.UserRole)
        label_name_to_delete = current_item.text()
        self.dataset_manager.delete_label(label_id_to_delete, label_name_to_delete, current_item)

    def closeEvent(self, event):
        self.dataset_manager.save_labels_to_json()
        super().closeEvent(event)

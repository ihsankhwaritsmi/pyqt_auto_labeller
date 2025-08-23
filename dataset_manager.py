import os
import json
from PyQt6.QtCore import Qt, QDir, QSize, pyqtSignal, QRectF
from PyQt6.QtGui import QPixmap, QImageReader
from PyQt6.QtWidgets import QFileDialog, QListWidgetItem, QInputDialog, QLineEdit, QApplication

from widgets import ImageListItemWidget
from canvas_widget import ZoomPanLabel

class DatasetManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.dataset_folder = None
        self.image_files = []
        self.image_visibility = {}
        self.image_bounding_boxes = {} # {image_path: [(class_id, QRectF), ...]}
        self.current_image_path = None
        self.labels = [] # [{'id': 0, 'name': 'label1'}, ...]
        self.current_label_id = -1

    def load_dataset(self):
        folder_path = QFileDialog.getExistingDirectory(self.main_window, "Select Dataset Folder")
        if folder_path:
            self.dataset_folder = folder_path
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
            QApplication.processEvents()

            self.populate_image_list()
            self.load_labels_from_json()
            self.main_window.statusBar.showMessage(f"Dataset loaded: {os.path.basename(folder_path)}")

            QApplication.restoreOverrideCursor()
        else:
            self.main_window.statusBar.showMessage("Dataset loading cancelled")

    def populate_image_list(self):
        if not self.dataset_folder:
            return

        self.image_files = []
        self.image_visibility = {}
        self.image_bounding_boxes = {}
        self.labels = []
        self.current_label_id = -1
        self.main_window.left_panel_list.clear()
        self.main_window.label_list_widget.clear()

        supported_extensions = QImageReader.supportedImageFormats()
        supported_extensions = [ext.data().decode('ascii') for ext in supported_extensions]

        for filename in os.listdir(self.dataset_folder):
            file_path = os.path.join(self.dataset_folder, filename)
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
                if file_ext in supported_extensions:
                    self.image_files.append(file_path)
                    self.image_visibility[file_path] = True
                    self.image_bounding_boxes[file_path] = []

                    label_filename = os.path.splitext(os.path.basename(file_path))[0] + ".txt"
                    label_filepath = os.path.join(self.dataset_folder, label_filename)
                    is_labelled = os.path.exists(label_filepath) and os.path.getsize(label_filepath) > 0

                    list_item_widget = ImageListItemWidget(file_path)
                    list_item_widget.visibility_changed.connect(self.on_visibility_changed)
                    list_item_widget.set_labelled_status(is_labelled)

                    list_item = QListWidgetItem(self.main_window.left_panel_list)
                    list_item.setSizeHint(list_item_widget.sizeHint())
                    self.main_window.left_panel_list.setItemWidget(list_item, list_item_widget)

        if not self.image_files:
            self.main_window.statusBar.showMessage("No images found in the selected folder.")
        else:
            self.main_window.left_panel_list.setCurrentRow(0)
            self.display_image(self.image_files[0])

    def display_image(self, image_path):
        if image_path in self.image_visibility and not self.image_visibility[image_path]:
            self.main_window.canvas_label.set_pixmap(QPixmap())
            self.main_window.canvas_label.clear_bounding_boxes()
            self.main_window.statusBar.showMessage(f"Image hidden: {os.path.basename(image_path)}")
            self.current_image_path = None
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.main_window.canvas_label.set_pixmap(QPixmap())
            self.main_window.canvas_label.clear_bounding_boxes()
            self.main_window.statusBar.showMessage(f"Error loading image: {os.path.basename(image_path)}")
            self.current_image_path = None
            return

        self.main_window.canvas_label.set_pixmap(pixmap)
        self.current_image_path = image_path
        self.main_window.statusBar.showMessage(f"Image dimensions: {self.main_window.canvas_label.original_width}x{self.main_window.canvas_label.original_height}")

        loaded_boxes = []
        label_filename = os.path.splitext(os.path.basename(image_path))[0] + ".txt"
        label_filepath = os.path.join(self.dataset_folder, label_filename)

        if os.path.exists(label_filepath):
            try:
                with open(label_filepath, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            class_id = int(parts[0])
                            center_x = float(parts[1])
                            center_y = float(parts[2])
                            width = float(parts[3])
                            height = float(parts[4])

                            original_width = self.main_window.canvas_label.original_width
                            original_height = self.main_window.canvas_label.original_height

                            if original_width is None or original_height is None or original_width == 0 or original_height == 0:
                                self.main_window.statusBar.showMessage("Error: Original image dimensions not available for loading labels.")
                                loaded_boxes = []
                                break

                            x = (center_x - width / 2) * original_width
                            y = (center_y - height / 2) * original_height
                            w = width * original_width
                            h = height * original_height
                            
                            loaded_boxes.append((class_id, QRectF(x, y, w, h)))
                self.main_window.statusBar.showMessage(f"Labels loaded from {label_filename}. Found {len(loaded_boxes)} boxes.")
                if loaded_boxes:
                    first_box = loaded_boxes[0][1]
                    self.main_window.statusBar.showMessage(f"First box: x={first_box.x():.2f}, y={first_box.y():.2f}, w={first_box.width():.2f}, h={first_box.height():.2f}")
            except Exception as e:
                self.main_window.statusBar.showMessage(f"Error loading labels from {label_filename}: {e}")
        
        self.image_bounding_boxes[image_path] = loaded_boxes
        self.main_window.canvas_label.set_bounding_boxes(loaded_boxes)

        self.main_window.statusBar.showMessage(f"Displaying: {os.path.basename(image_path)}")

    def on_image_list_item_changed(self, current_item, previous_item):
        if previous_item and self.current_image_path:
            self.image_bounding_boxes[self.current_image_path] = self.main_window.canvas_label.get_bounding_boxes()

        if current_item:
            widget = self.main_window.left_panel_list.itemWidget(current_item)
            if widget and isinstance(widget, ImageListItemWidget):
                self.display_image(widget.image_path)
        else:
            if self.current_image_path:
                self.image_bounding_boxes[self.current_image_path] = self.main_window.canvas_label.get_bounding_boxes()
            self.main_window.canvas_label.set_pixmap(QPixmap())
            self.main_window.canvas_label.clear_bounding_boxes()
            self.current_image_path = None
            self.main_window.statusBar.showMessage("No image selected.")

    def on_visibility_changed(self, image_path, is_visible):
        self.image_visibility[image_path] = is_visible
        current_item = self.main_window.left_panel_list.currentItem()
        if current_item:
            widget = self.main_window.left_panel_list.itemWidget(current_item)
            if widget and widget.image_path == image_path:
                self.display_image(image_path)

    def load_labels_from_json(self):
        if not self.dataset_folder:
            return

        labels_filepath = os.path.join(self.dataset_folder, "labels.json")
        self.labels = []
        self.main_window.label_list_widget.clear()
        self.current_label_id = -1

        if os.path.exists(labels_filepath):
            try:
                with open(labels_filepath, 'r') as f:
                    loaded_labels = json.load(f)
                    if isinstance(loaded_labels, list):
                        self.labels = loaded_labels
                        for label in self.labels:
                            item = QListWidgetItem(label['name'])
                            item.setData(Qt.ItemDataRole.UserRole, label['id'])
                            self.main_window.label_list_widget.addItem(item)
                        self.main_window.statusBar.showMessage(f"Labels loaded from labels.json")
                        if self.labels:
                            self.main_window.label_list_widget.setCurrentRow(0)
                            self.current_label_id = self.labels[0]['id']
                    else:
                        self.main_window.statusBar.showMessage("Error: labels.json content is not a list.")
            except json.JSONDecodeError as e:
                self.main_window.statusBar.showMessage(f"Error decoding labels.json: {e}")
            except IOError as e:
                self.main_window.statusBar.showMessage(f"Error reading labels.json: {e}")
        else:
            self.main_window.statusBar.showMessage("No labels.json found. Starting with empty labels.")

    def save_labels_to_json(self):
        if not self.dataset_folder:
            return

        labels_filepath = os.path.join(self.dataset_folder, "labels.json")
        try:
            with open(labels_filepath, 'w') as f:
                json.dump(self.labels, f, indent=4)
            self.main_window.statusBar.showMessage(f"Labels saved to labels.json")
        except IOError as e:
            self.main_window.statusBar.showMessage(f"Error saving labels to labels.json: {e}")

    def add_label(self, label_name, label_id):
        new_label = {'id': label_id, 'name': label_name}
        self.labels.append(new_label)
        item = QListWidgetItem(label_name)
        item.setData(Qt.ItemDataRole.UserRole, label_id)
        self.main_window.label_list_widget.addItem(item)
        self.main_window.label_list_widget.setCurrentItem(item)
        self.save_labels_to_json()
        self.main_window.statusBar.showMessage(f"Label '{label_name}' added.")

    def edit_label(self, label_id, new_label_name, current_item):
        for label in self.labels:
            if label['id'] == label_id:
                label['name'] = new_label_name
                break
        current_item.setText(new_label_name)
        self.save_labels_to_json()
        self.main_window.statusBar.showMessage(f"Label updated to '{new_label_name}'.")

    def delete_label(self, label_id_to_delete, label_name_to_delete, current_item):
        self.labels = [label for label in self.labels if label['id'] != label_id_to_delete]
        row = self.main_window.label_list_widget.row(current_item)
        self.main_window.label_list_widget.takeItem(row)
        
        if self.current_label_id == label_id_to_delete:
            self.current_label_id = -1
            if self.labels:
                self.main_window.label_list_widget.setCurrentRow(0)
                self.current_label_id = self.labels[0]['id']

        self.save_labels_to_json()
        self.main_window.statusBar.showMessage(f"Label '{label_name_to_delete}' deleted.")

    def save_labels(self):
        current_item = self.main_window.left_panel_list.currentItem()
        if not current_item:
            self.main_window.statusBar.showMessage("No image selected to save labels.")
            return

        widget = self.main_window.left_panel_list.itemWidget(current_item)
        if not widget or not hasattr(widget, 'image_path'):
            self.main_window.statusBar.showMessage("Could not get image path.")
            return

        image_path = widget.image_path
        image_filename = os.path.basename(image_path)
        base_name, _ = os.path.splitext(image_filename)
        label_filename = base_name + ".txt"
        label_filepath = os.path.join(self.dataset_folder, label_filename)

        bounding_boxes = self.image_bounding_boxes.get(image_path, [])
        
        if not bounding_boxes:
            self.main_window.statusBar.showMessage("No bounding boxes to save for this image.")
            if os.path.exists(label_filepath):
                try:
                    os.remove(label_filepath)
                    self.main_window.statusBar.showMessage(f"Removed empty label file: {label_filename}")
                    self._update_image_list_item_labelled_status(image_path, False)
                except OSError as e:
                    self.main_window.statusBar.showMessage(f"Error removing file {label_filename}: {e}")
            return

        original_width = self.main_window.canvas_label.original_width
        original_height = self.main_window.canvas_label.original_height

        if original_width is None or original_height is None or original_width == 0 or original_height == 0:
            self.main_window.statusBar.showMessage("Error: Original image dimensions not available for normalization.")
            return

        try:
            with open(label_filepath, 'w') as f:
                for class_id, rect in bounding_boxes:
                    if rect.width() <= 0 or rect.height() <= 0:
                        continue

                    center_x = (rect.x() + rect.width() / 2) / original_width
                    center_y = (rect.y() + rect.height() / 2) / original_height
                    width = rect.width() / original_width
                    height = rect.height() / original_height

                    f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
            
            self.main_window.statusBar.showMessage(f"Labels saved to {label_filename}")
            self._update_image_list_item_labelled_status(image_path, True)
        except IOError as e:
            self.main_window.statusBar.showMessage(f"Error saving labels to {label_filename}: {e}")
        except Exception as e:
            self.main_window.statusBar.showMessage(f"An unexpected error occurred: {e}")

    def clear_labels(self):
        if self.current_image_path and self.current_image_path in self.image_bounding_boxes:
            self.image_bounding_boxes[self.current_image_path] = []
            self.main_window.canvas_label.clear_bounding_boxes()
            self.main_window.statusBar.showMessage("Bounding boxes cleared for current image.")
            self._update_image_list_item_labelled_status(self.current_image_path, False)
        else:
            self.main_window.statusBar.showMessage("No image selected or no bounding boxes to clear.")

    def on_label_selected(self, current_item, previous_item):
        """Handles selection changes in the label list widget."""
        if current_item:
            label_id = current_item.data(Qt.ItemDataRole.UserRole)
            if label_id is not None:
                self.current_label_id = label_id
                # Update the canvas widget to know which label is currently selected for annotation
                self.main_window.ui_manager.main_window.canvas_label.set_current_class_id(label_id)
                self.main_window.statusBar.showMessage(f"Selected label: {current_item.text()}")
            else:
                self.current_label_id = -1
                self.main_window.ui_manager.main_window.canvas_label.set_current_class_id(-1)
                self.main_window.statusBar.showMessage("No label ID found for selected item.")
        else:
            self.current_label_id = -1
            self.main_window.ui_manager.main_window.canvas_label.set_current_class_id(-1)
            self.main_window.statusBar.showMessage("No label selected.")

    def _update_image_list_item_labelled_status(self, image_path: str, is_labelled: bool):
        for i in range(self.main_window.left_panel_list.count()):
            item = self.main_window.left_panel_list.item(i)
            widget = self.main_window.left_panel_list.itemWidget(item)
            if isinstance(widget, ImageListItemWidget) and widget.image_path == image_path:
                widget.set_labelled_status(is_labelled)
                break

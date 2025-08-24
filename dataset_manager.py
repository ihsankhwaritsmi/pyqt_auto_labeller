import os
import json
from ultralytics import YOLO
from PyQt6.QtCore import Qt, QDir, QSize, pyqtSignal, QRectF, QObject
from PyQt6.QtGui import QPixmap, QImageReader, QColor # Import QColor
from PyQt6.QtWidgets import QFileDialog, QListWidgetItem, QInputDialog, QLineEdit, QApplication, QMessageBox

from widgets import ImageListItemWidget
from canvas_widget import ZoomPanLabel

class DatasetManager(QObject):
    labels_updated = pyqtSignal(list) # New signal to emit when labels are updated
    current_image_has_bounding_boxes = pyqtSignal(bool) # Signal to indicate if current image has bounding boxes
    
    def __init__(self, main_window):
        super().__init__() # Call the parent class's __init__ method
        self.main_window = main_window
        self.dataset_folder = None
        self.image_files = []
        self.image_visibility = {} # {image_path: True/False (based on filter and manual toggle)}
        self.image_labelled_status = {} # {image_path: True/False (based on label file existence)}
        self.image_bounding_boxes = {} # {image_path: [(class_id, QRectF), ...]}
        self.current_image_path = None
        self.labels = [] # [{'id': 0, 'name': 'label1', 'color': '#RRGGBB'}, ...]
        self.current_label_id = -1
        self.label_colors = {} # {label_id: QColor}
        self.has_unsaved_changes = False # New flag to track unsaved changes
        self.current_filter = "All" # Default filter
        self.yolo_model = None

    def auto_label_image(self):
        if not self.current_image_path:
            self.main_window.statusBar.showMessage("No image selected for auto-labeling.")
            return

        if not hasattr(self, 'yolo_model_path') or not self.yolo_model_path:
            self.main_window.statusBar.showMessage("Please import a YOLO model first.")
            return

        try:
            if self.yolo_model is None:
                self.yolo_model = YOLO(self.yolo_model_path)
            
            results = self.yolo_model(self.current_image_path)
            
            new_boxes = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0]
                    conf = box.conf[0]
                    class_id = int(box.cls[0])
                    if conf > 0.5: # Confidence threshold
                        w = x2 - x1
                        h = y2 - y1
                        new_boxes.append((class_id, QRectF(float(x1), float(y1), float(w), float(h))))
            
            self.image_bounding_boxes[self.current_image_path].extend(new_boxes)
            self.main_window.canvas_label.set_bounding_boxes(self.image_bounding_boxes[self.current_image_path])
            self.set_unsaved_changes()
            self.main_window.statusBar.showMessage(f"Auto-labeling complete. Found {len(new_boxes)} new boxes.")

        except Exception as e:
            self.main_window.statusBar.showMessage(f"Error during auto-labeling: {e}")

    def set_unsaved_changes(self):
        self.has_unsaved_changes = True
        self.main_window.statusBar.showMessage("Unsaved changes detected.")

    def load_dataset(self):
        folder_path = QFileDialog.getExistingDirectory(self.main_window, "Select Dataset Folder")
        if folder_path:
            self.dataset_folder = folder_path
            self.main_window.show_loading_cursor()
            try:
                self.populate_image_list()
                self.load_labels_from_json()
                self.main_window.statusBar.showMessage(f"Dataset loaded: {os.path.basename(folder_path)}")
            finally:
                self.main_window.hide_loading_cursor()
        else:
            self.main_window.statusBar.showMessage("Dataset loading cancelled")

    def populate_image_list(self):
        if not self.dataset_folder:
            return

        self.image_files = []
        self.image_visibility = {}
        self.image_labelled_status = {}
        self.image_bounding_boxes = {}
        self.labels = []
        self.current_label_id = -1
        self.main_window.left_panel_list.clear()
        self.main_window.label_list_widget.clear()
        self.has_unsaved_changes = False # Reset on new dataset load
        self.current_filter = "All" # Reset filter on new dataset load
        self.main_window.filter_combobox.setCurrentText("All") # Reset combobox

        supported_extensions = QImageReader.supportedImageFormats()
        supported_extensions = [ext.data().decode('ascii') for ext in supported_extensions]

        for filename in os.listdir(self.dataset_folder):
            file_path = os.path.join(self.dataset_folder, filename)
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
                if file_ext in supported_extensions:
                    self.image_files.append(file_path)
                    self.image_visibility[file_path] = True # Initially all are visible
                    self.image_bounding_boxes[file_path] = []

                    label_filename = os.path.splitext(os.path.basename(file_path))[0] + ".txt"
                    label_filepath = os.path.join(self.dataset_folder, label_filename)
                    is_labelled = os.path.exists(label_filepath) and os.path.getsize(label_filepath) > 0
                    self.image_labelled_status[file_path] = is_labelled # Store labelled status
        
        # After populating image_files and their statuses, apply the initial filter
        self.apply_filter(0) # Apply "All" filter initially (index 0)

        if not self.image_files:
            self.main_window.statusBar.showMessage("No images found in the selected folder.")
        # The first image will be displayed by apply_filter

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
        self.main_window.canvas_label.fit_to_width() # Fit image to width after setting pixmap
        self.current_image_path = image_path
        self.main_window.statusBar.showMessage(f"Image dimensions: {self.main_window.canvas_label.original_width}x{self.main_window.canvas_label.original_height}")
        self.has_unsaved_changes = False # No unsaved changes after loading a new image

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
        self.current_image_has_bounding_boxes.emit(bool(loaded_boxes)) # Emit signal based on loaded boxes

    def import_yolo_model(self):
        """Opens a file dialog to select a YOLO model file (.pt)."""
        model_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Select YOLO Model",
            "", # Start directory
            "YOLO Models (*.pt)"
        )
        if model_path:
            self.yolo_model_path = model_path
            self.main_window.statusBar.showMessage(f"YOLO model loaded: {os.path.basename(model_path)}")
            # Optionally, load the model here or lazily when auto_label_image is called
            # For now, just store the path
        else:
            self.main_window.statusBar.showMessage("YOLO model selection cancelled.")

    def on_image_list_item_changed(self, current_item, previous_item):
        # Always update the bounding boxes from the canvas to the internal dictionary before any checks or saves
        if self.current_image_path:
            self.image_bounding_boxes[self.current_image_path] = self.main_window.canvas_label.get_bounding_boxes()

        # It's possible for list items to be deleted (e.g., by a filter change) while a modal dialog is open.
        # We must check if the items are still valid before using them.
        if previous_item and not previous_item.listWidget():
            previous_item = None # It has been deleted.

        if self.has_unsaved_changes and self.current_image_path:
            reply = QMessageBox.warning(
                self.main_window,
                "Unsaved Changes",
                f"Labels for '{os.path.basename(self.current_image_path)}' have not been saved. Do you want to save them?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                # Save labels for the image that had unsaved changes.
                self.save_labels_for_path(self.current_image_path)
                # After saving, the list may have been rebuilt by a filter update.
                # The original current_item is now invalid, so we must exit this
                # handler. A new currentItemChanged signal will be emitted for the
                # new selection in the list, which will be handled correctly.
                return
            elif reply == QMessageBox.StandardButton.Discard:
                self.has_unsaved_changes = False # Discard changes
            elif reply == QMessageBox.StandardButton.Cancel:
                # Revert to previous item if user cancels, but only if it's still valid.
                # We also need to block signals to prevent an infinite loop.
                if previous_item:
                    self.main_window.left_panel_list.blockSignals(True)
                    self.main_window.left_panel_list.setCurrentItem(previous_item)
                    self.main_window.left_panel_list.blockSignals(False)
                return
            # If discard, just proceed without saving

        # After the dialog, the current_item might also be invalid.
        if current_item and not current_item.listWidget():
            current_item = None # It has been deleted.

        if current_item:
            widget = self.main_window.left_panel_list.itemWidget(current_item)
            if widget and isinstance(widget, ImageListItemWidget):
                self.display_image(widget.image_path)
        else:
            self.main_window.canvas_label.set_pixmap(QPixmap())
            self.main_window.canvas_label.clear_bounding_boxes()
            self.current_image_path = None
            self.main_window.statusBar.showMessage("No image selected.")
        
        # The has_unsaved_changes flag is now managed by save_labels() or explicit discard.
        # No need to reset it here unconditionally.

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
                        self._assign_colors_to_labels() # Assign colors to loaded labels
                        for label in self.labels:
                            item = QListWidgetItem(label['name'])
                            item.setData(Qt.ItemDataRole.UserRole, label['id'])
                            self.main_window.label_list_widget.addItem(item)
                        self.main_window.statusBar.showMessage(f"Labels loaded from labels.json")
                        if self.labels:
                            self.main_window.label_list_widget.setCurrentRow(0)
                            self.current_label_id = self.labels[0]['id']
                        self.labels_updated.emit(self.labels) # Emit signal after loading labels
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

    def _generate_random_color(self):
        # Generate a random color that is not too dark or too light
        r = 0
        g = 0
        b = 0
        while (r + g + b < 300) or (r + g + b > 600): # Ensure reasonable brightness
            r = QColor.fromHsv(QApplication.instance().rng.randint(0, 359), 200, 200).red()
            g = QColor.fromHsv(QApplication.instance().rng.randint(0, 359), 200, 200).green()
            b = QColor.fromHsv(QApplication.instance().rng.randint(0, 359), 200, 200).blue()
        return QColor(r, g, b).name() # Return hex string

    def _assign_colors_to_labels(self):
        self.label_colors = {}
        for label in self.labels:
            if 'color' not in label:
                label['color'] = self._generate_random_color()
            self.label_colors[label['id']] = QColor(label['color'])
        self.labels_updated.emit(self.labels) # Emit signal after assigning colors

    def add_label(self, label_name, label_id):
        color = self._generate_random_color()
        new_label = {'id': label_id, 'name': label_name, 'color': color}
        self.labels.append(new_label)
        self.label_colors[label_id] = QColor(color) # Store QColor object
        item = QListWidgetItem(label_name)
        item.setData(Qt.ItemDataRole.UserRole, label_id)
        self.main_window.label_list_widget.addItem(item)
        self.main_window.label_list_widget.setCurrentItem(item)
        self.save_labels_to_json()
        self.labels_updated.emit(self.labels) # Emit signal after adding a label
        self.main_window.statusBar.showMessage(f"Label '{label_name}' added with color {color}.")

    def edit_label(self, label_id, new_label_name, current_item):
        for label in self.labels:
            if label['id'] == label_id:
                label['name'] = new_label_name
                break
        current_item.setText(new_label_name)
        self.save_labels_to_json()
        self.labels_updated.emit(self.labels) # Emit signal after editing a label
        self.main_window.statusBar.showMessage(f"Label updated to '{new_label_name}'.")
        # No need to update color here, as only name is changed

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
        self.labels_updated.emit(self.labels) # Emit signal after deleting a label
        self.main_window.statusBar.showMessage(f"Label '{label_name_to_delete}' deleted.")

    def save_labels(self):
        """Saves labels for the currently displayed image."""
        if not self.current_image_path:
            self.main_window.statusBar.showMessage("No image selected to save labels.")
            return
        self.save_labels_for_path(self.current_image_path)

    def save_labels_for_path(self, image_path: str):
        """Saves labels for a specific image path."""
        if not self.dataset_folder:
            self.main_window.statusBar.showMessage("No dataset folder loaded.")
            return

        self.main_window.show_loading_cursor()
        try:
            image_filename = os.path.basename(image_path)
            base_name, _ = os.path.splitext(image_filename)
            label_filename = base_name + ".txt"
            label_filepath = os.path.join(self.dataset_folder, label_filename)

            bounding_boxes = self.image_bounding_boxes.get(image_path, [])
            
            if not bounding_boxes:
                self.main_window.statusBar.showMessage(f"No bounding boxes to save for {os.path.basename(image_path)}.")
                if os.path.exists(label_filepath):
                    try:
                        os.remove(label_filepath)
                        self.main_window.statusBar.showMessage(f"Removed empty label file: {label_filename}")
                        self._update_image_list_item_labelled_status(image_path, False)
                    except OSError as e:
                        self.main_window.statusBar.showMessage(f"Error removing file {label_filename}: {e}")
                self.has_unsaved_changes = False # No boxes, so no unsaved changes
                self.current_image_has_bounding_boxes.emit(False) # No bounding boxes after saving
                return

            # Need to get original dimensions for the image being saved, not necessarily the currently displayed one
            # This assumes original_width/height are properties of the image itself, not just the canvas
            # For now, we'll use the canvas's dimensions, but this might need refinement if images have different sizes
            original_width = self.main_window.canvas_label.original_width
            original_height = self.main_window.canvas_label.original_height

            # If the image being saved is not the current one, we might not have its dimensions readily available
            # A more robust solution would store dimensions per image in image_bounding_boxes or a separate dict
            if image_path != self.current_image_path or original_width is None or original_height is None or original_width == 0 or original_height == 0:
                # Attempt to load dimensions if not current image or dimensions are missing
                temp_pixmap = QPixmap(image_path)
                if not temp_pixmap.isNull():
                    original_width = temp_pixmap.width()
                    original_height = temp_pixmap.height()
                else:
                    self.main_window.statusBar.showMessage(f"Error: Could not get original image dimensions for {os.path.basename(image_path)} for normalization.")
                    return


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
            self.has_unsaved_changes = False # Labels are now saved
        except IOError as e:
            self.main_window.statusBar.showMessage(f"Error saving labels to {label_filename}: {e}")
        except Exception as e:
            self.main_window.statusBar.showMessage(f"An unexpected error occurred: {e}")
        finally:
            self.main_window.hide_loading_cursor()

    def clear_labels(self):
        if self.current_image_path and self.current_image_path in self.image_bounding_boxes:
            self.image_bounding_boxes[self.current_image_path] = []
            self.main_window.canvas_label.clear_bounding_boxes()
            self.main_window.statusBar.showMessage("Bounding boxes cleared for current image.")
            self.current_image_has_bounding_boxes.emit(False) # No bounding boxes after clearing
            
            self.main_window.show_loading_cursor()
            try:
                # Also delete the corresponding label file
                image_filename = os.path.basename(self.current_image_path)
                base_name, _ = os.path.splitext(image_filename)
                label_filename = base_name + ".txt"
                label_filepath = os.path.join(self.dataset_folder, label_filename)
                if os.path.exists(label_filepath):
                    try:
                        os.remove(label_filepath)
                        self.main_window.statusBar.showMessage(f"Removed label file: {label_filename}")
                        self.has_unsaved_changes = False # No unsaved changes after deleting the file
                    except OSError as e:
                        self.main_window.statusBar.showMessage(f"Error removing label file {label_filename}: {e}")
                        self.has_unsaved_changes = True # If deletion failed, still consider it as having unsaved changes (e.g., if user wants to retry saving)
                else:
                    self.has_unsaved_changes = False # No label file existed, so no unsaved changes after clearing

                self._update_image_list_item_labelled_status(self.current_image_path, False)
            finally:
                self.main_window.hide_loading_cursor()
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
        self.image_labelled_status[image_path] = is_labelled # Update internal status
        for i in range(self.main_window.left_panel_list.count()):
            item = self.main_window.left_panel_list.item(i)
            widget = self.main_window.left_panel_list.itemWidget(item)
            if isinstance(widget, ImageListItemWidget) and widget.image_path == image_path:
                widget.set_labelled_status(is_labelled)
                break
        
        # Re-apply the current filter to update the list display
        filter_index = self.main_window.filter_combobox.findText(self.current_filter)
        if filter_index != -1:
            self.apply_filter(filter_index)

    def apply_filter(self, index: int):
        """Applies a filter to the image list based on the selected index."""
        if not self.dataset_folder:
            return

        filter_type = self.main_window.filter_combobox.itemText(index)
        self.current_filter = filter_type
        
        # Disconnect signal to prevent issues during list clearing and repopulation
        self.main_window.left_panel_list.currentItemChanged.disconnect(self.on_image_list_item_changed)
        self.main_window.left_panel_list.clear()
        
        filtered_image_paths = []
        for image_path in self.image_files:
            should_be_visible = False
            if filter_type == "All":
                should_be_visible = True
            elif filter_type == "Labelled":
                should_be_visible = self.image_labelled_status.get(image_path, False)
            elif filter_type == "Unlabelled":
                should_be_visible = not self.image_labelled_status.get(image_path, False)
            
            self.image_visibility[image_path] = should_be_visible

            if should_be_visible:
                filtered_image_paths.append(image_path)
                list_item_widget = ImageListItemWidget(image_path)
                list_item_widget.visibility_changed.connect(self.on_visibility_changed)
                list_item_widget.set_labelled_status(self.image_labelled_status.get(image_path, False))

                list_item = QListWidgetItem(self.main_window.left_panel_list)
                list_item.setSizeHint(list_item_widget.sizeHint())
                self.main_window.left_panel_list.setItemWidget(list_item, list_item_widget)
        
        if not filtered_image_paths:
            self.main_window.statusBar.showMessage(f"No {filter_type.lower()} images found.")
            self.main_window.canvas_label.set_pixmap(QPixmap())
            self.main_window.canvas_label.clear_bounding_boxes()
            self.current_image_path = None
        else:
            # Try to maintain current selection if it's still visible
            if self.current_image_path and self.current_image_path in filtered_image_paths:
                for i in range(self.main_window.left_panel_list.count()):
                    item = self.main_window.left_panel_list.item(i)
                    widget = self.main_window.left_panel_list.itemWidget(item)
                    if isinstance(widget, ImageListItemWidget) and widget.image_path == self.current_image_path:
                        self.main_window.left_panel_list.setCurrentItem(item)
                        self.display_image(self.current_image_path)
                        break
                else: # If current image not found in new list, select the first one
                    self.main_window.left_panel_list.setCurrentRow(0)
                    first_widget = self.main_window.left_panel_list.itemWidget(self.main_window.left_panel_list.item(0))
                    if first_widget:
                        self.display_image(first_widget.image_path)
            else: # If no current image or it's not in the filtered list, select the first one
                self.main_window.left_panel_list.setCurrentRow(0)
                first_widget = self.main_window.left_panel_list.itemWidget(self.main_window.left_panel_list.item(0))
                if first_widget:
                    self.display_image(first_widget.image_path)
                else:
                    self.main_window.canvas_label.set_pixmap(QPixmap())
                    self.main_window.canvas_label.clear_bounding_boxes()
                    self.current_image_path = None
                    self.main_window.statusBar.showMessage("No image selected after filtering.")
        
        # Reconnect the signal after the list has been repopulated
        self.main_window.left_panel_list.currentItemChanged.connect(self.on_image_list_item_changed)

        self.main_window.statusBar.showMessage(f"Filter applied: {filter_type}. Displaying {len(filtered_image_paths)} images.")

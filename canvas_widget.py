from PyQt6.QtWidgets import QLabel, QWidget, QMenu, QInputDialog # Import QMenu and QInputDialog
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, QEvent, QPointF, QRectF, QSizeF, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QTransform, QAction, QColor # Import QAction and QColor

class ZoomPanLabel(QLabel):
    label_needed_signal = pyqtSignal(str) # New signal to request status bar message, defined as class attribute
    bounding_box_added = pyqtSignal() # New signal to indicate a bounding box has been added

    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap = None
        self.current_pixmap_scaled = None
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.is_panning = False
        self.space_pressed = False # Added flag for spacebar state
        self.last_pan_pos = QPoint()
        self.current_mode = "select" # Default mode
        self.drawing_box = False
        self.start_point = QPointF() # Change to QPointF
        self.current_rect = QRectF() # Change to QRectF for image coordinates
        self.bounding_boxes = [] # List to store bounding boxes: [(class_id, QRectF), ...]
        self.current_class_id = -1 # New: Store the currently selected class ID for new boxes
        self.original_width = None
        self.original_height = None
        self.mouse_pos = QPoint(0, 0) # To store current mouse position for ruler lines
        
        self.history = [] # Stores states of bounding_boxes for undo/redo
        self.history_index = -1 # Current position in history
        self._save_history_state() # Save initial empty state

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.selected_box_index = -1 # New: Store the index of the currently selected bounding box
        self.labels_map = {} # New: Store class_id to {'name': '...', 'color': '...'} mapping
        self.label_colors_map = {} # New: Store class_id to QColor mapping
        self.bounding_boxes_visible = True # New: Flag to control bounding box visibility

    def _save_history_state(self):
        # Clear any redo history if a new action is performed
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        # Save a deep copy of the current bounding boxes
        self.history.append([box for box in self.bounding_boxes])
        self.history_index = len(self.history) - 1
        # Limit history size to prevent excessive memory usage
        if len(self.history) > 100: # Keep last 100 states
            self.history.pop(0)
            self.history_index -= 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.bounding_boxes = [box for box in self.history[self.history_index]]
            self.update_display()
            self.label_needed_signal.emit("Undo last annotation.")
        else:
            self.label_needed_signal.emit("Nothing to undo.")

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.bounding_boxes = [box for box in self.history[self.history_index]]
            self.update_display()
            self.label_needed_signal.emit("Redo last annotation.")
        else:
            self.label_needed_signal.emit("Nothing to redo.")

    def widget_to_image_coords(self, point: QPointF) -> QPointF:
        if self.zoom_level == 0:
            return QPointF(0, 0)
        # Adjust for pan offset first, then scale
        return (point - QPointF(self.pan_offset)) / self.zoom_level

    def image_to_widget_coords(self, point: QPointF) -> QPointF:
        # Scale first, then adjust for pan offset
        return point * self.zoom_level + QPointF(self.pan_offset)

    def rect_to_image_coords(self, rect: QRect) -> QRectF:
        top_left_image = self.widget_to_image_coords(QPointF(rect.topLeft()))
        bottom_right_image = self.widget_to_image_coords(QPointF(rect.bottomRight()))
        return QRectF(top_left_image, bottom_right_image)

    def rect_to_widget_coords(self, rect: QRectF) -> QRect:
        top_left_widget = self.image_to_widget_coords(rect.topLeft())
        bottom_right_widget = self.image_to_widget_coords(rect.bottomRight())
        return QRect(top_left_widget.toPoint(), bottom_right_widget.toPoint())

    def set_mode(self, mode):
        self.current_mode = mode
        if mode == "annotate":
            self.setCursor(Qt.CursorShape.CrossCursor)
        else: # select mode or other modes
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def update_cursor(self):
        if self.is_panning:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif self.space_pressed:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif self.current_mode == "annotate" and self.drawing_box:
            self.setCursor(Qt.CursorShape.CrossCursor) # Keep crosshair while drawing
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_pixmap(self, pixmap):
        self.original_pixmap = pixmap
        self.original_width = pixmap.width()
        self.original_height = pixmap.height()
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.update_display()

    def update_display(self):
        # This method just triggers a repaint. The actual drawing is in paintEvent.
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self.original_pixmap is None:
            # Draw default text if no pixmap is loaded
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Canvas Area")
            painter.end()
            return

        # Calculate the scaled pixmap
        transform = QTransform()
        transform.scale(self.zoom_level, self.zoom_level)
        self.current_pixmap_scaled = self.original_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)

        # Calculate the drawing rectangle considering pan offset
        scaled_width = self.current_pixmap_scaled.width()
        scaled_height = self.current_pixmap_scaled.height()

        # The drawing rectangle is the scaled pixmap's dimensions, offset by pan_offset
        draw_rect = QRect(self.pan_offset.x(), self.pan_offset.y(), scaled_width, scaled_height)
        
        # Draw the scaled pixmap onto the label
        painter.drawPixmap(draw_rect, self.current_pixmap_scaled)

        # Draw bounding boxes only if visible
        if self.bounding_boxes_visible and self.bounding_boxes:
            for i, (class_id, rect_image_coords) in enumerate(self.bounding_boxes):
                box_color = self.label_colors_map.get(class_id, Qt.GlobalColor.green) # Default to green if color not found
                
                if i == self.selected_box_index:
                    # For selected box, use a slightly different color or thicker pen
                    pen = painter.pen()
                    pen.setColor(Qt.GlobalColor.red) # Red for selected
                    pen.setWidth(2)
                    painter.setPen(pen)
                else:
                    pen = painter.pen()
                    pen.setColor(box_color)
                    pen.setWidth(1)
                    painter.setPen(pen)
                
                painter.setBrush(Qt.BrushStyle.NoBrush)
                rect_widget_coords = self.rect_to_widget_coords(rect_image_coords)
                painter.drawRect(rect_widget_coords)


        # Draw current rectangle being drawn only in annotate mode
        if self.current_mode == "annotate" and self.drawing_box:
            # Use the color of the currently selected label for the drawing box
            draw_box_color = self.label_colors_map.get(self.current_class_id, Qt.GlobalColor.red)
            pen = painter.pen()
            pen.setColor(draw_box_color)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush) # No fill
            painter.drawRect(self.rect_to_widget_coords(self.current_rect))

        # Draw ruler lines if in annotate mode and mouse is over the canvas
        if self.current_mode == "annotate" and self.original_pixmap is not None:
            pen = painter.pen()
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setColor(Qt.GlobalColor.white)
            painter.setPen(pen)
            # Horizontal line
            painter.drawLine(0, self.mouse_pos.y(), self.width(), self.mouse_pos.y())
            # Vertical line
            painter.drawLine(self.mouse_pos.x(), 0, self.mouse_pos.x(), self.height())
        
        painter.end()

    def wheelEvent(self, event):
        if self.original_pixmap is None:
            super().wheelEvent(event)
            return
            
        # If in annotation mode and drawing, do not allow zoom/pan
        if self.current_mode == "annotate" and self.drawing_box:
            return

        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        # Get mouse position relative to the widget
        mouse_pos = event.position()

        if event.angleDelta().y() > 0: # Zoom in
            new_zoom_level = self.zoom_level * zoom_in_factor
        else: # Zoom out
            new_zoom_level = self.zoom_level * zoom_out_factor

        min_zoom = 0.1
        max_zoom = 10.0
        new_zoom_level = max(min_zoom, min(max_zoom, new_zoom_level))

        if new_zoom_level == self.zoom_level:
            return

        # Calculate the new pan offset to keep the zoom centered on the cursor
        # Formula: new_pan = mouse_pos - (mouse_pos - current_pan) * (new_zoom / current_zoom)
        delta_zoom_factor = new_zoom_level / self.zoom_level

        # Calculate the new pan offset
        # The mouse position relative to the current pan offset
        mouse_relative_to_pan = mouse_pos - QPointF(self.pan_offset)
        
        # Adjust the pan offset based on the zoom delta and mouse position
        self.pan_offset.setX(int(self.pan_offset.x() + mouse_relative_to_pan.x() * (1 - delta_zoom_factor)))
        self.pan_offset.setY(int(self.pan_offset.y() + mouse_relative_to_pan.y() * (1 - delta_zoom_factor)))

        self.zoom_level = new_zoom_level
        self.update_display()

    def _get_bounding_box_at_pos(self, pos: QPoint) -> int:
        """Returns the index of the bounding box at the given widget position, or -1 if none."""
        for i, (class_id, rect_image_coords) in enumerate(self.bounding_boxes):
            rect_widget_coords = self.rect_to_widget_coords(rect_image_coords)
            if rect_widget_coords.contains(pos):
                return i
        return -1

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.current_mode == "annotate" and self.space_pressed:
                self.is_panning = True # Enable panning in annotate mode with spacebar + left click
                self.last_pan_pos = event.pos()
            elif self.current_mode == "annotate" and not self.space_pressed:
                self.drawing_box = True
                self.start_point = self.widget_to_image_coords(event.position()) # Convert to image coordinates
                self.current_rect = QRectF(self.start_point, QSizeF()) # Initialize with start point and zero size (QRectF)
                self.update_cursor() # Update cursor to crosshair
            elif self.space_pressed: # Panning in select mode with spacebar + left click
                self.is_panning = True # Enable panning
                self.last_pan_pos = event.pos()
            elif self.current_mode == "select":
                # In select mode, left click can select a box
                self.selected_box_index = self._get_bounding_box_at_pos(event.pos())
                self.update_display() # Redraw to highlight selected box
        elif event.button() == Qt.MouseButton.RightButton and self.current_mode == "select":
            # Handle right-click for context menu in select mode
            clicked_box_index = self._get_bounding_box_at_pos(event.pos())
            if clicked_box_index != -1:
                self.selected_box_index = clicked_box_index
                self.update_display() # Highlight the box before showing menu
                self._show_context_menu(event.pos())
            else:
                self.selected_box_index = -1 # Deselect if right-clicked outside a box
                self.update_display()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.last_pan_pos = event.pos()
        super().mousePressEvent(event)

    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        edit_action = QAction("Edit Class ID", self)
        delete_action = QAction("Delete", self)

        edit_action.triggered.connect(self._edit_selected_bounding_box)
        delete_action.triggered.connect(self._delete_selected_bounding_box)

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec(self.mapToGlobal(pos))

    def _edit_selected_bounding_box(self):
        if self.selected_box_index != -1:
            current_class_id, rect = self.bounding_boxes[self.selected_box_index]
            
            # Prepare a list of existing label names for the QInputDialog
            label_names = [info['name'] for info in self.labels_map.values()]
            
            # Find the current label name
            current_label_info = self.labels_map.get(current_class_id)
            current_label_name = current_label_info['name'] if current_label_info else f"ID {current_class_id} (Unknown)"
            
            # Get the new label name from the user
            new_label_name, ok = QInputDialog.getItem(self, "Edit Class ID", "Select New Class:", label_names, 
                                                      label_names.index(current_label_name) if current_label_name in label_names else 0, 
                                                      False)
            
            if ok and new_label_name:
                # Find the class ID corresponding to the selected label name
                new_class_id = -1
                for label_id, info in self.labels_map.items():
                    if info['name'] == new_label_name:
                        new_class_id = label_id
                        break
                
                if new_class_id != -1:
                    self.bounding_boxes[self.selected_box_index] = (new_class_id, rect)
                    self._save_history_state()
                    self.update_display()
                    self.label_needed_signal.emit(f"Bounding box class ID updated to {new_label_name} (ID: {new_class_id}).")
                else:
                    self.label_needed_signal.emit(f"Error: Could not find ID for label '{new_label_name}'.")
            
            self.selected_box_index = -1 # Deselect after editing
            self.update_display()

    def _delete_selected_bounding_box(self):
        if self.selected_box_index != -1:
            del self.bounding_boxes[self.selected_box_index]
            self._save_history_state()
            self.update_display()
            self.label_needed_signal.emit("Bounding box deleted.")
            self.selected_box_index = -1 # Deselect after deleting
            self.update_display()

    def mouseMoveEvent(self, event):
        if self.is_panning:
            self.setCursor(Qt.CursorShape.DragMoveCursor) # Set grabbing cursor when dragging
            delta = event.pos() - self.last_pan_pos
            self.pan_offset += delta
            self.last_pan_pos = event.pos()
            self.update_display()
        elif self.space_pressed: # If space is pressed but not panning, show OpenHandCursor
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif self.current_mode == "annotate" and self.drawing_box:
            # Update the current rectangle being drawn, converting mouse position to image coordinates
            self.current_rect.setBottomRight(self.widget_to_image_coords(event.position()))
            self.update_display()
            self.update_cursor() # Ensure cursor stays as crosshair
        elif self.current_mode == "annotate": # If in annotate mode and not panning/drawing, show CrossCursor
            self.setCursor(Qt.CursorShape.CrossCursor)
        else: # If not panning and space is not pressed, show default cursor
            self.setCursor(Qt.CursorShape.ArrowCursor)
        
        self.mouse_pos = event.pos() # Update mouse position for ruler lines
        self.update() # Trigger repaint to draw ruler lines
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        # Reset cursor when mouse leaves the widget
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drawing_box: # If we were drawing a box
                self.drawing_box = False
                # Add the completed bounding box to the list (already in image coordinates)
                if self.current_class_id != -1: # Only add if a label is selected
                    self.bounding_boxes.append((self.current_class_id, self.current_rect.normalized())) # Use current_class_id
                    self._save_history_state() # Save state after adding a box
                    self.bounding_box_added.emit() # Emit signal that a bounding box was added
                else:
                    self.label_needed_signal.emit("Please select a label before annotating.") # Emit signal
                self.current_rect = QRectF() # Clear the current rectangle
                self.update_display()
                self.update_cursor() # Reset cursor if needed
            elif self.is_panning:
                self.is_panning = False # Stop panning on left button release
                if self.space_pressed:
                    self.setCursor(Qt.CursorShape.OpenHandCursor) # Revert to OpenHand if space is still held
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor) # Reset to Arrow if space is released
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor) # Reset cursor to default
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = True # Set flag when space is pressed
            # Capture the current mouse position relative to the widget
            self.last_pan_pos = self.mapFromGlobal(self.cursor().pos())
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.undo()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self.redo()
        self.update_cursor() # Update cursor based on new state
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = False # Clear flag when space is released
        self.update_cursor() # Update cursor based on new state
        super().keyReleaseEvent(event)

    def sizeHint(self):
        return QSize(400, 400)

    def get_bounding_boxes(self):
        return self.bounding_boxes

    def set_bounding_boxes(self, boxes):
        self.bounding_boxes = boxes
        self.update_display()

    def set_current_class_id(self, class_id: int):
        self.current_class_id = class_id

    def set_labels_map(self, labels: list):
        self.labels_map = {label['id']: {'name': label['name'], 'color': label['color']} for label in labels}
        self.label_colors_map = {label['id']: QColor(label['color']) for label in labels}
        self.update_display() # Redraw to show updated labels

    def clear_bounding_boxes(self):
        self.bounding_boxes = []
        self.update_display()

    def fit_to_width(self):
        if self.original_pixmap is None:
            return

        # Calculate zoom level to fit width
        widget_width = self.width()
        original_image_width = self.original_pixmap.width()
        
        if original_image_width > 0:
            self.zoom_level = widget_width / original_image_width
        else:
            self.zoom_level = 1.0 # Default if image width is zero

        # Center the image horizontally and vertically
        scaled_height = self.original_pixmap.height() * self.zoom_level
        self.pan_offset.setX(0)
        self.pan_offset.setY(int((self.height() - scaled_height) / 2))
        
        self.update_display()

    def toggle_bounding_box_visibility(self):
        self.bounding_boxes_visible = not self.bounding_boxes_visible
        self.update_display()

    def set_bounding_box_visibility(self, visible: bool):
        self.bounding_boxes_visible = visible
        self.update_display()

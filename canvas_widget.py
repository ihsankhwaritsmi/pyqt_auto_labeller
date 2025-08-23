from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, QEvent, QPointF, QRectF, QSizeF, pyqtSignal # Import pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QTransform

class ZoomPanLabel(QLabel):
    label_needed_signal = pyqtSignal(str) # New signal to request status bar message, defined as class attribute

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
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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

        # Draw bounding boxes
        # Always draw saved bounding boxes
        if self.bounding_boxes:
            painter.setPen(Qt.GlobalColor.green) # Green color for saved boxes
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for class_id, rect_image_coords in self.bounding_boxes:
                painter.drawRect(self.rect_to_widget_coords(rect_image_coords))

        # Draw current rectangle being drawn only in annotate mode
        if self.current_mode == "annotate" and self.drawing_box:
            painter.setPen(Qt.GlobalColor.red) # Red color for bounding box
            painter.setBrush(Qt.BrushStyle.NoBrush) # No fill
            painter.drawRect(self.rect_to_widget_coords(self.current_rect))

        # Draw ruler lines if in annotate mode and mouse is over the canvas
        if self.current_mode == "annotate" and self.original_pixmap is not None:
            painter.setPen(Qt.PenStyle.DashLine)
            painter.setPen(Qt.GlobalColor.white)
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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.current_mode == "annotate":
                if not self.space_pressed: # Only draw if not panning
                    self.drawing_box = True
                    self.start_point = self.widget_to_image_coords(event.position()) # Convert to image coordinates
                    self.current_rect = QRectF(self.start_point, QSizeF()) # Initialize with start point and zero size (QRectF)
                    self.update_cursor() # Update cursor to crosshair
            elif self.space_pressed: # If spacebar is pressed, start panning
                self.is_panning = True # Enable panning
                self.last_pan_pos = event.pos()
        elif event.button() == Qt.MouseButton.MiddleButton: # Example: Middle mouse button for panning if spacebar is not used
            # For middle button panning, we assume it works independently for now,
            # as the user only specified left-click panning with spacebar.
            self.is_panning = True
            self.last_pan_pos = event.pos()
        super().mousePressEvent(event)

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

    def clear_bounding_boxes(self):
        self.bounding_boxes = []
        self.update_display()

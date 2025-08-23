from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, QEvent, QPointF
from PyQt6.QtGui import QPixmap, QImage, QPainter, QTransform

class ZoomPanLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap = None
        self.current_pixmap_scaled = None
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.is_panning = False
        self.space_pressed = False # Added flag for spacebar state
        self.last_pan_pos = QPoint()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def update_cursor(self):
        if self.is_panning:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif self.space_pressed:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_pixmap(self, pixmap):
        self.original_pixmap = pixmap
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
        
        painter.end()

    def wheelEvent(self, event):
        if self.original_pixmap is None:
            super().wheelEvent(event)
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
            # If spacebar is pressed, start panning
            if self.space_pressed: # Check if spacebar is held
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
        else: # If not panning and space is not pressed, show default cursor
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_panning:
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

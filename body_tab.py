import random
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPixmap, QPolygonF, QColor, QBrush, QPen, QPainter
from PySide6.QtCore import Qt, QPointF, QTimer

class BodyTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)

        pixmap = QPixmap("body_silhouette.png")
        if pixmap.isNull():
            print("Warning: Could not load body_silhouette.png. Check file path!")
        scaled_pixmap = pixmap.scaled(1000, 2000, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.pixmap_item = self.scene.addPixmap(scaled_pixmap)
        self.pixmap_item.setPos(0, 0)

        self.body_parts = {}

        # Create body part polygons
        self.create_body_part("head", [
            QPointF(450, 50),
            QPointF(550, 50),
            QPointF(570, 150),
            QPointF(430, 150),
        ])

        self.create_body_part("left_arm", [
            QPointF(390, 200),
            QPointF(430, 200),
            QPointF(380, 400),
            QPointF(340, 400),
        ])

        self.create_body_part("right_arm", [
            QPointF(570, 200),
            QPointF(610, 200),
            QPointF(660, 400),
            QPointF(620, 400),
        ])

        self.create_body_part("torso", [
            QPointF(430, 150),
            QPointF(570, 150),
            QPointF(570, 600),
            QPointF(430, 600),
        ])

        self.create_body_part("left_leg", [
            QPointF(430, 600),
            QPointF(500, 600),
            QPointF(500, 900),
            QPointF(430, 900),
        ])

        self.create_body_part("right_leg", [
            QPointF(500, 600),
            QPointF(570, 600),
            QPointF(570, 900),
            QPointF(500, 900),
        ])

        self.scene.setSceneRect(0, 0, 1000, 2000)
        self.view.setRenderHints(self.view.renderHints() | QPainter.Antialiasing)

        # Set up a QTimer to update highlights in real time
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_highlights)
        self.timer.start(1000) # 1000 ms

    def create_body_part(self, part_name, points):
        """Creates and stores a polygon for a body part."""
        polygon = QPolygonF(points)
        item = self.scene.addPolygon(polygon)
        item.setPen(QPen(Qt.transparent))
        item.setBrush(QBrush(QColor(255, 0, 0, 0)))
        item.setZValue(1)
        self.body_parts[part_name] = item

    def highlight_part(self, part_name, value):
        """
        Highlights a body part in red.
        'value' should be between 0.0 (no highlight) and 1.0 (fully red).
        """
        if part_name not in self.body_parts:
            print(f"No body part named '{part_name}' found.")
            return

        # Alpha value (0-255)
        value = max(0.0, min(1.0, value))
        alpha = int(255 * value)
        color = QColor(255, 0, 0, alpha)
        self.body_parts[part_name].setBrush(QBrush(color))

    def clear_highlights(self):
        """Clears all highlights by setting the alpha to 0."""
        for part in self.body_parts.values():
            part.setBrush(QBrush(QColor(255, 0, 0, 0)))

    def update_highlights(self):
        """
        This method is called by the timer.
        In a real application, you would update highlight values based on live data.
        Here we simulate by assigning random highlight values.
        """
        # For each body part, generate a random value between 0.0 and 1.0
        # This is for just a placeholder
        for part_name in self.body_parts:
            simulated_value = random.random()
            self.highlight_part(part_name, simulated_value)

    def resizeEvent(self, event):
        """
        Override resizeEvent to ensure the view fits the pixmap.
        """
        super().resizeEvent(event)
        self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

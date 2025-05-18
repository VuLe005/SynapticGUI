import random
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PySide6.QtGui import (
    QPixmap, QPolygonF, QColor,
    QBrush, QPen, QPainter
)
from PySide6.QtCore import Qt, QPointF, QTimer, QRectF

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
        scaled = pixmap.scaled(1000, 2000, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.pixmap_item = self.scene.addPixmap(scaled)
        self.pixmap_item.setPos(0, 0)

        # container for our highlight items
        self.body_parts = {}

        # 1) HEAD as an ellipse
        head_rect = QRectF(435, 0, 130, 130)  
        head_item = self.scene.addEllipse(head_rect)
        head_item.setPen(QPen(Qt.transparent))
        head_item.setBrush(QBrush(QColor(255, 0, 0, 0)))
        head_item.setZValue(1)
        self.body_parts["head"] = head_item

        # 2) Other parts as polygons
        self.create_body_part("left_arm", [
            QPointF(390, 200), QPointF(430, 200),
            QPointF(380, 400), QPointF(340, 400),
        ])
        self.create_body_part("right_arm", [
            QPointF(570, 200), QPointF(610, 200),
            QPointF(660, 400), QPointF(620, 400),
        ])
        self.create_body_part("torso", [
            QPointF(430, 150), QPointF(570, 150),
            QPointF(570, 600), QPointF(430, 600),
        ])
        self.create_body_part("left_leg", [
            QPointF(430, 600), QPointF(500, 600),
            QPointF(500, 900), QPointF(430, 900),
        ])
        self.create_body_part("right_leg", [
            QPointF(500, 600), QPointF(570, 600),
            QPointF(570, 900), QPointF(500, 900),
        ])

        self.scene.setSceneRect(0, 0, 1000, 2000)
        self.view.setRenderHints(self.view.renderHints() | QPainter.Antialiasing)

        # timer for demo highlighting
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_highlights)
        self.timer.start(1000)

    def create_body_part(self, part_name, points):
        poly = QPolygonF(points)
        item = self.scene.addPolygon(poly)
        item.setPen(QPen(Qt.transparent))
        item.setBrush(QBrush(QColor(255, 0, 0, 0)))
        item.setZValue(1)
        self.body_parts[part_name] = item

    def highlight_part(self, part_name, value):
        if part_name not in self.body_parts:
            print(f"No body part named '{part_name}'")
            return
        value = max(0.0, min(1.0, value))
        alpha = int(255 * value)
        color = QColor(255, 0, 0, alpha)
        self.body_parts[part_name].setBrush(QBrush(color))

    def clear_highlights(self):
        for item in self.body_parts.values():
            item.setBrush(QBrush(QColor(255, 0, 0, 0)))

    def update_highlights(self):
        # random demo; replace with real data
        for part in self.body_parts:
            self.highlight_part(part, random.random())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # always keep the silhouette fully visible
        self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

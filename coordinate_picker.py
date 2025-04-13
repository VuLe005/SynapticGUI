import sys
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QMouseEvent, QPainter
from PySide6.QtCore import Qt, QPointF

class CoordinatePicker(QGraphicsView):
    def __init__(self, image_path):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            raise ValueError(f"Failed to load image: {image_path}")

        scaled_pixmap = pixmap.scaled(1000, 2000, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.pixmap_item = QGraphicsPixmapItem(scaled_pixmap)
        self.scene.addItem(self.pixmap_item)

        self.setRenderHints(self.renderHints() | self.renderHints() | QPainter.Antialiasing)
        self.setSceneRect(self.scene.itemsBoundingRect())

        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            print(f"Clicked at: ({int(scene_pos.x())}, {int(scene_pos.y())})")

def main():
    app = QApplication(sys.argv)
    picker = CoordinatePicker("body_silhouette.png")
    picker.setWindowTitle("Coordinate Picker - Click to Get (x, y)")
    picker.resize(1000, 2000)
    picker.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
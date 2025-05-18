import sys
from threading import Thread

from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QTabWidget,
    QDialog, QDialogButtonBox, QComboBox, QFormLayout, QMenu
)
from PySide6.QtCore import Qt, QPoint

from recorder import run_brainflow, stop_event
from time_series_tab import TimeSeriesTab
from network_tab import NetworkTab
from body_tab import BodyTab


class TabTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Tab Type")
        layout = QFormLayout(self)
        self.combo = QComboBox()
        self.combo.addItems(["Time Series", "BodyTab", "Network"])
        layout.addRow("Tab Type:", self.combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_tab_type(self):
        return self.combo.currentText()


class SynapticGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synaptic GUI - 3 Columns, Then Next Row")
        self.resize(1200, 800)
        self.tab_count = 0

        # root vertical splitter
        self.root_vsplitter = QSplitter(Qt.Vertical)
        self.root_vsplitter.setOpaqueResize(False)
        self.setCentralWidget(self.root_vsplitter)

        # track our horizontal “rows”
        self.rows = []
        self._create_new_row()
        self._setup_menu()

    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setFont(QFont("Arial", 14))

        file_menu = menubar.addMenu("File")
        open_act = QAction("Open", self)
        open_act.triggered.connect(self.open_new_tab)
        file_menu.addAction(open_act)

        connect_act = QAction("Connect", self)
        connect_act.triggered.connect(self.connect_action_triggered)
        menubar.addAction(connect_act)

    def _create_new_row(self):
        row = QSplitter(Qt.Horizontal)
        row.setOpaqueResize(False)
        self.rows.append(row)
        self.root_vsplitter.addWidget(row)
        self._renormalize_splitters()
        return row

    def _renormalize_splitters(self):
        # 1) Vertical: each row equal stretch
        for i in range(self.root_vsplitter.count()):
            self.root_vsplitter.setStretchFactor(i, 1)
        # 2) Horizontal: each column equal stretch within each row
        for row in self.rows:
            for j in range(row.count()):
                row.setStretchFactor(j, 1)

    def _get_last_row(self):
        if not self.rows or self._count_tabs(self.rows[-1]) >= 3:
            return self._create_new_row()
        return self.rows[-1]

    def _count_tabs(self, splitter):
        return sum(
            isinstance(splitter.widget(i), QTabWidget)
            for i in range(splitter.count())
        )

    def _make_tab_widget(self):
        tw = QTabWidget()
        tw.setMovable(True)
        tw.setMinimumWidth(50)
        bar = tw.tabBar()
        bar.setContextMenuPolicy(Qt.CustomContextMenu)
        bar.customContextMenuRequested.connect(self._show_tab_menu)
        return tw

    def open_new_tab(self):
        dlg = TabTypeDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return

        kind = dlg.get_tab_type()
        content = {
            "Time Series": TimeSeriesTab,
            "BodyTab": BodyTab,
            "Network": NetworkTab
        }[kind]()
        if kind == "BodyTab":
            content.highlight_part("head", 0.5)

        self.tab_count += 1
        title = f"{kind} {self.tab_count}"
        row = self._get_last_row()
        tw = self._make_tab_widget()
        tw.addTab(content, title)
        row.addWidget(tw)
        self._renormalize_splitters()

    def _show_tab_menu(self, pos: QPoint):
        bar = self.sender()
        idx = bar.tabAt(pos)
        if idx < 0:
            return
        self._ctx_idx = idx
        self._ctx_tw = bar.parent()
        menu = QMenu()
        undock_act = menu.addAction("Undock Tab")
        if menu.exec(bar.mapToGlobal(pos)) == undock_act:
            self.undock_tab(self._ctx_idx, self._ctx_tw)

    def undock_tab(self, idx, tw: QTabWidget):
        w = tw.widget(idx)
        tw.removeTab(idx)
        w.setParent(None)
        w.deleteLater()

        if tw.count() == 0:
            tw.setParent(None)
            tw.deleteLater()

        self._cleanup_empty_rows()
        self._renormalize_splitters()

    def _cleanup_empty_rows(self):
        for i in reversed(range(len(self.rows))):
            row = self.rows[i]
            if self._count_tabs(row) == 0:
                row.setParent(None)
                row.deleteLater()
                self.rows.pop(i)

    def connect_action_triggered(self):
        # 1) (optional) open a Time-Series tab automatically
        ts_tab = TimeSeriesTab()
        self.tab_count += 1
        name = f"Time Series {self.tab_count}"
        row = self._get_last_row()
        tw = self._make_tab_widget()
        tw.addTab(ts_tab, name)
        row.addWidget(tw)
        self._renormalize_splitters()

        # 2) clear any previous stop flag & start acquisition
        stop_event.clear()
        Thread(target=run_brainflow, daemon=True).start()


def main():
    app = QApplication(sys.argv)
    gui = SynapticGUI()
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

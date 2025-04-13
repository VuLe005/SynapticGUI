import sys
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QTabWidget,
    QDialog, QDialogButtonBox, QComboBox, QFormLayout, QMenu
)
from PySide6.QtCore import Qt, QPoint

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
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_tab_type(self):
        return self.combo.currentText()

class SynapticGUI(QMainWindow):
    """
    A main window with a vertical splitter (`root_vsplitter`).
    Each 'row' is a horizontal splitter that can hold up to 3 QTabWidgets.
    When you add a 4th tab, it creates a new horizontal splitter below the first one.
    You can drag horizontally to resize columns, and drag vertically to resize rows.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synaptic GUI - 3 Columns, Then Next Row")
        self.resize(1200, 800)
        self.tab_count = 0

        # A vertical splitter to hold multiple "rows"
        self.root_vsplitter = QSplitter(Qt.Vertical)
        self.root_vsplitter.setOpaqueResize(False)
        self.setCentralWidget(self.root_vsplitter)
        self.rows = []

        # Create the first row
        self.create_new_row()

        # Setup the menu bar
        menubar = self.menuBar()
        menubar.setFont(QFont("Arial", 14))

        file_menu = menubar.addMenu("File")
        add_action = QAction("Open", self)
        add_action.triggered.connect(self.open_new_tab)
        file_menu.addAction(add_action)

        help_menu = menubar.addMenu("Help")

        connect_action = QAction("Connect", self)
        connect_action.triggered.connect(self.connect_action_triggered)
        menubar.addAction(connect_action)

        # For storing which tab was right-clicked
        self.context_tab_index = None
        self.context_tab_widget = None


    # This is to create the row for the GRID
    def create_new_row(self):
        """
        Create a new horizontal splitter row,
        add it to the root vertical splitter, and store it in self.rows.
        """
        row_splitter = QSplitter(Qt.Horizontal)
        row_splitter.setOpaqueResize(False)
        self.rows.append(row_splitter)
        self.root_vsplitter.addWidget(row_splitter)
        return row_splitter

    def get_or_create_last_row(self):
        """
        Return the last row_splitter if it has <3 tab widgets.
        Otherwise create a new row and return that.
        """
        if not self.rows:
            return self.create_new_row()

        last_row = self.rows[-1]
        if self.count_tab_widgets_in_row(last_row) < 3:
            return last_row
        else:
            return self.create_new_row()

    def count_tab_widgets_in_row(self, row_splitter):
        """Count how many QTabWidgets are in this horizontal splitter."""
        count = 0
        for i in range(row_splitter.count()):
            w = row_splitter.widget(i)
            if isinstance(w, QTabWidget):
                count += 1
        return count


    def create_new_tab_widget(self):
        """
        Create a QTabWidget, set up the context menu, return it.
        """
        tab_widget = QTabWidget()
        tab_widget.setMovable(True)
        tab_widget.setMinimumWidth(50)  # let it shrink quite small
        # The context menu for undocking only
        tab_bar = tab_widget.tabBar()
        tab_bar.setContextMenuPolicy(Qt.CustomContextMenu)
        tab_bar.customContextMenuRequested.connect(self.show_tab_context_menu)
        return tab_widget

    def remove_empty_rows(self):
        """
        Check each row. If it has no QTabWidgets, remove it from root_vsplitter.
        """
        for i in range(len(self.rows) - 1, -1, -1):
            row = self.rows[i]
            if self.count_tab_widgets_in_row(row) == 0:
                self.rows.pop(i)
                row.setParent(None)
                row.deleteLater()

    # New tab
    def open_new_tab(self):
        dialog = TabTypeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            tab_type = dialog.get_tab_type()
            if tab_type == "Time Series":
                new_tab = TimeSeriesTab()
            elif tab_type == "BodyTab":
                new_tab = BodyTab()
            else:
                new_tab = NetworkTab()

            self.tab_count += 1
            tab_name = f"{tab_type} {self.tab_count}"

            # Decide which row to put this new tab in
            row_splitter = self.get_or_create_last_row()
            # Create a QTabWidget for this tab
            tab_widget = self.create_new_tab_widget()
            tab_widget.addTab(new_tab, tab_name)
            # Insert the tab widget into the row splitter
            row_splitter.addWidget(tab_widget)

            if tab_type == "BodyTab":
                new_tab.highlight_part("head", 0.5)


    def show_tab_context_menu(self, pos: QPoint):
        """
        Called when user right-clicks on a tab.
        """
        tab_bar = self.sender()
        tab_index = tab_bar.tabAt(pos)
        if tab_index < 0:
            return

        self.context_tab_index = tab_index
        self.context_tab_widget = tab_bar.parent()  # the QTabWidget

        menu = QMenu()
        undock_action = menu.addAction("Undock Tab")
        action = menu.exec(tab_bar.mapToGlobal(pos))

        if action == undock_action:
            self.undock_tab(self.context_tab_index, self.context_tab_widget)

    def undock_tab(self, index, tab_widget):
        """
        Remove the specified tab from the QTabWidget and open it in a floating window.
        """
        widget = tab_widget.widget(index)
        tab_name = tab_widget.tabText(index)
        tab_widget.removeTab(index)

        undocked_window = QMainWindow()
        undocked_window.setWindowTitle(f"Undocked: {tab_name}")
        undocked_window.setCentralWidget(widget)
        undocked_window.resize(800, 600)
        undocked_window.show()

        self.remove_empty_rows()

    # Connection to unicorn?
    def connect_action_triggered(self):
        pass

def main():
    app = QApplication(sys.argv)
    gui = SynapticGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

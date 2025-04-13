import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class ChannelRow(QWidget):
    def __init__(self, channel_index, parent=None):
        super().__init__(parent)
        self.channel_index = channel_index
        self.amp_multiplier = 0.0
        self.x_data = []
        self.y_data = []
        self.time_counter = 0

        # Horizontal layout for the row
        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(5, 5, 5, 5)
        row_layout.setSpacing(5)

        # + button
        self.plus_button = QPushButton("+")
        self.plus_button.clicked.connect(self.handle_plus)
        row_layout.addWidget(self.plus_button)

        # - button
        self.minus_button = QPushButton("-")
        self.minus_button.clicked.connect(self.handle_minus)
        row_layout.addWidget(self.minus_button)

        # Channel label
        self.label = QLabel(f"Channel {channel_index}")
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        row_layout.addWidget(self.label)

        # Create a matplotlib figure
        self.figure = Figure()
        self.figure.set_tight_layout(True)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_ylim(0, 10)
        self.ax.set_xlim(0, 50)

        # Wrap the canvas in a frame
        self.plot_frame = QFrame()
        self.plot_frame.setObjectName("PlotFrame")
        # We fix the height so the plot doesn't grow/shrink vertically
        self.plot_frame.setFixedHeight(200)

        plot_layout = QVBoxLayout(self.plot_frame)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.canvas)

        # Let it expand horizontally, but fix vertical
        self.plot_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_layout.addWidget(self.plot_frame)

    def handle_plus(self):
        self.amp_multiplier += 0.5
        print(f"Channel {self.channel_index} amplitude increased to {self.amp_multiplier}")

    def handle_minus(self):
        self.amp_multiplier -= 0.5
        print(f"Channel {self.channel_index} amplitude decreased to {self.amp_multiplier}")

    def update_data(self, global_time):
        # For now, random data
        self.time_counter += 1
        sample = random.random() * 10
        amplitude = (2 ** self.amp_multiplier) * sample
        self.x_data.append(global_time)
        self.y_data.append(amplitude)
        if len(self.x_data) > 50:
            self.x_data = self.x_data[-50:]
            self.y_data = self.y_data[-50:]

    def redraw(self):
        self.ax.clear()
        self.ax.plot(self.x_data, self.y_data, color="blue")
        self.ax.set_ylim(0, 40)
        if self.x_data:
            self.ax.set_xlim(left=max(0, self.x_data[-1] - 50), right=self.x_data[-1])
        self.canvas.draw()


class TimeSeriesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.streaming = False
        self.global_time = 0

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Top control panel ---
        top_panel = QWidget()
        top_panel_layout = QHBoxLayout(top_panel)
        top_panel_layout.setContentsMargins(5, 5, 5, 5)
        top_panel_layout.setSpacing(10)

        stream_label = QLabel("Stream")
        stream_label.setAlignment(Qt.AlignCenter)
        top_panel_layout.addWidget(stream_label)

        self.start_button = QPushButton("Start Streaming")
        self.start_button.clicked.connect(self.on_start_stream)
        top_panel_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Streaming")
        self.stop_button.clicked.connect(self.on_stop_stream)
        top_panel_layout.addWidget(self.stop_button)

        self.add_channel_button = QPushButton("Add Channel")
        self.add_channel_button.clicked.connect(self.on_add_channel)
        top_panel_layout.addWidget(self.add_channel_button)

        self.remove_channel_button = QPushButton("Remove Channel")
        self.remove_channel_button.clicked.connect(self.on_remove_channel)
        top_panel_layout.addWidget(self.remove_channel_button)

        top_panel_layout.addStretch()
        main_layout.addWidget(top_panel, stretch=0)

        # --- Scroll area for channel rows ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(5)

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area, stretch=1)

        self.channel_rows = []
        for i in range(1, 9):
            self.add_channel_row(i)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(100)  # update every 100 ms

        # --- Stylesheet ---
        self.setStyleSheet("""
            TimeSeriesTab, QWidget {
                background-color: #A3541F;
            }
            QLabel {
                color: white;
                font-size: 16pt;
            }
            QPushButton {
                background-color: #803F17;
                color: white;
                font-size: 14pt;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #A3541F;
            }
            QPushButton:pressed {
                background-color: #C36520;
            }
            QFrame#PlotFrame {
                background-color: white;
            }
        """)

    def add_channel_row(self, index):
        row = ChannelRow(index, parent=self.scroll_content)
        self.channel_rows.append(row)
        self.scroll_layout.addWidget(row)

    def remove_channel_row(self):
        if self.channel_rows:
            row = self.channel_rows.pop()
            row.setParent(None)
            row.deleteLater()

    def on_add_channel(self):
        new_index = len(self.channel_rows) + 1
        self.add_channel_row(new_index)

    def on_remove_channel(self):
        self.remove_channel_row()

    def on_start_stream(self):
        self.streaming = True
        print("Started streaming")

    def on_stop_stream(self):
        self.streaming = False
        print("Stopped streaming")

    def update_plots(self):
        if not self.streaming:
            return
        self.global_time += 1
        for row in self.channel_rows:
            row.update_data(self.global_time)
            row.redraw()

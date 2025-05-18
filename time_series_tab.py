from queue import Empty
from recorder import data_queue, stop_event
import pandas as pd

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

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(5, 5, 5, 5)
        row_layout.setSpacing(5)

        self.plus_button = QPushButton("+")
        self.plus_button.clicked.connect(self.handle_plus)
        row_layout.addWidget(self.plus_button)

        self.minus_button = QPushButton("-")
        self.minus_button.clicked.connect(self.handle_minus)
        row_layout.addWidget(self.minus_button)

        self.label = QLabel(f"Channel {channel_index+1}")
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        row_layout.addWidget(self.label)

        # Matplotlib setup
        self.figure = Figure()
        self.figure.set_tight_layout(True)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_ylim(0, 10)
        self.ax.set_xlim(0, 50)

        self.canvas = FigureCanvas(self.figure)

        self.plot_frame = QFrame()
        self.plot_frame.setFixedHeight(200)
        self.plot_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        plot_layout = QVBoxLayout(self.plot_frame)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.canvas)

        row_layout.addWidget(self.plot_frame)

    def handle_plus(self):
        self.amp_multiplier += 0.5

    def handle_minus(self):
        self.amp_multiplier -= 0.5

    def update_data(self, global_time, sample):
        amp = (2 ** self.amp_multiplier) * sample
        self.x_data.append(global_time)
        self.y_data.append(amp)
        if len(self.x_data) > 50:
            self.x_data = self.x_data[-50:]
            self.y_data = self.y_data[-50:]

    def redraw(self):
        self.ax.clear()
        self.ax.plot(self.x_data, self.y_data, color="blue")
        self.ax.set_ylim(0, 40)
        if self.x_data:
            last = self.x_data[-1]
            self.ax.set_xlim(last - 50, last)
        self.canvas.draw()


class TimeSeriesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.streaming = False
        self.global_time = 0

        # for recording CSV
        self.record_times = []
        self.record_data = []  # list of lists, one per channel

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Top control panel ---
        top_panel = QWidget()
        tp_layout = QHBoxLayout(top_panel)
        tp_layout.setContentsMargins(5, 5, 5, 5)
        tp_layout.setSpacing(10)

        tp_layout.addWidget(QLabel("Stream"))
        self.start_button = QPushButton("Start Streaming")
        self.start_button.clicked.connect(self.on_start_stream)
        tp_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Streaming")
        self.stop_button.clicked.connect(self.on_stop_stream)
        tp_layout.addWidget(self.stop_button)

        self.add_channel_button = QPushButton("Add Channel")
        self.add_channel_button.clicked.connect(self.on_add_channel)
        tp_layout.addWidget(self.add_channel_button)

        self.remove_channel_button = QPushButton("Remove Channel")
        self.remove_channel_button.clicked.connect(self.on_remove_channel)
        tp_layout.addWidget(self.remove_channel_button)

        tp_layout.addStretch()
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

        # initialize 8 channels
        self.channel_rows = []
        for i in range(8):
            self.add_channel_row(i)

        # timer for live updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(100)

        # optional stylesheet…
        self.setStyleSheet("""
            /* your existing styles */
        """)

    def add_channel_row(self, idx):
        row = ChannelRow(idx, parent=self.scroll_content)
        self.channel_rows.append(row)
        self.scroll_layout.addWidget(row)
        # add a record list for this channel
        self.record_data.append([])

    def on_add_channel(self):
        self.add_channel_row(len(self.channel_rows))

    def on_remove_channel(self):
        if self.channel_rows:
            # remove last row & its record list
            self.channel_rows.pop().deleteLater()
            self.record_data.pop()

    def on_start_stream(self):
        # reset recording buffers
        self.record_times = []
        self.record_data = [[] for _ in self.channel_rows]
        stop_event.clear()
        self.streaming = True

    def on_stop_stream(self):
        self.streaming = False
        stop_event.set()
        self.save_csv()

    def save_csv(self):
        """Save recorded data to CSV with dynamic columns."""
        df_dict = {'Time': self.record_times}
        for idx, data_list in enumerate(self.record_data):
            df_dict[f'Channel_{idx+1}'] = data_list
        df = pd.DataFrame(df_dict)
        df.to_csv('time_series_data.csv', index=False)
        print("Saved time_series_data.csv")

    def update_plots(self):
        if not self.streaming:
            return

        self.global_time += 1

        # record timestamp
        self.record_times.append(self.global_time)

        # fetch latest data chunk
        chunk = None
        while True:
            try:
                chunk = data_queue.get_nowait()
            except Empty:
                break

        if chunk is None:
            # no new data: append zeros
            for lst in self.record_data:
                lst.append(0.0)
            # and skip plotting
            return

        eeg_chunk, aux_chunk, ts_chunk = chunk
        # for each channel row, take last sample
        for idx, row in enumerate(self.channel_rows):
            sample = float(eeg_chunk[idx, -1])
            # record actual sample
            self.record_data[idx].append(sample)
            # update plot
            row.update_data(self.global_time, sample)
            row.redraw()

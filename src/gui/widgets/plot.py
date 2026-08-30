import numpy as np
from typing import Optional
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QDialog, QVBoxLayout

import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False


class PlotWindow(QDialog):
    def __init__(self, ax: Axes, parent: Optional[QDialog] = None, title='新建图表'):
        super().__init__(parent)

        if isinstance(ax, list) or isinstance(ax, tuple) or isinstance(ax, np.ndarray):
            figure = ax[0].figure
        else:
            figure = ax.figure

        # Create canvas to plot the ax figure.
        self.setWindowTitle(title)
        self.canvas = FigureCanvas(figure)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

        # Draw canvas figure.
        self.canvas.draw_idle()

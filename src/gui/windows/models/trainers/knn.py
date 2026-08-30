import pandas as pd
from typing import Dict, Any, Type
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QSlider, QVBoxLayout
from superqt import QLabeledSlider
from src.database.model import ModelDatabase
from src.gui.widgets.sliders import add_snap_behavior
from src.gui.windows.models.trainer import TrainerDialog
from src.models.classifiers.knn import KNN


class KNNTrainerDialog(TrainerDialog):
    """ KNN trainer window. """

    def __init__(self, df: pd.DataFrame, model_db: ModelDatabase):
        self._neighbors_step = 6
        self._weights = {'等权重': 'uniform', '按距离': 'distance'}
        self._distances = {'曼哈顿距离': 1, '欧氏距离': 2}

        self._slider_neighbors = None
        self._combo_weights = None
        self._combo_distances = None

        super().__init__(
            df=df,
            model_db=model_db,
            title='KNN 训练器',
            width=800,
            height=250,
            supports_calibration=True
        )

    def get_model_cls(self) -> Type:
        return KNN

    def _add_trainer_widgets(self, root: QVBoxLayout):
        row1_box = QHBoxLayout()
        row1_box.setContentsMargins(0, 10, 0, 0)
        row1_box.addStretch(1)

        self._slider_neighbors = QLabeledSlider(Qt.Orientation.Horizontal)
        self._slider_neighbors.setFixedWidth(150)
        self._slider_neighbors.setRange(3, 99)
        self._slider_neighbors.setSingleStep(6)
        self._slider_neighbors.setTickInterval(12)
        self._slider_neighbors.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._slider_neighbors.setValue(15)
        add_snap_behavior(slider=self._slider_neighbors, step=6)
        self._add_tunable_param(
            name='近邻数',
            placeholder_name='n_neighbors',
            widget=self._slider_neighbors,
            layout=row1_box,
            tooltip='最近邻实例（邻居）的数量。'
        )

        self._combo_weights = QComboBox()
        self._combo_weights.setFixedWidth(100)
        for weight in self._weights:
            self._combo_weights.addItem(weight)
        self._combo_weights.setCurrentIndex(1)
        self._add_tunable_param(
            name='邻居权重',
            placeholder_name='weights',
            widget=self._combo_weights,
            layout=row1_box,
            tooltip='KNN 邻居的权重方式。若为等权重，则所有邻居权重相同。'
        )

        self._combo_distances = QComboBox()
        self._combo_distances.setFixedWidth(100)
        for metric in self._distances:
            self._combo_distances.addItem(metric)
        self._combo_distances.setCurrentIndex(1)
        self._add_tunable_param(
            name='距离度量',
            placeholder_name='p',
            widget=self._combo_distances,
            layout=row1_box,
            tooltip='两个实例之间的距离度量方式。'
        )

        row1_box.addStretch(1)
        root.addLayout(row1_box)

    def _get_model_params(self) -> Dict[str, Any]:
        return {
            'n_neighbors': self._slider_neighbors.value(),
            'weights': self._weights[self._combo_weights.currentText()],
            'p': self._distances[self._combo_distances.currentText()]
        }

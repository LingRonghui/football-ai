import pandas as pd
from typing import Dict, Any, Type
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QSlider, QVBoxLayout
from superqt import QLabeledSlider, QLabeledDoubleSlider
from src.database.model import ModelDatabase
from src.gui.widgets.sliders import add_snap_behavior
from src.gui.windows.models.trainer import TrainerDialog
from src.models.classifiers.svm import SVM


class SVMTrainerDialog(TrainerDialog):
    """ SVM trainer window. """

    def __init__(self, df: pd.DataFrame, model_db: ModelDatabase):
        self._kernels = {'线性': 'linear', 'RBF': 'rbf', '多项式': 'poly', 'Sigmoid': 'sigmoid'}
        self._class_weights = {'是': True, '否': False}
        self._gamma_step = 0.1
        
        self._combo_kernel = None
        self._slider_degree = None
        self._slider_gamma = None
        self._combo_class = None

        super().__init__(
            df=df,
            model_db=model_db,
            title='SVM 训练器',
            width=800,
            height=250,
            supports_calibration=True
        )

    def get_model_cls(self) -> Type:
        return SVM

    def _add_trainer_widgets(self, root: QVBoxLayout):
        row1_box = QHBoxLayout()
        row1_box.setContentsMargins(0, 10, 0, 0)
        row1_box.addStretch(1)

        self._combo_kernel = QComboBox()
        self._combo_kernel.setFixedWidth(90)
        for kernel in self._kernels:
            self._combo_kernel.addItem(kernel)
        self._combo_kernel.setCurrentIndex(1)
        self._add_tunable_param(
            name='核函数',
            placeholder_name='kernel',
            widget=self._combo_kernel,
            layout=row1_box,
            tooltip='SVM 核函数。'
        )

        self._slider_degree = QLabeledSlider(Qt.Orientation.Horizontal)
        self._slider_degree.setFixedWidth(100)
        self._slider_degree.setRange(3, 6)
        self._slider_degree.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._slider_degree.setTickInterval(1)
        self._slider_degree.setSingleStep(1)
        self._add_tunable_param(
            name='多项式阶数',
            placeholder_name='degree',
            widget=self._slider_degree,
            layout=row1_box,
            tooltip='核函数的多项式阶数（仅适用于多项式核）。'
        )

        self._slider_gamma = QLabeledDoubleSlider(Qt.Orientation.Horizontal)
        self._slider_gamma.setFixedWidth(170)
        self._slider_gamma.setRange(0.1, 2.0)
        self._slider_gamma.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._slider_gamma.setTickInterval(0.2)
        self._slider_gamma.setSingleStep(0.1)
        self._slider_gamma.setValue(1.0)
        add_snap_behavior(slider=self._slider_gamma, step=0.1)
        self._add_tunable_param(
            name='Gamma 系数',
            placeholder_name='gamma',
            widget=self._slider_gamma,
            layout=row1_box,
            tooltip='Gamma 正则化常数。'
        )

        self._combo_class = QComboBox()
        self._combo_class.setFixedWidth(60)
        for class_weight in self._class_weights:
            self._combo_class.addItem(class_weight)
        self._add_tunable_param(
            name='类别权重',
            placeholder_name='class_weight',
            widget=self._combo_class,
            layout=row1_box,
            tooltip='是否平衡类别权重（各目标的权重）。'
        )

        row1_box.addStretch(1)
        root.addLayout(row1_box)

    def _get_model_params(self) -> Dict[str, Any]:
        return {
            'kernel': self._kernels[self._combo_kernel.currentText()],
            'degree': self._slider_degree.value(),
            'gamma': self._slider_gamma.value(),
            'class_weight': self._class_weights[self._combo_class.currentText()]
        }

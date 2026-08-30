import pandas as pd
from typing import Dict, Any, Type
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QSlider, QSpinBox, QDoubleSpinBox, QVBoxLayout
from superqt import QLabeledSlider, QLabeledDoubleSlider
from src.database.model import ModelDatabase
from src.gui.widgets.sliders import add_snap_behavior
from src.gui.windows.models.trainer import TrainerDialog
from src.models.classifiers.extremeboosting import XGBoost


class ExtremeBoostingTrainerDialog(TrainerDialog):
    """ Random Forest trainer window. """

    def __init__(self, df: pd.DataFrame, model_db: ModelDatabase):
        self._estimators_step = 50
        self._depth_step = 1
        self._child_step = 1
        self._lr_step = 0.005
        self._lambda_step = 0.1
        self._alpha_step = 0.1

        self._spin_estimators = None
        self._slider_depth = None
        self._slider_child = None
        self._spin_lr = None
        self._slider_lambda = None
        self._slider_alpha = None

        super().__init__(
            df=df,
            model_db=model_db,
            title='XGBoost 训练器',
            width=800,
            height=500,
            supports_calibration=True
        )

    def get_model_cls(self) -> Type:
        return XGBoost

    def _add_trainer_widgets(self, root: QVBoxLayout):
        row1_box = QHBoxLayout()
        row1_box.setContentsMargins(0, 10, 0, 0)
        row1_box.addStretch(1)

        self._spin_estimators = QSpinBox()
        self._spin_estimators.setFixedWidth(100)
        self._spin_estimators.setRange(50, 500)
        self._spin_estimators.setSingleStep(self._estimators_step)
        self._spin_estimators.setValue(100)
        self._add_tunable_param(
            name='树的数量',
            placeholder_name='n_estimators',
            widget=self._spin_estimators,
            layout=row1_box,
            tooltip='决策树（估计器）的数量。'
        )

        self._slider_depth = QLabeledSlider(Qt.Orientation.Horizontal)
        self._slider_depth.setFixedWidth(170)
        self._slider_depth.setRange(1, 15)
        self._slider_depth.setSingleStep(self._depth_step)
        self._slider_depth.setTickInterval(1)
        self._slider_depth.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._slider_depth.setValue(6)
        add_snap_behavior(slider=self._slider_depth, step=self._depth_step)
        self._add_tunable_param(
            name='最大深度',
            placeholder_name='max_depth',
            widget=self._slider_depth,
            layout=row1_box,
            tooltip='树的最大深度。'
        )

        row1_box.addStretch(1)
        root.addLayout(row1_box)

        row2_box = QHBoxLayout()
        row2_box.setContentsMargins(0, 10, 0, 0)
        row2_box.addStretch(1)

        self._slider_child = QLabeledSlider(Qt.Orientation.Horizontal)
        self._slider_child.setFixedWidth(120)
        self._slider_child.setRange(1, 5)
        self._slider_child.setSingleStep(self._child_step)
        self._slider_child.setTickInterval(1)
        self._slider_child.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._add_tunable_param(
            name='最小子节点权重',
            placeholder_name='min_child_weight',
            widget=self._slider_child,
            layout=row2_box,
            tooltip='每个子节点的最小权重。'
        )

        self._spin_lr = QDoubleSpinBox()
        self._spin_lr.setFixedWidth(170)
        self._spin_lr.setRange(0.005, 0.5)
        self._spin_lr.setSingleStep(self._lr_step)
        self._spin_lr.setDecimals(4)
        self._spin_lr.setValue(0.3)
        self._add_tunable_param(
            name='学习率',
            placeholder_name='learning_rate',
            widget=self._spin_lr,
            layout=row2_box,
            tooltip='优化学习率，控制参数更新幅度。'
        )

        row2_box.addStretch(1)
        root.addLayout(row2_box)

        row3_box = QHBoxLayout()
        row3_box.setContentsMargins(0, 10, 0, 0)
        row3_box.addStretch(1)

        self._slider_lambda = QLabeledDoubleSlider(Qt.Orientation.Horizontal)
        self._slider_lambda.setFixedWidth(150)
        self._slider_lambda.setRange(0.1, 2.0)
        self._slider_lambda.setSingleStep(self._lambda_step)
        self._slider_lambda.setTickInterval(0.1)
        self._slider_lambda.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._slider_lambda.setValue(1.0)
        add_snap_behavior(slider=self._slider_lambda, step=self._lambda_step)
        self._add_tunable_param(
            name='L2 正则化 (Lambda)',
            placeholder_name='lambda_regularization',
            widget=self._slider_lambda,
            layout=row3_box,
            tooltip='L2 正则化系数 (Lambda)。'
        )

        self._slider_alpha = QLabeledDoubleSlider(Qt.Orientation.Horizontal)
        self._slider_alpha.setFixedWidth(130)
        self._slider_alpha.setRange(0.0, 1.0)
        self._slider_alpha.setSingleStep(self._alpha_step)
        self._slider_alpha.setTickInterval(0.1)
        self._slider_alpha.setTickPosition(QSlider.TickPosition.TicksBelow)
        add_snap_behavior(slider=self._slider_alpha, step=self._alpha_step)
        self._add_tunable_param(
            name='L1 正则化 (Alpha)',
            placeholder_name='alpha_regularization',
            widget=self._slider_alpha,
            layout=row3_box,
            tooltip='L1 正则化系数 (Alpha)。'
        )

        row3_box.addStretch(1)
        root.addLayout(row3_box)

    def _get_model_params(self) -> Dict[str, Any]:
        return {
            'n_estimators': self._spin_estimators.value(),
            'max_depth': self._slider_depth.value(),
            'min_child_weight': self._slider_child.value(),
            'learning_rate': self._spin_lr.value(),
            'lambda_regularization': self._slider_lambda.value(),
            'alpha_regularization': self._slider_alpha.value()
        }

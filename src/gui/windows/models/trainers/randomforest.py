import pandas as pd
from typing import Dict, Any, Type
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QSlider, QSpinBox, QVBoxLayout
from superqt import QLabeledSlider
from src.database.model import ModelDatabase
from src.gui.widgets.sliders import add_snap_behavior
from src.gui.windows.models.trainer import TrainerDialog
from src.models.classifiers.randomforest import RandomForest


class RandomForestTrainerDialog(TrainerDialog):
    """ Random Forest trainer window. """

    def __init__(self, df: pd.DataFrame, model_db: ModelDatabase):
        self._estimators_step = 50
        self._criterion_options = {'Gini 系数': 'gini', '信息熵': 'entropy', '对数损失': 'log_loss'}
        self._leaf_step = 2
        self._samples_step = 2
        self._feature_options = {'无': None, 'SQRT': 'sqrt', 'Log2': 'log2'}
        self._depth_step = 1
        self._class_weights = {'是': True, '否': False}

        self._combo_criterion = None
        self._slider_leaf = None
        self._slider_samples = None
        self._combo_features = None
        self._slider_depth = None
        self._combo_class = None
        self._spin_estimators = None

        super().__init__(
            df=df,
            model_db=model_db,
            title='Random Forest 训练器',
            width=800,
            height=500,
            supports_calibration=True
        )

    def get_model_cls(self) -> Type:
        return RandomForest

    def _add_trainer_widgets(self, root: QVBoxLayout):
        row1_box = QHBoxLayout()
        row1_box.setContentsMargins(0, 10, 0, 0)
        row1_box.addStretch(1)

        self._combo_criterion = QComboBox()
        self._combo_criterion.setFixedWidth(90)
        for criterion in self._criterion_options:
            self._combo_criterion.addItem(criterion)
        self._add_tunable_param(
            name='划分标准',
            placeholder_name='criterion',
            widget=self._combo_criterion,
            layout=row1_box,
            tooltip='决策树的目标函数。'
        )

        self._slider_leaf = QLabeledSlider(Qt.Orientation.Horizontal)
        self._slider_leaf.setFixedWidth(150)
        self._slider_leaf.setRange(1, 35)
        self._slider_leaf.setSingleStep(self._leaf_step)
        self._slider_leaf.setTickInterval(4)
        self._slider_leaf.setTickPosition(QSlider.TickPosition.TicksBelow)
        add_snap_behavior(slider=self._slider_leaf, step=self._leaf_step)
        self._add_tunable_param(
            name='叶节点最小样本数',
            placeholder_name='min_samples_leaf',
            widget=self._slider_leaf,
            layout=row1_box,
            tooltip='形成叶节点（终止/目标节点）所需的最小样本数。'
        )

        self._slider_samples = QLabeledSlider(Qt.Orientation.Horizontal)
        self._slider_samples.setFixedWidth(150)
        self._slider_samples.setRange(2, 30)
        self._slider_samples.setSingleStep(step=self._samples_step)
        self._slider_samples.setTickInterval(4)
        self._slider_samples.setTickPosition(QSlider.TickPosition.TicksBelow)
        add_snap_behavior(slider=self._slider_samples, step=self._samples_step)
        self._add_tunable_param(
            name='分裂最小样本数',
            placeholder_name='min_samples_split',
            widget=self._slider_samples,
            layout=row1_box,
            tooltip='分裂节点所需的最小样本数。'
        )
        row1_box.addStretch(1)
        root.addLayout(row1_box)

        row2_box = QHBoxLayout()
        row2_box.setContentsMargins(0, 10, 0, 0)
        row2_box.addStretch(1)

        self._combo_features = QComboBox()
        self._combo_features.setFixedWidth(80)
        for feature in self._feature_options:
            self._combo_features.addItem(feature)
        self._add_tunable_param(
            name='最大特征数',
            placeholder_name='max_features',
            widget=self._combo_features,
            layout=row2_box,
            tooltip='所使用的最大特征数量。'
        )

        self._slider_depth = QLabeledSlider(Qt.Orientation.Horizontal)
        self._slider_depth.setFixedWidth(170)
        self._slider_depth.setRange(0, 15)
        self._slider_depth.setSingleStep(self._depth_step)
        self._slider_depth.setTickInterval(1)
        self._slider_depth.setTickPosition(QSlider.TickPosition.TicksBelow)
        add_snap_behavior(slider=self._slider_depth, step=self._depth_step)
        self._add_tunable_param(
            name='最大深度',
            placeholder_name='max_depth',
            widget=self._slider_depth,
            layout=row2_box,
            tooltip='树的最大深度。'
        )

        self._combo_class = QComboBox()
        self._combo_class.setFixedWidth(60)
        for class_weight in self._class_weights:
            self._combo_class.addItem(class_weight)
        self._add_tunable_param(
            name='类别权重',
            placeholder_name='class_weight',
            widget=self._combo_class,
            layout=row2_box,
            tooltip='是否平衡类别权重（各目标的权重）。'
        )

        row2_box.addStretch(1)
        root.addLayout(row2_box)

        row3_box = QHBoxLayout()
        row3_box.setContentsMargins(0, 10, 0, 0)
        row3_box.addStretch(1)

        self._spin_estimators = QSpinBox()
        self._spin_estimators.setFixedWidth(100)
        self._spin_estimators.setRange(50, 500)
        self._spin_estimators.setSingleStep(self._estimators_step)
        self._spin_estimators.setValue(100)
        self._add_tunable_param(
            name='树的数量',
            placeholder_name='n_estimators',
            widget=self._spin_estimators,
            layout=row3_box,
            tooltip='决策树（估计器）的数量。'
        )

        row3_box.addStretch(1)
        root.addLayout(row3_box)

    def _get_model_params(self) -> Dict[str, Any]:
        return {
            'n_estimators': self._spin_estimators.value(),
            'criterion': self._criterion_options[self._combo_criterion.currentText()],
            'min_samples_leaf': self._slider_leaf.value(),
            'min_samples_split': self._slider_samples.value(),
            'max_features': self._feature_options[self._combo_features.currentText()],
            'max_depth': self._slider_depth.value(),
            'class_weight': self._class_weights[self._combo_class.currentText()]
        }

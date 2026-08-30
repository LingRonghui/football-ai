import math
import pandas as pd
from abc import abstractmethod
from typing import Any, Dict, Optional, Type
from optuna.visualization.matplotlib import plot_param_importances
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QDialog, QFrame, QLabel, QCheckBox, QComboBox, QHBoxLayout, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget
)
from src.database.model import ModelDatabase
from src.gui.utils.taskrunner import TaskRunnerDialog
from src.gui.widgets.plot import PlotWindow
from src.gui.widgets.tables import SimpleTableDialog
from src.models.model import ClassificationModel
from src.models.trainer import Trainer
from src.models.tuner import Tuner
from src.preprocessing.utils.normalization import NormalizerType
from src.preprocessing.utils.sampling import SamplerType
from src.preprocessing.utils.target import TargetType
from src.preprocessing.selection import train_test_split


class TrainerDialog(QDialog):
    """ Base class for all trainer dialogs. It utilizes a standard train/eval and tuning procedures for all models. """

    def __init__(
            self,
            df: pd.DataFrame,
            model_db: ModelDatabase,
            title: str,
            width: int,
            height: int,
            supports_calibration: bool = True
    ):
        super().__init__()

        if width < 250 or height < 250:
            raise ValueError(f'Both width x height should be at least 250px, got {width}x{height}.')

        self._df = df
        self._model_db = model_db
        self._trainer = Trainer()

        self._league_id = model_db.league_id
        self._title = title
        self._width = width
        self._height = height
        self._supports_calibration = supports_calibration

        # Set trainer placeholders.
        self._target_types = {'胜平负 (1/X/2)': TargetType.RESULT, '大小球 2.5': TargetType.OVER_UNDER}
        self._normalizer_types = {
            '无': None,
            '标准化': NormalizerType.STANDARD,
            'Min-Max 归一化': NormalizerType.MIN_MAX,
            'Max-Abs 归一化': NormalizerType.MAX_ABS
        }
        self._sampler_types = {
            '无': None,
            'SVM-Smote（过采样）': SamplerType.SVM_SMOTE,
            'Near-Miss（欠采样）': SamplerType.NEARMISS,
            '难度阈值（欠采样）': SamplerType.INSTANCE_HARDNESS_THRESHOLD
        }
        self._calibration_options = {'是': True, '否': False}
        self._optimization_metrics = ['Accuracy', 'F1', 'Precision', 'Recall']
        self._min_eval_ratio = 5
        self._max_eval_ratio = 30

        self._tunable_placeholders = {}

        # Declare UI placeholders.
        self._msg_tune = None
        self._msg_crossval = None
        self._msg_sliding_crossval = None
        self._msg_trainval = None

        self._line_edit_id = None
        self._combo_target = None
        self._spin_eval_samples_perc = None
        self._samples_label = None
        self._check_tune = None
        self._spin_trials = None
        self._combo_objective = None
        self._combo_norm = None
        self._combo_sampler = None
        self._combo_calibration = None
        self._check_cross_valid = None
        self._check_sliding_cross_valid = None

        self._initialize_window()
        self._add_widgets()
        self._set_tunable_param_states(enabled=False)
        self._show_eval_samples()

        QTimer.singleShot(200, self._show_instructions)

    @abstractmethod
    def get_model_cls(self) -> Type:
        pass

    @abstractmethod
    def _add_trainer_widgets(self, root: QVBoxLayout):
        pass

    @abstractmethod
    def _get_model_params(self) -> Dict[str, Any]:
        pass

    def get_model_params(self, model_id: str) -> Dict[str, Any]:
        """ Returns all model constructor params. """

        # Add basic model parameters.
        model_params = {
            'league_id': self._league_id,
            'model_id': model_id,
            'target_type': self._target_types[self._combo_target.currentText()],
            'normalizer': self._normalizer_types[self._combo_norm.currentText()],
            'sampler': self._sampler_types[self._combo_sampler.currentText()]
        }

        if self._supports_calibration:
            model_params['calibrate_probabilities'] = self._calibration_options[self._combo_calibration.currentText()]

        # Add classifier-specific parameters.
        model_params.update(self._get_model_params())
        return model_params

    def train(self):
        """ Trains (and optionally tunes) the selected model. """

        model_id = self._line_edit_id.text()

        # Validate model id.
        if len(model_id) < 1:
            QMessageBox.critical(
                self,
                '模型创建失败',
                '模型创建失败：模型 ID 为空。请设置一个唯一的模型 ID。'
            )
            return
        if self._model_db.model_exists(model_id=model_id):
            QMessageBox.critical(
                self,
                '模型已存在',
                f'联赛 "{self._league_id}" 下已存在 ID 为 "{model_id}" 的模型。请设置一个唯一的模型 ID。'
            )
            return

        # Get model class and params.
        model_cls = self.get_model_cls()
        model_config = self.get_model_params(model_id=model_id)

        eval_samples_size = float(self._spin_eval_samples_perc.value())
        model_config['train'] = {'eval_samples_size': eval_samples_size, 'results': {}}

        # Apply hyperparameter tuning.
        if self._check_tune.isChecked():
            model_config = self.tune(model_cls=model_cls, fixed_params=model_config)

        # Apply Cross Validation
        if self._check_cross_valid.isChecked():
            model = model_cls(**model_config)
            metrics_df = TaskRunnerDialog(
                parent=self,
                title='交叉验证',
                info='这可能需要一些时间...',
                task_fn=lambda: self._trainer.cross_validation(model=model, df=self._df)
            ).run()
            metrics_df['Model'] = model_id
            metrics_df['Model Type'] = model.__class__
            SimpleTableDialog(df=metrics_df, parent=self, title='交叉验证结果').show()
            model_config['train']['results']['cv'] = metrics_df

        # Apply Cross Validation
        if self._check_sliding_cross_valid.isChecked():
            model = model_cls(**model_config)
            metrics_df = TaskRunnerDialog(
                parent=self,
                title='滑动交叉验证',
                info='这可能需要一些时间...',
                task_fn=lambda: self._trainer.sliding_cross_validation(model=model, df=self._df, test_ratio=eval_samples_size)
            ).run()
            metrics_df['Model'] = model_id
            metrics_df['Model Type'] = model.__class__
            SimpleTableDialog(parent=self, df=metrics_df, title='滑动交叉验证结果').show()
            model_config['train']['results']['sliding-cv'] = metrics_df

        # Initializing model.
        model = model_cls(**model_config)
        train_df, eval_df = train_test_split(df=self._df, test_size=eval_samples_size)
        model, metrics_df = self._trainer.train(
            model=model,
            train_df=train_df,
            eval_df=eval_df,
            check_nan=True
        )
        metrics_df['Model'] = model_id
        metrics_df['Model Type'] = model.__class__
        SimpleTableDialog(df=metrics_df, parent=self, title='训练结果').show()

        model_config['cls'] = model.__class__
        model_config['train']['results']['fit'] = metrics_df

        # Saving model, config in the database.
        self._save_trained_model(model=model, model_config=model_config)

    def tune(self, model_cls: Type, fixed_params: Dict[str, Any]) -> Dict[str, Any]:
        """ Applies Optuna's hyperparameter tuning, visualizes optuna's study and returns best model parameters. """

        tunable_params = {}
        for param, tunable_dict in self._tunable_placeholders.items():
            if tunable_dict['checkbox'].isChecked():
                tunable_params[param] = model_cls.get_suggest_param_values(param=param)

        if len(tunable_params) == 0:
            QMessageBox.information(
                self,
                '未选择可调参数',
                '未选择任何可调参数，将在不调参的情况下继续。'
            )
            return fixed_params

        # Initialize Optuna study.
        metric = self._combo_objective.currentText()
        trials = self._spin_trials.value()
        tuner = Tuner(
            model_cls=model_cls,
            fixed_params=fixed_params,
            tunable_params=tunable_params,
            df=self._df,
            metric=metric
        )
        study = TaskRunnerDialog(
            title='超参数调参',
            info='这可能需要一些时间...',
            task_fn=lambda: tuner.tune(trials=trials),
            parent=self
        ).run()

        try:
            ax = plot_param_importances(study)
            PlotWindow(ax=ax, parent=self, title='超参数敏感性分析').show()
        except Exception as e:
            QMessageBox.critical(
                self,
                '超参数绘图错误',
                f'无法生成重要性图。\n错误：{e}。\n将继续展示调参结果。'
            )

        # Displaying best results.
        trials_df = study.trials_dataframe().drop(columns=['number', 'datetime_start', 'datetime_complete'])
        trials_df['duration'] = (trials_df['duration'].dt.total_seconds() / 60)
        trials_df = trials_df.rename(columns={
            'value': metric,
            'duration': 'Duration(m)',
            **{col: col.split('_', 1)[1] for col in trials_df.columns if col.startswith('params_')}
        }).sort_values(by=metric, ascending=False).round(3)
        trials_dialog = SimpleTableDialog(df=trials_df, parent=self, title='超参数调参结果')
        trials_dialog.table.selectRow(0)
        trials_dialog.show()

        # Add model params to model config.
        fixed_params['train']['results']['tune'] = trials_df
        best_params = study.best_trial.params
        fixed_params.update(**best_params)
        return fixed_params

    def _initialize_window(self):
        self.setWindowTitle(self._title)
        self.resize(self._width, self._height)

    def _add_widgets(self):
        root = QVBoxLayout(self)

        # --- Model initialization ---
        model_hbox = QHBoxLayout()
        model_hbox.addStretch(1)

        self._line_edit_id = QLineEdit(text=self._league_id)
        self._line_edit_id.setFixedWidth(200)
        self._line_edit_id.setPlaceholderText('请输入唯一的模型 ID...')
        model_hbox.addWidget(QLabel('模型 ID: '))
        model_hbox.addWidget(self._line_edit_id)

        self._combo_target = QComboBox()
        self._combo_target.setFixedWidth(120)
        for target in self._target_types:
            self._combo_target.addItem(target)
        model_hbox.addWidget(QLabel(' 预测目标: '))
        model_hbox.addWidget(self._combo_target)

        self._spin_eval_samples_perc = QSpinBox(self)
        self._spin_eval_samples_perc.setFixedWidth(80)
        self._spin_eval_samples_perc.setMinimum(self._min_eval_ratio)
        self._spin_eval_samples_perc.setMaximum(self._max_eval_ratio)
        self._spin_eval_samples_perc.setSingleStep(5)
        self._spin_eval_samples_perc.setValue(20)
        self._spin_eval_samples_perc.setToolTip(f'从共 {self._df.shape[0]} 条样本中预留用于模型评估的最近样本 (%)。')
        self._spin_eval_samples_perc.valueChanged.connect(self._show_eval_samples)
        model_hbox.addWidget(QLabel(' 验证样本 (%): '))
        model_hbox.addWidget(self._spin_eval_samples_perc)

        self._samples_label = QLabel('()')
        model_hbox.addWidget(self._samples_label)
        model_hbox.addStretch(1)
        root.addLayout(model_hbox)

        # --- Tunables initialization ---
        tunable_hbox = QHBoxLayout()
        tunable_hbox.setContentsMargins(0, 10, 0, 0)
        tunable_hbox.addStretch(1)

        self._check_tune = QCheckBox(text='调参')
        self._check_tune.setChecked(False)
        self._check_tune.setToolTip(
            '是否启用/禁用超参数调参流程。如果不清楚哪些超参数有效，建议启用。'
        )
        self._check_tune.stateChanged.connect(self._set_tunable_param_states)
        tunable_hbox.addWidget(self._check_tune)

        self._spin_trials = QSpinBox(self)
        self._spin_trials.setEnabled(False)
        self._spin_trials.setFixedWidth(80)
        self._spin_trials.setMinimum(25)
        self._spin_trials.setMaximum(1000)
        self._spin_trials.setSingleStep(25)
        self._spin_trials.setValue(25)
        self._spin_trials.setToolTip('超参数调参的迭代次数。')
        tunable_hbox.addWidget(QLabel('试验次数:'))
        tunable_hbox.addWidget(self._spin_trials)

        self._combo_objective = QComboBox()
        self._combo_objective.setEnabled(False)
        self._combo_objective.setFixedWidth(90)
        for objective in self._optimization_metrics:
            self._combo_objective.addItem(objective)
        self._combo_objective.setToolTip(
            '调参优化目标（指标）。调参器将选择使该指标最大化的最优超参数。'
        )
        tunable_hbox.addWidget(QLabel('优化目标:'))
        tunable_hbox.addWidget(self._combo_objective)
        tunable_hbox.addStretch(1)
        root.addLayout(tunable_hbox)

        basic_hbox = QHBoxLayout()
        basic_hbox.setContentsMargins(0, 10, 0, 0)
        basic_hbox.addStretch(1)

        self._combo_norm = QComboBox()
        self._combo_norm.setFixedWidth(90)
        for normalizer in self._normalizer_types:
            self._combo_norm.addItem(normalizer)
        self._add_tunable_param(
            name='数据标准化',
            placeholder_name='normalizer',
            widget=self._combo_norm,
            layout=basic_hbox,
            tooltip='选择特征数据标准化类型。'
        )

        self._combo_sampler = QComboBox()
        self._combo_sampler.setFixedWidth(220)
        for sampler in self._sampler_types:
            self._combo_sampler.addItem(sampler)
        self._add_tunable_param(
            name='采样策略',
            placeholder_name='sampler',
            widget=self._combo_sampler,
            layout=basic_hbox,
            tooltip='选择特征采样器类型。当类别不平衡时很有用。'
        )

        if self._supports_calibration:
            self._combo_calibration = QComboBox()
            self._combo_calibration.setFixedWidth(60)
            for calibration in self._calibration_options:
                self._combo_calibration.addItem(calibration)
            self._add_tunable_param(
                name='概率校准',
                placeholder_name='calibrate_probabilities',
                widget=self._combo_calibration,
                layout=basic_hbox,
                tooltip='是否校准模型输出的概率。'
            )

        basic_hbox.addStretch(1)
        root.addLayout(basic_hbox)

        # Adding children trainer widgets.
        self._add_trainer_widgets(root=root)

        # Adding evaluation options widgets.
        eval_row = QHBoxLayout()
        eval_row.setContentsMargins(0, 10, 0, 0)     # Adding 10px top margin.
        eval_row.setSpacing(8)

        # Adding left/right horizontal lines (separators).
        left_line = QFrame()
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setFrameShadow(QFrame.Shadow.Sunken)
        right_line = QFrame()
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setFrameShadow(QFrame.Shadow.Sunken)

        # stretch to keep the middle centered; lines expand, label stays centered
        eval_row.addStretch(1)
        eval_row.addWidget(left_line, 1)
        eval_row.addWidget(QLabel('模型评估'))
        eval_row.addWidget(right_line, 1)
        eval_row.addStretch(1)
        root.addLayout(eval_row)

        final_hbox = QHBoxLayout()
        final_hbox.setContentsMargins(0, 10, 0, 0)
        final_hbox.addStretch(1)
        self._check_cross_valid = QCheckBox(text='交叉验证')
        self._check_cross_valid.setChecked(True)
        self._check_cross_valid.setToolTip('是否在训练前执行交叉验证并展示结果。')
        final_hbox.addWidget(self._check_cross_valid)
        self._check_sliding_cross_valid = QCheckBox(text='滑动交叉验证')
        self._check_sliding_cross_valid.setChecked(True)
        self._check_sliding_cross_valid.setToolTip('是否在训练前执行滑动交叉验证并展示结果。')
        final_hbox.addWidget(self._check_sliding_cross_valid)
        final_hbox.addStretch(1)
        root.addLayout(final_hbox)

        train_btn = QPushButton('训练')
        train_btn.setFixedWidth(100)
        train_btn.setFixedHeight(30)
        train_btn.clicked.connect(self.train)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 10, 0, 0)
        btn_row.addStretch(1)
        btn_row.addWidget(train_btn)
        btn_row.addStretch(1)
        root.addLayout(btn_row)
        root.addStretch(1)

    def _add_tunable_param(
            self,
            name: str,
            placeholder_name: str,
            widget: QWidget,
            layout: QHBoxLayout,
            tooltip: Optional[str]
    ):
        """ Adds a tunable option to the dialog & updates the tunable placeholder dict. """

        checkbox = QCheckBox(text=f'{name}: ')
        checkbox.setChecked(False)
        checkbox.setToolTip(f'调参: "{name}"')
        checkbox.stateChanged.connect(lambda checked: widget.setEnabled(not checked))

        widget.setToolTip(tooltip)
        layout.addWidget(checkbox)
        layout.addWidget(widget)

        self._tunable_placeholders[placeholder_name] = {'checkbox': checkbox, 'widget': widget}

    def _set_tunable_param_states(self, enabled: bool):
        """ Enables/Disables hyperparameter tuning selections. """

        for name, tunable_dict in self._tunable_placeholders.items():
            checkbox = tunable_dict['checkbox']
            tunable_dict['checkbox'].setEnabled(enabled)

            if not enabled:
                tunable_dict['widget'].setEnabled(True)
            else:
                tunable_dict['widget'].setEnabled(not checkbox.isChecked())

        self._spin_trials.setEnabled(enabled)
        self._combo_objective.setEnabled(enabled)

    def _show_eval_samples(self):
        perc = self._spin_eval_samples_perc.value()
        num_samples = int(math.floor(perc*self._df.shape[0]/100))
        self._samples_label.setText(f'({num_samples})/{self._df.shape[0]}')

    def _save_trained_model(self, model: ClassificationModel, model_config: Dict[str, Any]):
        self._model_db.save_model(model=model, model_config=model_config)

    def _show_instructions(self):
        QMessageBox.information(
            self,
            '训练说明',
            '请设置模型超参数后点击"训练"。'
            '如果不清楚该选择哪些超参数，请启用"调参"并设置试验次数和优化目标（需最大化的指标）。'
            '最后勾选需要参与调参的超参数。'
        )

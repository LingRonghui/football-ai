from datetime import date
from typing import Optional, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QLabel, QLineEdit, QMessageBox,
    QDialog, QFrame, QHBoxLayout, QPushButton, QSpinBox, QVBoxLayout
)
from superqt import QLabeledDoubleRangeSlider
from src.database.league import LeagueDatabase
from src.gui.utils.taskrunner import TaskRunnerDialog
from src.network.leagues.league import League
from src.network.leagues.downloaders.extra import ExtraLeagueDownloader
from src.network.leagues.downloaders.main import MainLeagueDownloader
from src.preprocessing.statistics import StatisticsEngine


class NewLeagueWindow(QDialog):
    """ New League dialog, where user can download and create a new league. """

    def __init__(self, league_db: LeagueDatabase):
        super().__init__()

        self._league_db = league_db

        self._title = '新建联赛'
        self._width = 800
        self._height = 450
        self._num_rows = 7
        self._start_year_threshold = date.today().year - 4

        # Declare placeholders here.
        self.league_df = None
        self.league = None

        # Fetch all available leagues and the available league columns.
        self._mandatory_columns = {'Date', 'Season', 'Home', 'Away', 'HG', 'AG', 'Result', '1', 'X', '2'}

        # Fetch all statistic columns.
        basic_stats = StatisticsEngine.get_basic_stat_columns()
        extended_stats = StatisticsEngine.get_extended_stat_columns()
        all_stats = basic_stats + extended_stats
        self._all_stats = set(all_stats)
        self._all_columns = MainLeagueDownloader().expected_columns + all_stats
        self._main_columns = set(self._all_columns).difference(self._mandatory_columns)
        self._extra_columns = set(ExtraLeagueDownloader().expected_columns + basic_stats).difference(self._mandatory_columns)
        self._column_tips = {
            'Date': '比赛记录日期',
            'Season': '比赛所属赛季',
            'Home': '主队名称',
            'Away': '客队名称',
            'HG': '主队进球数',
            'AG': '客队进球数',
            'Result': '比赛结果：主胜 (H) / 平局 (D) / 客胜 (A)',
            '1': '主胜赔率',
            'X': '平局赔率',
            '2': '客胜赔率',
            'HST': '主队射正次数',
            'AST': '客队射正次数',
            'HC': '主队角球数',
            'AC': '客队角球数',
            'HW': '主队最近 N 场胜场数',
            'AW': '客队最近 N 场胜场数',
            'HL': '主队最近 N 场负场数',
            'AL': '客队最近 N 场负场数',
            'HGF': '主队进球累计（最近 N 场主队进球数之和）',
            'AGF': '客队进球累计（最近 N 场客队进球数之和）',
            'HAGF': '主客进球累计差（HAGF = HGF - AGF）',
            'HGA': '主队失球累计（最近 N 场主队失球数之和）',
            'AGA': '客队失球累计（最近 N 场客队失球数之和）',
            'HAGA': '主客失球累计差（HAGA = HGA - AGA）',
            'HGD': '主队净胜球（HGD = HGF - HGA）',
            'AGD': '客队净胜球（AGD = AGF - AGA）',
            'HAGD': '主客净胜球差（HAGD = HGD - AGD）',
            'HWGD': '主队净胜球获胜累计（最近 N 场主队以净胜球门限获胜的场次数）',
            'AWGD': '客队净胜球获胜累计（最近 N 场客队以净胜球门限获胜的场次数）',
            'HAWGD': '主客净胜球获胜累计差（HAWGD = HWGD - AWGD）',
            'HLGD': '主队净胜球落败累计（最近 N 场主队以净胜球门限落败的场次数）',
            'ALGD': '客队净胜球落败累计（最近 N 场客队以净胜球门限落败的场次数）',
            'HALGD': '主客净胜球落败累计差（HALGD = HLGD = ALGD）',
            'HW%': '主队胜率（自赛季开始起）',
            'HL%': '主队负率（自赛季开始起）',
            'AW%': '客队胜率（自赛季开始起）',
            'AL%': '客队负率（自赛季开始起）',
            'HSTF': '主队射正累计（最近 N 场主队射正次数之和）。需要 HST，主联赛',
            'ASTF': '客队射正累计（最近 N 场客队射正次数之和）。需要 AST，主联赛',
            'HCF': '主队角球累计（最近 N 场主队获得角球数之和）。需要 HCF，主联赛',
            'ACF': '客队角球累计（最近 N 场客队获得角球数之和）。需要 ACF，主联赛'
        }
        self._leagues = self._league_db.leagues

        # UI placeholders
        self._combobox_league = None
        self._line_edit_id = None
        self._odd_sliders = []
        self._start_year_spin = None
        self._match_history_spin = None
        self._goal_diff_spin = None
        self._checkboxes = {}

        self._initialize_window()
        self._add_widgets()

    def _initialize_window(self):
        """ Initializes dialog window. """

        self.setWindowTitle(self._title)
        self.resize(self._width, self._height)

    def _add_widgets(self):
        """ Adds dialog widgets. """

        root = QVBoxLayout(self)

        # --- League selection ---
        league_hbox = QHBoxLayout()
        league_hbox.addStretch(1)   # Stretch all to left.
        league_hbox.addWidget(QLabel('选择联赛：'))

        self._combobox_league = QComboBox()
        self._combobox_league.setFixedWidth(200)
        for i, league in enumerate(self._leagues):
            icon = QIcon(f'storage/graphics/countries/{league.country}.png')
            self._combobox_league.addItem(icon, league.name)
            self._combobox_league.setItemData(i, f'类别：{league.category}', Qt.ItemDataRole.ToolTipRole)
        self._combobox_league.currentIndexChanged.connect(self._set_league_changed)
        league_hbox.addWidget(self._combobox_league)

        self._line_edit_id = QLineEdit()
        self._line_edit_id.setFixedWidth(200)
        self._line_edit_id.setPlaceholderText('请输入唯一的联赛 ID...')
        league_hbox.addWidget(QLabel('ID：'))
        league_hbox.addWidget(self._line_edit_id)
        league_hbox.addStretch(1)   # Stretch all to right.
        root.addLayout(league_hbox)

        # --- League Filters ---
        row = QHBoxLayout()
        row.setContentsMargins(0, 10, 0, 0)     # Adding 10px top margin.
        row.setSpacing(8)

        # Adding left/right horizontal lines (separators).
        left_line = QFrame()
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setFrameShadow(QFrame.Shadow.Sunken)
        right_line = QFrame()
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setFrameShadow(QFrame.Shadow.Sunken)

        # stretch to keep the middle centered; lines expand, label stays centered
        row.addStretch(1)
        row.addWidget(left_line, 1)
        row.addWidget(QLabel('联赛筛选'))
        row.addWidget(right_line, 1)
        row.addStretch(1)
        root.addLayout(row)

        # Adding odd range filters.
        filters_hbox = QHBoxLayout()
        filters_hbox.addStretch(1)  # Adding left stretch.

        for odd in ['1', 'X', '2']:
            label = QLabel(f'赔率 {odd}：')
            label.setToolTip(
                f'仅包含赔率 {odd} 在此范围内的比赛。设为 10.0 表示不启用右边界。'
            )
            label.setStyleSheet('margin-top: 20px;')    # Add margin to align label with the slider.
            filters_hbox.addWidget(label)

            slider = QLabeledDoubleRangeSlider(Qt.Orientation.Horizontal)
            slider.setRange(1.0, 10.0)
            slider.setSingleStep(0.1)
            slider.setDecimals(1)
            slider.setValue((1.0, 10.0))
            slider.setFixedWidth(200)
            filters_hbox.addWidget(slider)
            self._odd_sliders.append(slider)

        filters_hbox.addStretch(1)  # Adding right stretch to center widgets.
        root.addLayout(filters_hbox)

        # Adding year, match history and goal diff margin filters.
        spinners_hbox = QHBoxLayout()
        spinners_hbox.setContentsMargins(0, 10, 0, 0)     # Adding 10px top margin.
        spinners_hbox.setSpacing(20)
        spinners_hbox.addStretch(1)  # Adding left stretch.

        label = QLabel('起始年份：')
        label.setToolTip(f'下载数据的年份范围选择：[起始年份, {self._start_year_threshold}]')
        spinners_hbox.addWidget(label)
        self._start_year_spin = QSpinBox(self)
        self._start_year_spin.setFixedWidth(100)
        spinners_hbox.addWidget(self._start_year_spin)

        label = QLabel('比赛历史窗口：')
        label.setToolTip('用于计算统计数据的最近 N 场比赛数量。通常设为 3 或 4 场。')
        spinners_hbox.addWidget(label)
        self._match_history_spin = QSpinBox(self)
        self._match_history_spin.setRange(2, 5)
        self._match_history_spin.setValue(3)
        self._match_history_spin.setFixedWidth(100)
        spinners_hbox.addWidget(self._match_history_spin)

        label = QLabel('净胜球门限：')
        label.setToolTip('达到提前派彩所需的净胜球数。通常设为 2 或 3 球。')
        spinners_hbox.addWidget(label)
        self._goal_diff_spin = QSpinBox(self)
        self._goal_diff_spin.setRange(2, 5)
        self._goal_diff_spin.setValue(2)
        self._goal_diff_spin.setFixedWidth(100)
        spinners_hbox.addWidget(self._goal_diff_spin)

        spinners_hbox.addStretch(1)  # Adding right stretch.
        root.addLayout(spinners_hbox)

        # --- Columns (6 per line) right below the spinners ---
        columns_grid = QGridLayout()
        columns_grid.setContentsMargins(10, 10, 10, 10)
        columns_grid.setSpacing(10)

        self._build_columns_grid(grid=columns_grid)
        root.addLayout(columns_grid)

        # Push all widgets to the top and add a download button on the bottom.
        download_btn = QPushButton('下载')
        download_btn.setFixedWidth(160)
        download_btn.setFixedHeight(30)
        download_btn.clicked.connect(self._download_league)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(download_btn)
        btn_row.addStretch(1)
        root.addLayout(btn_row)

        # Push all widgets to the top
        root.addStretch(1)

        # Trigger the first selected league.
        self._set_league_changed(index=0)

    def _set_league_changed(self, index: int):
        """ Sets the default league id. """

        league = self._leagues[index]

        def set_default_league_id():
            self._line_edit_id.setText(f'{league.name}-{league.country}-01')

        def set_default_start_year():
            start_year = league.start_year
            self._start_year_spin.setRange(start_year, self._start_year_threshold)
            self._start_year_spin.setValue(start_year)

        def set_available_league_columns():
            category = league.category

            if category == 'main':
                valid_columns = self._main_columns
            elif category == 'extra':
                valid_columns = self._extra_columns
            else:
                raise ValueError(f'Undefined column category: {category}')

            # Check the columns supported by the selected league.
            for col, checkbox in self._checkboxes.items():
                checkbox.setEnabled(col in valid_columns)

        set_default_league_id()
        set_default_start_year()
        set_available_league_columns()

    def _build_columns_grid(self, grid: QGridLayout):
        """ Adds all columns in a grid and builds column dependencies. """

        def link_disable_dependency(key: str, dependent_key: str):
            """ If checkbox is disabled, force dependent checkbox to be disabled+unchecked. """

            key_cb = self._checkboxes[key]
            dependent_cb = self._checkboxes[dependent_key]

            def dependency(checked: bool):
                if not checked:
                    dependent_cb.setChecked(False)
                    dependent_cb.setEnabled(False)
                else:
                    dependent_cb.setEnabled(True)

            key_cb.toggled.connect(dependency)

        # Build all the columns.
        for i, column_name in enumerate(self._all_columns):
            row = i // self._num_rows
            col = i % self._num_rows
            checkbox = QCheckBox(column_name, checked=True, enabled=column_name not in self._mandatory_columns)

            # Adding tooltip to checkbox.
            tip = self._column_tips.get(column_name)
            if tip:
                checkbox.setToolTip(tip)
            grid.addWidget(checkbox, row, col)

            self._checkboxes[column_name] = checkbox

        # Build column dependencies.
        link_disable_dependency(key='HC', dependent_key='HCF')
        link_disable_dependency(key='AC', dependent_key='ACF')
        link_disable_dependency(key='HST', dependent_key='HSTF')
        link_disable_dependency(key='AST', dependent_key='ASTF')

    def _prepare_league_data(self, league: League):
        def get_min_max_odds(slider: QLabeledDoubleRangeSlider) -> Optional[Tuple[float, float]]:
            min_val, max_val = slider.value()

            if min_val == 1.0 and max_val == 10.0:
                return None

            if max_val == 10.0:
                max_val = 1000

            return min_val, max_val

        return league.clone(
            start_year=self._start_year_spin.value(),
            league_id=self._line_edit_id.text(),
            match_history_window=self._match_history_spin.value(),
            goal_diff_margin=self._goal_diff_spin.value(),
            stats_columns=[
                col for col, checkbutton in self._checkboxes.items() if
                checkbutton.isEnabled() and
                checkbutton.isChecked() and
                col in self._all_stats
            ],
            odd_1_range=get_min_max_odds(slider=self._odd_sliders[0]),
            odd_x_range=get_min_max_odds(slider=self._odd_sliders[1]),
            odd_2_range=get_min_max_odds(slider=self._odd_sliders[2])
        )

    def _download_league(self):
        league_id = self._line_edit_id.text()

        if len(league_id) < 1:
            QMessageBox.critical(
                self,
                '创建联赛失败',
                '创建联赛失败：联赛 ID 为空。请输入唯一的联赛 ID。'
            )
            return

        league = self._leagues[self._combobox_league.currentIndex()]
        league = self._prepare_league_data(league=league)

        # Validate odds data.
        odd_1_range = league.odd_1_range
        if odd_1_range is not None and league.odd_1_range[1] - league.odd_1_range[0] < 0.5:
            QMessageBox.critical(
                self,
                '赔率差值',
                f'赔率 1 的最大值与最小值之差应至少为 0.5。',
                QMessageBox.StandardButton.Ok
            )
            return

        odd_x_range = league.odd_x_range
        if odd_x_range is not None and league.odd_x_range[1] - league.odd_x_range[0] < 0.5:
            QMessageBox.critical(
                self,
                '赔率差值',
                f'赔率 X 的最大值与最小值之差应至少为 0.5。',
                QMessageBox.StandardButton.Ok
            )
            return

        odd_2_range = league.odd_2_range
        if odd_2_range is not None and league.odd_2_range[1] - league.odd_2_range[0] < 0.5:
            QMessageBox.critical(
                self,
                '赔率差值',
                f'赔率 2 的最大值与最小值之差应至少为 0.5。',
                QMessageBox.StandardButton.Ok
            )
            return

        if self._league_db.league_exists(league_id=league_id):
            QMessageBox.critical(
                self,
                '联赛已存在',
                f'已存在使用相同 ID 的联赛：{league_id}。请为该联赛输入其他 ID。',
                QMessageBox.StandardButton.Ok
            )
            return

        # Running download task.
        dialog = TaskRunnerDialog(
            title='创建联赛',
            info='正在初始化联赛...',
            task_fn=lambda: self._league_db.create_league(league=league),
            parent=self
        )

        # Storing downloaded data (df and id).
        self.league_df = dialog.run()
        self.league = league

        self.close()

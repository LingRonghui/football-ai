from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDialog, QMessageBox, QPushButton, QVBoxLayout
from src.database.league import LeagueDatabase
from src.gui.utils.taskrunner import TaskRunnerDialog


class LoadLeagueWindow(QDialog):
    def __init__(self, league_db: LeagueDatabase, current_league_id: Optional[str]):
        super().__init__()

        self._league_db = league_db
        self._league_ids = league_db.get_league_ids()
        self._current_league_id = current_league_id

        self._title = '加载联赛'
        self._width = 350
        self._height = 120

        # Declare league placeholders.
        self.league_df = None
        self.league = None

        # UI placeholders
        self._combobox_league = None
        self._checkbox_update = None

        self._initialize_window()
        self._add_widgets()

    def exec(self):
        if len(self._league_ids) == 0:
            QMessageBox.critical(
                self,
                '暂无已有联赛',
                '没有可加载的已有联赛。',
                QMessageBox.StandardButton.Ok
            )
            return QDialog.Rejected

        super().exec()

    def _initialize_window(self):
        self.setWindowTitle(self._title)
        self.resize(self._width, self._height)

    def _add_widgets(self):
        root = QVBoxLayout(self)

        self._combobox_league = QComboBox()
        self._combobox_league.setFixedWidth(250)
        for league_id in self._league_ids:
            self._combobox_league.addItem(league_id)
        root.addWidget(self._combobox_league, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._checkbox_update = QCheckBox('更新联赛', checked=True)
        self._checkbox_update.setToolTip('勾选后，将在加载前先更新该联赛数据。')
        root.addWidget(self._checkbox_update, alignment=Qt.AlignmentFlag.AlignHCenter)

        download_btn = QPushButton('打开')
        download_btn.setFixedWidth(160)
        download_btn.setFixedHeight(30)
        download_btn.clicked.connect(self._load_league)
        root.addWidget(download_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(1)

    def _load_league(self):
        """ Loads the league matches and its id and optionally performs an update operation in the database. """

        cb_index = self._combobox_league.currentIndex()
        league_id = self._league_ids[cb_index]

        if league_id == self._current_league_id:
            QMessageBox.critical(
                self,
                '联赛已打开',
                f'联赛 {league_id} 已经处于打开状态。',
                QMessageBox.StandardButton.Ok
            )
            return

        def update_and_load():
            if self._checkbox_update.isChecked():
                return self._league_db.update_league(league_id=league_id)

            return self._league_db.load_league(league_id=league_id)

        diag = TaskRunnerDialog(
            title='加载联赛',
            info=f'正在打开：{league_id}...',
            task_fn=update_and_load,
            parent=self
        )
        self.league_df = diag.run()
        self.league = self._league_db.index[league_id]
        self.close()

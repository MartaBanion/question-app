from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout

from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton


class RandomPracticeDialog(QDialog):
    def __init__(self, total_count: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("创建随机练习")
        self.setObjectName("confirmDialog")
        self.total_count = max(total_count, 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        title = QLabel("创建随机练习")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel(f"当前题库可选题目：{total_count} 题"))

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("题目数量"))
        self.count_input = QSpinBox()
        self.count_input.setRange(1, self.total_count)
        self.count_input.setValue(min(20, self.total_count))
        count_row.addWidget(self.count_input)
        for value in [10, 20, 30, 50]:
            btn = SecondaryButton(str(value))
            btn.setEnabled(value <= self.total_count)
            btn.clicked.connect(lambda _, v=value: self.count_input.setValue(v))
            count_row.addWidget(btn)
        layout.addLayout(count_row)

        layout.addWidget(QLabel("题型"))
        self.type_checks: dict[str, QCheckBox] = {}
        type_row = QHBoxLayout()
        for qtype in ["单选题", "多选题", "判断题", "填空题"]:
            box = QCheckBox(qtype)
            box.setChecked(True)
            self.type_checks[qtype] = box
            type_row.addWidget(box)
        layout.addLayout(type_row)

        self.shuffle_questions = QCheckBox("打乱题目顺序")
        self.shuffle_questions.setChecked(True)
        self.shuffle_options = QCheckBox("打乱选项顺序（预留）")
        self.include_wrong = QCheckBox("包含错题")
        self.include_wrong.setChecked(True)
        layout.addWidget(QLabel("其他"))
        layout.addWidget(self.shuffle_questions)
        layout.addWidget(self.shuffle_options)
        layout.addWidget(self.include_wrong)

        actions = QHBoxLayout()
        actions.addStretch()
        cancel = SecondaryButton("取消")
        start = PrimaryButton("开始练习")
        cancel.clicked.connect(self.reject)
        start.clicked.connect(self.accept)
        actions.addWidget(cancel)
        actions.addWidget(start)
        layout.addLayout(actions)

    def selected_types(self) -> list[str]:
        return [key for key, box in self.type_checks.items() if box.isChecked()]

    def count(self) -> int:
        return self.count_input.value()

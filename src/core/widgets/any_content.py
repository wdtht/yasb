from abc import ABC, abstractmethod

from PyQt6.QtGui import QKeyEvent, QTextCursor
from core.widgets.base import BaseWidget
from core.validation.widgets.example import EXAMPLE_VALIDATION_SCHEMA
from PyQt6.QtWidgets import QLabel, QCheckBox, QTextEdit, QTextBrowser, QDialog, QVBoxLayout, QDateTimeEdit, \
    QDialogButtonBox
from PyQt6.QtCore import Qt, pyqtSignal, pyqtBoundSignal, QDateTime
from rx import operators as ops
from rx.subject import BehaviorSubject as LiveData


class AnyContentWidget(BaseWidget):
    validation_schema = EXAMPLE_VALIDATION_SCHEMA

    def __init__(
            self,
            label,
            label_alt,
            update_interval: int,
            callbacks: dict[str, str],
    ):
        super().__init__(update_interval, class_name="template-widget")
        self._task_list = [
            {"task": "这里是第一个示例任务", "completed": False, "next_step": "", "all_step": "", "remind_time": "", "priority": 1},
            {"task": "这里是第二个示例任务", "completed": False, "next_step": "", "all_step": "", "remind_time": "", "priority": 1},
            {"task": "这里是第三个示例任务", "completed": False, "next_step": "", "all_step": "", "remind_time": "", "priority": 1},
            {"task": "这里是第四个示例任务", "completed": False, "next_step": "", "all_step": "", "remind_time": "", "priority": 1},
            {"task": "这里是第五个示例任务", "completed": False, "next_step": "", "all_step": "", "remind_time": "", "priority": 1},
            {"task": "这里是第六个示例任务", "completed": False, "next_step": "", "all_step": "", "remind_time": "", "priority": 1},
            {"task": "这里是第七个示例任务", "completed": False, "next_step": "", "all_step": "", "remind_time": "", "priority": 1},
            {"task": "这里是第八个示例任务", "completed": False, "next_step": "", "all_step": "", "remind_time": "", "priority": 1},
            {"task": "这里是第九个示例任务", "completed": False, "next_step": "", "all_step": "", "remind_time": "", "priority": 1},
            {"task": "这里是第十个示例任务", "completed": False, "next_step": "", "all_step": "", "remind_time": "", "priority": 1}
        ]
        self._init_view()
        self._current_task_index = LiveData(-1)

        self._show_current_task_title_business()
        self._next_step_business()
        self._show_current_step_business()
        self._complete_current_task_business()
        self._add_task_business()

        self._current_task_index.on_next(0)

    def _enter_next_uncheck_task(self):
        start_index = (self._current_task_index.value + 1) % len(self._task_list)
        for index, task in enumerate(self._task_list[start_index:], start_index):
            if not task["completed"]:
                self._current_task_index.on_next(index)
                return
        self._current_task_index.on_next(-1)

    # noinspection PyUnresolvedReferences
    def _complete_current_task_business(self):
        self._current_task_completed = LiveData(True)

        self._current_task_completed.pipe(ops.distinct_until_changed()).subscribe(
            lambda x: self._complete.setChecked(x))

        # 更新数据
        def update_complete(completed: bool):
            self._task_list[self._current_task_index.value]["completed"] = completed

        self._current_task_completed.pipe(ops.distinct_until_changed()).subscribe(lambda x: update_complete(x))

        self._complete.checkStateChanged.connect(
            lambda: self._current_task_completed.on_next(self._complete.isChecked()))

        # 用户点击复选框时，完成任务, 并进入下一个未完成任务
        def complete_current_task():
            self._enter_next_uncheck_task()

        self._complete.clicked.connect(lambda x: complete_current_task() if self._complete.isChecked() else None)

        def update_current_task(index: int):
            if index == -1:
                self._current_task_completed.on_next(True)
            else:
                self._current_task_completed.on_next(self._task_list[index]["completed"])

        self._current_task_index.pipe(ops.distinct_until_changed()).subscribe(lambda x: update_current_task(x))

    def _next_step_business(self):
        self._current_task_next_step = LiveData("默认任务没有下一步计划")

        self._current_task_next_step.subscribe(
            lambda x: self._next_step.setPlainText(x))

        def update_current_step_and_enter_next_task():
            input_text = self._next_step.toPlainText().strip()
            if input_text:
                current_all_step = self._current_task_all_step.value
                if current_all_step != "":
                    current_all_step += "\n"
                self._current_task_all_step.on_next(current_all_step + f"{input_text}")
                self._enter_next_uncheck_task()

        self._next_step.taskSubmitted.connect(
            lambda: self._current_task_next_step.on_next(self._next_step.toPlainText()))

        def update_current_task(index: int):
            if index == -1:
                self._current_task_next_step.on_next("默认任务没有下一步计划")
            else:
                self._current_task_next_step.on_next(self._task_list[index]["next_step"])

        self._current_task_index.pipe(ops.distinct_until_changed()).subscribe(lambda x: update_current_task(x))

        # 构造并弹出时间选择器, 并在用户选择时间后更新下一步计划
        def show_time_picker():
            dialog = QDialog()
            dialog.setWindowTitle("选择时间")

            # 设置布局和时间选择控件
            layout = QVBoxLayout()
            time_picker = QDateTimeEdit()
            time_picker.setCalendarPopup(True)
            time_picker.setDateTime(QDateTime.currentDateTime())
            time_picker.setMinimumDateTime(QDateTime.currentDateTime())
            time_picker.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            layout.addWidget(time_picker)

            # 添加按钮
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            dialog.setLayout(layout)

            def update_current_and_enter_next_task():
                self._task_list[self._current_task_index.value]["remind_time"] = time_picker.dateTime().toString("yyyy-MM-dd HH:mm:ss")
                self._task_list[self._current_task_index.value]["priority"] = -1
                update_current_step_and_enter_next_task()

            dialog.accepted.connect(update_current_and_enter_next_task)

            dialog.exec()

        self._next_step.taskSubmitted.connect(show_time_picker)

    def _show_current_task_title_business(self):
        self._current_task_title.pipe(ops.distinct_until_changed()).subscribe(lambda x: self._label.setText(x))

        def update_current_task(index: int):
            if index == -1:
                self._current_task_title.on_next("没有未完成的任务")
            else:
                self._current_task_title.on_next(self._task_list[index]["task"])

        self._current_task_index.pipe(ops.distinct_until_changed()).subscribe(lambda x: update_current_task(x))

    def _show_current_step_business(self):
        self._current_task_all_step = LiveData("默认任务没有什么步骤")

        def update_steps_and_scroll(steps):
            """更新步骤文本并自动滚动到底部"""
            self._current_step.setPlainText(steps)
            self._current_step.verticalScrollBar().setValue(
                self._current_step.verticalScrollBar().maximum())

        # 绑定所有步骤，并自动滚动到最后
        self._current_task_all_step.pipe(
            ops.distinct_until_changed()
        ).subscribe(update_steps_and_scroll)

        def update_all_step(all_step: str):
            self._task_list[self._current_task_index.value]["all_step"] = all_step

        self._current_task_all_step.pipe(ops.distinct_until_changed()).subscribe(lambda x: update_all_step(x))

        def update_current_task(index: int):
            if index == -1:
                self._current_task_all_step.on_next("")
            else:
                self._current_task_all_step.on_next(self._task_list[index]["all_step"])

        self._current_task_index.pipe(ops.distinct_until_changed()).subscribe(lambda x: update_current_task(x))

    def _init_view(self):
        self._complete = QCheckBox()
        self._complete.setProperty("class", "complete")
        self.widget_layout.addWidget(self._complete)

        self._current_task_title = LiveData("默认任务")
        self._label = QLabel()
        self._label.setProperty("class", "label")
        self.widget_layout.addWidget(self._label)

        self._current_step = QTextBrowser()
        self._current_step.setProperty("class", "current-step")
        self.widget_layout.addWidget(self._current_step)

        self._next_step = TaskTextEdit(self)
        self._next_step.setProperty("class", "next-step")
        self._next_step.setPlaceholderText("输入下一步计划以跳过当前任务")
        self.widget_layout.addWidget(self._next_step)

        self._add_task = TaskTextEdit(self)
        self._add_task.setProperty("class", "add-task")
        self._add_task.setPlaceholderText("输入标题以快速创建新任务")
        self.widget_layout.addWidget(self._add_task)

    def _add_task_business(self):
        def handle_add_task_input():
            input_text = self._add_task.toPlainText().strip()
            if input_text:
                self._task_list.append({"task": input_text, "completed": False, "next_step": "", "all_step": "", "remind_time": "", "priority": 0})
                self._current_task_index.on_next(len(self._task_list) - 1)
                self._add_task.clear()

        self._add_task.taskSubmitted.connect(handle_add_task_input)


class TaskTextEdit(QTextEdit):
    # 定义一个无参数的信号
    taskSubmitted: pyqtBoundSignal = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Return:
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                # 如果按下Shift+Enter，则插入换行
                self.insertPlainText("\n")
            else:
                # 发射信号而不是直接调用方法
                self.taskSubmitted.emit()
        else:
            super().keyPressEvent(event)

# 遍历任务列表时不能遗漏了开头

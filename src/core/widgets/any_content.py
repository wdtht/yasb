from PyQt6.QtGui import QKeyEvent, QTextCursor
from core.widgets.base import BaseWidget
from core.validation.widgets.example import EXAMPLE_VALIDATION_SCHEMA
from PyQt6.QtWidgets import QLabel, QCheckBox, QTextEdit, QTextBrowser
from PyQt6.QtCore import Qt, pyqtSignal, pyqtBoundSignal
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
        self._init()
        self._complete_current_task_business()
        self._next_step_business()

    def _init(self):
        self._init_data()
        self._init_ui()
        self._bind_data_to_ui()
        self._bind_ui_to_data()

    def _init_ui(self):
        self._init_complete_box()
        self._init_current_task()
        self._init_current_step()
        self._init_next_step()

    def _init_complete_box(self):
        self._complete = QCheckBox()
        self._complete.setProperty("class", "complete")
        self.widget_layout.addWidget(self._complete)

    def _init_next_step(self):
        self._next_step = TaskTextEdit(self)
        self._next_step.setProperty("class", "next-step")
        self._next_step.setPlaceholderText("输入下一步计划以跳过当前任务")
        self.widget_layout.addWidget(self._next_step)

    def _handle_next_step_input(self):
        # 处理用户输入来跳过当前任务
        input_text = self._next_step.toPlainText().strip()
        if input_text:
            current_all_step = self._current_task_all_step.value
            if current_all_step != "":
                current_all_step += "\n"
            self._current_task_all_step.on_next(current_all_step + f"{input_text}")
            self._enter_next_uncheck_task()

    def _init_current_task(self):
        self._label = QLabel()
        self._label.setProperty("class", "label")
        self.widget_layout.addWidget(self._label)

    def _enter_next_uncheck_task(self):
        start_index = (self._current_task_index.value + 1) % len(self._task_list)
        for index, task in enumerate(self._task_list[start_index:], start_index):
            if not task["completed"]:
                self._current_task_index.on_next(index)
                return
        self._current_task_index.on_next(-1)

    def _init_current_step(self):
        self._current_step = QTextBrowser()
        self._current_step.setProperty("class", "current-step")
        self.widget_layout.addWidget(self._current_step)

    def _bind_data_to_ui(self):
        self._current_task_title.pipe(ops.distinct_until_changed()).subscribe(lambda x: self._label.setText(x))
        self._current_task_completed.pipe(ops.distinct_until_changed()).subscribe(
            lambda x: self._complete.setChecked(x))
        self._current_task_next_step.pipe(ops.distinct_until_changed()).subscribe(
            lambda x: self._next_step.setPlainText(x))
        # 绑定所有步骤，并自动滚动到最后
        self._current_task_all_step.pipe(
            ops.distinct_until_changed()
        ).subscribe(self._update_steps_and_scroll)

    def _update_steps_and_scroll(self, steps):
        """更新步骤文本并自动滚动到底部"""
        self._current_step.setPlainText(steps)
        self._current_step.verticalScrollBar().setValue(
            self._current_step.verticalScrollBar().maximum())

    def _init_data(self):
        self._task_list = [
            {"task": "这里是第一个示例任务", "completed": False, "next_step": "", "all_step": ""},
            {"task": "这里是第二个示例任务", "completed": False, "next_step": "", "all_step": ""},
            {"task": "这里是第三个示例任务", "completed": False, "next_step": "", "all_step": ""},
            {"task": "这里是第四个示例任务", "completed": False, "next_step": "", "all_step": ""},
            {"task": "这里是第五个示例任务", "completed": False, "next_step": "", "all_step": ""},
            {"task": "这里是第六个示例任务", "completed": False, "next_step": "", "all_step": ""},
            {"task": "这里是第七个示例任务", "completed": False, "next_step": "", "all_step": ""},
            {"task": "这里是第八个示例任务", "completed": False, "next_step": "", "all_step": ""},
            {"task": "这里是第九个示例任务", "completed": False, "next_step": "", "all_step": ""},
            {"task": "这里是第十个示例任务", "completed": False, "next_step": "", "all_step": ""}
        ]
        self._current_task_index = LiveData(-1)
        self._current_task_title = LiveData("默认任务")
        self._current_task_completed = LiveData(True)
        self._current_task_next_step = LiveData("")
        self._current_task_all_step = LiveData("默认任务没有什么步骤")

        def update_current_task(index: int):
            if index == -1:
                self._current_task_title.on_next("没有未完成的任务")
                self._current_task_completed.on_next(True)
                self._current_task_next_step.on_next("输入内容以添加新任务")
                self._current_task_all_step.on_next("")
            else:
                self._current_task_title.on_next(self._task_list[index]["task"])
                self._current_task_completed.on_next(self._task_list[index]["completed"])
                self._current_task_next_step.on_next(self._task_list[index]["next_step"])
                self._current_task_all_step.on_next(self._task_list[index]["all_step"])

        self._current_task_index.pipe(ops.distinct_until_changed()).subscribe(lambda x: update_current_task(x))
        self._current_task_index.on_next(0)

    # noinspection PyUnresolvedReferences
    def _bind_ui_to_data(self):
        def update_complete(completed: bool):
            self._task_list[self._current_task_index.value]["completed"] = completed

        self._current_task_completed.pipe(ops.distinct_until_changed()).subscribe(lambda x: update_complete(x))

        def update_all_step(all_step: str):
            self._task_list[self._current_task_index.value]["all_step"] = all_step

        self._current_task_all_step.pipe(ops.distinct_until_changed()).subscribe(lambda x: update_all_step(x))
        self._complete.checkStateChanged.connect(
            lambda: self._current_task_completed.on_next(self._complete.isChecked()))
        self._next_step.taskSubmitted.connect(
            lambda: self._current_task_next_step.on_next(self._next_step.toPlainText()))

    # noinspection PyUnresolvedReferences
    def _complete_current_task_business(self):
        def complete_current_task():
            self._enter_next_uncheck_task()

        self._complete.clicked.connect(lambda x: complete_current_task() if self._complete.isChecked() else None)

    def _next_step_business(self):
        self._next_step.taskSubmitted.connect(self._handle_next_step_input)


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


# all_step自动滚动到最后
# 遍历任务列表时不能遗漏了开头
from PyQt6.QtGui import QKeyEvent

from core.widgets.base import BaseWidget
from core.validation.widgets.example import EXAMPLE_VALIDATION_SCHEMA
from PyQt6.QtWidgets import QLabel, QCheckBox, QTextEdit
from PyQt6.QtCore import Qt, pyqtSignal, pyqtBoundSignal


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
        self._current_task_index = 0

        self._init_complete_box()

        self._init_current_task()

        self._init_next_step()

        self.callback_left = callbacks['on_left']
        self.callback_right = callbacks['on_right']
        self.callback_middle = callbacks['on_middle']
        self.callback_timer = "update_label"

        self._label.show()

    def _init_complete_box(self):
        self._complete = QCheckBox("完成")
        check_state_changed: pyqtBoundSignal = self._complete.checkStateChanged # type: ignore
        check_state_changed.connect(
            lambda: self._complete_current_task() if self._complete.isChecked() else None)
        self._complete.setProperty("class", "complete")
        self.widget_layout.addWidget(self._complete)

    def _complete_current_task(self):
        self._task_list[self._current_task_index]["completed"] = True
        self._enter_next_uncheck_task()
        self._update_label()

    def _init_next_step(self):
        self._next_step = TaskTextEdit(self)
        self._next_step.setProperty("class", "next-step")
        self._next_step.setPlaceholderText("输入下一步计划以跳过当前任务")
        self.widget_layout.addWidget(self._next_step)
        # 连接自定义信号到相应槽
        self._next_step.taskSubmitted.connect(self._handle_next_step_input)

    def _handle_next_step_input(self):
        # 处理用户输入来跳过当前任务
        input_text = self._next_step.toPlainText().strip()
        if input_text:
            self._enter_next_uncheck_task()
            self._next_step.clear()  # 清除文本框，避免重复跳过

    def _init_current_task(self):
        self._label = QLabel()
        self._label.setProperty("class", "label")
        self.widget_layout.addWidget(self._label)

    def _update_label(self):
        # Update the active label at each timer interval
        if self._current_task_index == -1:
            self._label.setText("没有未完成的任务")
            self._complete.setCheckState(Qt.CheckState.Checked)
            self._next_step.setPlaceholderText("输入内容以添加新任务")
        else:
            self._label.setText(self._task_list[self._current_task_index]["task"])
            self._complete.setCheckState(Qt.CheckState.Checked if self._task_list[self._current_task_index]["completed"] else Qt.CheckState.Unchecked)

    def _enter_next_uncheck_task(self):
        for task in self._task_list[(self._current_task_index + 1) % len(self._task_list):]:
            if not task["completed"]:
                self._current_task_index = self._task_list.index(task)
                self._next_step.clear()
                return
        self._current_task_index = -1


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

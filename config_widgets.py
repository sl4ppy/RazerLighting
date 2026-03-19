"""Parameter widgets for the Razer Lighting configuration GUI."""

from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSlider, QSpinBox,
    QDoubleSpinBox, QCheckBox, QColorDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)

from config_parser import humanize_name


class IntParamWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        layout.addWidget(label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(int(param.range_min))
        self.slider.setMaximum(int(param.range_max))
        self.slider.setSingleStep(int(param.range_step))
        self.slider.setValue(int(param.value))
        layout.addWidget(self.slider, 1)

        self.spin = QSpinBox()
        self.spin.setMinimum(int(param.range_min))
        self.spin.setMaximum(int(param.range_max))
        self.spin.setSingleStep(int(param.range_step))
        self.spin.setValue(int(param.value))
        self.spin.setFixedWidth(65)
        layout.addWidget(self.spin)

        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
        self.spin.valueChanged.connect(lambda: self.value_changed.emit())

    def get_value(self):
        return self.spin.value()

    def set_value(self, val):
        self.spin.blockSignals(True)
        self.slider.blockSignals(True)
        self.spin.setValue(int(val))
        self.slider.setValue(int(val))
        self.spin.blockSignals(False)
        self.slider.blockSignals(False)


class FloatParamWidget(QWidget):
    value_changed = pyqtSignal()

    SLIDER_STEPS = 10000

    def __init__(self, param):
        super().__init__()
        self.param = param
        self._fmin = param.range_min
        self._fmax = param.range_max
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        layout.addWidget(label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.SLIDER_STEPS)
        self.slider.setValue(self._to_slider(param.value))
        layout.addWidget(self.slider, 1)

        # Determine decimal places from step size
        decimals = max(1, min(6, len(str(param.range_step).rstrip('0').split('.')[-1]))) if param.range_step < 1 else 2
        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(decimals)
        self.spin.setMinimum(param.range_min)
        self.spin.setMaximum(param.range_max)
        self.spin.setSingleStep(param.range_step)
        self.spin.setValue(param.value)
        self.spin.setFixedWidth(75)
        layout.addWidget(self.spin)

        self.slider.valueChanged.connect(self._slider_to_spin)
        self.spin.valueChanged.connect(self._spin_to_slider)
        self.spin.valueChanged.connect(lambda: self.value_changed.emit())

    def _to_slider(self, fval):
        if self._fmax == self._fmin:
            return 0
        t = (fval - self._fmin) / (self._fmax - self._fmin)
        return int(t * self.SLIDER_STEPS)

    def _from_slider(self, sval):
        t = sval / self.SLIDER_STEPS
        return self._fmin + t * (self._fmax - self._fmin)

    def _slider_to_spin(self, sval):
        self.spin.blockSignals(True)
        self.spin.setValue(self._from_slider(sval))
        self.spin.blockSignals(False)

    def _spin_to_slider(self, fval):
        self.slider.blockSignals(True)
        self.slider.setValue(self._to_slider(fval))
        self.slider.blockSignals(False)

    def get_value(self):
        return self.spin.value()

    def set_value(self, val):
        self.spin.blockSignals(True)
        self.slider.blockSignals(True)
        self.spin.setValue(float(val))
        self.slider.setValue(self._to_slider(float(val)))
        self.spin.blockSignals(False)
        self.slider.blockSignals(False)


class BoolParamWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        self.check = QCheckBox(humanize_name(param.name))
        self.check.setChecked(param.value)
        self.check.setToolTip(param.tooltip)
        self.check.toggled.connect(lambda: self.value_changed.emit())
        layout.addWidget(self.check)

    def get_value(self):
        return self.check.isChecked()

    def set_value(self, val):
        self.check.blockSignals(True)
        self.check.setChecked(bool(val))
        self.check.blockSignals(False)


class ColorButton(QPushButton):
    """A button that shows a color swatch and opens a color picker on click."""
    color_changed = pyqtSignal(tuple)

    def __init__(self, color=(0, 0, 0)):
        super().__init__()
        self._color = tuple(color)
        self.setFixedSize(36, 28)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        r, g, b = self._color
        # Use light or dark text depending on brightness
        brightness = r * 0.299 + g * 0.587 + b * 0.114
        text_color = "#000000" if brightness > 127 else "#ffffff"
        self.setStyleSheet(
            f"QPushButton {{ background-color: rgb({r},{g},{b}); "
            f"border: 1px solid #555; border-radius: 3px; color: {text_color}; "
            f"font-size: 9px; }}"
            f"QPushButton:hover {{ border-color: #00ff00; }}"
        )

    def _pick_color(self):
        r, g, b = self._color
        color = QColorDialog.getColor(QColor(r, g, b), self, "Pick Color")
        if color.isValid():
            self._color = (color.red(), color.green(), color.blue())
            self._update_style()
            self.color_changed.emit(self._color)

    def get_color(self):
        return self._color

    def set_color(self, color):
        self._color = tuple(color)
        self._update_style()


class ColorParamWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        layout.addWidget(label)

        self.btn = ColorButton(param.value)
        self.btn.color_changed.connect(lambda: self.value_changed.emit())
        layout.addWidget(self.btn)

        r, g, b = param.value
        self.hex_label = QLabel(f"#{r:02x}{g:02x}{b:02x}")
        self.hex_label.setStyleSheet("color: #888; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.hex_label)
        layout.addStretch()

        self.btn.color_changed.connect(self._update_hex)

    def _update_hex(self, color):
        r, g, b = color
        self.hex_label.setText(f"#{r:02x}{g:02x}{b:02x}")

    def get_value(self):
        return self.btn.get_color()

    def set_value(self, val):
        self.btn.set_color(val)
        r, g, b = val
        self.hex_label.setText(f"#{r:02x}{g:02x}{b:02x}")


class PaletteWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        self._colors = list(param.value)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 2, 0, 2)

        header = QHBoxLayout()
        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        header.addWidget(label)

        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(28, 28)
        self.add_btn.clicked.connect(self._add_color)
        header.addWidget(self.add_btn)

        self.remove_btn = QPushButton("-")
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.clicked.connect(self._remove_color)
        header.addWidget(self.remove_btn)
        header.addStretch()
        main_layout.addLayout(header)

        self.colors_layout = QHBoxLayout()
        self.colors_layout.setSpacing(4)
        main_layout.addLayout(self.colors_layout)

        self._rebuild_buttons()

    def _rebuild_buttons(self):
        while self.colors_layout.count():
            item = self.colors_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, color in enumerate(self._colors):
            btn = ColorButton(color)
            btn.color_changed.connect(partial(self._color_changed, i))
            self.colors_layout.addWidget(btn)
        self.colors_layout.addStretch()

    def _color_changed(self, index, color):
        self._colors[index] = color
        self.value_changed.emit()

    def _add_color(self):
        last = self._colors[-1] if self._colors else (128, 128, 128)
        self._colors.append(last)
        self._rebuild_buttons()
        self.value_changed.emit()

    def _remove_color(self):
        if len(self._colors) > 1:
            self._colors.pop()
            self._rebuild_buttons()
            self.value_changed.emit()

    def get_value(self):
        return list(self._colors)

    def set_value(self, val):
        self._colors = list(val)
        self._rebuild_buttons()


class FloatListWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        self._values = list(param.value)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 2, 0, 2)

        header = QHBoxLayout()
        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        header.addWidget(label)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(self._add_item)
        header.addWidget(add_btn)

        remove_btn = QPushButton("-")
        remove_btn.setFixedSize(28, 28)
        remove_btn.clicked.connect(self._remove_item)
        header.addWidget(remove_btn)
        header.addStretch()
        main_layout.addLayout(header)

        self.items_layout = QHBoxLayout()
        self.items_layout.setSpacing(4)
        main_layout.addLayout(self.items_layout)

        self._rebuild_spins()

    def _rebuild_spins(self):
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, val in enumerate(self._values):
            spin = QDoubleSpinBox()
            spin.setDecimals(3)
            spin.setMinimum(-100.0)
            spin.setMaximum(100.0)
            spin.setSingleStep(0.1)
            spin.setValue(val)
            spin.valueChanged.connect(partial(self._item_changed, i))
            self.items_layout.addWidget(spin)
        self.items_layout.addStretch()

    def _item_changed(self, index, val):
        self._values[index] = val
        self.value_changed.emit()

    def _add_item(self):
        self._values.append(0.0)
        self._rebuild_spins()
        self.value_changed.emit()

    def _remove_item(self):
        if len(self._values) > 1:
            self._values.pop()
            self._rebuild_spins()
            self.value_changed.emit()

    def get_value(self):
        return list(self._values)

    def set_value(self, val):
        self._values = list(val)
        self._rebuild_spins()


class IntListWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        self._values = list(param.value)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 2, 0, 2)

        header = QHBoxLayout()
        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        header.addWidget(label)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(self._add_item)
        header.addWidget(add_btn)

        remove_btn = QPushButton("-")
        remove_btn.setFixedSize(28, 28)
        remove_btn.clicked.connect(self._remove_item)
        header.addWidget(remove_btn)
        header.addStretch()
        main_layout.addLayout(header)

        self.items_layout = QHBoxLayout()
        self.items_layout.setSpacing(4)
        main_layout.addLayout(self.items_layout)

        self._rebuild_spins()

    def _rebuild_spins(self):
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, val in enumerate(self._values):
            spin = QSpinBox()
            spin.setMinimum(-100)
            spin.setMaximum(100)
            spin.setValue(val)
            spin.valueChanged.connect(partial(self._item_changed, i))
            self.items_layout.addWidget(spin)
        self.items_layout.addStretch()

    def _item_changed(self, index, val):
        self._values[index] = val
        self.value_changed.emit()

    def _add_item(self):
        self._values.append(0)
        self._rebuild_spins()
        self.value_changed.emit()

    def _remove_item(self):
        if len(self._values) > 1:
            self._values.pop()
            self._rebuild_spins()
            self.value_changed.emit()

    def get_value(self):
        return list(self._values)

    def set_value(self, val):
        self._values = list(val)
        self._rebuild_spins()


class TupleListWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        self._values = [list(t) for t in param.value]
        self._tuple_len = len(param.value[0]) if param.value else 2

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 2, 0, 2)

        header = QHBoxLayout()
        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        header.addWidget(label)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(self._add_row)
        header.addWidget(add_btn)

        remove_btn = QPushButton("-")
        remove_btn.setFixedSize(28, 28)
        remove_btn.clicked.connect(self._remove_row)
        header.addWidget(remove_btn)
        header.addStretch()
        main_layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(self._tuple_len)
        self.table.setMaximumHeight(150)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.cellChanged.connect(self._cell_changed)
        main_layout.addWidget(self.table)

        self._rebuild_table()

    def _rebuild_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self._values))
        for i, tup in enumerate(self._values):
            for j, val in enumerate(tup):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        self.table.blockSignals(False)

    def _cell_changed(self, row, col):
        try:
            val = int(self.table.item(row, col).text())
            self._values[row][col] = val
            self.value_changed.emit()
        except (ValueError, AttributeError):
            pass

    def _add_row(self):
        last = self._values[-1] if self._values else [0] * self._tuple_len
        self._values.append(list(last))
        self._rebuild_table()
        self.value_changed.emit()

    def _remove_row(self):
        if len(self._values) > 1:
            self._values.pop()
            self._rebuild_table()
            self.value_changed.emit()

    def get_value(self):
        return [tuple(t) for t in self._values]

    def set_value(self, val):
        self._values = [list(t) for t in val]
        self._rebuild_table()


def create_param_widget(param):
    """Factory: create the appropriate widget for a ConfigParam."""
    widgets = {
        "int": IntParamWidget,
        "float": FloatParamWidget,
        "bool": BoolParamWidget,
        "rgb": ColorParamWidget,
        "palette": PaletteWidget,
        "float_list": FloatListWidget,
        "int_list": IntListWidget,
        "tuple_list": TupleListWidget,
    }
    cls = widgets.get(param.param_type)
    if cls:
        return cls(param)
    return None

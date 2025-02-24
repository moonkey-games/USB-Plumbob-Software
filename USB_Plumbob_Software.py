from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QSlider,
    QComboBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import (
    QColor,
    QFontDatabase,
    QFont,
    QCursor,
    QPixmap,
)
import res # import qt resources

import serial.tools.list_ports

import re, sys, os

from utils import WidgetEffects, QPlumbob, ColorCircle
from ui import Ui_MainWindow

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_cursors()
        self.setup_window()
        self.load_custom_font()
        self.connect_signals()
        self.apply_effects()
        self.user_interaction = True
        self.color = QColor(0, 0, 0)
        self.plumbob = QPlumbob(self, self.plumbobGeometry, image_path=resource_path("ui/plumbob_shine.png"))
        self.setup_color_wheel()
        self.rgbSliderChanged()
        self.refresh()

    def setup_cursors(self):
        self.cursor = QCursor(QPixmap(resource_path("ui/cursor.png")), 1, 1)
        self.setCursor(self.cursor)
        self.cursorSelect = QCursor(QPixmap(resource_path("ui/cursor_select.png")), 6, 4)
        self.cursorClic = QCursor(QPixmap(resource_path("ui/cursor_clic.png")), 6, 4)
        self.cursorHand = QCursor(QPixmap(resource_path("ui/hand.png")), 6, 4)
        self.cursorGrab = QCursor(QPixmap(resource_path("ui/grab.png")), 6, 4)

    def setup_window(self):
        self.plumbobGeometry = (495, 80, 160, 329)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def load_custom_font(self):
        font_id = QFontDatabase.addApplicationFont(resource_path("ui/ITCKabelStdDemi.ttf"))
        if font_id == -1:
            print("Failed to load custom font.")

    def connect_signals(self):
        self.ui.testButton.clicked.connect(self.on_send_button_click)
        self.ui.testButton_2.clicked.connect(self.on_save_button_click)
        self.ui.closeButton.clicked.connect(self.close)
        self.ui.minusButton.clicked.connect(self.showMinimized)
        self.ui.refreshButton.clicked.connect(self.refresh)

        for slider in self.findChildren(QSlider):
            slider.installEventFilter(self)

        self.ui.redSlider.valueChanged.connect(self.rgbSliderChanged)
        self.ui.greenSlider.valueChanged.connect(self.rgbSliderChanged)
        self.ui.blueSlider.valueChanged.connect(self.rgbSliderChanged)
        self.ui.hueSlider.valueChanged.connect(self.hslSliderChanged)
        self.ui.saturationSlider.valueChanged.connect(self.hslSliderChanged)
        self.ui.lightnessSlider.valueChanged.connect(self.hslSliderChanged)

    def apply_effects(self):
        for button in self.findChildren(QPushButton):
            button.installEventFilter(self)
            WidgetEffects.apply_shadow(button)

        for combo in self.findChildren(QComboBox):
            combo.installEventFilter(self)
            combo.view().installEventFilter(self)
            WidgetEffects.apply_shadow(combo)
            combo.view().window().setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
            combo.view().window().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        for checkbox in self.findChildren(QCheckBox):
            checkbox.installEventFilter(self)
            WidgetEffects.apply_shadow(checkbox)

    def setup_color_wheel(self):
        self.wheel = ColorCircle(self, startupcolor=(0, 192, 0))
        self.wheel.setParent(self.ui.tab_wheel)
        self.wheel.setGeometry(25, 5, 283, 283)
        WidgetEffects.apply_shadow(self.wheel)
        self.ui.wheelValueSlider.valueChanged.connect(lambda x: self.wheel.setValue(x / 511))
        self.wheel.currentColorChanged.connect(self.wheelChanged)

    def plumbobSetCursor(self, color: QColor, event: str):
        if event in ["enter", "release"]:
            self.setCursor(self.cursorSelect)
        elif event == "leave":
            self.setCursor(self.cursor)
        elif event == "clic":
            self.setCursor(self.cursorClic)
            self.set_rgb_sliders(color, True)

    def set_rgb_sliders(self, color: QColor, bypass: bool = False):
        self.user_interaction = bypass
        self.ui.redSlider.setValue(color.red())
        self.ui.greenSlider.setValue(color.green())
        self.ui.blueSlider.setValue(color.blue())
        self.user_interaction = True

    def set_hsl_sliders(self, color: QColor):
        self.user_interaction = False
        h, s, l, _ = color.getHslF()
        self.ui.hueSlider.setValue(int(h * 360))
        self.ui.saturationSlider.setValue(int(s * 100))
        self.ui.lightnessSlider.setValue(int(l * 100))
        self.user_interaction = True

    def set_color_wheel(self, color: QColor):
        self.user_interaction = False
        self.wheel.setColor(color)
        self.ui.wheelValueSlider.setValue(int(color.valueF() * 511))
        self.user_interaction = True

    def rgbSliderChanged(self):
        self.ui.redLabel.setText(f"Red : {self.ui.redSlider.value()}")
        self.ui.greenLabel.setText(f"Green : {self.ui.greenSlider.value()}")
        self.ui.blueLabel.setText(f"Blue : {self.ui.blueSlider.value()}")
        if self.user_interaction:
            self.color = QColor(
                int(self.ui.redSlider.value()),
                int(self.ui.greenSlider.value()),
                int(self.ui.blueSlider.value()),
            )
            self.set_hsl_sliders(self.color)
            self.plumbob.change_color(self.color)
            self.set_color_wheel(self.color)
            self.updateWheelSliderColor()

    def hslSliderChanged(self):
        self.ui.hueLabel.setText(f"Hue : {self.ui.hueSlider.value()}°")
        self.ui.saturationLabel.setText(f"Saturation : {self.ui.saturationSlider.value()}%")
        self.ui.lightnessLabel.setText(f"Lightness : {self.ui.lightnessSlider.value()}%")
        if self.user_interaction:
            self.color = QColor().fromHslF(
                self.ui.hueSlider.value() / 360,
                self.ui.saturationSlider.value() / 100,
                self.ui.lightnessSlider.value() / 100,
                1,
            )
            self.set_rgb_sliders(self.color)
            self.plumbob.change_color(self.color)
            self.set_color_wheel(self.color)
            self.updateWheelSliderColor()

    def wheelChanged(self, color: QColor):
        if self.user_interaction:
            self.color = color
            self.set_hsl_sliders(self.color)
            self.set_rgb_sliders(self.color)
            self.plumbob.change_color(self.color)
            self.updateWheelSliderColor()

    def eventFilter(self, obj, event):
        if isinstance(obj, (QPushButton, QComboBox, QCheckBox)):
            if event.type() in [QEvent.Type.Enter, QEvent.Type.MouseButtonRelease]:
                self.setCursor(self.cursorSelect)
            elif event.type() == QEvent.Type.MouseButtonPress:
                self.setCursor(self.cursorClic)
            elif event.type() == QEvent.Type.Leave:
                self.setCursor(self.cursor)
        elif isinstance(obj, QSlider):
            if event.type() == QEvent.Type.Enter:
                self.setCursor(self.cursorHand)
            elif event.type() == QEvent.Type.Leave:
                self.setCursor(self.cursor)
            elif event.type() == QEvent.Type.MouseButtonPress:
                self.setCursor(self.cursorGrab)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.setCursor(self.cursorHand)

        if obj is self and event.type() == QEvent.Type.MouseButtonPress:
            for combo in self.findChildren(QComboBox):
                if combo.view().isVisible():
                    combo.hidePopup()
        return super().eventFilter(obj, event)

    def refresh(self):
        try:
            self.ui.comboBox.clear()
            ports = serial.tools.list_ports.comports()
            for port, desc, hwid in sorted(ports):
                if "1038:1500" in hwid:
                    print(f"{port}: {desc} [{hwid}]")
                    self.ui.comboBox.addItem(port)
            if self.ui.comboBox.count() > 0:
                self.ui.comboBox.setCurrentIndex(0)
        except Exception as e:
            print(e)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ui.closeButton.move(self.width() - 45, 15)
        self.ui.minusButton.move(self.width() - 90, 15)

    def on_send_button_click(self):
        try:
            ser = serial.Serial(self.ui.comboBox.currentText(), 115200, timeout=10)
            msg = f"SET RGB {self.color.red()} {self.color.green()} {self.color.blue()}\n"
            print(msg)
            ser.write(msg.encode())
        except Exception as e:
            print(e)

    def on_save_button_click(self):
        try:
            ser = serial.Serial(self.ui.comboBox.currentText(), 115200, timeout=10)
            msg = "SAVE SETTINGS\n"
            print(msg)
            ser.write(msg.encode())
        except Exception as e:
            print(e)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_position = event.globalPosition()

    def mouseMoveEvent(self, event):
        try:
            if self.old_position is not None:
                delta = event.globalPosition() - self.old_position
                self.move(self.x() + int(delta.x()), self.y() + int(delta.y()))
                self.old_position = event.globalPosition()
                self.update()
        except Exception as e:
            print(e)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_position = None

    def updateFontSize(self, value: int):
        font = QFont(self.custom_font, int(value))
        self.ui.testButton.setFont(font)

    def updateBorderRadius(self, value: int):
        self.editStylesheetProperty(self.ui.testButton, "QPushButton", "border-radius", f"{value}px")

    def updateWheelSliderColor(self):
        color = QColor()
        color.setHsvF(self.wheel.getHue(), self.wheel.getSaturation(), 1)
        self.editStylesheetProperty(
            self.ui.wheelValueSlider,
            "QSlider::groove",
            "background-color",
            f"qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgb({color.red()},{color.green()},{color.blue()}), stop: 1 #000000);",
        )

    def editStylesheetProperty(self, widget, selector: str, property_name: str, property_value: str):
        current_stylesheet = widget.styleSheet()
        pattern = r"(\s*" + re.escape(selector) + r"\s*{[^}]*" + re.escape(property_name) + r"\s*:\s*)([^;]+)"
        if re.search(pattern, current_stylesheet):
            new_stylesheet = re.sub(pattern, lambda match: match.group(1) + property_value, current_stylesheet)
        else:
            selector_pattern = r"(\s*" + re.escape(selector) + r"\s*{[^}]*})"
            if re.search(selector_pattern, current_stylesheet):
                new_stylesheet = re.sub(selector_pattern, r"\g<0> " + property_name + ": " + property_value + ";", current_stylesheet)
            else:
                new_stylesheet = current_stylesheet.strip() + f"\n{selector} {{ {property_name}: {property_value}; }}"
        widget.setStyleSheet(new_stylesheet)


def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    app = QApplication([])

    # Create and display the frameless window
    window = Window()
    window.show()

    app.exec()

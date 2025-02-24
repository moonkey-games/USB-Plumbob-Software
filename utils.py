from PyQt6.QtCore import (
    QPropertyAnimation,
    QVariantAnimation,
    Qt,
    QPoint,
    QPointF,
    QRect,
    pyqtSignal,
    QLineF,
)
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QWidget, QSizePolicy
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QConicalGradient,
    QRadialGradient,
    QResizeEvent,
    QPaintEvent,
    QMouseEvent,
    QPen,
    QPixmap,
)


class WidgetEffects:
    @staticmethod
    def apply_shadow(widget: QWidget, blur_radius: int = 10, offset: tuple = (0, 2), color: QColor = QColor(0, 0, 0, 120)) -> None:
        """Add a drop shadow effect to a widget."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur_radius)
        shadow.setOffset(*offset)
        shadow.setColor(color)
        widget.setGraphicsEffect(shadow)

    @staticmethod
    def apply_hover_animation(widget: QWidget, start_geometry: QRect, end_geometry: QRect, duration: int = 50) -> None:
        """Add a hover animation to a widget."""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setStartValue(start_geometry)
        animation.setEndValue(end_geometry)

        # Connect the animation to hover events
        def on_hover_enter():
            animation.setDirection(QPropertyAnimation.Direction.Forward)
            animation.start()

        def on_hover_leave():
            animation.setDirection(QPropertyAnimation.Direction.Backward)
            animation.start()

        widget.enterEvent = lambda event: on_hover_enter()
        widget.leaveEvent = lambda event: on_hover_leave()

    @staticmethod
    def apply_font_animation(widget: QWidget, start_size: int, end_size: int, duration: int = 50, font_family: str = "Arial") -> None:
        """Add an animation to change the font size of a widget."""
        animation = QVariantAnimation()
        animation.setStartValue(start_size)
        animation.setEndValue(end_size)
        animation.setDuration(duration)

        def update_font(value):
            font = widget.font()
            font.setPointSize(int(value))
            font.setFamily(font_family)
            widget.setFont(font)

        animation.valueChanged.connect(update_font)

        # Connect the animation to hover events
        widget.enterEvent = lambda event: animation.start()


class PlumbobBackground(QLabel):
    def __init__(self, color: QColor = QColor(0, 192, 0), parent: QWidget = None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shape_color = color  # Initialize the color of the diamond

    def paintEvent(self, event: QPaintEvent) -> None:
        """Handle the paint event to draw the diamond shape."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Disable the outline and set the fill color
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.shape_color)

        # Define the points of the diamond
        points = [
            QPoint(self.width() // 2, 0),  # Top
            QPoint(self.width(), self.height() // 2),  # Right
            QPoint(self.width() // 2, self.height()),  # Bottom
            QPoint(0, self.height() // 2),  # Left
        ]

        # Draw the diamond
        painter.drawPolygon(*points)

    def change_color(self, color: QColor) -> None:
        """Change the color of the diamond and redraw the widget."""
        self.shape_color = color
        self.update()


class PlumbobShine(QLabel):
    mouseEvent = pyqtSignal(QColor, str)

    def __init__(self, color: QColor, parent: QWidget = None):
        super().__init__(parent)
        self.mouse_inside = False  # Track the state of the mouse
        self.color = color

    def enterEvent(self, event: QMouseEvent) -> None:
        """Handle the event when the mouse enters the widget."""
        self.mouseEvent.emit(self.color, "enter")
        super().enterEvent(event)

    def leaveEvent(self, event: QMouseEvent) -> None:
        """Handle the event when the mouse leaves the widget."""
        self.mouseEvent.emit(self.color, "leave")
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle the event when the mouse is pressed on the widget."""
        self.mouseEvent.emit(self.color, "clic")
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle the event when the mouse is released on the widget."""
        self.mouseEvent.emit(self.color, "release")
        super().mouseReleaseEvent(event)


class QPlumbob:
    def __init__(self, parent: QWidget, geometry: tuple, initial_color: QColor = QColor(0, 192, 0), image_path: str = "ui/plumbob_shine.png"):
        """
        Initialize a QPlumbob with a color and geometry.

        :param parent: Parent widget.
        :param geometry: Tuple (x, y, width, height) to define the geometry.
        :param initial_color: Initial color of the diamond.
        :param image_path: Path to the PNG image with transparency.
        """
        self.parent = parent
        self.geometry = geometry
        self.initial_color = initial_color
        self.image_path = image_path

        # Create and configure the QLabel for the diamond
        self.plumbobBG = PlumbobBackground(color=initial_color, parent=parent)
        self.plumbobBG.setGeometry(*geometry)
        WidgetEffects.apply_shadow(self.plumbobBG)
        # Create and configure the QLabel for the image
        self.plumbobShine = PlumbobShine(self.initial_color, self.parent)
        self.plumbobShine.setGeometry(*geometry)

        # Load and configure the image if a path is provided
        if image_path:
            self.set_image(image_path)

    def set_image(self, image_path: str) -> None:
        """Set the image on the QLabel."""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                self.geometry[2],
                self.geometry[3],
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.plumbobShine.setPixmap(pixmap)

    def change_color(self, color: QColor) -> None:
        """Change the color of the diamond."""
        self.plumbobBG.change_color(color)


class ColorCircle(QWidget):
    currentColorChanged = pyqtSignal(QColor)

    def __init__(self, parent: QWidget = None, startupcolor: list = [255, 255, 255], margin: int = 10) -> None:
        super().__init__(parent=parent)
        self.radius = 0
        self.selected_color = QColor(startupcolor[0], startupcolor[1], startupcolor[2], 255)
        self.x = 0.5
        self.y = 0.5
        self.h = self.selected_color.hueF()
        self.s = self.selected_color.saturationF()
        self.v = self.selected_color.valueF()
        self.margin = margin

        qsp = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

    def resizeEvent(self, ev: QResizeEvent) -> None:
        """Handle the resize event to adjust the size of the color circle."""
        size = min(self.width(), self.height()) - self.margin * 2
        self.radius = size / 2
        self.square = QRect(0, 0, size, size)
        self.square.moveCenter(self.rect().center())

    def paintEvent(self, ev: QPaintEvent) -> None:
        """Handle the paint event to draw the color circle."""
        center = QPointF(self.width() / 2, self.height() / 2)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setViewport(
            self.margin,
            self.margin,
            self.width() - 2 * self.margin,
            self.height() - 2 * self.margin,
        )
        hsv_grad = QConicalGradient(center, 90)
        for deg in range(360):
            col = QColor.fromHsvF(deg / 360, 1, self.v)
            hsv_grad.setColorAt(deg / 360, col)

        val_grad = QRadialGradient(center, self.radius)
        val_grad.setColorAt(0.0, QColor.fromHsvF(0.0, 0.0, self.v, 1.0))
        val_grad.setColorAt(1.0, Qt.GlobalColor.transparent)

        p.setPen(Qt.GlobalColor.transparent)
        p.setBrush(hsv_grad)
        p.drawEllipse(self.square)
        p.setBrush(val_grad)
        p.drawEllipse(self.square)

        line = QLineF.fromPolar(self.radius * self.s, 360 * self.h + 90)
        line.translate(QPointF(self.rect().center()))

        # Draw the border with radial gradient
        border_rect = self.square.adjusted(-5, -5, 5, 5)
        center = QPointF(border_rect.center())
        radius = border_rect.width() / 2
        border_grad = QRadialGradient(center, radius)
        border_grad.setColorAt(
            (border_rect.width() - 10) / border_rect.width(), QColor(255, 255, 255)
        )
        border_grad.setColorAt(1.0, QColor(245, 245, 245))
        p.setPen(QPen(border_grad, 10))
        p.setBrush(Qt.GlobalColor.transparent)
        p.drawEllipse(border_rect)

        # shadow on picker
        shadow = QRadialGradient(line.p2() + QPointF(0, 1.5), 20)
        shadow.setColorAt(0.4, QColor(0, 0, 0, 115))
        shadow.setColorAt(0.85, Qt.GlobalColor.transparent)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(shadow)
        p.drawEllipse(line.p2() + QPointF(0, 1.5), 20, 20)

        # picker
        border_grad = QRadialGradient(line.p2(), 10)
        border_grad.setColorAt(12 / 14, QColor(255, 255, 255))
        border_grad.setColorAt(1.0, QColor(245, 245, 245))
        p.setPen(QPen(border_grad, 4))
        p.setBrush(self.selected_color)
        p.drawEllipse(line.p2(), 12, 12)

    def recalc(self) -> None:
        """Recalculate the selected color and emit the color changed signal."""
        self.selected_color.setHsvF(self.h, self.s, self.v)
        self.currentColorChanged.emit(self.selected_color)
        self.repaint()

    def map_color(self, x: int, y: int) -> QColor:
        """Map the given coordinates to a color in the HSV color space."""
        line = QLineF(QPointF(self.rect().center()), QPointF(x, y))
        s = min(1.0, line.length() / self.radius)
        h = (line.angle() - 90) / 360 % 1.0
        return QColor.fromHsvF(h, s, self.v)

    def processMouseEvent(self, ev: QMouseEvent) -> None:
        """Process mouse events to update the selected color."""
        if ev.button() == Qt.MouseButton.RightButton:
            self.h, self.s, self.v = 0, 0, 1
        else:
            color = self.map_color(ev.pos().x(), ev.pos().y())
            self.h, self.s, self.v = color.hueF(), color.saturationF(), color.valueF()
        self.x = ev.pos().x() / self.width()
        self.y = ev.pos().y() / self.height()
        self.recalc()

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        """Handle mouse move events."""
        self.processMouseEvent(ev)

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        """Handle mouse press events."""
        self.processMouseEvent(ev)

    def setHue(self, hue: float) -> None:
        """Set the hue value and recalculate the color."""
        if 0 <= hue <= 1:
            self.h = float(hue)
            self.recalc()
        else:
            raise TypeError("Value must be between 0.0 and 1.0")

    def setSaturation(self, saturation: float) -> None:
        """Set the saturation value and recalculate the color."""
        if 0 <= saturation <= 1:
            self.s = float(saturation)
            self.recalc()
        else:
            raise TypeError("Value must be between 0.0 and 1.0")

    def setValue(self, value: float) -> None:
        """Set the value (brightness) and recalculate the color."""
        if 0 <= value <= 1:
            self.v = float(value)
            self.recalc()
        else:
            raise TypeError("Value must be between 0.0 and 1.0")

    def setColor(self, color: QColor) -> None:
        """Set the color using a QColor object and recalculate."""
        self.h = color.hueF()
        self.s = color.saturationF()
        self.v = color.valueF()
        self.recalc()

    def getHue(self) -> float:
        """Get the current hue value."""
        return self.h

    def getSaturation(self) -> float:
        """Get the current saturation value."""
        return self.s

    def getValue(self) -> float:
        """Get the current value (brightness)."""
        return self.v

    def getColor(self) -> QColor:
        """Get the current selected color."""
        return self.selected_color

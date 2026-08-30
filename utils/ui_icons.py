from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def toolbar_icon(name, size=18, color='#56616b'):
    """Create a crisp monochrome toolbar icon without external bitmap assets."""
    ratio = 2
    pixmap = QPixmap(size * ratio, size * ratio)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.scale(ratio, ratio)
    pen = QPen(QColor(color), 1.35)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    if name == 'image':
        painter.drawRoundedRect(QRectF(2.5, 3.0, 13.0, 12.0), 1.5, 1.5)
        painter.drawEllipse(QPointF(11.8, 6.5), 1.2, 1.2)
        path = QPainterPath(QPointF(4.0, 13.0))
        path.lineTo(7.1, 9.4)
        path.lineTo(9.4, 11.7)
        path.lineTo(11.0, 10.1)
        path.lineTo(14.0, 13.0)
        painter.drawPath(path)
    elif name == 'folder':
        path = QPainterPath(QPointF(2.5, 5.0))
        path.lineTo(7.0, 5.0)
        path.lineTo(8.3, 6.4)
        path.lineTo(15.5, 6.4)
        path.lineTo(14.2, 14.0)
        path.lineTo(3.4, 14.0)
        path.closeSubpath()
        painter.drawPath(path)
    elif name == 'import':
        painter.drawRoundedRect(QRectF(3.0, 10.0, 12.0, 5.0), 1.2, 1.2)
        painter.drawLine(QPointF(9.0, 2.5), QPointF(9.0, 11.3))
        painter.drawLine(QPointF(5.8, 8.2), QPointF(9.0, 11.4))
        painter.drawLine(QPointF(12.2, 8.2), QPointF(9.0, 11.4))
    elif name == 'export':
        painter.drawRoundedRect(QRectF(3.0, 6.0, 9.0, 9.0), 1.2, 1.2)
        painter.drawLine(QPointF(8.0, 10.0), QPointF(15.0, 3.0))
        painter.drawLine(QPointF(10.4, 3.0), QPointF(15.0, 3.0))
        painter.drawLine(QPointF(15.0, 3.0), QPointF(15.0, 7.6))
    elif name == 'cursor':
        path = QPainterPath(QPointF(4.0, 2.5))
        path.lineTo(14.2, 9.0)
        path.lineTo(9.6, 10.0)
        path.lineTo(7.5, 15.0)
        path.closeSubpath()
        painter.drawPath(path)
    elif name == 'hand':
        path = QPainterPath(QPointF(5.0, 8.7))
        path.lineTo(5.0, 5.3)
        path.quadTo(5.0, 4.2, 6.0, 4.2)
        path.quadTo(7.0, 4.2, 7.0, 5.3)
        path.lineTo(7.0, 3.8)
        path.quadTo(7.0, 2.7, 8.0, 2.7)
        path.quadTo(9.0, 2.7, 9.0, 3.8)
        path.lineTo(9.0, 5.0)
        path.quadTo(9.0, 3.9, 10.0, 3.9)
        path.quadTo(11.0, 3.9, 11.0, 5.0)
        path.lineTo(11.0, 5.8)
        path.quadTo(11.0, 4.8, 12.0, 4.8)
        path.quadTo(13.0, 4.8, 13.0, 5.9)
        path.lineTo(13.0, 10.0)
        path.quadTo(12.8, 15.0, 8.7, 15.0)
        path.quadTo(6.2, 15.0, 4.2, 12.0)
        path.lineTo(2.9, 10.2)
        path.quadTo(2.2, 9.2, 3.0, 8.5)
        path.quadTo(3.8, 7.9, 5.0, 8.7)
        painter.drawPath(path)
    elif name in ('zoom_in', 'zoom_out'):
        painter.drawEllipse(QPointF(7.5, 7.5), 5.0, 5.0)
        painter.drawLine(QPointF(11.2, 11.2), QPointF(15.2, 15.2))
        painter.drawLine(QPointF(5.0, 7.5), QPointF(10.0, 7.5))
        if name == 'zoom_in':
            painter.drawLine(QPointF(7.5, 5.0), QPointF(7.5, 10.0))
    elif name == 'reset':
        path = QPainterPath(QPointF(4.0, 6.2))
        path.cubicTo(6.4, 2.8, 12.3, 3.0, 14.0, 7.0)
        path.cubicTo(15.5, 10.6, 12.8, 14.6, 9.0, 14.6)
        painter.drawPath(path)
        painter.drawLine(QPointF(4.0, 6.2), QPointF(4.3, 2.8))
        painter.drawLine(QPointF(4.0, 6.2), QPointF(7.3, 6.0))
    elif name == 'palette':
        painter.drawEllipse(QRectF(2.5, 3.0, 13.0, 12.0))
        painter.drawEllipse(QPointF(6.0, 6.4), 0.8, 0.8)
        painter.drawEllipse(QPointF(9.0, 5.5), 0.8, 0.8)
        painter.drawEllipse(QPointF(12.0, 7.0), 0.8, 0.8)
        painter.drawEllipse(QPointF(10.8, 11.2), 1.8, 1.4)

    painter.end()
    pixmap.setDevicePixelRatio(ratio)
    return QIcon(pixmap)

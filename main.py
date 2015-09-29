#!env python

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(1280, 720)
        view = QGraphicsView(self)
        scene = QGraphicsScene()
        scene.setSceneRect(0, 0, 1280, 720)
        view.setScene(scene)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);

        self.setCentralWidget(view)
        self.scene = scene

        bg = QBrush(QPixmap('bg.png'))
        scene.setBackgroundBrush(bg)
        window1 = Window(QRect(100, 200, 500, 300))
        compiz = Compositor(scene)
        compiz.addWindow(window1)
        window2 = Window(QRect(200, 100, 500, 300))
        compiz.addWindow(window2)

class Compositor(object):
    def __init__(self, scene):
        self.scene = scene
        self.windows = []
        # self.buffer = QImage(1280, 720, QImage.Format_ARGB32)
        # self.painter = QPainter(self.buffer)
        self.needRender = False

    def invalidate(self, window):
        if not self.needRender:
            self.needRender = True
            index = self.windows.index(window)
            for w in self.windows:
                i = self.windows.index(w)
                if i >= index and w.collidesWithItem(window):
                    w.updateBackground()

    def addWindow(self, window):
        self.windows.append(window)
        window.compositor = self
        window.events.changed.connect(self.invalidate)
        self.scene.addItem(window)

    def renderBackground(self, buffer, pos, rect):
        painter = QPainter(buffer)
        r = QRectF(pos.x(), pos.y(), rect.width(), rect.height())
        self.scene.render(painter, source=r, target=QRectF(0,0,rect.width(),rect.height()))
        self.needRender = False
        return QPixmap(buffer)

    def getBackground(self, window):
        index = self.windows.index(window)
        for w in self.windows:
            if w.bg is not None and w.collidesWithItem(window):
                i = self.windows.index(w)
                if i >= index:
                    w.bg.hide()
                    w.title.hide()
                    w.border.setOpacity(0)
        bg = self.renderBackground(
            window.buffer,
            QPointF(window.scenePos().x(), window.scenePos().y()+window.titleHeight),
            QRect(0, 0, window.border.boundingRect().width(), window.border.boundingRect().height())
        )
        for w in self.windows:
            if w.bg is not None and not w.bg.isVisible():
                w.bg.show()
                w.title.show()
                w.border.setOpacity(1)
                # w.border.show()
        return bg

class Window(QGraphicsItemGroup):
    def __init__(self, rect):
        QGraphicsItemGroup.__init__(self)
        self.setPos(rect.x(), rect.y())
        self.titleHeight = 30
        self.buffer = QImage(rect.width(), rect.height() - self.titleHeight, QImage.Format_RGB16)
        self.bg = None
        self.title = QGraphicsRectItem(QRectF(rect.x(), rect.y(), rect.width(), self.titleHeight))
        self.title.setBrush(QColor('#222'))
        self.title.setZValue(10)
        self.text = QGraphicsTextItem('Window')
        self.text.setZValue(15)
        self.text.setPos(rect.x() + 10, rect.y())
        self.text.setDefaultTextColor(QColor('#eee'))
        self.border = QGraphicsRectItem(QRectF(rect.x(), rect.y()+self.titleHeight, rect.width(), rect.height()-self.titleHeight))
        self.border.setPen(QPen(QColor('#444')))
        self.border.setZValue(5)
        self.addToGroup(self.border)
        self.addToGroup(self.title)
        self.addToGroup(self.text)
        self.effect = QGraphicsBlurEffect()
        self.effect.setBlurRadius(8)
        self.effect.setBlurHints(QGraphicsBlurEffect.PerformanceHint)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.lastPos = None

        class Emitter(QObject):
            changed = pyqtSignal(Window)

        self.events = Emitter()
        self.events.changed.emit(self)

    def updateBackground(self):
        bg = self.compositor.getBackground(self)
        if self.bg is None:
            self.bg = QGraphicsPixmapItem(bg)
            self.bg.setPos(self.pos().x(), self.pos().y()+30)
            self.addToGroup(self.bg)
            self.bg.setZValue(0)
            self.bg.setGraphicsEffect(self.effect)
        else:
            self.bg.setPixmap(bg)

    def paint(self, *args):
        if self.lastPos != self.pos():
            self.events.changed.emit(self)
            self.lastPos = self.pos()
        QGraphicsItemGroup.paint(self, *args)

app = QApplication(sys.argv)
win = MainWindow()
win.show()
app.exec_()
sys.exit()

#coding:utf-8

from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QPushButton, QLabel, QGridLayout, QFileDialog, QFrame, QDesktopWidget
from PyQt5.QtGui import QPixmap, QCursor, QBitmap, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint, QThread, pyqtSignal
import sys
from system_hotkey import SystemHotkey


class TakeScreenshotWindow(QWidget):
    sig = pyqtSignal()

    def __init__(self):
        super(TakeScreenshotWindow, self).__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)  # 无边框 置顶 不显示任务栏图标
        self.setStyleSheet('''background-color:black; ''')
        self.setWindowOpacity(0.3)
        self.desktopRect = QDesktopWidget().screenGeometry()
        self.setGeometry(self.desktopRect)
        self.setCursor(Qt.CrossCursor)
        self.blackMask = QBitmap(self.desktopRect.size())
        self.blackMask.fill(Qt.black)
        self.availTopLeftPoint = QDesktopWidget().availableGeometry().topLeft()  # 有效显示区域左上角点

        self.isDrawing = False
        self.startPoint = QPoint()
        self.endPoint = QPoint()

        self.hk_start, self.hk_stop = SystemHotkey(), SystemHotkey()  # 初始化两个热键
        # 绑定快捷键和对应的信号发送函数
        self.hk_start.register(('control', '1'), callback=lambda x: self.send_key_event("snap1"))
        self.hk_stop.register(('control', 'shift', 'j'), callback=lambda x: self.send_key_event("snap2"))

        self.sig.connect(self.create_chlid_win)
        self.childWinDict = {}
        self.childWinNum = 0

    def create_chlid_win(self):
        self.childWinNum += 1
        self.childWinDict[self.childWinNum] = DisplayWindow(self.screenshot, self.startPoint + self.availTopLeftPoint)
        self.childWinDict[self.childWinNum].show()

    # 热键信号发送函数(将外部信号，转化成qt信号)
    def send_key_event(self, i_str):
        self.show()  # 显示截图窗口

    def paintEvent(self, event):
        if self.isDrawing:
            self.mask = self.blackMask.copy()
            pp = QPainter(self.mask)
            pen = QPen()
            pen.setStyle(Qt.NoPen)
            pp.setPen(pen)
            brush = QBrush(Qt.white)
            pp.setBrush(brush)
            pp.drawRect(QRect(self.startPoint, self.endPoint))
            self.setMask(QBitmap(self.mask))

    def keyPressEvent(self, event):  # Q键关闭窗口
        if event.key() == Qt.Key_F3:
            self.show()

    def mousePressEvent(self, event):
        print("press")
        if event.button() == Qt.LeftButton:
            self.isDrawing = True
            self.startPoint = event.pos()  # 相对有效区域左上角点的坐标
            self.endPoint = self.startPoint

    def mouseMoveEvent(self, event):
        if Qt.LeftButton and self.isDrawing:
            self.endPoint = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.endPoint = event.pos()
            self.isDrawing = False

            if abs(self.endPoint.x() - self.startPoint.x()) > 10 and abs(self.endPoint.y() - self.startPoint.y()) > 10:  # 框选区域太小不进行截图
                screenshot = QApplication.primaryScreen().grabWindow(QApplication.desktop().winId())  # 全屏截图
                self.screenshot = screenshot.copy(QRect(self.startPoint + self.availTopLeftPoint, self.endPoint + self.availTopLeftPoint))
                # self.screenshot.save('./test.jpg', format='JPG', quality=100)

                self.hide() # 隐藏截图窗口
                self.setMask(QBitmap((self.blackMask.copy())))  # 恢复窗口mask

                # 在子窗口中显示截图
                # app = DisplayWindow(self.screenshot, self.startPoint + self.availTopLeftPoint)
                # # app.exec_()
                # app.show()

                self.sig.emit()  # 触发信号创建新的子窗口


class DisplayWindow(QWidget):
    def __init__(self, screenshot=None, lefttop=None):
        super(DisplayWindow, self).__init__()
        self.screenshot = screenshot
        self.leftTop = lefttop
        self.create_widgets()

    def create_widgets(self):
        self.widgets_created = True
        self.img_preview = QLabel()
        self.move(self.leftTop)  # 移动到框选区域附近

        print(self.img_preview.frameGeometry())
        self.img_preview.setFrameShape(QFrame.Panel)  # Box Panel
        self.img_preview.setFrameShadow(QFrame.Raised)  # Raised、Sunken、Plain
        self.img_preview.setLineWidth(1)
        self.img_preview.setStyleSheet('background-color: rgb(0, 255, 255, 100)')

        self.img_preview.setPixmap(self.screenshot)
        self.resize(self.screenshot.width(), self.screenshot.height())
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SplashScreen)  # 隐藏标题栏 窗口置顶 隐藏任务栏图标
        self.set_layout()


    def set_layout(self):
        self.layout = QGridLayout(self)
        self.layout.addWidget(self.img_preview)
        self.setLayout(self.layout)

    def save_screenshot(self):
        img, _ = QFileDialog.getSaveFileName(self,"Salvar Arquivo", filter="PNG(*.png);; JPEG(*.jpg)")
        if img[-3:] == "png":
            self.screenshot.save(img, "png")
        elif img[-3:] == "jpg":
            self.screenshot.save(img, "jpg")
        else:
            self.screenshot.save(img + ".png", "png")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_drag = True
            self.m_DragPosition = event.globalPos() - self.pos()
            event.accept()
            self.setCursor(QCursor(Qt.OpenHandCursor))

    def mouseMoveEvent(self, event):
        if Qt.LeftButton and self.m_drag:
            self.move(event.globalPos() - self.m_DragPosition)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_drag = False
            self.setCursor(QCursor(Qt.ArrowCursor))

    def keyPressEvent(self, event):  # Q键关闭窗口
        if event.key() == Qt.Key_Q:
            self.close()
        elif event.key() == Qt.Key_S:
            self.save_screenshot()

    def mouseDoubleClickEvent(self, event):  # 双击关闭窗口
        if event.button() == Qt.LeftButton:
            self.close()


root = QApplication(sys.argv)
app = TakeScreenshotWindow()
app.show()
sys.exit(root.exec_())

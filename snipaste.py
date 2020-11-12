#coding:utf-8

import sys
from system_hotkey import SystemHotkey
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QPushButton, QLabel, QGridLayout, QFileDialog, QFrame, QDesktopWidget
from PyQt5.QtGui import QPixmap, QCursor, QBitmap, QPainter, QPen, QBrush, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint, QThread, pyqtSignal


class GrabToolWindow(QWidget):
    """抓取工具窗口，显示在最前端"""
    sigDisplay = pyqtSignal()  # 创建信号，用于新建贴图窗口
    sigScreenShot = pyqtSignal()

    def __init__(self):
        super(GrabToolWindow, self).__init__()
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
        self.hk_start.register(('control', '1'), callback=lambda x: self.showGrabWindow())
        self.hk_stop.register(('control', 'shift', 'j'), callback=lambda x: self.showGrabWindow())

        self.sigDisplay.connect(self.createDisplayWin)  # 信号连接到子窗口创建函数
        self.displayWinDict = {}
        self.displayWinNum = 0

        self.sigScreenShot.connect(self.createScreenShotWin)

    def createDisplayWin(self):  # 这里使用字典存储新建的窗口，当窗口关闭时未进行内存释放，可进行优化
        self.displayWinDict[self.displayWinNum] = DisplayWindow(self.screenshot, self.startPoint + self.availTopLeftPoint, self.displayWinNum)
        self.displayWinDict[self.displayWinNum].show()
        self.displayWinNum += 1

    def createScreenShotWin(self):
        self.screenshotWindow = ScreenshotWindow()
        self.screenshot_full_screen = self.screenshotWindow.screenShot
        self.screenshotWindow.show()

    def showGrabWindow(self):
        self.sigScreenShot.emit()  # 创建并显示全屏截图窗口
        self.activateWindow() # 激活窗口以在最顶部显示
        self.setWindowState(Qt.WindowActive)  # 设置为激活窗口，以便使用快捷键
        self.show()  # 显示抓取窗口（主窗口）

    def keyPressEvent(self, event):  # Alt+Q键或ESC关闭窗口退出程序
        if event.key() == Qt.Key_Escape:
            self.close(), exit(0)
        elif event.key() == Qt.Key_Q:
            if QApplication.keyboardModifiers() == Qt.AltModifier:
                self.close(), exit(0)

    def paintMask(self):
        self.mask = self.blackMask.copy()
        pp = QPainter(self.mask)
        pen = QPen()
        pen.setStyle(Qt.NoPen)
        pp.setPen(pen)
        brush = QBrush(Qt.white)
        pp.setBrush(brush)
        pp.drawRect(QRect(self.startPoint, self.endPoint))
        self.setMask(QBitmap(self.mask))
        self.update()

    def paintEvent(self, event):
        if self.isDrawing:
            self.paintMask()

    def mousePressEvent(self, event):
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
            self.paintMask()  # 确保mask绘制完整
            self.isDrawing = False

            if self.endPoint.x() - self.startPoint.x() > 10 and self.endPoint.y() - self.startPoint.y() > 10:  # 框选区域太小或从右至左框选不进行截图
                self.screenshot = self.screenshot_full_screen.copy(QRect(self.startPoint, self.endPoint))  # 截取框选区域
                self.hide() # 隐藏抓取工具窗口
                self.screenshotWindow.close()  # 关闭全屏截图显示窗口
                self.sigDisplay.emit()  # 触发信号创建新的子窗口来显示截图

            self.setMask(QBitmap((self.blackMask.copy())))  # 框选操作结束, 恢复窗口mask


class DisplayWindow(QWidget):
    """贴图窗口"""
    def __init__(self, screenshot, lefttop, num):
        super(DisplayWindow, self).__init__()
        self.screenshot = screenshot
        self.leftTop = lefttop
        self.num = num
        self.isopen = True

        self.color_board = [QColor(0, 255, 255, 200),  # 浅蓝
                            QColor(0, 255, 0, 200),    # 绿
                            QColor(255, 255, 0, 200),  # 黄
                            QColor(255, 0, 255, 200),  # 紫
                            QColor(255, 0, 0, 200),    # 红
                            QColor(0, 0, 255, 200), ]  # 蓝

        self.createWindow()  # 利用窗口背景显示截图
        # self.createWindowLabel()  # 利用label显示截图（位置不好控制）

    def createWindow(self):
        self.move(self.leftTop)  # 移动到框选区域附近
        self.resize(self.screenshot.width(), self.screenshot.height())
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SplashScreen)  # 隐藏标题栏（无边框） 窗口置顶 隐藏任务栏图标

        # 设置窗口背景为抓取的截图区域
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(QPixmap(self.screenshot)))
        self.setPalette(palette)

        self.activateWindow()  # 激活窗口以在最顶部显示
        self.setWindowState(Qt.WindowActive)  # 设置为激活窗口以加深阴影显示效果

    def paintEvent(self, event):  # 绘制边框
        rect = QRect(QPoint(0,0), QPoint(self.width()-2, self.height()-2))
        painter = QPainter(self)
        painter.setPen(QPen(self.color_board[self.num % len(self.color_board)], 1, Qt.SolidLine))
        painter.drawRect(rect)

    def createWindowLabel(self):
        color_board = ['background-color: rgb(0, 255, 255, 100)',  # 浅蓝
                       'background-color: rgb(0, 255, 0, 100)',  # 绿
                       'background-color: rgb(255, 255, 0, 100)',  # 黄
                       'background-color: rgb(255, 0, 255, 100)',  # 紫
                       'background-color: rgb(255, 0, 0, 100)',  # 红
                       'background-color: rgb(0, 0, 255, 100)',  # 蓝
                       ]
        self.move(self.leftTop)  # 移动到框选区域附近
        self.resize(self.screenshot.width(), self.screenshot.height())
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SplashScreen)  # 隐藏标题栏（无边框） 窗口置顶 隐藏任务栏图标

        # 利用label显示截图区域
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明
        self.imgLabel = QLabel()
        self.imgLabel.setFrameShape(QFrame.Panel)  # Box Panel
        self.imgLabel.setFrameShadow(QFrame.Raised)  # Raised、Sunken、Plain
        self.imgLabel.setLineWidth(1)
        self.imgLabel.setStyleSheet(color_board[self.num % len(color_board)])
        self.imgLabel.setPixmap(self.screenshot)
        self.layout = QGridLayout(self)
        self.layout.addWidget(self.imgLabel)
        self.setLayout(self.layout)

        self.activateWindow()  # 激活窗口以在最顶部显示
        self.setWindowState(Qt.WindowActive)  # 设置为激活窗口以便使用快捷键

    def save_screenshot(self):
        img, formate = QFileDialog.getSaveFileName(self,"Salvar Arquivo", filter="PNG(*.png);; JPEG(*.jpg)")
        if img[-3:] == "png":
            self.screenshot.save(img, "png", quality=100)
        elif img[-3:] == "jpg":
            self.screenshot.save(img, "jpg", quality=100)
        elif formate == "PNG(*.png)":
            self.screenshot.save(img + ".png", "png", quality=100)
        elif formate == "JPEG(*.jpg)":
            self.screenshot.save(img + ".jpg", "jpg", quality=100)

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt+Q退出程序
                exit(0)
            else: # Q键关闭窗口
                self.close()
                self.isopen = False  # 窗口关闭
        elif event.key() == Qt.Key_S:
            self.save_screenshot()

    def mouseDoubleClickEvent(self, event):  # 双击关闭窗口
        if event.button() == Qt.LeftButton:
            self.close()
            self.isopen = False  # 窗口关闭

    def isOpen(self):
        return self.isopen


class ScreenshotWindow(QWidget):
    """全屏截图窗口，抓取全屏截图（显示在截图工具窗口下面）"""
    def __init__(self):
        super(ScreenshotWindow, self).__init__()
        availTopLeftPoint = QDesktopWidget().availableGeometry().topLeft()  # 有效显示区域左上角点
        availBottomRightPoint = QDesktopWidget().availableGeometry().bottomRight()  # 有效显示区域左上角点
        self.screenshot = QApplication.primaryScreen().grabWindow(QApplication.desktop().winId())  # 全屏截图
        self.screenshot = self.screenshot.copy(QRect(availTopLeftPoint, availBottomRightPoint))  # 获取有效区域截图
        self.resize(self.screenshot.width(), self.screenshot.height())

        # 设置窗口背景为截图
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(QPixmap(self.screenshot)))
        self.setPalette(palette)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SplashScreen)  # Qt.WindowStaysOnTopHint

    def mouseDoubleClickEvent(self, event):  # 双击关闭窗口
        if event.button() == Qt.LeftButton:
            self.close()

    @property
    def screenShot(self):
        return self.screenshot


root = QApplication(sys.argv)
app = GrabToolWindow()
# app.showGrabWindow()
sys.exit(root.exec_())

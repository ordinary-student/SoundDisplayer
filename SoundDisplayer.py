# -*- coding:utf-8 -*-
import random
import sys
import keyword
from PySide2.QtCore import QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, QRect, QThread, Signal, Qt, Property
from PySide2.QtGui import QColor, QFont, QIcon, QPalette, QPixmap, QMouseEvent, QContextMenuEvent, QKeyEvent
from PySide2.QtWidgets import QAction, QApplication, QLabel, QMenu, QMessageBox, QWidget
import pyqtgraph as pg
import numpy as np
import pyaudio
import audioop

# app名称
APP_NAME = '''SoundDisplayer'''
# app信息
APP_MESSAGE = '''声音立绘展示器'''
# 作者
AUTHOR = '''ordinary-student'''
# 版本
VERSION = '''v2.0.0'''
# 最后更新日期
LAST_UPDATE = '''2021-07-11'''

# 身体图片路径
BODY_PIC_PATH = '''resources/body.png'''
# 头发图片路径
HAIR_PIC_PATH = '''resources/hair.png'''
# 关于图片路径
ABOUT_PIC_PATH = '''resources/about.png'''
# 退出图片路径
EXIT_PIC_PATH = '''resources/exit.png'''


class DetectSoundThread(QThread):
    '''创建检测麦克风音量线程类'''
    # 声音采样信号 发射类型为list
    volume_signal = Signal(list)

    def __init__(self):
        '''构造函数'''
        super(DetectSoundThread, self).__init__()
        # 运行标志
        self.runFlag = True

    def run(self):
        '''线程运行'''
        # 初始化PyAudio实例
        p = pyaudio.PyAudio()
        # 打开音频流对象 读取话筒输入缓冲区
        stream = p.open(format=pyaudio.paInt16, channels=1,
                        rate=44100, input=True)
        # 用于存放响度值的列表
        volume = []
        # 无限循环读取话筒音频流 必须在run()里面实现 否则UI界面会卡死
        while self.runFlag:
            # 每次读取3个采样点
            data = stream.read(3)
            # 使用audioop.rms计算音量响度 然后通过开方和除法缩小数值
            volume.append(audioop.rms(data, 2) ** 0.8 / 4000 + 1)
            # 当列表长度到达180个时
            if len(volume) == 180:
                # 将响度列表发射给主窗口线程
                self.volume_signal.emit(volume)
                # 清空列表 重新采样
                volume = []

    def stop(self):
        '''停止线程'''
        self.runFlag = False


class HairLabel(QLabel):
    '''用于显示假发的QLabel类'''

    def __init__(self, w: int, h: int, parent: QWidget):
        '''构造函数'''
        # w, h参数接受宽高 parent接受的是主窗口对象
        # 将主窗口传给parent后 通过super()将假发部件嵌入主窗口界面
        super(HairLabel, self).__init__(parent)

        # 加载本地假发png文件
        pixmap = QPixmap(HAIR_PIC_PATH)
        # 抗锯齿缩放至指定大小
        pixmap = pixmap.scaled(w, h, Qt.IgnoreAspectRatio,
                               Qt.SmoothTransformation)
        # 用setPixmap将假发展示到QLabel上
        self.setPixmap(pixmap)

    def mousePressEvent(self, e: QMouseEvent):
        '''重写鼠标按下事件'''
        # 左键按下
        if e.buttons() == Qt.LeftButton:
            # 记录第一下鼠标点击的坐标
            self.start_pos = e.pos()

    def mouseMoveEvent(self, e: QMouseEvent):
        '''重写鼠标移动事件'''
        # 左键按下
        if e.buttons() == Qt.LeftButton:
            # 移动至当前坐标加上鼠标移动偏移量
            self.move(self.pos() + e.pos() - self.start_pos)


class TextLabel(QLabel):
    '''用于显示文字的QLabel类'''

    def __init__(self, text: str, parent: QWidget):
        '''构造函数'''
        super().__init__(text, parent)
        self.text_animation = None

    def setTextColor(self, color: QColor):
        '''设置文字颜色'''
        # 调色板
        palette = self.palette()
        # 设置字体颜色
        palette.setColor(QPalette.WindowText, color)
        # 上色
        self.setPalette(palette)

    # 颜色属性
    color = Property(QColor, fset=setTextColor)

    def startAnimation(self):
        '''启动动画'''
        # 停止上次的动画
        self.stopAnimation()
        # 创建动画
        self.text_animation = QPropertyAnimation(self, b"color")
        # 持续随机10-15秒
        self.text_animation.setDuration(random.randint(10000, 15000))

        # 起始值 红色
        self.text_animation.setStartValue(QColor(255, 0, 0, 100))
        # 循环设置关键帧
        for i in range(7):
            self.text_animation.setKeyValueAt(
                i/8, QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(50, 255)))
        # 结束值 红
        self.text_animation.setEndValue(QColor(255, 0, 0, 100))
        # 开始动画
        self.text_animation.start()

    def stopAnimation(self):
        '''停止动画'''
        if self.text_animation != None:
            self.text_animation.stop()

    def mousePressEvent(self, e: QMouseEvent):
        '''重写鼠标按下事件'''
        # 左键按下
        if e.buttons() == Qt.LeftButton:
            # 记录第一下鼠标点击的坐标
            self.start_pos = e.pos()

    def mouseMoveEvent(self, e: QMouseEvent):
        '''重写鼠标移动事件'''
        # 左键按下
        if e.buttons() == Qt.LeftButton:
            # 移动至当前坐标加上鼠标移动偏移量
            self.move(self.pos() + e.pos() - self.start_pos)


class TextSmokeThread(QThread):
    '''创建文字烟雾线程类'''
    # 文字标签变色动画
    colorChange_signal = Signal()
    # 文字烟雾启动动画信号
    startAnimation_signal = Signal()

    def __init__(self):
        '''构造函数'''
        super(TextSmokeThread, self).__init__()
        # 运行标志
        self.runFlag = True
        self.times = 0

    def run(self):
        '''运行线程'''
        while self.runFlag:
            # 发射烟雾动画信号
            self.startAnimation_signal.emit()
            # 判断
            if self.times == 0:
                # 发射变色信号
                self.colorChange_signal.emit()
                self.times = 10
            # 休眠随机时间
            t = random.randint(1000, 2000)/1000
            self.sleep(t)
            #
            self.times = self.times - 1

    def stop(self):
        '''停止线程'''
        self.times = 0
        self.runFlag = False


class TextSmokeLabel(TextLabel):
    '''文字烟雾类'''

    def __init__(self, text: str, parent: QWidget):
        '''构造函数'''
        super().__init__(text, parent)

    def startAnimation(self):
        '''启动动画'''
        # 创建颜色变化动画
        self.textColorAnimation = QPropertyAnimation(self, b"color")
        # 创建位置变化动画
        self.textPositionAnimation = QPropertyAnimation(self, b'pos')

        # 变色动画持续随机12-15秒
        self.textColorAnimation.setDuration(random.randint(12000, 15000))
        # 位移动画持续随机6-10秒
        self.textPositionAnimation.setDuration(random.randint(6000, 10000))

        # 颜色
        r = [100, 0, 25, 50, 75, 100, 125, 150, 175,
             200, 210, 220, 225, 230, 235, 240, 245, 250, 255]
        g = [100, 0, 25, 50, 75, 100, 125, 150, 175,
             200, 210, 220, 225, 230, 235, 240, 245, 250, 255]
        b = [100, 0, 25, 50, 75, 100, 125, 150, 175,
             200, 210, 220, 225, 230, 235, 240, 245, 250, 255]
        # 透明度
        alpha = [100, 255, 225, 200, 175, 150, 125,
                 100, 90, 75, 60, 50, 30, 25, 20, 15, 10, 5, 0]
        # 关键帧
        step = [i/len(r) for i in range(len(r))]

        # 起始值 白色
        self.textColorAnimation.setStartValue(QColor(255, 255, 255, 0))
        # 起始位置
        startx = random.randint(310, 340)
        starty = random.randint(460, 470)
        self.textPositionAnimation.setStartValue(QPoint(startx, starty))

        # 循环设置关键帧
        for i in range(0, len(r)):
            self.textColorAnimation.setKeyValueAt(
                step[i], QColor(r[i], g[i], b[i], alpha[i]))

        # 结束值 白色
        self.textColorAnimation.setEndValue(QColor(255, 255, 255, 0))
        # 结束位置
        endx = random.randint(150, 200)
        endy = random.randint(200, 250)
        self.textPositionAnimation.setEndValue(QPoint(endx, endy))

        # 设置动画插值类型为-线性移动
        self.textPositionAnimation.setEasingCurve(QEasingCurve.Linear)

        # 创建并行动画组-并行动画组就是组内的动画同时执行
        self.parallelAnimationGroup = QParallelAnimationGroup()
        # 往动画组里添加动画
        self.parallelAnimationGroup.addAnimation(self.textColorAnimation)
        self.parallelAnimationGroup.addAnimation(self.textPositionAnimation)

        # 启动动画组
        self.parallelAnimationGroup.start()


class MainWindow(QWidget):
    '''主窗口'''

    def __init__(self, app: QApplication):
        '''构造函数'''
        super(MainWindow, self).__init__()
        self.app = app

        # 初始化窗体界面
        self.initUI()

        # 创建检测话筒音量线程
        self.detectSoundThread = DetectSoundThread()
        # 接收DetectSoundThread传回来的信号并连接到self.setWave函数
        self.detectSoundThread.volume_signal.connect(self.setWave)

        # 创建文字烟雾线程
        self.textSmokeThread = TextSmokeThread()
        self.textSmokeThread.colorChange_signal.connect(self.textColorChange)
        self.textSmokeThread.startAnimation_signal.connect(
            self.startSmokeAnimation)

        # 启动线程
        self.detectSoundThread.start()
        self.textSmokeThread.start()

    def initUI(self):
        '''初始化窗体界面'''
        # 将窗口大小
        self.resize(800, 720)
        # 设置窗口图标
        self.setWindowIcon(QIcon(QPixmap(ABOUT_PIC_PATH)))
        # 设置主窗口背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 设置主窗口无边框
        self.setWindowFlag(Qt.FramelessWindowHint)
        # 设置主窗口置顶显示
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        # 窗口居中
        self.center()

        # pyqtgraph设置抗锯齿+背景透明
        pg.setConfigOptions(antialias=True, background='#00000000')
        # 在主窗口创建一个pyqtgraph画布
        self.graph = pg.PlotWidget(self)
        # 画布背景透明
        self.graph.setStyleSheet('background-color:#00000000')
        # 将画布移动至坐标(0, 0) 设置宽高为(800, 720)
        self.graph.setGeometry(0, 0, 800, 720)
        # 获取画布里的plotItem对象
        plotItem = self.graph.getPlotItem()
        # 隐藏左侧y轴
        plotItem.hideAxis('left')
        # 隐藏底部x轴
        plotItem.hideAxis('bottom')

        # 用numpy生成一个从0到π 180等分的等差数列
        self.theta = np.linspace(0, np.pi, 180)
        # 按等差数列计算对应的x值 既半圆曲线的x轴数组
        x = np.cos(self.theta)
        # 按等差数列计算对应的y值 既半圆曲线的y轴数组
        y = np.sin(self.theta)
        # 选择一个好看的颜色用来画曲线 这里我选了天蓝色
        color = '#B3DCFD'
        # 绘制半圆曲线
        # 将画笔设为天蓝色 透明度80/FF 粗细=5 样式=实线
        # 填充曲线和直线y=0之间的区域 笔刷设为天蓝色 透明度20/FF
        self.line = self.graph.plot(x, y, pen=pg.mkPen(
            color + '80', width=5), fillLevel=0, brush=color + '20')
        # 再绘制一个新的半圆曲线
        # 画笔天蓝色 粗细=1.5 样式=点虚线
        self.dotLine = self.graph.plot(
            x, y, pen=pg.mkPen(color, width=1.5, style=Qt.DotLine))

        # 创建一个QLabel用于展示立绘图
        figLabel = QLabel(self)
        # 用QPixmap加载本地png图片
        pixmap = QPixmap(BODY_PIC_PATH)
        # 抗锯齿缩放至800x720
        pixmap = pixmap.scaled(
            800, 720, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        # 用setPixmap将立绘展示到QLabel上
        figLabel.setPixmap(pixmap)
        # 将QLabel覆盖到graph上面
        figLabel.setGeometry(0, 0, 800, 720)

        # 假发初始坐标
        self.hairX = 261
        self.hairY = 82
        # 假发宽高
        self.hairW = 280
        self.hairH = 280
        # 实例化hairLabel 并将宽高和主窗口对象传给它 将它嵌入主窗口
        self.hairLabel = HairLabel(self.hairW, self.hairH, self)
        # 移动至指定坐标处
        self.hairLabel.move(self.hairX, self.hairY)

        # 文字标签初始坐标
        self.textLabelX = 480
        self.textLabelY = 650
        # 文字标签宽高
        self.textLabelW = 320
        self.textLabelH = 60
        # 文字标签
        self.textLabel = TextLabel("声音立绘展示器", self)
        # 设置字体
        self.textLabel.setFont(QFont('华文彩云', 32))
        # 设置文字颜色
        self.textLabel.setTextColor(QColor(255, 50, 50, 50))
        # 设置坐标，大小
        self.textLabel.setGeometry(
            self.textLabelX, self.textLabelY, self.textLabelW, self.textLabelH)

    def keyPressEvent(self, e: QKeyEvent):
        '''重写键盘按下事件'''
        # 判断按下的键是否为空格键 是的话就创建动画让假发和文字标签飞回来
        if e.key() == Qt.Key_Space:
            # 给hairLabel创建一个动画 类型为geometry
            hairAnimation = QPropertyAnimation(
                self.hairLabel, b'geometry', self)
            textAnimation = QPropertyAnimation(
                self.textLabel, b'geometry', self)
            # 设置动画持续时长为1000毫秒
            hairAnimation.setDuration(1000)
            textAnimation.setDuration(1000)
            # 动画结束位置为假发初始位置
            hairAnimation.setEndValue(
                QRect(self.hairX, self.hairY, self.hairW, self.hairH))
            textAnimation.setEndValue(
                QRect(self.textLabelX, self.textLabelY, self.textLabelW, self.textLabelH))
            # 设置动画插值类型为“来回弹跳”
            hairAnimation.setEasingCurve(QEasingCurve.OutElastic)
            textAnimation.setEasingCurve(QEasingCurve.OutElastic)
            # 开始动画效果
            hairAnimation.start()
            textAnimation.start()

    def mousePressEvent(self, e: QMouseEvent):
        '''重写鼠标按下事件'''
        # 左键按下
        if e.buttons() == Qt.LeftButton:
            # 记录第一下鼠标点击的坐标
            self.start_pos = e.pos()

    def mouseMoveEvent(self, e: QMouseEvent):
        '''重写鼠标移动事件'''
        # 左键按下
        if e.buttons() == Qt.LeftButton:
            # 移动至当前坐标加上鼠标移动偏移量
            self.move(self.pos() + e.pos() - self.start_pos)

    def setWave(self, volume: list):
        '''接收DetectSound发射回来的长度为180的响度列表并绘画波形'''
        # 将响度作为新半径来计算新的x值
        x = volume * np.cos(self.theta)
        # 将响度作为新半径来计算新的y值
        y = volume * np.sin(self.theta)
        # 刷新点虚线
        self.dotLine.setData(x, y)

    def contextMenuEvent(self, e: QContextMenuEvent):
        '''重写鼠标右键菜单事件'''
        # 实例化一个QMenu对象
        menu = QMenu()
        menu.setStyleSheet("""
        QMenu {
            background-color: rgb(50,50,50);
            color: rgb(255,255,255);
            border: 1px solid ;
        }
        QMenu::item::selected {
            color: orange;
        }
        """)

        # 添加关于菜单项
        about_action = QAction('关于', menu)
        # 设置字体
        about_action.setFont(QFont('宋体', 20))
        # 设置图标
        about_action.setIcon(QIcon(QPixmap(ABOUT_PIC_PATH)))
        # 绑定事件
        about_action.triggered.connect(self.about)

        # 添加退出菜单项
        exit_action = QAction('退出', menu)
        # 设置字体
        exit_action.setFont(QFont('宋体', 20))
        # 设置图标
        exit_action.setIcon(QIcon(QPixmap(EXIT_PIC_PATH)))
        # 绑定事件
        exit_action.triggered.connect(self.exit)

        # 添加菜单项
        menu.addAction(about_action)
        menu.addSeparator()
        menu.addAction(exit_action)

        # 将e.pos()映射为屏幕全局坐标 然后在此坐标弹出菜单
        menu.exec_(self.mapToGlobal(e.pos()))

    def center(self):
        '''窗口居中显示'''
        screen = self.app.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def about(self):
        '''关于'''
        # 显示弹窗
        QMessageBox.about(self, f'关于{APP_NAME}',
                          "{}<br>{}<br>author：<a href='https://github.com/ordinary-student'>{}</a><br>版本：{}<br>Last-Update：{}<br>© Copyright {}".format(APP_NAME, APP_MESSAGE, AUTHOR, VERSION, LAST_UPDATE, LAST_UPDATE[0:4]))

    def exit(self):
        '''退出'''
        # 停止采样线程
        self.detectSoundThread.stop()
        # 停止文字烟雾线程
        self.textSmokeThread.stop()
        # 关闭窗体
        self.close()

    def textColorChange(self):
        '''文字标签颜色变化'''
        self.textLabel.startAnimation()

    def startSmokeAnimation(self):
        '''启动文字烟雾动画'''
        # 关键词文字
        text = random.choice(keyword.kwlist)
        # 创建标签
        label = TextSmokeLabel(text, self)
        # 设置字体
        label.setFont(QFont('微软雅黑', 16))
        # 设置文字颜色
        label.setTextColor(QColor(255, 255, 255, 0))
        # 设置坐标位置
        lx = random.randint(300, 350)
        ly = random.randint(450, 470)
        label.move(lx, ly)
        label.show()
        # 启动动画
        label.startAnimation()


if __name__ == '__main__':
    # Qt主进程后台管理
    app = QApplication(sys.argv)
    # 实例化主窗口
    mainWindow = MainWindow(app)
    # 显示主窗口
    mainWindow.show()
    # 启动Qt主进程循环直到收到退出信号
    sys.exit(app.exec_())

from functools import partial

import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
from PyQt5 import QtGui

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
import datetime

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('background', 'w')
pg.setConfigOption('antialias', True)  # Set to False if there is too much lag when dragging scene


class LeftAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMaximumWidth(70)
        self.setMinimumWidth(70)

    def _updateWidth(self):
        pass


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [datetime.datetime.fromtimestamp(value).strftime("%Y-%m-%d") for value in values]


class ItemSample(pg.GraphicsWidget):
    """ Class responsible for drawing a single item in a LegendItem (sans label).

    This may be subclassed to draw custom graphics in a Legend.
    """

    ## Todo: make this more generic; let each item decide how it should be represented.
    def __init__(self, item):
        pg.GraphicsWidget.__init__(self)
        self.item = item

    def paint(self, p, *args):
        opts = self.item.opts

        if opts.get('antialias'):
            p.setRenderHint(p.Antialiasing)

        if not isinstance(self.item, pg.ScatterPlotItem):
            p.setPen(pg.mkPen(opts['pen']))
            p.drawLine(0, 11, 20, 11)

        symbol = opts.get('symbol', None)
        if symbol is not None:
            if isinstance(self.item, pg.PlotDataItem):
                opts = self.item.scatter.opts

            pen = pg.mkPen(opts['pen'])
            brush = pg.mkBrush(opts['brush'])
            size = opts['size']

            p.translate(10, 10)
            path = pg.ScatterPlotItem.drawSymbol(p, symbol, size, pen, brush)


class LegendItem(pg.LegendItem):
    def __init__(self, *args, **kargs):
        super(LegendItem, self).__init__(labelTextSize='8pt', *args, **kargs)
        self.curves = {}
        self.grid = []
        self.added = []
        self.item_count = 0
        for j in range(0, 20, 2):
            for i in range(4):
                self.grid.append([i, j])

    def mouseDragEvent(self, ev):
        pass


class ColorAction(QtWidgets.QWidgetAction):
    colorSelected = QtCore.pyqtSignal(QtGui.QColor)

    def __init__(self, parent):

        QtWidgets.QWidgetAction.__init__(self, parent)
        self.color_id = {}
        widget = QtWidgets.QWidget(parent)
        layout = QtWidgets.QGridLayout(widget)

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        palette = self.palette()
        count = len(palette)
        rows = count // round(count ** .5)
        for row in range(rows):
            for column in range(count // rows):
                color = palette.pop()

                button = QtWidgets.QToolButton(widget)
                button.setAutoRaise(True)
                button.clicked.connect(partial(self.handleButton, color))

                pixmap = QtGui.QPixmap(16, 16)
                pixmap.fill(color)
                button.setIcon(QtGui.QIcon(pixmap))
                layout.addWidget(button, row, column)
        self.setDefaultWidget(widget)

    def handleButton(self, color):
        self.parent().hide()
        self.colorSelected.emit(color)

    def palette(self):
        palette = []
        for g in range(4):
            for r in range(4):
                for b in range(3):
                    palette.append(QtGui.QColor(
                        r * 255 // 3, g * 255 // 3, b * 255 // 2))
        return palette


class PlotCurveItem(pg.PlotCurveItem):
    def __init__(self, *args, **kargs):

        super(PlotCurveItem, self).__init__(*args, **kargs)

        self.menu = QtWidgets.QMenu()

        self.colorAction = ColorAction(self.menu)
        self.colorAction.colorSelected.connect(self.handleColorSelected)
        self.menu.addAction(self.colorAction)
        self.menu.addSeparator()

        fontColor = QtWidgets.QAction('Custom color', self)
        self.menu.addAction(fontColor)
        fontColor.triggered.connect(self.custom_color)

    def setData(self, *args, **kargs):

        if bool(args):
            newargs = list(args)
            if hasattr(args[0][0], 'timestamp'):
                newargs[0] = [i.timestamp() for i in args[0]]

            super().setData(*newargs, **kargs)

    def custom_color(self):
        color = QtGui.QColorDialog.getColor()
        color.getRgb()
        pen = pg.mkPen(color=color.getRgb(), width=1)
        self.setPen(pen)

    def handleColorSelected(self, color):

        pen = pg.mkPen(color=color.getRgb(), width=1)
        self.setPen(pen)

    def mouseClickEvent(self, ev):
        pos = ev.pos()
        if ev.button() == QtCore.Qt.RightButton:

            if self.mouseShape().contains(pos):

                if self.raiseContextMenu(ev):
                    ev.accept()

    def raiseContextMenu(self, ev):
        menu = self.getContextMenus()

        # Let the scene add on to the end of our context menu
        # (this is optional)
        # menu = self.scene().addParentContextMenus(self, menu, ev)

        pos = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))
        return True

    # This method will be called when this item's _children_ want to raise
    # a context menu that includes their parents' menus.
    def getContextMenus(self, event=None):

        return self.menu

from functools import partial

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import *

from plotting.items import PlotCurveItem, TimeAxisItem, LegendItem

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
import datetime

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('background', 'w')

pg.setConfigOption('antialias', True)  # Set to False if there is too much lag when dragging scene

TODAY = datetime.datetime.today().timestamp() + 15 * 3600 * 24


class PlotWidget(pg.PlotWidget):
    def __init__(self, combobox, plot_title, *args, **kargs):
        super(PlotWidget, self).__init__(*args, **kargs)
        self.plot_title = plot_title
        self.setAxisItems(axisItems={'bottom': TimeAxisItem(orientation='bottom')})

        self.line_colors = [QColor(*i) for i in
                            [(28, 134, 238), (227, 26, 28), (0, 139, 0), (106, 61, 154), (255, 127, 0), (0, 0, 0), (255, 215, 0), (126, 192, 238),
                             (251, 154, 153),
                             (144, 238, 144), (202, 178, 214), (253, 191, 111), (179, 179, 179), (238, 230, 133), (176, 48, 96), (255, 131, 250),
                             (255, 20, 147),
                             (0, 0, 255), (54, 100, 139), (0, 206, 209), (0, 255, 0), (139, 139, 0), (205, 205, 0), (139, 69, 0), (165, 42, 42)]]

        self.plotItem.ctrlMenu = None  # get rid of 'Plot Options'
        legend = LegendItem()

        self.getPlotItem().legend = legend
        legend.setParentItem(self.getPlotItem())
        legend.setOffset(500)

        self.getPlotItem().layout.setContentsMargins(200, 0, 30, 0)
        self.scene().contextMenu = None  # get rid of 'Export'
        self.menu = QtWidgets.QMenu()
        self.menu.setTitle('Options')

        self.plotItem.vb.borderRect.setPen(pg.mkPen((0, 0, 0), width=1.02))

        self.combo_plots = {}
        self.combo = combobox
        self.combo.currentTextChanged.connect(self.select_plot)

        scale = QtWidgets.QAction("Autoscale", self.menu)
        scale.triggered.connect(self.toogle_scale)
        self.menu.addAction(scale)
        self.menu.scale = scale

        tooltip = QtWidgets.QAction("Show information", self.menu)
        tooltip.setCheckable(True)
        tooltip.setChecked(True)
        tooltip.triggered.connect(self.toogle_tooltip)
        self.menu.addAction(tooltip)
        self.menu.tooltip = tooltip
        self.scene().sigMouseMoved.connect(partial(self.tool_tip, self.getPlotItem()))
        self.scene().sigMouseClicked.connect(self.tradespace_click)

        grid = QtWidgets.QAction("Grid", self.menu)
        grid.setCheckable(True)
        grid.setChecked(True)
        grid.triggered.connect(self.toogle_grid)
        self.menu.addAction(grid)
        self.menu.grid = grid
        self.toogle_grid()


        self.tradespace = False
        self.show_tooltip = True
        self.show_hline = False
        self.plotItem.vb.menu = self.menu
        self.getPlotItem().setAxisItems({})
        self.getPlotItem().getAxis('left').setWidth(35)
        self.getPlotItem().getAxis('right').setWidth(35)

        self.plottooltip = pg.TextItem('None', color=(0, 0, 0), anchor=(1, 1))

        self.plotItem.addItem = self.addItem
        self.plotItem.vb.sigXRangeChanged.connect(self.rescaley)
        self.plotItem.vb.sigYRangeChanged.connect(self.rescaley)
        self.plotItem.vb.setDefaultPadding(0.1)

    def rescaley(self):
        self.enableAutoRange(axis='y')
        self.setAutoVisible(y=True)

    def add_plot(self, name, plot_items):
        a = []
        i = 0
        for sname, xy in plot_items.items():

            if 'IPCA' in sname:
                s = QtCore.Qt.DashLine
            else:
                s = QtCore.Qt.SolidLine

            item = PlotCurveItem(xy[0], xy[1], pen=pg.mkPen(color=self.line_colors[i], width=2, style=s), name=sname)
            a.append(item)
            i += 1

        self.combo_plots[name] = a
        self.combo.addItem(name)

    def select_plot(self, a):
        self.plot_title.setText(a)
        self.plot_title.setStyleSheet("font-weight: bold; color: black; size:8")
        if a in self.combo_plots.keys():
            self.clear()
            for plot in self.combo_plots[a]:
                self.addItem(plot)
            self.menu.close()

        self.plotItem.vb.setLimits(xMin=self.combo_plots[a][0].getData()[0][0] * 0.98, xMax=TODAY * 1.02)
        self.enableAutoRange(axis='x')
        self.rescaley()

    def clear(self):
        for item in self.plotItem.curves:
            self.plotItem.removeItem(item)

    # On right-click, raise the context menu

    def tradespace_click(self, ev):
        if self.tradespace:
            if ev.button() == QtCore.Qt.LeftButton:
                for item in self.getPlotItem().curves:
                    item.tool_tip(ev)

            else:
                if self.raiseContextMenu(ev):
                    ev.accept()
                    self.mousepoint1 = self.mapToView(ev.scenePos())

    def mouseClickEvent(self, ev):

        if ev.button() == QtCore.Qt.RightButton:
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

    def toogle_grid(self):
        if self.menu.grid.isChecked():

            self.plotItem.showGrid(True, True, 0.3)
        else:

            self.plotItem.showGrid(False, False, 0.3)

    def toogle_scale(self):

        self.plotItem.vb.enableAutoRange()

    def tool_tip(self, plot, evt):

        if self.show_tooltip:
            mousePoint1 = plot.mapToView(evt)
            show = False
            for item in plot.curves:
                if isinstance(item, PlotCurveItem):
                    corrected = QtCore.QPointF(mousePoint1.x(), mousePoint1.y())

                    if item.mouseShape().contains(corrected):
                        ind = (np.abs(item.xData - mousePoint1.x()).argmin())
                        # y = item.yData[ind] + (mousePoint1.x() - item.xData[ind]) * (item.yData[ind + 1] - item.yData[ind]) / (item.xData[ind + 1] - item.xData[ind])

                        show = True

                        self.plottooltip.setText(
                            '{}\n{}\n{}'.format(item.name().split('=')[0], datetime.datetime.utcfromtimestamp(float(item.xData[ind])).strftime("%Y-%m-%d"),
                                                round(item.yData[ind], 2)))

                        self.plottooltip.setPos(mousePoint1.x(), mousePoint1.y())

                        if self.plottooltip not in plot.items:
                            plot.addItem(self.plottooltip, ignoreBounds=True)

            if show == False:
                plot.removeItem(self.plottooltip)
        else:
            plot.removeItem(self.plottooltip)

    def toogle_tooltip(self):
        if self.menu.tooltip.isChecked():
            self.show_tooltip = True
        else:
            self.show_tooltip = False

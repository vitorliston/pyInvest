from functools import partial

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from plotting.items import PlotCurveItem, TimeAxisItem

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
import datetime

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('background', 'w')

pg.setConfigOption('antialias', True)  # Set to False if there is too much lag when dragging scene


class AssetWidget(pg.PlotWidget):
    def __init__(self, *args, **kargs):
        super(AssetWidget, self).__init__(*args, **kargs)

        self.setAxisItems(axisItems={'bottom': TimeAxisItem(orientation='bottom')})

        self.getPlotItem().layout.setContentsMargins(0, 0, 0, 0)

        self.plotItem.vb.borderRect.setPen(pg.mkPen((0, 0, 0), width=1.02))

        self.scene().sigMouseMoved.connect(partial(self.tool_tip, self.getPlotItem()))

        self.show_tooltip = True

        self.getPlotItem().setAxisItems({})
        self.getPlotItem().getAxis('left').setWidth(35)
        self.getPlotItem().getAxis('right').setWidth(35)

        self.plottooltip = pg.TextItem('None', color=(0, 0, 0), anchor=(1, 1))

    # On right-click, raise the context menu
    def mousePressEvent(self, ev):
        pass

    def tool_tip(self, plot, evt):

        if self.show_tooltip:
            mousePoint1 = plot.mapToView(evt)
            show = False
            for item in plot.curves:
                if isinstance(item, PlotCurveItem):
                    corrected = QtCore.QPointF(mousePoint1.x(), mousePoint1.y())

                    if item.mouseShape().contains(corrected):
                        ind = (np.abs(item.xData - mousePoint1.x()).argmin())

                        show = True

                        self.plottooltip.setText(
                            '{}\n{}'.format(datetime.datetime.utcfromtimestamp(float(item.xData[ind])).strftime("%Y-%m-%d"),
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

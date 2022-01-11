from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot


class Thread(QThread):
    signalStatus = pyqtSignal(str)

    def __init__(self, function, inputs):
        QThread.__init__(self)
        self.function = function
        self.inputs = inputs




    @pyqtSlot()
    def run(self):

        if self.inputs!=None:
            self.result=self.function(*self.inputs)
        else:

            self.result=self.function()

        self.signalStatus.emit('Done')
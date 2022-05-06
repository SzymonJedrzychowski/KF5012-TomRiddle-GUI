from PyQt5 import QtWidgets, QtCore, QtGui
from CTCovidDetection import CTCovidDetection
import json
import csv
import os

# Worker class is responsible for running the prediction code without freezing the GUI


class Worker(QtCore.QObject):
    def __init__(self, predictionModel, fileNames):
        super(Worker, self).__init__()
        self.finished = QtCore.pyqtSignal(list)
        self.predictionModel = predictionModel
        self.fileNames = fileNames
        self.pause = False

    @QtCore.pyqtSlot()
    def run(self):
        runTime = 0
        allTimeResults = [1, {}]

        # Prediction is split so that only 100 files are predicted at once so it can be stopped by cancel button
        while not self.pause and runTime*100 < len(self.fileNames):
            results = self.predictionModel.predict(
                self.fileNames[runTime*100:min((runTime+1)*100, len(self.fileNames))])

            if results[0] != 1:
                allTimeResults[0] = results[0]
                allTimeResults[1] = None
                self.pause = True
            else:
                allTimeResults[1] = allTimeResults[1] | results[1]

            runTime += 1

        # Pass the results at the end
        self.finished.emit(allTimeResults)


class mainScreen(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(mainScreen, self).__init__(parent)
        self.setMinimumSize(1000, 700)
        self.createInterface()

        self.predictionModel = CTCovidDetection()
        self.fileNames = []
        self.results = [1, {}]
        self.worker = 0

    def createInterface(self):
        # Create the GUI widgets and functionalities

        bigFont = QtGui.QFont()
        bigFont.setPointSize(18)

        smallFont = QtGui.QFont()
        smallFont.setPointSize(16)

        self.setWindowTitle("CTCovidDetection")

        centralWidget = QtWidgets.QWidget(self)

        gridLayout = QtWidgets.QGridLayout(centralWidget)
        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.setContentsMargins(30, 30, 30, 30)

        # Create menu bar
        menuBar = self.menuBar()

        exportBar = menuBar.addMenu('Export data')

        exportFileJson = QtWidgets.QAction("Export as .json", self)
        exportFileJson.triggered.connect(self.exportDataJson)
        exportBar.addAction(exportFileJson)

        exportFileCsv = QtWidgets.QAction("Export as .csv", self)
        exportFileCsv.triggered.connect(self.exportDataCsv)
        exportBar.addAction(exportFileCsv)

        # Create main label
        titleLabel = QtWidgets.QLabel(centralWidget)
        titleLabel.setFont(bigFont)
        titleLabel.setText("CTCovidDetection")
        verticalLayout.addWidget(titleLabel, 0, QtCore.Qt.AlignHCenter)

        tableVerticalLayout = QtWidgets.QVBoxLayout()
        tableVerticalLayout.setContentsMargins(30, 30, 30, 30)

        # Create table label
        tableLabel = QtWidgets.QLabel(centralWidget)
        tableLabel.setFont(smallFont)
        tableLabel.setText("Predicted photos")
        tableVerticalLayout.addWidget(tableLabel, 0, QtCore.Qt.AlignHCenter)

        # Create model for items in the table
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(
            ["File name", "Covid prediction (%)"])

        # Create filter for items in table
        self.filter = QtCore.QSortFilterProxyModel()
        self.filter.setSourceModel(self.model)
        self.filter.setFilterKeyColumn(0)
        self.filter.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        # Create tableView and set the column/row properties
        self.tableView = QtWidgets.QTableView(centralWidget)
        self.tableView.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.tableView.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)

        # Set model for the table
        self.tableView.setModel(self.model)

        tableVerticalLayout.addWidget(self.tableView)

        fileSearchLayout = QtWidgets.QHBoxLayout()

        # Create widgets to search files
        searchFileLabel = QtWidgets.QLabel(centralWidget)
        searchFileLabel.setFont(smallFont)
        searchFileLabel.setText("Search file:")
        fileSearchLayout.addWidget(searchFileLabel, 0)

        lineEdit = QtWidgets.QLineEdit(centralWidget)
        lineEdit.setFont(smallFont)
        fileSearchLayout.addWidget(lineEdit)
        lineEdit.textChanged.connect(self.filter.setFilterRegExp)

        buttonLayout = QtWidgets.QHBoxLayout()

        # Create import button
        self.importPhotos = QtWidgets.QPushButton(centralWidget)
        self.importPhotos.setFont(smallFont)
        self.importPhotos.setText("Import photos")
        buttonLayout.addWidget(self.importPhotos)

        # Create predict button
        self.predictResult = QtWidgets.QPushButton(centralWidget)
        self.predictResult.setFont(smallFont)
        self.predictResult.setText("Predict")
        buttonLayout.addWidget(self.predictResult)

        # Connect buttons
        self.importPhotos.clicked.connect(self.loadPhotos)
        self.predictResult.clicked.connect(self.predict)

        tableVerticalLayout.addLayout(fileSearchLayout)
        verticalLayout.addLayout(tableVerticalLayout)
        verticalLayout.addLayout(buttonLayout)
        gridLayout.addLayout(verticalLayout, 0, 0, 1, 1)

        self.setCentralWidget(centralWidget)

    def loadPhotos(self):
        # Method to load photos

        self.results = [1, {}]

        # File dialog
        fileDialog = QtWidgets.QFileDialog()
        fileDialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        fileDialog.setNameFilter(("Images (*.png *.jpg)"))
        if fileDialog.exec_() == QtWidgets.QDialog.Accepted:
            self.fileNames = fileDialog.selectedFiles()

        # Update model
        self.model = QtGui.QStandardItemModel(len(self.fileNames), 1)
        self.model.setHorizontalHeaderLabels(
            ["File name", "Covid prediction (%)"])

        # Show file names
        for row, fileName in enumerate(self.fileNames):
            fileNameColumn = QtGui.QStandardItem(fileName.split("/")[-1])
            fileNameColumn.setToolTip(fileName.split("/")[-1])
            covidPredictionColumn = QtGui.QStandardItem("")
            self.model.setItem(row, 0, fileNameColumn)
            self.model.setItem(row, 1, covidPredictionColumn)

        # Update filter and model for table
        self.filter.setSourceModel(self.model)
        self.tableView.setModel(self.filter)

    def predict(self):
        # Method to predict the loaded photos

        # Check if model.h5 is in directory
        successInformation = self.predictionModel.load_model('model.h5')
        if successInformation == 0:
            self.createMessage("Prediction model not found.",
                               "Make sure that model.h5 file is in the same repository as the main.py file.")
            return

        # Create a thread to run the code (Based on the code from: https://www.pythonguis.com/tutorials/multithreading-pyqt-applications-qthreadpool/)
        if len(self.fileNames) > 0:
            self.thread = QtCore.QThread(parent=self)
            self.worker = Worker(self.predictionModel, self.fileNames)
            self.worker.moveToThread(self.thread)
            self.thread.setTerminationEnabled(True)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.updateList)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            # Change status of buttons
            self.predictResult.setText("Cancel prediction")
            self.predictResult.clicked.connect(self.stopPrediction)
            self.predictResult.clicked.disconnect(self.predict)
            self.importPhotos.setEnabled(False)

            self.thread.start()
        else:
            return

    def updateList(self, results):
        # Method to show predictions

        self.results = results

        if self.results[0] == -1:
            self.createMessage("Prediction model not found.",
                               "Make sure that model.h5 file is in the same repository as the main.py file.")
        elif self.results[0] == 0:
            self.createMessage(
                "Prediction error.", "During prediction unexpected error has occurred.")
        else:
            # Show predictions in the column
            for row, fileName in enumerate(self.fileNames):
                if fileName in self.results[1]:
                    self.results[1][fileName] = float(
                        self.results[1][fileName])
                    covidPredictionColumn = QtGui.QStandardItem(
                        str(round(100*self.results[1][fileName], 2)))
                    covidPredictionColumn.setTextAlignment(
                        QtCore.Qt.AlignCenter)
                    self.model.setItem(row, 1, covidPredictionColumn)

        # Change status of buttons
        self.predictResult.setText("Predict")
        self.predictResult.clicked.disconnect(self.stopPrediction)
        self.predictResult.clicked.connect(self.predict)
        self.importPhotos.setEnabled(True)

    def stopPrediction(self):
        # Pause predicting code
        if self.worker:
            self.worker.pause = True

    def createMessage(self, title, message):
        # Method to create popup window
        popup = QtWidgets.QMessageBox()
        popup.setWindowTitle(title)
        popup.setText(message)
        popup.setStandardButtons(QtWidgets.QMessageBox.Ok)
        popup.exec_()

    def exportDataJson(self):
        # Method to export the data to .json file

        if len(self.results[1]) > 0:
            # Get the name of the file
            fileDialog = QtWidgets.QFileDialog()
            fileDialog.setDefaultSuffix('json')
            fileDialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            fileDialog.setNameFilters(['JSON (*.json)'])
            if fileDialog.exec_() == QtWidgets.QDialog.Accepted:
                name = fileDialog.fileSelected()
                if name.split(".")[-1] != "json":
                    name += ".json"
            else:
                return

            # Try saving the file
            try:
                with open(name, "w") as f:
                    json.dump(self.results[1], f)
                self.createMessage(
                    "Save message", "File was saved successfully.")
            except Exception as exc:
                os.remove(name)
                print(exc)
                self.createMessage("Save message", "File could not be saved.")

        else:
            self.createMessage("Save error", "There is no data to save.")

    def exportDataCsv(self):
        # Method to export the data to .csv file

        if len(self.results[1]) > 0:
            # Get the name of the file
            fileDialog = QtWidgets.QFileDialog()
            fileDialog.setDefaultSuffix('csv')
            fileDialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            fileDialog.setNameFilters(['CSV (*.csv)'])
            if fileDialog.exec_() == QtWidgets.QDialog.Accepted:
                name = fileDialog.fileSelected()
                if name.split(".")[-1] != "csv":
                    name += ".csv"
            else:
                return

            # Try saving the file
            try:
                with open(name, "w", newline="") as f:
                    file = csv.writer(f)

                    # Write rows in the .csv file
                    for line in self.results[1]:
                        file.writerow([line, self.results[1][line]])

                self.createMessage(
                    "Save message", "File was saved successfully.")
            except Exception as exc:
                print(exc)
                os.remove(name)
                self.createMessage("Save message", "File could not be saved.")

        else:
            self.createMessage("Save error", "There is no data to save.")

    def showEvent(self, event):
        # Update the width of columns of table when shown
        self.tableView.setColumnWidth(0, int(0.8*self.tableView.width()))
        self.tableView.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch)

    def resizeEvent(self, event):
        # Update the width of columns of table when window is resized
        self.tableView.setColumnWidth(0, int(0.8*self.tableView.width()))
        self.tableView.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch)

    def closeEvent(self, event):
        # Pause the worker when program is closed during predicting
        if self.worker:
            self.worker.pause = True

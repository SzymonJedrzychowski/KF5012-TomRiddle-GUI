#from CTCovidDetection import CTCovidDetection
from PyQt5 import QtWidgets
import mainScreen
import sys


def main():
    app = QtWidgets.QApplication(sys.argv)
    screen = mainScreen.mainScreen()
    screen.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
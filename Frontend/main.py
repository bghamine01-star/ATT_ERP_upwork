from login_window import LoginWindow
from main_window import MainWindow
from PyQt6.QtWidgets import QApplication
import sys

class AppController:
    def __init__(self):
        self.show_login()

    def show_login(self):
        """Initialise et affiche la fenêtre de login"""
        self.login_win = LoginWindow()
        self.login_win.login_success.connect(self.show_main)
        self.login_win.show()

    def show_main(self, token, role):
        """Initialise et affiche la fenêtre principale"""
        self.main_win = MainWindow(token, role)
        # On connecte le signal de déconnexion à la méthode show_login
        self.main_win.logout_requested.connect(self.show_login)
        self.main_win.showMaximized()
        self.login_win.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = AppController()
    sys.exit(app.exec())
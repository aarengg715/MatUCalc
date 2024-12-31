import sys
import math
import keyboard
import webbrowser
import json
import os
import shutil
from colorsys import rgb_to_hls, hls_to_rgb
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QMainWindow, QApplication, QLabel, QToolBar, QStatusBar, QCheckBox, QVBoxLayout, QDialogButtonBox, QDialog, QGridLayout, QRadioButton, QWidget, QGroupBox, QPushButton, QLineEdit, QFileDialog
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPixmap, QFont
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QRect, QEasingCurve
from imgconv import convertImage
from fetchcolors import fetchColor
from modifysvg import modifySvg

def read_prefs(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def write_prefs(file_path, prefs):
    with open(file_path, "w") as file:
        json.dump(prefs, file, indent=4)


def adjust_color(hexcolor, factor):
    if isinstance(hexcolor, tuple):
        hexcolor = ''.join(f'{c:02x}' for c in hexcolor)
    hexcolor = hexcolor.lstrip('#')
    
    if len(hexcolor) != 6:  
        return '#000000'  
    
    rgb = tuple(int(hexcolor[i:i+2], 16) for i in range(0, 6, 2))
    adjusted_rgb = tuple(min(255, max(0, int(c * factor))) for c in rgb)
    
    return f"#{adjusted_rgb[0]:02x}{adjusted_rgb[1]:02x}{adjusted_rgb[2]:02x}"


def invert_color(hexcolor):
    if isinstance(hexcolor, tuple):
        hexcolor = ''.join(f'{c:02x}' for c in hexcolor)
    hexcolor = hexcolor.lstrip('#')
    
    if len(hexcolor) != 6:  
        return '#ffffff'  

    rgb = tuple(int(hexcolor[i:i+2], 16) for i in range(0, 6, 2))
    inverted_rgb = tuple(255 - c for c in rgb)

    return f"#{inverted_rgb[0]:02x}{inverted_rgb[1]:02x}{inverted_rgb[2]:02x}"


class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.clicked.connect(self.animate_click)

    def animate_click(self):
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(0)
        start_rect = self.geometry()
        end_rect = QRect(start_rect.x() + 5, start_rect.y() + 5, start_rect.width() - 10, start_rect.height() - 10)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        #self.anim.start()

class CalculatorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculator")
        self.setFixedSize(400, 600)

        layout = QGridLayout()
        layout.setContentsMargins(10,10,10,10)
        layout.setSpacing(10)

        self.display = QLineEdit()
        self.display.setFont(QFont("Roboto", 24))
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setFixedHeight(80)
        self.display.setReadOnly(True)
        layout.addWidget(self.display, 0, 0, 1, 4)

        self.bracket_toggle = True

        self.buttons = {
            "AC": (1, 0), "()": (1, 1), "%": (1, 2), "÷": (1, 3),
            "√": (2, 0), "π": (2, 1), "^": (2, 2), "!": (2, 3),
            "7": (3, 0), "8": (3, 1), "9": (3, 2), "×": (3, 3),
            "4": (4, 0), "5": (4, 1), "6": (4, 2), "-": (4, 3),
            "1": (5, 0), "2": (5, 1), "3": (5, 2), "+": (5, 3),
            "0": (6, 0), ".": (6, 1), "⌫": (6, 2), "=": (6, 3),
        }

        prefs = read_prefs("config/prefs.json")
        theme = prefs.get("theme")
        accent = read_prefs("config/accent.json") 
        self.accent_color = accent.get("accent_color_main")
        color = ""

        if theme == "light":
            color = adjust_color(self.accent_color, 1.2)
        elif theme == "dark":
            color = adjust_color(self.accent_color, 0.8)
        elif theme == "fetched":
            if accent.get("accent_color_fetched") != "":
                color = accent.get("accent_color_fetched")
            
        textcolor = invert_color(color)
        self.setStyleSheet(f"background-color: {color}; color: {textcolor};")

        self.light_color = adjust_color(self.accent_color, 1.5)
        self.dark_color = adjust_color(self.accent_color, 0.7)
        self.neutral_color = adjust_color(self.accent_color, 1.0)

        self.text_color = invert_color(self.accent_color)

        self.display.setStyleSheet(
            f"background-color: {self.neutral_color}; color: {self.text_color}; border: 2px solid {self.light_color}; padding: 10px;"
        )

        self.button_colors = {
            "AC": self.light_color,
            "()": self.neutral_color,
            "%": self.neutral_color,
            "÷": self.neutral_color,
            "√": self.light_color,
            "π": self.light_color,
            "^": self.light_color,
            "!": self.light_color,
            "7": self.light_color,
            "8": self.light_color,
            "9": self.light_color,
            "×": self.neutral_color,
            "4": self.light_color,
            "5": self.light_color,
            "6": self.light_color,
            "-": self.neutral_color,
            "1": self.light_color,
            "2": self.light_color,
            "3": self.light_color,
            "+": self.neutral_color,
            "0": self.light_color,
            ".": self.light_color,
            "⌫": self.light_color,
            "=": self.light_color,
        }

        self.button_widgets = {}
        for text, (row, col) in self.buttons.items():
            button = AnimatedButton(text)
            button.setFont(QFont("Roboto", 18))
            button.setFixedSize(80, 80)
            button.setStyleSheet(f"background-color: {self.button_colors[text]}; color: {self.text_color}; border-radius: 40px;")
            button.pressed.connect(lambda t=text: self.on_button_pressed(t))
            button.released.connect(lambda t=text: self.on_button_released(t))
            layout.addWidget(button, row, col)
            self.button_widgets[text] = button
        
        self.setLayout(layout)

        self.allowed_symbols = ["(", ")", "%", "÷", "×", "-", "+", "π", "√", "^", "!"]
        self.last_char = ""

    def on_button_pressed(self, button_text):
        self.button_widgets[button_text].setStyleSheet(
            f"border-radius: 40px; background-color: {self.light_color}; color: {self.text_color}; border: 2px solid {self.neutral_color};"
        )
        self.process_button_click(button_text)

    def on_button_released(self, button_text):
        self.button_widgets[button_text].setStyleSheet(
            f"border-radius: 40px; background-color: {self.button_colors[button_text]}; color: {self.text_color};"
        )
        
    def process_button_click(self, button_text):

        if button_text == "AC":
            self.display.clear()
            self.last_char = ""
            self.bracket_toggle = True
        elif button_text == "()":
            current_text = self.display.text()
            if self.bracket_toggle == True:
                current_text += "("
                self.bracket_toggle = False
            elif self.bracket_toggle == False:
                current_text += ")"
                self.bracket_toggle = True

            self.display.setText(current_text)
            
        
        elif button_text == "=":
            try:  
                expression = self.display.text().replace("÷", "/").replace("×", "*").replace("π", "math.pi").replace("^", "**")
                while "√" in expression:
                    index = expression.index("√")
                    num_start = index + 1
                    num_end = num_start
                    while num_end < len(expression) and (expression[num_end].isdigit() or expression[num_end] == "."):
                        num_end += 1
                    number = expression[num_start:num_end]
                    sqrt_result = f"math.sqrt({number})"
                    expression = expression[:index] + sqrt_result + expression[num_end:]
                print(expression)
                if "!" in expression:
                    expression = self.handle_factorial(expression)
                result = eval(expression)
                self.display.setText(str(result))
                self.last_char = str(result)[-1] if result else ""
            except Exception as e:
                self.showAlert(f"Error")
                self.last_char = ""
        elif button_text in self.allowed_symbols:
            if self.last_char in self.allowed_symbols:
                return  
            self.display.setText(self.display.text() + button_text)
            self.last_char = button_text
        elif button_text == "⌫":
            text = self.display.text()
            if text:
                self.display.setText(text[:-1])
                self.last_char = text[-2] if len(text) > 1 else ""
        else:
            self.display.setText(self.display.text() + button_text)
            self.last_char = button_text

    def handle_factorial(self, expression):
        while "!" in expression:
            index = expression.index("!")
            num_start = index - 1
            while num_start >= 0 and (expression[num_start].isdigit() or expression[num_start] == "."):
                num_start -= 1
            num_start += 1
            number = expression[num_start:index]
            fact_result = str(math.factorial(int(number)))
            expression = expression[:num_start] + fact_result + expression[index + 1:]
        return expression

    def simulate_button_press(self, key):
        if key in self.button_widgets:
            self.on_button_pressed(key)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Backspace:
            self.process_button_click("⌫")
        elif key == Qt.Key.Key_Enter or Qt.Key.Key_Return or Qt.Key.Key_Equal:
            self.process_button_click("=")
        elif key in self.allowed_symbols + [str(i) for i in range(10)] + ["."]:
            self.process_button_click(key)
        super().keyPressEvent(event)

    def showAlert(self, message):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg.setText(message)
        msg.setWindowTitle("Info")
        msg.exec()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        calc = CalculatorWindow()
        self.setCentralWidget(calc)
        self.setWindowIcon(QIcon("cache/assets/calc.png"))
        self.setFixedSize(400, 635)

        self.setWindowTitle("MatUCalc")

        setimage_icon_path = "cache/assets/setimage.png"
        settings_icon_path = "cache/assets/settings.png"
        about_icon_path = "cache/assets/aboutwindow.png"
        star_icon_path = "cache/assets/star.png"

        file_action = QAction(QIcon(setimage_icon_path), "Fetch Colors From Image", self)
        file_action.setStatusTip("Set A Wallpaper")
        file_action.triggered.connect(self.fetchBackground)

        settings_action = QAction(QIcon(settings_icon_path), "Settings", self)
        settings_action.triggered.connect(self.openSettingsWindow)

        about_action = QAction(QIcon(about_icon_path), "About", self)
        about_action.setStatusTip("About MatUCalc")
        about_action.triggered.connect(self.openAboutWindow)

        star_github = QAction(QIcon(star_icon_path), "Star Us On Github!", self)
        star_github.setStatusTip("Star Us!")
        star_github.triggered.connect(self.OpenGithub)


        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        edit_menu = menu.addMenu("&Edit")
        about_menu = menu.addMenu("&Help")

        file_menu.addAction(file_action)
        about_menu.addAction(about_action)
        edit_menu.addAction(settings_action)
        about_menu.addAction(star_github)

    def openSettingsWindow(self):
        settings_win = SettingsWindow()
        settings_win.exec()

    def openAboutWindow(self):
        about_win = AboutWindow("cache/assets/calc.png")
        about_win.exec()

    def fetchBackground(self, s):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Image Files (*.png *.jpg *.webp)")
        if file_path:
            custom_directory = "fetch_img"
            if not os.path.exists(custom_directory):
                os.makedirs(custom_directory)
                
            base_filename = os.path.basename(file_path)
            destination_path = os.path.join(custom_directory, base_filename)

            shutil.copy(file_path, destination_path)
            print(f"Selected file: {file_path}")
            print(f"Copied to: {destination_path}")

            print({destination_path})
            convertImage()
            fetchColor(destination_path, "max", True)

    def OpenGithub(self, s):
        webbrowser.open('https://trigor.com')

class AboutWindow(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About Us")
        self.setFixedSize(250, 375)

        self.setWindowIcon(QIcon("cache/assets/aboutwindow.png"))

        file = read_prefs("config/prefs.json")
        accent = read_prefs("config/accent.json") 
        accent_color = accent.get("accent_color_main")
        theme = file.get("theme")
        color = ""

        if theme == "light":
            color = adjust_color(accent_color, 1.2)
        else:
            color = adjust_color(accent_color, 0.8)

        textcolor = invert_color(color)

        self.setStyleSheet(f"background-color: rgb{color}; color: rgb{textcolor}")

        layout = QVBoxLayout()

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap)
        
        layout.addWidget(self.image_label)

        label = QLabel("MatUCalc\nver0.1(pre-release)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        authors_box = QGroupBox("Authors")
        authors_layout = QVBoxLayout()
        authors_label = QLabel(self)
        authors_label.setText(
            f'<a style="color: rgb{textcolor};" href="https://github.com/LinusFreakvalds">Pliskin</a><br>'
            f'<a style="color: rgb{textcolor};" href="https://github.com/aarengg715">AarenGG</a><br>'
        )
        print(textcolor)
        authors_label.setOpenExternalLinks(True)
        authors_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        authors_layout.addWidget(authors_label)
        authors_box.setLayout(authors_layout)
        layout.addWidget(authors_box)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        file = read_prefs("config/prefs.json")
        accent = read_prefs("config/accent.json") 
        accent_color = accent.get("accent_color_main")
        theme = file.get("theme")
        color = ""

        if theme == "light":
            color = adjust_color(accent_color, 1.2)
        else:
            color = adjust_color(accent_color, 0.8)

        textcolor = invert_color(color)
        self.setStyleSheet(f"background-color: rgb{color}; color: rgb{textcolor}")

        

        

        self.setWindowTitle("Settings")
        self.setFixedSize(200, 180)
        self.setWindowIcon(QIcon("cache/assets/settings.png"))

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        group_box = QGroupBox("Theme")

        self.radio1 = QRadioButton("Light")
        self.radio2 = QRadioButton("Dark")
        self.radio3 = QRadioButton("Fetch from image")
        self.label = QLabel("To choose file from which to fetch, click File > Fetch from image")
        self.label.setWordWrap(True)
        self.label.setVisible(False)

        radio_layout = QVBoxLayout()
        radio_layout.addWidget(self.radio1)
        radio_layout.addWidget(self.radio2)
        radio_layout.addWidget(self.radio3)
        radio_layout.addWidget(self.label)
        group_box.setLayout(radio_layout)

        self.radio3.toggled.connect(self.label.setVisible)

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(group_box)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

        self.load_settings()

    def load_settings(self):
        prefs = read_prefs("config/prefs.json")
        theme = prefs.get("theme")
        prefs.update()
        if theme == "light":
            self.radio1.setChecked(True)
            self.radio2.setChecked(False)
            self.radio3.setChecked(False)
            
        elif theme == "dark":
            self.radio1.setChecked(False)
            self.radio2.setChecked(True)
            self.radio3.setChecked(False)

        elif theme == "fetched":
            self.radio1.setChecked(False)
            self.radio2.setChecked(False)
            self.radio3.setChecked(True)

    def accept(self):
        with open("config/prefs.json", 'r') as file:
            prefs = json.load(file)
        with open("config/accent.json", 'r') as file2:
            accent = json.load(file2)
        accentcolor = read_prefs("config/accent.json") 

        if self.radio1.isChecked():
            prefs['theme'] = 'light'
            accent['accent_color_main'] = "#c8c8c8"
        elif self.radio2.isChecked():
            prefs['theme'] = 'dark'
            accent['accent_color_main'] = "#373737"
        elif self.radio3.isChecked() and accent['accent_color_fetched'] != "":
            prefs['theme'] = 'fetched'
            accent['accent_color_main'] = accent["accent_color_fetched"]

        
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg.setText("For theme to start working, you should restart app")
        msg.setWindowTitle("Info")
        msg.exec()

        with open("config/prefs.json", 'w') as file:
            json.dump(prefs, file, indent=4)
        with open("config/accent.json", 'w') as file2:
            json.dump(accent, file2, indent=4)

        super().accept()
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    modifySvg()

    window.show()
    sys.exit(app.exec())
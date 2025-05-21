import sys
import os
import shutil
from pathlib import Path
import tools

from .. import main_tool

from PyQt5.QtGui import QColor, QPalette, QTextCursor, QDesktopServices
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtCore import Qt, QUrl, QTimer, QMetaObject, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QAction,QMenu, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QTextEdit,
                             QWidget, QLineEdit, QPushButton, QFrame, QSizePolicy, QMessageBox, QDialog)

class MainApp(QMainWindow):
    def __init__(self):

        self.main_block = None
        self.screens = None
        self.file_loaders = []

        self.tool_selected= None
        self.partial_agg_results_flag=False

        super().__init__()

        #Set the main window
        self.setWindowTitle("IHRAT")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.apply_dark_theme()

        #Set the central widget and the main layout in it
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("""
                    background-color: rgb(53, 53, 53);
                    border-radius: 10px;
                """)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.central_widget.setLayout(main_layout)

        #Set the title bar in the main layout
        self.create_title_bar()
        main_layout.addWidget(self.title_bar)

        #Set the content layout in the main layout
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(content_layout)

        #Set the sidebar in the content layout
        self.create_side_bar() #REVISAR QUE HACEMOS CON ELLA
        content_layout.addWidget(self.sidebar)

        #Set the main block in the content layout (the one displaying the different screens)
        self.main_block = QVBoxLayout()
        content_layout.addLayout(self.main_block, stretch=1)

        self.show_screen("input_screen")

    def apply_dark_theme(self):

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Highlight, QColor(0, 188, 212))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setPalette(dark_palette)

        self.central_widget = QWidget()

    def create_title_bar(self):

        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("""
               background-color: #353535;
               border-top-left-radius: 10px;
               border-top-right-radius: 10px;
           """)
        layout = QHBoxLayout(self.title_bar)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)

        self.title_label = QLabel("IHRAT")
        self.title_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        #Create min,max,close buttons
        self.minimize_button = QPushButton("−")
        self.maximize_button = QPushButton("□")
        self.close_button = QPushButton("×")
        for button in [self.minimize_button, self.maximize_button, self.close_button]:
            button.setFixedSize(30, 30)
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #00BCD4;
                }
            """)
            layout.addWidget(button)
        self.minimize_button.clicked.connect(self.showMinimized)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        self.close_button.clicked.connect(self.close)

        #Add movement to the window while pressing and moving the title bar
        self.title_bar.mousePressEvent = self.titleBarMousePressEvent
        self.title_bar.mouseMoveEvent = self.titleBarMouseMoveEvent

        #Create a bottom line for the title bar
        bottom_line = QWidget(self.title_bar)
        bottom_line.setFixedHeight(1)
        bottom_line.setStyleSheet("background-color: #00BCD4;")
        bottom_line.move(0, 29)
        bottom_line.resize(self.title_bar.width(), 1)

        #Resize the title bar with the window
        self.title_bar.resizeEvent = lambda event: bottom_line.resize(event.size().width(), 1)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def titleBarMousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.isMaximized():
                self.drag_start_position = (event.globalPos() - self.frameGeometry().topLeft()) / 3
            else:
                self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def titleBarMouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.isMaximized():
                self.showNormal()
                self.move(event.globalPos())
            else:
                self.move(event.globalPos() - self.drag_start_position)
            event.accept()

    def create_side_bar(self):

        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(80)
        self.sidebar.setStyleSheet("""
                            QWidget {
                                background-color: #1E1E1E;
                                border-right: 1px solid #2D2D2D;
                                border-radius: 0px;
                                border-bottom-left-radius: 10px;
                            }
                        """)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        self.sidebar.setLayout(sidebar_layout)

        self.sidebar_buttons = []
        button_data = [("Inputs", "📁"), ("Exe", "⚙️")]
        for j, (text, icon) in enumerate(button_data):
            btn = QPushButton(f"{icon}\n{text}")
            btn.setFixedHeight(80)
            btn.setStyleSheet("""
                                QPushButton {
                                    background-color: transparent;
                                    color: #CCCCCC;
                                    border: none;
                                    font-size: 12px;
                                    font-weight: bold;
                                    text-align: center;
                                    padding: 5px;
                                }
                                QPushButton:hover {
                                    background-color: #2D2D2D;
                                }
                                QPushButton:pressed {
                                    background-color: #3D3D3D;
                                }
                            """)
            btn.clicked.connect(lambda _, i=j: self.show_screen(i))
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)
        sidebar_layout.addStretch()

    def show_screen(self, screen):
        # Limpiar el bloque general
        for i in reversed(range(self.main_block.count())):
            widget = self.main_block.itemAt(i).widget()
            self.main_block.removeWidget(widget)
            widget.setParent(None)

        #Mostrar la pantalla seleccionada
        screen_fun = getattr(self, screen)
        screen_fun()

    def input_screen(self):

        buttons_stylesheet="""
                            QPushButton {
                                background-color: #00BCD4;
                                color: white;
                                border: none;
                                padding: 10px;
                                border-radius: 5px;
                            }
                            QPushButton:hover {
                                background-color: #00ACC1;
                            }
                        """

        button_menu_stylesheet="""
            QPushButton {
                                background-color: #00BCD4;
                                color: white;
                                border: none;
                                font-weight: bold;
                                padding: 10px;
                                border-radius: 5px;
                            }
                            QPushButton:hover {
                                background-color: #00ACC1;
                            }
            QPushButton::menu-indicator {
        subcontrol-origin: content;
        subcontrol-position: center right; /* justo al final del texto */
        padding-left: 5px;
    }
        """

        menu_stylesheet="""
    QMenu {
        background-color: white;
        color: #00BCD4;
        border: none;
        padding: 5px;
        border-radius: 5px;
    }
    QMenu::item {
        padding: 8px 15px;
        background-color: transparent;
        border-radius: 3px;
    }
    QMenu::item:selected {
        background-color: #00ACC1;
        color: white;
    }
"""

        #Initialize the screen widget and layout
        screen = QWidget()
        screen_layout = QVBoxLayout()
        screen.setLayout(screen_layout)

        # Set the title for the input screen
        inputs_title_layout = QHBoxLayout()
        inputs_title = QLabel("Inputs")
        inputs_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        inputs_title_layout.addWidget(inputs_title)
        screen_layout.addLayout(inputs_title_layout)


        #Set the input files layout in the screen layout
        inputs_files_layout = QVBoxLayout()
        inputs_files_layout.setContentsMargins(0, 10, 0, 10)

        # Set the title for the choosing the input data (r-r o s-r)
        inputs_title_layout = QHBoxLayout()
        inputs_title = QLabel("Types of input data")
        inputs_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        inputs_title_layout.addWidget(inputs_title)
        screen_layout.addLayout(inputs_title_layout)

        #Set the button for choosing the inputs format
        format_button = QPushButton("Select input files format")
        format_button.setStyleSheet(button_menu_stylesheet)
        format_menu = QMenu()
        format_menu.setStyleSheet(menu_stylesheet)
        option1 = QAction("Exposure: raster (.tif) - Impact: raster (.tif)", format_button)
        option2 = QAction("Exposure: shapefile (.shp) - Impact: raster (.tif)", format_button)
        option1.triggered.connect(lambda: self.select_rr(format_button,partial_agg_button))
        option2.triggered.connect(lambda: self.select_sr(format_button,partial_agg_button))
        format_menu.addAction(option1)
        format_menu.addAction(option2)
        format_button.setMenu(format_menu)
        screen_layout.addWidget(format_button)

        # Set the title for the partial aggregation possibility
        inputs_title_layout = QHBoxLayout()
        inputs_title = QLabel("Partial aggregated results")
        inputs_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        inputs_title_layout.addWidget(inputs_title)
        screen_layout.addLayout(inputs_title_layout)

        # Set the button for choosing if the s-r uses partial aggregation
        partial_agg_button = QPushButton("Select partial aggregation (only possible in shapefile-raster)")
        partial_agg_button.setEnabled(False)
        partial_agg_button.setStyleSheet(button_menu_stylesheet)
        format_menu = QMenu()
        format_menu.setStyleSheet(menu_stylesheet)
        option1 = QAction("Partial aggregated results", partial_agg_button)
        option2 = QAction("No partial aggregated results", partial_agg_button)
        option1.triggered.connect(lambda: self.select_partial(partial_agg_button))
        option2.triggered.connect(lambda: self.select_no_partial(partial_agg_button))
        format_menu.addAction(option1)
        format_menu.addAction(option2)
        partial_agg_button.setMenu(format_menu)
        screen_layout.addWidget(partial_agg_button)

        #Set the title for the input files layout
        inputs_title_layout = QHBoxLayout()
        inputs_title = QLabel("Input files")
        inputs_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        inputs_title_layout.addWidget(inputs_title)
        screen_layout.addLayout(inputs_title_layout)

        #Set the inputs window layout
        inputs_windows_layout = QHBoxLayout()

        #Exposition files input
        exp_inputs_layout = QVBoxLayout()
        #Set the text box
        inputs_file_input_exp = QTextEdit()
        inputs_file_input_exp.setReadOnly(True)
        inputs_file_input_exp.setStyleSheet("""
                    QTextEdit {
                        background-color: #1E1E1E;
                        color: white;
                        border: 1px solid #2D2D2D;
                        padding: 5px;
                    }
                """)
        #Set the placeholder text
        inputs_file_input_exp.setPlaceholderText("Exposition inputs files...")
        #Read the files in the expmaps folder and, if any, show them in the text box
        inputs_file_input_exp.setText("\n".join(tools.reading_files('expmaps')))
        exp_inputs_layout.addWidget(inputs_file_input_exp)
        #Set the buttons layout
        exp_buttons_layout=QHBoxLayout()
        #Set the load button
        load_expfiles_button = QPushButton("Load")
        load_expfiles_button.setStyleSheet(buttons_stylesheet)
        load_expfiles_button.clicked.connect(lambda _, input=inputs_file_input_exp:
                                             self.load_files(input,'expmaps'))
        exp_buttons_layout.addWidget(load_expfiles_button)
        #Set the delete button
        delete_expfiles_button = QPushButton("Delete")
        delete_expfiles_button.setStyleSheet(buttons_stylesheet)
        delete_expfiles_button.clicked.connect(lambda _, input=inputs_file_input_exp:
                                        self.delete_files(input,'expmaps',"Exposition inputs files..."))
        exp_buttons_layout.addWidget(delete_expfiles_button)
        #Add buttons layout to exp files input layout
        exp_inputs_layout.addLayout(exp_buttons_layout)
        #Add the exp files input layout to the inputs window layout
        inputs_windows_layout.addLayout(exp_inputs_layout)

        #Impact files input
        imp_inputs_layout = QVBoxLayout()
        # Set the text box
        inputs_file_input_imp = QTextEdit()
        inputs_file_input_imp.setReadOnly(True)
        inputs_file_input_imp.setStyleSheet("""
                            QTextEdit {
                                background-color: #1E1E1E;
                                color: white;
                                border: 1px solid #2D2D2D;
                                padding: 5px;
                            }
                        """)
        # Set the placeholder text
        inputs_file_input_imp.setPlaceholderText("Impact inputs files...")
        # Read the files in the expmaps folder and, if any, show them in the text box
        inputs_file_input_imp.setText("\n".join(tools.reading_files('impmaps')))
        imp_inputs_layout.addWidget(inputs_file_input_imp)
        # Set the buttons layout
        imp_buttons_layout = QHBoxLayout()
        #Set the load button
        load_impfiles_button = QPushButton("Load")
        load_impfiles_button.setStyleSheet(buttons_stylesheet)
        load_impfiles_button.clicked.connect(lambda _, input=inputs_file_input_imp:
                                             self.load_files(input,'impmaps'))
        imp_buttons_layout.addWidget(load_impfiles_button)
        #Set the delete button
        delete_impfiles_button = QPushButton("Delete")
        delete_impfiles_button.setStyleSheet(buttons_stylesheet)
        delete_impfiles_button.clicked.connect(lambda _, input=inputs_file_input_exp:
                                            self.delete_files(input,'impmaps',"Impact inputs files..."))
        imp_buttons_layout.addWidget(delete_impfiles_button)
        # Add buttons layout to imp files input layout
        imp_inputs_layout.addLayout(imp_buttons_layout)
        #Add the exp files input layout to the inputs window layout
        inputs_windows_layout.addLayout(imp_inputs_layout)

        #Add the inputs window layout to the inputs files layout
        inputs_files_layout.addLayout(inputs_windows_layout)

        #Add the input files layout to the screen layout
        screen_layout.addLayout(inputs_files_layout, stretch=1)

        #Set the execution button
        hbox_layout = QHBoxLayout()
        hbox_layout.setContentsMargins(0, 10, 0, 10)
        button_execute = QPushButton("Run IHRAT")
        button_execute.setStyleSheet(buttons_stylesheet)
        button_execute.clicked.connect(self.execute_tool)

        button_execute.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        hbox_layout.addWidget(button_execute)
        hbox_layout.insertSpacing(0, 10)  # Margen izquierdo
        hbox_layout.addSpacing(10)  # Margen derecho

        screen_layout.addLayout(hbox_layout, stretch=2)

        self.main_block.addWidget(screen)

    def load_files(self, file_input,folder_name):

        #Select the files to load
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivo", "", "Todos los archivos (*.*)",
                                                   options=options)

        # Get the program folder to save the files
        folder_path = Path.cwd().parent.parent / folder_name
        # If it doesn't exist, create the folder
        os.makedirs(folder_path, exist_ok=True)

        #Add the files to the program folder
        if file_paths:
            file_names = []
            for path in file_paths:
                file_name = os.path.basename(path)
                file_names.append(file_name)
                file_path = os.path.join(folder_path, file_name)
                shutil.copy(path, file_path)
            #Add the file names to the input textbox
            file_input.append("\n".join(file_names))

    def delete_files(self, file_input,folder_name,text):

        # Get the program folder to delete the files from
        folder_path = Path.cwd().parent.parent / folder_name

        #Delete all the files
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        #Clean the input textbox and set the placeholder text
        file_input.clear()
        file_input.setPlaceholderText(text)

    def select_rr(self,button,partial_button):
        self.tool_selected = 'raster_raster'
        button.setText("Exposure: raster (.tif) - Impact: raster (.tif)")
        partial_button.setText("Select partial aggregation (only possible in shapefile-raster)")
        partial_button.setEnabled(False)
        self.partial_agg_results_flag = False

    def select_sr(self,button,partial_button):
        self.tool_selected='shape_raster'
        button.setText("Exposure: shapefile (.shp) - Impact: raster (.tif)")
        partial_button.setEnabled(True)

    def select_partial(self,partial_button):
        self.partial_agg_results_flag=True
        partial_button.setText("Partial aggregated results")

    def select_no_partial(self,partial_button):
        self.partial_agg_results_flag = False
        partial_button.setText("No partial aggregated results")

    def execute_tool(self):


def run_ihrat_gui():
    app = QApplication(sys.argv) #REVISAR
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_ihrat_gui()
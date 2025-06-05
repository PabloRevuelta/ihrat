import sys
import os
import shutil
from pathlib import Path
import time
import math

import traceback

import tools

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import Qt, QRunnable, pyqtSlot, QThreadPool, QObject, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QLineEdit, QAction, QMenu, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel,
                             QFileDialog, QTextEdit,
                             QWidget, QPushButton, QGridLayout, QScrollArea, QDialog, QFormLayout, QDialogButtonBox)

from ihrat.src import main_tool
from ihrat.src.dictionaries import keysdic, keysoutputdic


class MainApp(QMainWindow):
    def __init__(self):

        super().__init__()

        self.dam_fun_container = None
        self.function_menu = None
        self.dam_fun_container_layout = None
        self.sys_ticks_list = []
        self.scen_ticks_list = []
        self.central_widget = None
        self.drag_start_position = None
        self.sidebar = None
        self.sidebar_buttons = None
        self.title_bar = None
        self.main_block = None
        self.screens = None
        self.file_loaders = []

        self.threadpool = QThreadPool()

        self.tool_selected = None
        self.partial_agg_results_flag = False
        self.dam_fun_file_flag = False
        self.zonal_stats_method = None
        self.zonal_stats_value = None

        self.keysdic = keysdic
        self.keysoutputdic = keysoutputdic

        self.exp_maps_list = tools.reading_folder_files('expmaps', '.shp')
        self.imp_maps_list = tools.reading_folder_files('impmaps', '.tif')

        file_path = Path.cwd().parent / 'src//damage_functions//damage_functions_dic.py'
        self.dam_fun_list = tools.extraer_funciones_ast(file_path)

        self.buttons_stylesheet = """
                                    QPushButton {
                                        background-color: #00BCD4;
                                        color: white;
                                        border: none;
                                        padding: 10px;
                                        font-weight: bold;
                                        border-radius: 5px;
                                    }
                                    QPushButton:hover {
                                        background-color: #00ACC1;
                                    }
                                    QPushButton:pressed {
                                        background-color: #0097A7;
                                        padding-top: 12px;
                                        padding-bottom: 8px;
                                    }
                                    """

        self.button_menu_stylesheet = """
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

        self.menu_stylesheet = """
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

        self.init_ui()

    def init_ui(self):

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
        self.create_side_bar()  #REVISAR QUE HACEMOS CON ELLA
        content_layout.addWidget(self.sidebar)

        #Set the main block in the content layout (the one displaying the different screens)
        self.main_block = QVBoxLayout()
        content_layout.addLayout(self.main_block, stretch=1)

        self.init_screens()
        self.show_screen(0)

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

        title_label = QLabel("IHRAT")
        title_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(title_label)

        layout.addStretch()

        #Create min,max,close buttons
        minimize_button = QPushButton("−")
        maximize_button = QPushButton("□")
        close_button = QPushButton("×")
        for button in [minimize_button, maximize_button, close_button]:
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
        minimize_button.clicked.connect(self.showMinimized)
        maximize_button.clicked.connect(self.toggle_maximize)
        close_button.clicked.connect(self.close)

        #Add movement to the window while pressing and moving the title bar
        self.title_bar.mousePressEvent = self.title_bar_mouse_press_event
        self.title_bar.mouseMoveEvent = self.title_bar_mouse_move_event

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

    def title_bar_mouse_press_event(self, event):
        if event.button() == Qt.LeftButton:
            if self.isMaximized():
                self.drag_start_position = (event.globalPos() - self.frameGeometry().topLeft()) / 3
            else:
                self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def title_bar_mouse_move_event(self, event):
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
        button_data = [("Inputs", "📁"), ("Exe", "⚙️"), ("Dics", "📘"), ("Dam fun", "📈"), ("Results", "🗺️")]
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

    def init_screens(self):
        self.screens = []

        screen = self.input_screen()
        self.screens.append(screen)
        screen = self.executing_screen()
        self.screens.append(screen)
        screen = self.dictionaries_screen()
        self.screens.append(screen)
        screen = self.dam_fun_screen()
        self.screens.append(screen)
        screen = self.results_screen()
        self.screens.append(screen)

    def input_screen(self):

        # Initialize the screen widget and layout
        screen_layout = QVBoxLayout()
        screen = QWidget()
        screen.setLayout(screen_layout)

        # Set the title for the input screen
        inputs_title = QLabel("Inputs")
        inputs_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        screen_layout.addWidget(inputs_title)

        # Set the button for choosing the inputs format
        inputs_types_title = QLabel("Types of input data")
        inputs_types_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        screen_layout.addWidget(inputs_types_title)
        format_button = QPushButton("Select input files format")
        format_button.setStyleSheet(self.button_menu_stylesheet)
        format_menu = QMenu()
        format_menu.setStyleSheet(self.menu_stylesheet)
        option1 = QAction("Exposure: raster (.tif) - Impact: raster (.tif)", format_button)
        option2 = QAction("Exposure: shapefile (.shp) - Impact: raster (.tif)", format_button)
        option3 = QAction("Exposure: shapefile (.shp) - Impact: shapefile (.shp)", format_button)
        option1.triggered.connect(lambda: self.select_rr(format_button, partial_agg_button,
                                                         dam_fun_button, zonal_stats_method_button,
                                                         zonal_stats_value_button))
        option2.triggered.connect(lambda: self.select_sr(format_button, partial_agg_button,
                                                         dam_fun_button, zonal_stats_method_button,
                                                         zonal_stats_value_button))
        option3.triggered.connect(lambda: self.select_ss(format_button, partial_agg_button,
                                                         dam_fun_button, zonal_stats_method_button,
                                                         zonal_stats_value_button))
        format_menu.addAction(option1)
        format_menu.addAction(option2)
        format_menu.addAction(option3)
        format_button.setMenu(format_menu)
        screen_layout.addWidget(format_button)

        options_1_layout = QHBoxLayout()
        screen_layout.addLayout(options_1_layout)

        # Set the button for choosing if the s-r uses partial aggregation
        inputs_title_layout = QVBoxLayout()
        inputs_title = QLabel("Partial aggregated results")
        inputs_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        inputs_title_layout.addWidget(inputs_title)
        partial_agg_button = QPushButton("Select partial aggregation")
        partial_agg_button.setEnabled(False)
        partial_agg_button.setStyleSheet(self.button_menu_stylesheet)
        format_menu = QMenu()
        format_menu.setStyleSheet(self.menu_stylesheet)
        option1 = QAction("Partial aggregated results", partial_agg_button)
        option2 = QAction("No partial aggregated results", partial_agg_button)
        option1.triggered.connect(lambda: self.select_partial(partial_agg_button))
        option2.triggered.connect(lambda: self.select_no_partial(partial_agg_button))
        format_menu.addAction(option1)
        format_menu.addAction(option2)
        partial_agg_button.setMenu(format_menu)
        inputs_title_layout.addWidget(partial_agg_button)
        options_1_layout.addLayout(inputs_title_layout)

        # Set the button for choosing the damage functions option (rr)
        dam_fun_layout = QVBoxLayout()
        dam_fun_title = QLabel("Damage functions input (rr)")
        dam_fun_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        dam_fun_layout.addWidget(dam_fun_title)
        dam_fun_button = QPushButton("Select damage functions input (rr)")
        dam_fun_button.setEnabled(False)
        dam_fun_button.setStyleSheet(self.button_menu_stylesheet)
        format_menu = QMenu()
        format_menu.setStyleSheet(self.menu_stylesheet)
        option1 = QAction("Damage functions distribution shapefile", dam_fun_button)
        option2 = QAction("General damage function", dam_fun_button)
        option1.triggered.connect(lambda: self.select_file(dam_fun_button))
        option2.triggered.connect(lambda: self.select_no_file(dam_fun_button))
        format_menu.addAction(option1)
        format_menu.addAction(option2)
        dam_fun_button.setMenu(format_menu)
        dam_fun_layout.addWidget(dam_fun_button)
        options_1_layout.addLayout(dam_fun_layout)

        options_2_layout = QHBoxLayout()
        screen_layout.addLayout(options_2_layout)

        # Set the button for choosing the zonal stats method (sr)
        zonal_stats_method_layout = QVBoxLayout()
        zonal_stats_method_title = QLabel("Zonal stats method (sr)")
        zonal_stats_method_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        zonal_stats_method_layout.addWidget(zonal_stats_method_title)
        zonal_stats_method_button = QPushButton("Select zonal stats method (sr)")
        zonal_stats_method_button.setEnabled(False)
        zonal_stats_method_button.setStyleSheet(self.button_menu_stylesheet)
        format_menu = QMenu()
        format_menu.setStyleSheet(self.menu_stylesheet)
        option1 = QAction("Centers", zonal_stats_method_button)
        option2 = QAction("All touched", zonal_stats_method_button)
        option1.triggered.connect(lambda: self.select_centers(zonal_stats_method_button))
        option2.triggered.connect(lambda: self.select_all_touched(zonal_stats_method_button))
        format_menu.addAction(option1)
        format_menu.addAction(option2)
        zonal_stats_method_button.setMenu(format_menu)
        zonal_stats_method_layout.addWidget(zonal_stats_method_button)
        options_2_layout.addLayout(zonal_stats_method_layout)

        # Set the button for choosing the value used in computing zonal stats (sr-ss)
        zonal_stats_value_layout = QVBoxLayout()
        zonal_stats_value_title = QLabel("Value for zonal statistics (sr-ss)")
        zonal_stats_value_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        zonal_stats_value_layout.addWidget(zonal_stats_value_title)
        zonal_stats_value_button = QPushButton("Select value for zonal statistics (sr-ss)")
        zonal_stats_value_button.setEnabled(False)
        zonal_stats_value_button.setStyleSheet(self.button_menu_stylesheet)
        format_menu = QMenu()
        format_menu.setStyleSheet(self.menu_stylesheet)
        option1 = QAction("Mean", zonal_stats_value_button)
        option2 = QAction("Max", zonal_stats_value_button)
        option1.triggered.connect(lambda: self.select_mean(zonal_stats_value_button))
        option2.triggered.connect(lambda: self.select_max(zonal_stats_value_button))
        format_menu.addAction(option1)
        format_menu.addAction(option2)
        zonal_stats_value_button.setMenu(format_menu)
        zonal_stats_value_layout.addWidget(zonal_stats_value_button)
        options_2_layout.addLayout(zonal_stats_value_layout)

        #Set the title for the input files layout
        inputs_title = QLabel("Input files")
        inputs_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        screen_layout.addWidget(inputs_title)

        inputs_windows_layout = QHBoxLayout()
        screen_layout.addLayout(inputs_windows_layout)

        # Exposition files input
        exp_inputs_layout = QVBoxLayout()
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
        inputs_file_input_exp.setPlaceholderText("Exposition inputs files...")
        inputs_file_input_exp.setText("\n".join(tools.reading_files('inputs\\expmaps')))
        exp_inputs_layout.addWidget(inputs_file_input_exp)
        exp_buttons_layout = QHBoxLayout()
        load_expfiles_button = QPushButton("Load")
        load_expfiles_button.setStyleSheet(self.buttons_stylesheet)
        load_expfiles_button.clicked.connect(lambda _, inputs=inputs_file_input_exp:
                                             self.load_files(inputs, 'inputs\\expmaps'))
        exp_buttons_layout.addWidget(load_expfiles_button)
        delete_expfiles_button = QPushButton("Delete")
        delete_expfiles_button.setStyleSheet(self.buttons_stylesheet)
        delete_expfiles_button.clicked.connect(lambda _, inputs=inputs_file_input_exp:
                                               self.delete_files(inputs, 'inputs\\expmaps',
                                                                 "Exposition inputs files..."))
        exp_buttons_layout.addWidget(delete_expfiles_button)
        exp_inputs_layout.addLayout(exp_buttons_layout)
        inputs_windows_layout.addLayout(exp_inputs_layout)

        # Impact files input
        imp_inputs_layout = QVBoxLayout()
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
        inputs_file_input_imp.setPlaceholderText("Impact inputs files...")
        inputs_file_input_imp.setText("\n".join(tools.reading_files('inputs\\impmaps')))
        imp_inputs_layout.addWidget(inputs_file_input_imp)
        imp_buttons_layout = QHBoxLayout()
        load_impfiles_button = QPushButton("Load")
        load_impfiles_button.setStyleSheet(self.buttons_stylesheet)
        load_impfiles_button.clicked.connect(lambda _, inputs=inputs_file_input_imp:
                                             self.load_files(inputs, 'inputs\\impmaps'))
        imp_buttons_layout.addWidget(load_impfiles_button)
        delete_impfiles_button = QPushButton("Delete")
        delete_impfiles_button.setStyleSheet(self.buttons_stylesheet)
        delete_impfiles_button.clicked.connect(lambda _, inputs=inputs_file_input_imp:
                                               self.delete_files(inputs, 'inputs\\impmaps', "Impact inputs files..."))
        imp_buttons_layout.addWidget(delete_impfiles_button)
        imp_inputs_layout.addLayout(imp_buttons_layout)
        inputs_windows_layout.addLayout(imp_inputs_layout)

        inputs_windows_2_layout = QHBoxLayout()
        screen_layout.addLayout(inputs_windows_2_layout)

        # Partial aggregate map (r-r)
        partial_agg_file_layout = QVBoxLayout()
        partial_agg_file_input = QTextEdit()
        partial_agg_file_input.setReadOnly(True)
        partial_agg_file_input.setStyleSheet("""
                                    QTextEdit {
                                        background-color: #1E1E1E;
                                        color: white;
                                        border: 1px solid #2D2D2D;
                                        padding: 5px;
                                    }
                                """)
        partial_agg_file_input.setPlaceholderText("Partial aggregate file (r-r) ...")
        partial_agg_file_input.setText("\n".join(tools.reading_files('inputs\\partial_agg_map')))
        partial_agg_file_layout.addWidget(partial_agg_file_input)
        partial_agg_file_buttons_layout = QHBoxLayout()
        load_partial_agg_file_button = QPushButton("Load")
        load_partial_agg_file_button.setStyleSheet(self.buttons_stylesheet)
        load_partial_agg_file_button.clicked.connect(lambda _, inputs=partial_agg_file_input:
                                                     self.load_files(inputs, 'inputs\\partial_agg_map'))
        partial_agg_file_buttons_layout.addWidget(load_partial_agg_file_button)
        delete_partial_agg_file_button = QPushButton("Delete")
        delete_partial_agg_file_button.setStyleSheet(self.buttons_stylesheet)
        delete_partial_agg_file_button.clicked.connect(lambda _, inputs=partial_agg_file_input:
                                                       self.delete_files(inputs, 'inputs\\partial_agg_map',
                                                                         "Partial aggregate file (r-r) ..."))
        partial_agg_file_buttons_layout.addWidget(delete_partial_agg_file_button)
        partial_agg_file_layout.addLayout(partial_agg_file_buttons_layout)
        inputs_windows_2_layout.addLayout(partial_agg_file_layout)

        #Damage functions distribution file (r-r)
        dam_fun_file_layout = QVBoxLayout()
        dam_fun_file_input = QTextEdit()
        dam_fun_file_input.setReadOnly(True)
        dam_fun_file_input.setStyleSheet("""
                                            QTextEdit {
                                                background-color: #1E1E1E;
                                                color: white;
                                                border: 1px solid #2D2D2D;
                                                padding: 5px;
                                            }
                                        """)
        dam_fun_file_input.setPlaceholderText("Damage functions distribution file (r-r) ...")
        dam_fun_file_input.setText("\n".join(tools.reading_files('inputs\\dam_fun_files')))
        dam_fun_file_layout.addWidget(dam_fun_file_input)
        dam_fun_file_buttons_layout = QHBoxLayout()
        load_dam_fun_file_button = QPushButton("Load")
        load_dam_fun_file_button.setStyleSheet(self.buttons_stylesheet)
        load_dam_fun_file_button.clicked.connect(lambda _, inputs=dam_fun_file_input:
                                                 self.load_files(inputs, 'inputs\\dam_fun_files'))
        dam_fun_file_buttons_layout.addWidget(load_dam_fun_file_button)
        delete_dam_fun_file_button = QPushButton("Delete")
        delete_dam_fun_file_button.setStyleSheet(self.buttons_stylesheet)
        delete_dam_fun_file_button.clicked.connect(lambda _, inputs=dam_fun_file_input:
                                                   self.delete_files(inputs, 'inputs\\dam_fun_files',
                                                                     "Damage functions distribution file (r-r) ..."))
        dam_fun_file_buttons_layout.addWidget(delete_dam_fun_file_button)
        dam_fun_file_layout.addLayout(dam_fun_file_buttons_layout)
        inputs_windows_2_layout.addLayout(dam_fun_file_layout)

        # Set the execution button
        button_execute = QPushButton("Run IHRAT")
        button_execute.setStyleSheet(self.buttons_stylesheet)
        button_execute.clicked.connect(self.execute_tool)
        screen_layout.addWidget(button_execute)

        return screen

    def load_files(self, file_input, folder_name):

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

        if folder_name == 'inputs\\expmaps' or folder_name == 'inputs\\impmaps':
            self.exp_maps_list = tools.reading_folder_files('expmaps', '.shp')
            self.imp_maps_list = tools.reading_folder_files('impmaps', '.tif')
            screen = self.executing_screen()
            self.screens[1] = screen

    def delete_files(self, file_input, folder_name, text):

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

        if folder_name == 'inputs\\expmaps' or folder_name == 'inputs\\impmaps':
            self.exp_maps_list = tools.reading_folder_files('expmaps', '.shp')
            self.imp_maps_list = tools.reading_folder_files('impmaps', '.tif')
            screen = self.executing_screen()
            self.screens[1] = screen

    def select_rr(self, button, partial_button, dam_fun_button, zonal_stats_method_button, zonal_stats_value_button):
        self.tool_selected = 'raster_raster'
        button.setText("Exposure: raster (.tif) - Impact: raster (.tif)")
        partial_button.setEnabled(True)
        dam_fun_button.setEnabled(True)
        zonal_stats_method_button.setEnabled(False)
        zonal_stats_method_button.setText("Select zonal stats method (sr)")
        zonal_stats_value_button.setEnabled(False)
        zonal_stats_value_button.setText("Select value for zonal statistics (sr-ss)")

    def select_sr(self, button, partial_button, dam_fun_button, zonal_stats_method_button, zonal_stats_value_button):
        self.tool_selected = 'shape_raster'
        button.setText("Exposure: shapefile (.shp) - Impact: raster (.tif)")
        partial_button.setEnabled(True)
        dam_fun_button.setEnabled(False)
        dam_fun_button.setText("Select damage functions input (rr)")
        zonal_stats_method_button.setEnabled(True)
        zonal_stats_value_button.setEnabled(True)

    def select_ss(self, button, partial_button, dam_fun_button, zonal_stats_method_button, zonal_stats_value_button):
        self.tool_selected = 'shape_shape'
        button.setText("Exposure: shapefile (.shp) - Impact: shapefile (.shp)")
        partial_button.setEnabled(True)
        dam_fun_button.setEnabled(False)
        dam_fun_button.setText("Select damage functions input (rr)")
        zonal_stats_method_button.setEnabled(False)
        zonal_stats_method_button.setText("Select zonal stats method (sr)")
        zonal_stats_value_button.setEnabled(True)

    def select_partial(self, partial_button):
        self.partial_agg_results_flag = True
        partial_button.setText("Partial aggregated results")

    def select_no_partial(self, partial_button):
        self.partial_agg_results_flag = False
        partial_button.setText("No partial aggregated results")

    def select_file(self, dam_fun_button):
        self.dam_fun_file_flag = True
        dam_fun_button.setText("Partial aggregated results")

    def select_no_file(self, dam_fun_button):
        self.dam_fun_file_flag = False
        dam_fun_button.setText("No partial aggregated results")

    def select_centers(self, zonal_stats_method_button):
        self.zonal_stats_method = 'centers'
        zonal_stats_method_button.setText("Centers")

    def select_all_touched(self, zonal_stats_method_button):
        self.zonal_stats_method = 'all touched'
        zonal_stats_method_button.setText("All touched")

    def select_mean(self, zonal_stats_value_button):
        self.zonal_stats_value = 'mean'
        zonal_stats_value_button.setText("Mean")

    def select_max(self, zonal_stats_value_button):
        self.zonal_stats_value = 'max'
        zonal_stats_value_button.setText("Max")

    def executing_screen(self):
        # Initialize the screen widget and layout
        screen_layout = QVBoxLayout()
        screen = QWidget()
        screen.setLayout(screen_layout)

        # Set the title for the input screen
        inputs_title = QLabel("Executing")
        inputs_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        screen_layout.addWidget(inputs_title)

        input_files_layout = QVBoxLayout()
        screen_layout.addLayout(input_files_layout)
        input_files_title = QLabel("Input files")
        input_files_layout.addWidget(input_files_title)
        input_files_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout = QGridLayout()
        input_files_layout.addLayout(layout)
        row = 0
        for value in self.exp_maps_list:
            key_widget = QLineEdit(value)
            key_widget.setReadOnly(True)
            key_widget.setStyleSheet(
                "background-color: #004D5A   ;color: white;border: 1px solid #2D2D2D;padding: 5px;font-weight: bold;")
            layout.addWidget(key_widget, row, 0)
            btn = QPushButton("")
            btn.setEnabled(False)
            btn.setStyleSheet("font-size: 20px; color: green;")
            layout.addWidget(btn, row, 2)
            self.sys_ticks_list.append(btn)
            row += 1
            for value2 in self.imp_maps_list:
                key_widget = QLineEdit(value2)
                key_widget.setReadOnly(True)
                key_widget.setStyleSheet(
                    "background-color: #004D5A   ;color: white;border: 1px solid #2D2D2D;padding: 5px;font-weight: bold;")
                layout.addWidget(key_widget, row, 1)
                btn = QPushButton("")
                btn.setEnabled(False)
                btn.setStyleSheet("font-size: 20px; color: green;")
                layout.addWidget(btn, row, 2)
                self.scen_ticks_list.append(btn)
                row += 1

        return screen

    def dictionaries_screen(self):
        # Initialize the screen widget and layout
        screen_layout = QVBoxLayout()
        screen = QWidget()
        screen.setLayout(screen_layout)

        # Set the title for the input screen
        inputs_title = QLabel("Dictionaries")
        inputs_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        screen_layout.addWidget(inputs_title)

        dics_layout = QHBoxLayout()
        screen_layout.addLayout(dics_layout)

        keysdic_layout = QVBoxLayout()
        dics_layout.addLayout(keysdic_layout)
        keysdic_title = QLabel("Internal, input and .shp outputs keys dictionary")
        keysdic_layout.addWidget(keysdic_title)
        keysdic_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout1 = QGridLayout()
        keysdic_layout.addLayout(layout1)
        for row, (key, value) in enumerate(self.keysdic.items()):
            key_widget = QLineEdit(key)
            key_widget.setReadOnly(True)
            key_widget.setStyleSheet(
                "background-color: #004D5A   ;color: white;border: 1px solid #2D2D2D;padding: 5px;font-weight: bold;")
            value_widget = QLineEdit(str(value))
            value_widget.setStyleSheet("background-color: #1E1E1E;color: white;border: 1px solid #2D2D2D;padding: 5px")
            value_widget.textChanged.connect(lambda text, k=key: self.update_value(self.keysdic, k, None, text))
            layout1.addWidget(key_widget, row, 0)
            layout1.addWidget(value_widget, row, 1)
        key_widget1 = QLineEdit()
        key_widget1.setStyleSheet(
            "background: transparent  ;color: white;border: 1px solid #2D2D2D;padding: 5px;font-weight: bold;")
        key_widget1.setReadOnly(True)
        key_widget2 = QLineEdit()
        key_widget2.setStyleSheet(
            "background: transparent   ;color: white;border: 1px solid #2D2D2D;padding: 5px;font-weight: bold;")
        key_widget2.setReadOnly(True)
        layout1.addWidget(key_widget1, row + 1, 0)
        layout1.addWidget(key_widget2, row + 2, 0)

        outputsdic_layout = QVBoxLayout()
        dics_layout.addLayout(outputsdic_layout)
        outputsdic_title = QLabel("Outputs titles dictionary")
        outputsdic_layout.addWidget(outputsdic_title)
        outputsdic_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout2 = QGridLayout()
        outputsdic_layout.addLayout(layout2)
        row = 0
        for key, value in self.keysoutputdic.items():
            if key == 'Exposed value' or key == 'Impact damage':
                for key2, value2 in value.items():
                    key_widget = QLineEdit(key + ' - ' + key2)
                    value_widget = QLineEdit(str(value[key2]))
                    key_widget.setReadOnly(True)
                    key_widget.setStyleSheet(
                        "background-color: #004D5A;color: white;border: 1px solid #2D2D2D;padding: 5px;font-weight: bold;")
                    value_widget.setStyleSheet(
                        "background-color: #1E1E1E;color: white;border: 1px solid #2D2D2D;padding: 5px")
                    value_widget.textChanged.connect(
                        lambda text, k1=key, k2=key2: self.update_value(self.keysoutputdic, k1, k2, text))
                    layout2.addWidget(key_widget, row, 0)
                    layout2.addWidget(value_widget, row, 1)
                    row += 1
            else:
                key_widget = QLineEdit(key)
                value_widget = QLineEdit(str(value))
                key_widget.setReadOnly(True)
                key_widget.setStyleSheet(
                    "background-color: #004D5A   ;color: white;border: 1px solid #2D2D2D;padding: 5px;font-weight: bold;")
                value_widget.setStyleSheet(
                    "background-color: #1E1E1E;color: white;border: 1px solid #2D2D2D;padding: 5px")
                value_widget.textChanged.connect(
                    lambda text, k=key: self.update_value(self.keysoutputdic, k, None, text))
                layout2.addWidget(key_widget, row, 0)
                layout2.addWidget(value_widget, row, 1)
                row += 1
        dics_layout.addLayout(layout2)

        # Set the update button
        button_update_dics = QPushButton("Update dictionaries")
        button_update_dics.setStyleSheet(self.buttons_stylesheet)
        button_update_dics.clicked.connect(self.update_dics)
        screen_layout.addWidget(button_update_dics)

        return screen

    def update_value(self, dic, key1, key2, nuevo_valor):
        if key1 == 'Exposed value' or key1 == 'Impact damage':
            print(f"Updated '{key1}' - '{key2}' to '{nuevo_valor}'")
            dic[key1][key2] = nuevo_valor
        else:
            print(f"Updated '{key1}' to '{nuevo_valor}'")
            dic[key1] = nuevo_valor

    def update_dics(self):
        path = Path.cwd().parent / 'src/dictionaries.py'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"keysdic = {self.keysdic}\n")
            f.write(f"keysoutputdic = {self.keysoutputdic}\n")

    def results_screen(self):
        # Initialize the screen widget and layout
        screen_layout = QVBoxLayout()
        screen = QWidget()
        screen.setLayout(screen_layout)

        # Set the title for the input screen
        inputs_title = QLabel("Results")
        inputs_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        screen_layout.addWidget(inputs_title)

        outputs_windows_layout = QHBoxLayout()
        screen_layout.addLayout(outputs_windows_layout)

        # Charts (.csv) outputs
        csvs_output_layout = QVBoxLayout()
        csvs_title = QLabel("Charts (.csv) outputs")
        csvs_output_layout.addWidget(csvs_title)
        csvs_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        csvs_output_files = QTextEdit()
        csvs_output_files.setReadOnly(True)
        csvs_output_files.setStyleSheet("""
                                    QTextEdit {
                                        background-color: #1E1E1E;
                                        color: white;
                                        border: 1px solid #2D2D2D;
                                        padding: 5px;
                                    }
                                """)
        csvs_output_files.setPlaceholderText("Charts (.csv) outputs")
        csvs_output_files.setText("\n".join(tools.reading_files('results\\csvs')))
        csvs_output_layout.addWidget(csvs_output_files)
        save_csvs_button = QPushButton("Save")
        save_csvs_button.setStyleSheet(self.buttons_stylesheet)
        save_csvs_button.clicked.connect(lambda _, inputs=csvs_output_files:
                                         self.save_files('results\\csvs'))

        csvs_output_layout.addWidget(save_csvs_button)
        outputs_windows_layout.addLayout(csvs_output_layout)

        outputs_windows_2_layout = QHBoxLayout()
        screen_layout.addLayout(outputs_windows_2_layout)

        # Maps (.shp) outputs
        shp_output_layout = QVBoxLayout()
        shp_title = QLabel("Maps (.shp) outputs")
        shp_output_layout.addWidget(shp_title)
        shp_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        shp_output_files = QTextEdit()
        shp_output_files.setReadOnly(True)
        shp_output_files.setStyleSheet("""
                                            QTextEdit {
                                                background-color: #1E1E1E;
                                                color: white;
                                                border: 1px solid #2D2D2D;
                                                padding: 5px;
                                            }
                                        """)
        shp_output_files.setPlaceholderText("Maps (.shp) outputs")
        shp_output_files.setText("\n".join(tools.reading_files('results\\shps')))
        shp_output_layout.addWidget(shp_output_files)
        save_shp_button = QPushButton("Save")
        save_shp_button.setStyleSheet(self.buttons_stylesheet)
        save_shp_button.clicked.connect(lambda _, inputs=shp_output_files:
                                        self.save_files('results\\shps'))
        shp_output_layout.addWidget(save_shp_button)
        outputs_windows_2_layout.addLayout(shp_output_layout)

        # Maps (.tif) outputs
        tif_output_layout = QVBoxLayout()
        tifs_title = QLabel("Maps (.tif) outputs")
        tif_output_layout.addWidget(tifs_title)
        tifs_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        tifs_output_files = QTextEdit()
        tifs_output_files.setReadOnly(True)
        tifs_output_files.setStyleSheet("""
                                            QTextEdit {
                                                background-color: #1E1E1E;
                                                color: white;
                                                border: 1px solid #2D2D2D;
                                                padding: 5px;
                                            }
                                        """)
        tifs_output_files.setPlaceholderText("Maps (.tif) outputs")
        tifs_output_files.setText("\n".join(tools.reading_files('results\\tifs')))
        tif_output_layout.addWidget(tifs_output_files)
        save_tifs_button = QPushButton("Save")
        save_tifs_button.setStyleSheet(self.buttons_stylesheet)
        save_tifs_button.clicked.connect(lambda _, inputs=tifs_output_files:
                                         self.save_files('results\\tifs'))
        tif_output_layout.addWidget(save_tifs_button)
        outputs_windows_2_layout.addLayout(tif_output_layout)

        return screen

    def save_files(self, source_folder):
        try:
            target_folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save Files")
            folder_path = Path.cwd().parent.parent / source_folder
            if target_folder:
                for file_name in os.listdir(folder_path):
                    source_file = os.path.join(folder_path, file_name)
                    target_file = os.path.join(target_folder, file_name)
                    if os.path.isfile(source_file):
                        shutil.copy(source_file, target_file)
        except Exception as e:
            print(e)

    def show_screen(self, index):
        # Clean the central block
        for i in reversed(range(self.main_block.count())):
            widget = self.main_block.itemAt(i).widget()
            self.main_block.removeWidget(widget)
            widget.setParent(None)

        #Show the selected screen
        self.main_block.addWidget(self.screens[index])

    def execute_tool(self):

        worker1 = RunParallelTool(self.function_different_tools)

        status_signals = WorkerSignals()
        status_signals.update_tick_sys.connect(self.update_tick_sys)
        status_signals.update_tick_scen.connect(self.update_tick_scen)
        worker2 = RunParallelTool(self.check_status, status_signals)

        self.threadpool.start(worker1)
        self.threadpool.start(worker2)

        self.show_screen(1)

    def function_different_tools(self, signals):
        try:
            if self.tool_selected == 'raster_raster':
                main_tool.raster_raster_tool(self.partial_agg_results_flag, self.dam_fun_file_flag)

            elif self.tool_selected == 'shape_raster':
                main_tool.shape_raster_tool(self.partial_agg_results_flag, self.zonal_stats_method,
                                            self.zonal_stats_value)

            elif self.tool_selected == 'shape_shape':
                main_tool.shape_shape_tool(self.partial_agg_results_flag, self.zonal_stats_value)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def check_status(self, signals):
        sys_counter = -1
        while sys_counter < len(self.exp_maps_list) - 1:
            try:
                sys_counter = math.floor(main_tool.state_counter / len(self.imp_maps_list)) - 1
                scen_counter = main_tool.state_counter - 1
                signals.update_tick_sys.emit(sys_counter)
                signals.update_tick_scen.emit(scen_counter)
                time.sleep(10)
            except Exception as e:
                print(e)
        self.show_screen(3)

    def update_tick_sys(self, index):
        if 0 <= index < len(self.sys_ticks_list):
            btn = self.sys_ticks_list[index]
            btn.setText("✅")
            btn.repaint()

    def update_tick_scen(self, index):
        if 0 <= index < len(self.scen_ticks_list):
            btn = self.scen_ticks_list[index]
            btn.setText("✅")
            btn.repaint()

    def dam_fun_screen(self):

        # Initialize the screen widget and layout
        screen_layout = QVBoxLayout()
        screen = QWidget()
        screen.setLayout(screen_layout)

        # Set the title for the input screen
        dam_fun_title = QLabel("Damage functions dictionary")
        dam_fun_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        screen_layout.addWidget(dam_fun_title)

        scroll_area = QScrollArea()
        self.dam_fun_container = QWidget()
        self.dam_fun_container_layout = QGridLayout()

        for index, (name, code) in enumerate(self.dam_fun_list):
            row = index // 2
            col = index % 2

            function_layout = QVBoxLayout()

            name_widget = QLineEdit(name)
            name_widget.setReadOnly(True)
            name_widget.setStyleSheet(
                "background-color: #004D5A   ;color: white;border: 1px solid #2D2D2D;padding: 5px;font-weight: bold;")

            code_box = QTextEdit()
            code_box.setReadOnly(True)
            code_box.setText(code)
            code_box.setStyleSheet("""
                background-color: #1E1E1E;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
            """)
            function_layout.addWidget(name_widget)
            function_layout.addWidget(code_box)
            container_widget = QWidget()
            container_widget.setLayout(function_layout)
            self.dam_fun_container_layout.addWidget(container_widget, row, col)

        self.dam_fun_container.setLayout(self.dam_fun_container_layout)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.dam_fun_container)
        screen_layout.addWidget(scroll_area)

        # Set the add damage function button and delete buttons
        buttons_layout=QHBoxLayout()
        screen_layout.addLayout(buttons_layout)
        add_function_button = QPushButton("Add damage function")
        buttons_layout.addWidget(add_function_button)
        delete_function_button = QPushButton("Delete damage function")
        buttons_layout.addWidget(delete_function_button)
        delete_function_button.setStyleSheet(self.button_menu_stylesheet)

        add_function_button.setStyleSheet(self.buttons_stylesheet)
        add_function_button.clicked.connect(lambda _,inputs=screen:
                                            self.add_dam_fun(inputs,delete_function_button))
        self.function_menu = QMenu()
        self.function_menu.setStyleSheet(self.menu_stylesheet)
        delete_function_button.setMenu(self.function_menu)
        for index, (name, code) in enumerate(self.dam_fun_list):
            option= QAction(name, delete_function_button)
            self.function_menu.addAction(option)
            option.triggered.connect(lambda _, idx=index: self.delete_dam_fun(idx))
        return screen

    def add_dam_fun(self, screen,delete_function_button):
        dialog = QDialog(screen)
        dialog.setWindowTitle("Agregar nueva función")

        form_layout = QFormLayout(dialog)

        name_input = QLineEdit()
        code_input = QTextEdit()

        form_layout.addRow("Nombre:", name_input)
        form_layout.addRow("Código:", code_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        form_layout.addWidget(buttons)
        buttons.accepted.connect(lambda: self.accept_button_fun(dialog, name_input, code_input,delete_function_button))
        buttons.rejected.connect(dialog.reject)

        dialog.exec_()

    def accept_button_fun(self, dialog, name_input, code_input,delete_function_button):
        name = name_input.text().strip()
        code = code_input.toPlainText().strip()
        if name and code:
            self.dam_fun_list.append((name, code))
            index=len(self.dam_fun_list)-1
            row = index // 2
            col = index % 2

            function_layout = QVBoxLayout()
            name_widget = QLineEdit(name)
            name_widget.setReadOnly(True)
            name_widget.setStyleSheet(
                "background-color: #004D5A   ;color: white;border: 1px solid #2D2D2D;padding: 5px;font-weight: bold;")

            code_box = QTextEdit()
            code_box.setReadOnly(True)
            code_box.setText(code)
            code_box.setStyleSheet("""
                                        background-color: #1E1E1E;
                                        color: white;
                                        border: none;
                                        padding: 10px;
                                        font-size: 12px;
                                    """)
            function_layout.addWidget(name_widget)
            function_layout.addWidget(code_box)
            container_widget = QWidget()
            container_widget.setLayout(function_layout)
            self.dam_fun_container_layout.addWidget(container_widget, row, col)

            option = QAction(name, delete_function_button)
            self.function_menu.addAction(option)
            option.triggered.connect(lambda _, idx=index: self.delete_dam_fun(idx))

            dialog.accept()

            path = Path.cwd().parent / 'src/damage_functions/damage_functions_dic.py'
            with open(path, 'w', encoding='utf-8') as f:
                for (name,fun) in self.dam_fun_list:
                    f.write(f"{fun}\n")

    def delete_dam_fun(self,index):

        self.dam_fun_list.pop(index)
        actions_list=self.function_menu.actions()
        self.function_menu.removeAction(actions_list[index])

        # Eliminar widgets antiguos
        while self.dam_fun_container_layout.count():
            item = self.dam_fun_container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        QApplication.processEvents()

        # Reconstruir el layout con los elementos restantes
        for index, (name, code) in enumerate(self.dam_fun_list):
            row = index // 2
            col = index % 2

            function_layout = QVBoxLayout()

            name_widget = QLineEdit(name)
            name_widget.setReadOnly(True)
            name_widget.setStyleSheet(
                "background-color: #004D5A   ;color: white;border: 1px solid #2D2D2D;padding: 5px;font-weight: bold;")

            code_box = QTextEdit()
            code_box.setReadOnly(True)
            code_box.setText(code)
            code_box.setStyleSheet("""
                    background-color: #1E1E1E;
                    color: white;
                    border: none;
                    padding: 10px;
                    font-size: 12px;
                """)

            function_layout.addWidget(name_widget)
            function_layout.addWidget(code_box)
            container_widget = QWidget()
            container_widget.setLayout(function_layout)
            self.dam_fun_container_layout.addWidget(container_widget, row, col)

        self.dam_fun_container_layout.update()
        self.dam_fun_container.updateGeometry()
        self.dam_fun_container.repaint()

        path = Path.cwd().parent / 'src/damage_functions/damage_functions_dic.py'
        with open(path, 'w', encoding='utf-8') as f:
            for (name, fun) in self.dam_fun_list:
                f.write(f"{fun}\n")

class RunParallelTool(QRunnable):
    def __init__(self, function, signals=None):
        super().__init__()
        self.function = function
        self.signals = signals or WorkerSignals()

    @pyqtSlot()
    def run(self):
        self.function(self.signals)


class WorkerSignals(QObject):
    update_tick_sys = pyqtSignal(int)
    update_tick_scen = pyqtSignal(int)


def run_ihrat_gui():
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_ihrat_gui()

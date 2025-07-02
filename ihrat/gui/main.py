import sys
import os
import shutil
from pathlib import Path
import time
import math
import tools

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import Qt, QRunnable, pyqtSlot, QThreadPool, QObject, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QLineEdit, QAction, QMenu, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel,
                             QFileDialog, QTextEdit,
                             QWidget, QPushButton, QGridLayout, QScrollArea, QDialog, QFormLayout, QDialogButtonBox)

from ihrat.src import main_tool
from ihrat.src.dictionaries import keysdic, keysoutputdic


# noinspection PyUnresolvedReferences
class MainApp(QMainWindow):
    def __init__(self):

        super().__init__()

        self.dam_fun_container = None
        self.function_menu = None
        self.dam_fun_container_layout = None
        self.sys_ticks_list = []
        self.scen_ticks_list = []
        self.drag_start_position = None
        self.main_block = None
        self.screens = []
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

        def apply_dark_theme():
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

        #Set the main window
        self.setWindowTitle("IHRAT")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        apply_dark_theme()

        #Set the central widget and the main layout in it
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("""
                    background-color: rgb(53, 53, 53);
                    border-radius: 10px;
                """)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)

        #Set the title bar in the main layout
        self.create_title_bar(main_layout)

        #Set the content layout in the main layout
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(content_layout)

        #Set the sidebar in the content layout
        self.create_side_bar(content_layout)

        #Set the main block in the content layout (the one displaying the different screens)
        self.main_block = QVBoxLayout()
        content_layout.addLayout(self.main_block, stretch=1)

        #Iniciate screens and show the input screen
        self.screens.extend([self.input_screen(), self.executing_screen(), self.dictionaries_screen(),
                             self.dam_fun_screen(), self.results_screen()])
        self.show_screen(0)

    def show_screen(self, index):
        # Clean the central block
        for i in reversed(range(self.main_block.count())):
            widget = self.main_block.itemAt(i).widget()
            self.main_block.removeWidget(widget)
            widget.setParent(None)

        #Show the selected screen
        self.main_block.addWidget(self.screens[index])

    def create_title_bar(self,imp_layout):

        def toggle_maximize():
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()

        def title_bar_mouse_press_event(event):
            if event.button() == Qt.LeftButton:
                if self.isMaximized():
                    self.drag_start_position = (event.globalPos() - self.frameGeometry().topLeft()) / 3
                else:
                    self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

        def title_bar_mouse_move_event(event):
            if event.buttons() == Qt.LeftButton:
                if self.isMaximized():
                    self.showNormal()
                    self.move(event.globalPos())
                else:
                    self.move(event.globalPos() - self.drag_start_position)
                event.accept()

        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("""
               background-color: #353535;
               border-top-left-radius: 10px;
               border-top-right-radius: 10px;
           """)
        layout = QHBoxLayout(title_bar)
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
        maximize_button.clicked.connect(toggle_maximize)
        close_button.clicked.connect(self.close)

        #Add movement to the window while pressing and moving the title bar
        title_bar.mousePressEvent = title_bar_mouse_press_event
        title_bar.mouseMoveEvent = title_bar_mouse_move_event

        #Create a bottom line for the title bar
        bottom_line = QWidget(title_bar)
        bottom_line.setFixedHeight(1)
        bottom_line.setStyleSheet("background-color: #00BCD4;")
        bottom_line.move(0, 29)
        bottom_line.resize(title_bar.width(), 1)

        #Resize the title bar with the window
        title_bar.resizeEvent = lambda event: bottom_line.resize(event.size().width(), 1)

        imp_layout.addWidget(title_bar)

    def create_side_bar(self,imp_layout):

        sidebar = QWidget()
        sidebar.setFixedWidth(80)
        sidebar.setStyleSheet("""
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
        sidebar.setLayout(sidebar_layout)

        sidebar_buttons = []
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
            sidebar_buttons.append(btn)
        sidebar_layout.addStretch()

        imp_layout.addWidget(sidebar)

    def input_screen(self):

        def create_option_button(title: str, button_text: str,actions: list[tuple[str, callable]]):
            layout = QVBoxLayout()

            label = QLabel(title)
            label.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(label)

            button = QPushButton(button_text)
            button.setEnabled(False)
            button.setStyleSheet(self.button_menu_stylesheet)

            menu = QMenu()
            menu.setStyleSheet(self.menu_stylesheet)

            for action_text, action_func in actions:
                action = QAction(action_text, button)
                action.triggered.connect(lambda _, f=action_func: f(button))
                menu.addAction(action)

            button.setMenu(menu)
            layout.addWidget(button)

            return layout, button

        def create_file_input_block(placeholder: str, folder: str):
            layout = QVBoxLayout()

            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #1E1E1E;
                    color: white;
                    border: 1px solid #2D2D2D;
                    padding: 5px;
                }
            """)
            text_edit.setPlaceholderText(placeholder)
            text_edit.setText("\n".join(tools.reading_files(folder)))
            layout.addWidget(text_edit)

            button_layout = QHBoxLayout()

            load_button = QPushButton("Load")
            load_button.setStyleSheet(self.buttons_stylesheet)
            load_button.clicked.connect(lambda _, inputs=text_edit: load_files(inputs, folder))
            button_layout.addWidget(load_button)

            delete_button = QPushButton("Delete")
            delete_button.setStyleSheet(self.buttons_stylesheet)
            delete_button.clicked.connect(lambda _, inputs=text_edit: delete_files(inputs, folder, placeholder))
            button_layout.addWidget(delete_button)

            layout.addLayout(button_layout)
            return layout

        def select_tool(tool, button, partial_button, dam_fun_button_, zonal_stats_method_button_,
                        zonal_stats_value_button_):
            self.tool_selected = tool
            if tool == 'raster_raster':
                button.setText("Exposure: raster (.tif) - Impact: raster (.tif)")
                dam_fun_button_.setEnabled(True)
                zonal_stats_method_button_.setEnabled(False)
                zonal_stats_method_button_.setText("Select zonal stats method (sr)")
                zonal_stats_value_button_.setEnabled(False)
                zonal_stats_value_button_.setText("Select value for zonal statistics (sr-ss)")
            elif tool == 'shape_raster':
                button.setText("Exposure: shapefile (.shp) - Impact: raster (.tif)")
                dam_fun_button_.setEnabled(False)
                dam_fun_button_.setText("Select damage functions input (rr)")
                zonal_stats_method_button_.setEnabled(True)
                zonal_stats_value_button_.setEnabled(True)
            elif tool == 'shape_shape':
                button.setText("Exposure: shapefile (.shp) - Impact: shapefile (.shp)")
                dam_fun_button_.setEnabled(False)
                dam_fun_button_.setText("Select damage functions input (rr)")
                zonal_stats_method_button_.setEnabled(False)
                zonal_stats_method_button_.setText("Select zonal stats method (sr)")
                zonal_stats_value_button_.setEnabled(False)
                zonal_stats_value_button_.setText("Select value for zonal statistics (sr-ss)")
            partial_button.setEnabled(True)

        def load_files(file_input, folder_name):

            # Select the files to load
            options = QFileDialog.Options()
            file_paths, _ = QFileDialog.getOpenFileNames(self, "Select file(s)", "", "All files (*.*)", options=options)

            # Get the program folder to save the files
            folder_path = Path.cwd().parent.parent / folder_name
            # If it doesn't exist, create the folder
            os.makedirs(folder_path, exist_ok=True)

            # Add the files to the program folder
            if file_paths:
                file_names = []
                for path in file_paths:
                    file_name = os.path.basename(path)
                    file_names.append(file_name)
                    file_path = os.path.join(folder_path, file_name)
                    shutil.copy(path, file_path)
                # Add the file names to the input textbox
                file_input.append("\n".join(file_names))

            if folder_name == 'inputs\\expmaps' or folder_name == 'inputs\\impmaps':
                self.exp_maps_list = tools.reading_folder_files('expmaps', '.shp')
                self.imp_maps_list = tools.reading_folder_files('impmaps', '.tif')
                self.screens[1] = self.executing_screen()

        def delete_files(file_input, folder_name, text):

            # Get the program folder to delete the files from
            folder_path = Path.cwd().parent.parent / folder_name

            # Delete all the files
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            # Clean the input textbox and set the placeholder text
            file_input.clear()
            file_input.setPlaceholderText(text)

            if folder_name == 'inputs\\expmaps' or folder_name == 'inputs\\impmaps':
                self.exp_maps_list = tools.reading_folder_files('expmaps', '.shp')
                self.imp_maps_list = tools.reading_folder_files('impmaps', '.tif')
                self.screens[1] = self.executing_screen()

        def set_option(attribute_name, value, button, button_text):
            setattr(self, attribute_name, value)
            button.setText(button_text)

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
        option1.triggered.connect(lambda: select_tool('raster-raster',format_button, partial_agg_button,
                                                         dam_fun_button, zonal_stats_method_button,
                                                         zonal_stats_value_button))
        option2.triggered.connect(lambda: select_tool('shape_raster',format_button, partial_agg_button,
                                                         dam_fun_button, zonal_stats_method_button,
                                                         zonal_stats_value_button))
        option3.triggered.connect(lambda: select_tool('shape_shape',format_button, partial_agg_button,
                                                         dam_fun_button, zonal_stats_method_button,
                                                         zonal_stats_value_button))
        format_menu.addAction(option1)
        format_menu.addAction(option2)
        format_menu.addAction(option3)
        format_button.setMenu(format_menu)
        screen_layout.addWidget(format_button)

        #Layout for the rest of the buttons
        options_1_layout = QHBoxLayout()
        options_2_layout = QHBoxLayout()
        screen_layout.addLayout(options_1_layout)
        screen_layout.addLayout(options_2_layout)

        # Partial Aggregated Results Button
        partial_agg_layout, partial_agg_button = create_option_button("Partial aggregated results","Select partial aggregation",
            [("Partial aggregated results",lambda: set_option('partial_agg_results_flag', True, partial_agg_button,"Partial aggregated results")),
                ("No partial aggregated results",lambda: set_option('partial_agg_results_flag', False, partial_agg_button,"No partial aggregated results"))])
        options_1_layout.addLayout(partial_agg_layout)
        # Damage Functions Button
        dam_fun_layout, dam_fun_button = create_option_button("Damage functions input (rr)","Select damage functions input (rr)",
            [("Damage functions distribution shapefile",lambda: set_option('dam_fun_file_flag', True, dam_fun_button, "Partial aggregated results")),
                ("General damage function",lambda: set_option('dam_fun_file_flag', False, dam_fun_button, "No partial aggregated results"))])
        options_1_layout.addLayout(dam_fun_layout)
        # Zonal Stats Method Button
        zonal_stats_method_layout, zonal_stats_method_button = create_option_button("Zonal stats method (sr)","Select zonal stats method (sr)",
            [("Centers",lambda: set_option('zonal_stats_method', 'centers', zonal_stats_method_button, "Centers")),
                ("All touched",lambda: set_option('zonal_stats_method', 'all touched', zonal_stats_method_button, "All touched"))])
        options_2_layout.addLayout(zonal_stats_method_layout)
        # Zonal Stats Value Button
        zonal_stats_value_layout, zonal_stats_value_button = create_option_button("Value for zonal statistics (sr-ss)","Select value for zonal statistics (sr-ss)",
            [("Mean", lambda: set_option('zonal_stats_value', 'mean', zonal_stats_value_button, "Mean")),
                ("Max", lambda: set_option('zonal_stats_value', 'max', zonal_stats_value_button, "Max"))])
        options_2_layout.addLayout(zonal_stats_value_layout)

        #Set the title for the input files layout
        inputs_title = QLabel("Input files")
        inputs_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        screen_layout.addWidget(inputs_title)
        # Layout for the input files
        inputs_windows_layout = QHBoxLayout()
        screen_layout.addLayout(inputs_windows_layout)
        inputs_windows_2_layout = QHBoxLayout()
        screen_layout.addLayout(inputs_windows_2_layout)

        # Exposition input
        exp_inputs_layout = create_file_input_block("Exposition inputs files...",'inputs\\expmaps')
        inputs_windows_layout.addLayout(exp_inputs_layout)
        # Impact input
        imp_inputs_layout = create_file_input_block("Impact inputs files...",'inputs\\impmaps')
        inputs_windows_layout.addLayout(imp_inputs_layout)
        # Partial aggregate (r-r)
        partial_agg_file_layout = create_file_input_block("Partial aggregate file (r-r) ...",'inputs\\partial_agg_map')
        inputs_windows_2_layout.addLayout(partial_agg_file_layout)
        # Damage functions distribution file (r-r)
        dam_fun_file_layout = create_file_input_block("Damage functions distribution file (r-r) ...",'inputs\\dam_fun_files')
        inputs_windows_2_layout.addLayout(dam_fun_file_layout)

        # Set the execution button
        button_execute = QPushButton("Run IHRAT")
        button_execute.setStyleSheet(self.buttons_stylesheet)
        button_execute.clicked.connect(self.execute_tool)
        screen_layout.addWidget(button_execute)

        return screen

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

        def update_value(dic, key1, key2_, nuevo_valor):
            if key1 == 'Exposed value' or key1 == 'Impact damage':
                print(f"Updated '{key1}' - '{key2_}' to '{nuevo_valor}'")
                dic[key1][key2_] = nuevo_valor
            else:
                print(f"Updated '{key1}' to '{nuevo_valor}'")
                dic[key1] = nuevo_valor

        def update_dics():
            path = Path.cwd().parent / 'src/dictionaries.py'
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"keysdic = {self.keysdic}\n")
                f.write(f"keysoutputdic = {self.keysoutputdic}\n")

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
            value_widget.setMaxLength(10)
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
                        lambda text, k1=key, k2=key2: update_value(self.keysoutputdic, k1, k2, text))
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
                    lambda text, k=key: update_value(self.keysoutputdic, k, None, text))
                layout2.addWidget(key_widget, row, 0)
                layout2.addWidget(value_widget, row, 1)
                row += 1
        dics_layout.addLayout(layout2)

        # Set the update button
        button_update_dics = QPushButton("Update dictionaries")
        button_update_dics.setStyleSheet(self.buttons_stylesheet)
        button_update_dics.clicked.connect(update_dics)
        screen_layout.addWidget(button_update_dics)

        return screen

    def results_screen(self):

        def create_output_layout(title_text, placeholder_text, folder_path):
            layout = QVBoxLayout()

            title_label = QLabel(title_text)
            title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(title_label)

            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #1E1E1E;
                    color: white;
                    border: 1px solid #2D2D2D;
                    padding: 5px;
                }
            """)
            text_edit.setPlaceholderText(placeholder_text)
            text_edit.setText("\n".join(tools.reading_files(folder_path)))
            layout.addWidget(text_edit)

            save_button = QPushButton("Save")
            save_button.setStyleSheet(self.buttons_stylesheet)
            save_button.clicked.connect(lambda _, inputs=text_edit: save_files(folder_path))
            layout.addWidget(save_button)

            return layout

        def save_files(source_folder):
            target_folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save Files")
            folder_path = Path.cwd().parent.parent / source_folder
            if target_folder:
                for file_name in os.listdir(folder_path):
                    source_file = os.path.join(folder_path, file_name)
                    target_file = os.path.join(target_folder, file_name)
                    if os.path.isfile(source_file):
                        shutil.copy(source_file, target_file)

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
        outputs_windows_2_layout = QHBoxLayout()
        screen_layout.addLayout(outputs_windows_2_layout)

        # Charts (.csv) outputs
        csvs_output_layout = create_output_layout(
            title_text="Charts (.csv) outputs",
            placeholder_text="Charts (.csv) outputs",
            folder_path='results\\csvs'
        )
        outputs_windows_layout.addLayout(csvs_output_layout)

        # Maps (.shp) outputs
        shp_output_layout = create_output_layout(
            title_text="Maps (.shp) outputs",
            placeholder_text="Maps (.shp) outputs",
            folder_path='results\\shps'
        )
        outputs_windows_2_layout.addLayout(shp_output_layout)

        # Maps (.tif) outputs
        tif_output_layout = create_output_layout(
            title_text="Maps (.tif) outputs",
            placeholder_text="Maps (.tif) outputs",
            folder_path='results\\tifs'
        )
        outputs_windows_2_layout.addLayout(tif_output_layout)

        return screen

    def dam_fun_screen(self):

        def add_dam_fun():
            dialog = QDialog(screen)
            dialog.setWindowTitle("Add new function")

            form_layout = QFormLayout(dialog)

            name_input = QLineEdit()
            code_input = QTextEdit()

            form_layout.addRow("Name:", name_input)
            form_layout.addRow("Code:", code_input)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            form_layout.addWidget(buttons)
            buttons.accepted.connect(
                lambda: self.accept_button_fun(dialog, name_input, code_input, delete_function_button))
            buttons.rejected.connect(dialog.reject)

            dialog.exec_()

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
            container_widget=create_dam_fun_widget(self, index, name, code)
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
        add_function_button.clicked.connect(lambda _:add_dam_fun())
        self.function_menu = QMenu()
        self.function_menu.setStyleSheet(self.menu_stylesheet)
        delete_function_button.setMenu(self.function_menu)
        for index, (name, code) in enumerate(self.dam_fun_list):
            option= QAction(name, delete_function_button)
            self.function_menu.addAction(option)
            option.triggered.connect(lambda _, idx=index: self.delete_dam_fun(idx))
        return screen

    def accept_button_fun(self, dialog, name_input, code_input,delete_function_button):
        name = name_input.text().strip()
        code = code_input.toPlainText().strip()
        if name and code:
            self.dam_fun_list.append((name, code))
            index=len(self.dam_fun_list)-1
            row = index // 2
            col = index % 2
            container_widget=create_dam_fun_widget(self, index, name, code)

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

        #Elminate old widgets
        while self.dam_fun_container_layout.count():
            item = self.dam_fun_container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        QApplication.processEvents()

        # Rebuild layout
        for index, (name, code) in enumerate(self.dam_fun_list):
            row = index // 2
            col = index % 2
            container_widget=create_dam_fun_widget(self, index, name, code)
            self.dam_fun_container_layout.addWidget(container_widget, row, col)

        self.dam_fun_container_layout.update()
        self.dam_fun_container.updateGeometry()
        self.dam_fun_container.repaint()

        path = Path.cwd().parent / 'src/damage_functions/damage_functions_dic.py'
        with open(path, 'w', encoding='utf-8') as f:
            for (name, fun) in self.dam_fun_list:
                f.write(f"{fun}\n")

    def create_dam_fun_widget(self,name, code):
        function_layout = QVBoxLayout()

        name_widget = QLineEdit(name)
        name_widget.setReadOnly(True)
        name_widget.setStyleSheet(
            "background-color: #004D5A;color: white;border: 1px solid #2D2D2D;padding: 5px;font-weight: bold;"
        )

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

        return container_widget

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
        if self.tool_selected == 'raster_raster':
            main_tool.raster_raster_tool(self.partial_agg_results_flag, self.dam_fun_file_flag)

        elif self.tool_selected == 'shape_raster':
            main_tool.shape_raster_tool(self.partial_agg_results_flag, self.zonal_stats_method,
                                        self.zonal_stats_value)

        elif self.tool_selected == 'shape_shape':
            main_tool.shape_shape_tool(self.partial_agg_results_flag, self.zonal_stats_value)

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

import sys
import os
from pathlib import Path
import shutil
import py7zr
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, 
    QMessageBox, QComboBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette

class OblivionModManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Oblivion Remastered Mod Manager")
        self.setGeometry(100, 100, 800, 600)
        self.mod_extensions = {".esp", ".esm", ".bsa"}  # Add more as needed
        self.is_dark_theme = True
        self.config_file = Path.home() / ".oblivion_mod_manager" / "config.json"
        self.mod_dir = self.load_mod_dir()
        self.init_ui()
        self.load_mods()

    def load_mod_dir(self):
        # Default Oblivion Remastered Data path (Windows)
        default_mod_dir = Path("C:/Program Files (x86)/Bethesda Softworks/Oblivion Remastered/Data")
        # For Unix, try a common Steam path or similar (adjust as needed)
        unix_mod_dir = Path.home() / ".steam/steam/steamapps/common/Oblivion Remastered/Data"

        # Load from config file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    saved_path = Path(config.get("mod_dir", ""))
                    if saved_path.exists():
                        return saved_path
            except Exception as e:
                print(f"Error loading config: {e}")

        # Check default paths based on OS
        if sys.platform.startswith("win"):
            if default_mod_dir.exists():
                self.save_mod_dir(default_mod_dir)
                return default_mod_dir
        else:
            if unix_mod_dir.exists():
                self.save_mod_dir(unix_mod_dir)
                return unix_mod_dir

        # Prompt user to select Data folder
        mod_dir = self.prompt_mod_dir()
        if mod_dir:
            self.save_mod_dir(mod_dir)
            return mod_dir
        else:
            # Fallback to a safe default if user cancels
            return Path.home() / "Documents" / "My Games" / "Oblivion" / "Data"

    def prompt_mod_dir(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setWindowTitle("Select Oblivion Remastered Data Folder")
        if dialog.exec():
            selected_dir = Path(dialog.selectedFiles()[0])
            if (selected_dir / "Oblivion.esm").exists():  # Validate Data folder
                return selected_dir
            else:
                QMessageBox.critical(self, "Error", "Selected folder does not contain Oblivion.esm. Please select the correct Data folder.")
                return self.prompt_mod_dir()  # Recurse until valid or canceled
        return None

    def save_mod_dir(self, mod_dir):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump({"mod_dir": str(mod_dir)}, f)

    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Theme toggle
        theme_layout = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Theme", "Light Theme"])
        self.theme_combo.currentIndexChanged.connect(self.toggle_theme)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout

.addLayout(theme_layout)

        # Mod table
        self.mod_table = QTableWidget()
        self.mod_table.setColumnCount(4)
        self.mod_table.setHorizontalHeaderLabels(["Mod Name", "Type", "Status", "Size (MB)"])
        self.mod_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mod_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.mod_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.mod_table)

        # Buttons
        button_layout = QHBoxLayout()
        buttons = [
            ("Refresh", self.load_mods),
            ("Enable/Disable", self.toggle_mod),
            ("Install Mod", self.install_mod),
            ("Delete Mod", self.delete_mod),
            ("Change Data Folder", self.change_mod_dir)
        ]
        for text, func in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            button_layout.addWidget(btn)
        layout.addLayout(button_layout)

        # Apply initial theme
        self.toggle_theme(0)

    def change_mod_dir(self):
        new_mod_dir = self.prompt_mod_dir()
        if new_mod_dir:
            self.mod_dir = new_mod_dir
            self.save_mod_dir(new_mod_dir)
            self.load_mods()

    def toggle_theme(self, index):
        self.is_dark_theme = (index == 0)
        palette = QPalette()
        if self.is_dark_theme:
            palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        else:
            palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
        self.setPalette(palette)

    def load_mods(self):
        self.mod_table.setRowCount(0)
        if not self.mod_dir.exists():
            QMessageBox.warning(self, "Error", f"Mod directory not found: {self.mod_dir}")
            return

        for file in self.mod_dir.iterdir():
            if file.suffix.lower() in self.mod_extensions:
                row = self.mod_table.rowCount()
                self.mod_table.insertRow(row)
                self.mod_table.setItem(row, 0, QTableWidgetItem(file.name))
                self.mod_table.setItem(row, 1, QTableWidgetItem(file.suffix[1:].upper()))
                status = "Enabled" if file.suffix in self.mod_extensions else "Disabled"
                self.mod_table.setItem(row, 2, QTableWidgetItem(status))
                size_mb = file.stat().st_size / (1024 * 1024)
                self.mod_table.setItem(row, 3, QTableWidgetItem(f"{size_mb:.2f}"))

    def toggle_mod(self):
        selected = self.mod_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Error", "No mod selected")
            return
        mod_name = self.mod_table.item(selected, 0).text()
        mod_path = self.mod_dir / mod_name
        if mod_path.suffix in self.mod_extensions:
            new_path = mod_path.with_suffix(mod_path.suffix + ".bak")
            mod_path.rename(new_path)
        elif mod_path.suffix.endswith(".bak"):
            new_path = mod_path.with_suffix(mod_path.suffix[:-4])
            mod_path.rename(new_path)
        self.load_mods()

    def install_mod(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Mod Archive", "", "Archives (*.7z *.zip)")
        if not file:
            return
        try:
            with py7zr.SevenZipFile(file, mode='r') as archive:
                archive.extractall(path=self.mod_dir)
            QMessageBox.information(self, "Success", "Mod installed successfully")
            self.load_mods()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to install mod: {str(e)}")

    def delete_mod(self):
        selected = self.mod_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Error", "No mod selected")
            return
        mod_name = self.mod_table.item(selected, 0).text()
        mod_path = self.mod_dir / mod_name
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete {mod_name}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if mod_path.is_file():
                    mod_path.unlink()
                else:
                    shutil.rmtree(mod_path)
                QMessageBox.information(self, "Success", "Mod deleted successfully")
                self.load_mods()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete mod: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = OblivionModManager()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
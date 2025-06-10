# filename: gui.py
# author: AI Assistant
# date: 23.08.2024
# topic: Advanced PyQt5 GUI for TikTok-Voice-TTS
# version: 3.2 (Path-corrected)

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTextEdit, QPushButton, QFileDialog, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QUrl, QStandardPaths, Qt
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # When running as a .py script, the base path is the script's directory
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# --- Backend Library Import ---
try:
    from tiktok_voice import tts, Voice
except ModuleNotFoundError:
    # This check is crucial for user-friendliness
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "Fatal Error",
        "ERROR: 'tiktok_voice' library not found.\n\nPlease make sure the 'tiktok_voice' folder is in the same directory as this GUI script.")
    sys.exit(1)

# --- Voice Data Structure ---
VOICE_CATEGORIES = {
    "Regional Voices": [
        ("AU_FEMALE_1", "en_au_001.mp3"), ("AU_MALE_1", "en_au_002.mp3"),
        ("UK_MALE_1", "en_uk_001.mp3"), ("UK_MALE_2", "en_uk_003.mp3"),
        ("US_FEMALE_1", "en_us_001.mp3"), ("US_FEMALE_2", "en_us_002.mp3"),
        ("US_MALE_1", "en_us_006.mp3"), ("US_MALE_2", "en_us_007.mp3"),
        ("US_MALE_3", "en_us_009.mp3"), ("US_MALE_4", "en_us_010.mp3"),
    ], "Specialty Voices": [
        ("MALE_NARRATION", "en_male_narration.mp3"), ("MALE_FUNNY", "en_male_funny.mp3"),
        ("FEMALE_EMOTIONAL", "en_female_emotional.mp3"),
    ], "Singing Voices": [
        ("SING_FEMALE_WARMY_BREEZE", "en_female_f08_warmy_breeze.mp3"),
        ("SING_MALE_SUNSHINE_SOON", "en_male_m03_sunshine_soon.mp3"),
    ], "French Voices": [
        ("FR_MALE_1", "fr_001.mp3"), ("FR_MALE_2", "fr_002.mp3"),
    ], "Character Voices": [
        ("GHOSTFACE", "en_us_ghostface.mp3"), ("CHEWBACCA", "en_us_chewbacca.mp3"),
        ("C3PO", "en_us_c3po.mp3"), ("STITCH", "en_us_stitch.mp3"),
        ("STORMTROOPER", "en_us_stormtrooper.mp3"), ("ROCKET", "en_us_rocket.mp3"),
    ]
}

# --- Worker Thread for Non-Blocking TTS Generation ---
class Worker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    def __init__(self, text, voice_name, file_path):
        super().__init__()
        self.text, self.voice_name, self.file_path = text, voice_name, file_path
    def run(self):
        try:
            voice_enum = Voice.from_string(self.voice_name)
            if voice_enum is None: raise ValueError(f"Voice '{self.voice_name}' is not valid.")
            tts(self.text, voice_enum, self.file_path, play_sound=False)
            self.finished.emit(f"Success! Audio saved to:\n{self.file_path}")
        except Exception as e:
            self.error.emit(f"An error occurred:\n{str(e)}")

# --- Main Application Window ---
class TTS_GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.media_player = QMediaPlayer()
        self.initUI()
    def initUI(self):
        self.setWindowTitle('TikTok Text-To-Speech')
        self.setGeometry(100, 100, 500, 650)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.voice_tree = QTreeWidget()
        self.voice_tree.setColumnCount(2)
        self.voice_tree.setHeaderLabels(["Voice Name", "Play Sample"])
        self.voice_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.voice_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.populate_voice_list()
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Paste or type your text here...")
        self.export_button = QPushButton('Export')
        self.export_button.setStyleSheet("font-size: 16px; padding: 12px; font-weight: bold;")
        layout.addWidget(self.voice_tree)
        layout.addWidget(self.text_input)
        layout.addWidget(self.export_button)
        self.export_button.clicked.connect(self.start_export_process)
    def populate_voice_list(self):
        default_item = None
        for category, voices in VOICE_CATEGORIES.items():
            category_item = QTreeWidgetItem(self.voice_tree, [category])
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsSelectable)
            for voice_name, sample_file in voices:
                child_item = QTreeWidgetItem(category_item, [voice_name])
                play_button = QPushButton("▶️ Play")
                play_button.clicked.connect(lambda checked, sf=sample_file: self.play_sample(sf))
                self.voice_tree.setItemWidget(child_item, 1, play_button)
                if voice_name == 'US_FEMALE_1': default_item = child_item
        self.voice_tree.expandAll()
        if default_item: self.voice_tree.setCurrentItem(default_item)
    def play_sample(self, sample_filename):
        sample_path = resource_path(os.path.join('samples', sample_filename))
        if not os.path.exists(sample_path):
            QMessageBox.warning(self, "Sample Not Found", f"Could not find sample file:\n{sample_path}")
            return
        media_url = QUrl.fromLocalFile(os.path.abspath(sample_path))
        self.media_player.setMedia(QMediaContent(media_url))
        self.media_player.play()
    def start_export_process(self):
        text = self.text_input.toPlainText().strip()
        selected_item = self.voice_tree.currentItem()
        if not text:
            QMessageBox.warning(self, 'Input Error', 'Text field cannot be empty.')
            return
        if not selected_item or not selected_item.parent():
            QMessageBox.warning(self, 'Input Error', 'Please select a voice from the list.')
            return
        voice_name = selected_item.text(0)
        downloads_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        default_save_path = os.path.join(downloads_path, f"{voice_name}_output.mp3")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Audio File", default_save_path, "MP3 Files (*.mp3);;All Files (*)"
        )
        if not file_path: return
        self.export_button.setEnabled(False)
        self.export_button.setText("Generating...")
        self.thread = QThread()
        self.worker = Worker(text, voice_name, file_path)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_tts_finished)
        self.worker.error.connect(self.on_tts_error)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.start()
    def on_tts_finished(self, message):
        QMessageBox.information(self, 'Success', message)
        self.reset_button()
    def on_tts_error(self, error_message):
        QMessageBox.critical(self, 'Error', error_message)
        self.reset_button()
    def reset_button(self):
        self.export_button.setEnabled(True)
        self.export_button.setText("Export")

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QTreeWidget { font-size: 14px; } QTextEdit { font-size: 14px; }
        QPushButton { border: 1px solid #555; border-radius: 5px; background-color: #f0f0f0; padding: 5px; }
        QPushButton:hover { background-color: #e0e0e0; } QPushButton:pressed { background-color: #d0d0d0; }
    """)
    main_win = TTS_GUI()
    main_win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
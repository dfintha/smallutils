#!/usr/bin/env python3

"""Tool to tag whole albums consisting of MP3 files."""

import sys
import typing
import urllib.parse
import mutagen.id3
from PySide6.QtCore import QPoint, Qt, Slot
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class TrackList(QTableWidget):
    """Track list widget, that can accept dropped files."""

    headers = ["Artist", "Title", "Genre", "File Name"]

    def __init__(self):
        super().__init__()
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(TrackList.headers)
        self.setColumnWidth(3, 300)
        self.setAcceptDrops(True)

    def clear(self):
        """Clears all the items from the track list."""
        super().clear()
        self.setHorizontalHeaderLabels(TrackList.headers)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Called when an object is dragged into the widget."""
        mime_data = event.mimeData()
        if not mime_data.hasText():
            return
        text = mime_data.text().strip(" ").strip("\n").strip("\r")
        if text.endswith(".mp3"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Called when a dragged object is moved inside the widget."""
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Called when an object is dropped into the widget."""
        where = self.rowCount()
        text = event.mimeData().text()
        text = urllib.parse.unquote(text).strip("\n").strip("\r")
        item = QTableWidgetItem(text)
        self.insertRow(where)
        self.setItem(where, 3, item)
        metadata = get_file_metadata(text)
        self.setItem(where, 0, QTableWidgetItem(metadata["artist"]))
        self.setItem(where, 1, QTableWidgetItem(metadata["title"]))
        self.setItem(where, 2, QTableWidgetItem(metadata["genre"]))
        event.acceptProposedAction()


class AlbumTaggerApplication(QApplication):
    """Application class for the GUI."""

    def __init__(self):
        super().__init__(sys.argv)

        self.window = QFrame()
        self.album_artist = QLineEdit()
        self.year = QLineEdit()
        self.album = QLineEdit()
        self.album_art_path = QLineEdit()
        self.browse_album_art = QPushButton("Browse")
        self.tracks = TrackList()
        self.start = QPushButton("Start")
        self.clear = QPushButton("Clear")
        self.quit = QPushButton("Quit")
        self.wait_message = QLabel("")
        self.album_art_preview = QLabel()

        self.start.clicked.connect(self._start_clicked)
        self.clear.clicked.connect(self._clear_clicked)
        self.quit.clicked.connect(self._quit_clicked)
        self.browse_album_art.clicked.connect(self._browse_album_art_clicked)

        self.album_art_path.setEnabled(False)
        self.album_art_preview.setStyleSheet("background: #222222;")

        self.setWindowIcon(QIcon(""))
        self.window.setWindowIcon(QIcon(""))
        self.window.setWindowTitle("Album Tagger")

    @Slot()
    def _start_clicked(self) -> None:
        self._lock_state()
        track_count = self.tracks.rowCount()
        for i in range(track_count):
            metadata = {
                "cover": self.album_art_path.text(),
                "album_artist": self.album_artist.text(),
                "artist": self.tracks.item(i, 0).text(),
                "album": self.album.text(),
                "title": self.tracks.item(i, 1).text(),
                "year": self.year.text(),
                "genre": self.tracks.item(i, 2).text(),
                "track": f"{i + 1:02}/{track_count:02}",
            }
            tags = create_id3(metadata)
            tags.save(self.tracks.item(i, 3).text())
        self._unlock_state()
        self._clear_clicked()

    @Slot()
    def _clear_clicked(self) -> None:
        self.album_artist.setText("")
        self.year.setText("")
        self.album.setText("")
        self.album_art_path.setText("")
        self.album_art_preview.setPixmap(QPixmap())
        self.tracks.clear()

    @Slot()
    def _quit_clicked(self) -> None:
        self.closeAllWindows()

    @Slot()
    def _browse_album_art_clicked(self) -> None:
        (path, _) = QFileDialog.getOpenFileName(
            None,
            caption="Album Tagger",
            filter="Image Files (*.jpeg *.jpg *.png)"
        )
        self.album_art_path.setText(path)
        if path != "":
            image = QPixmap(path)
            self.album_art_preview.setPixmap(image.scaled(120, 120))

    def _toggle_state(self, lock: bool) -> None:
        self.album_artist.setEnabled(not lock)
        self.year.setEnabled(not lock)
        self.album.setEnabled(not lock)
        self.browse_album_art.setEnabled(not lock)
        self.tracks.setEnabled(not lock)
        self.start.setEnabled(not lock)
        self.clear.setEnabled(not lock)
        self.quit.setEnabled(not lock)
        self.wait_message.setText("Please Wait" if lock else "")

    def _lock_state(self) -> None:
        self._toggle_state(lock=True)

    def _unlock_state(self) -> None:
        self._toggle_state(lock=False)

    def _layout(self) -> None:
        window_minimum_width = 640
        label_width = 110
        self.window.setMinimumWidth(window_minimum_width)

        album_artist_label = QLabel("Album Artist")
        album_artist_label.setFixedWidth(label_width)
        album_artist_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        album_artist_layout = QHBoxLayout()
        album_artist_layout.addWidget(album_artist_label)
        album_artist_layout.addWidget(self.album_artist)

        album_title_label = QLabel("Album Title")
        album_title_label.setFixedWidth(label_width)
        album_title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        album_title_layout = QHBoxLayout()
        album_title_layout.addWidget(album_title_label)
        album_title_layout.addWidget(self.album)

        year_label = QLabel("Year of Release")
        year_label.setFixedWidth(label_width)
        year_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        year_layout = QHBoxLayout()
        year_layout.addWidget(year_label)
        year_layout.addWidget(self.year)

        album_art_label = QLabel("Album Art")
        album_art_label.setFixedWidth(label_width)
        album_art_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        album_art_browser_layout = QHBoxLayout()
        album_art_browser_layout.addWidget(album_art_label)
        album_art_browser_layout.addWidget(self.album_art_path)
        album_art_browser_layout.addWidget(self.browse_album_art)

        left_column_layout = QVBoxLayout()
        left_column_layout.addLayout(album_artist_layout)
        left_column_layout.addLayout(album_title_layout)
        left_column_layout.addLayout(year_layout)
        left_column_layout.addLayout(album_art_browser_layout)

        right_column_layout = QVBoxLayout()
        right_column_layout.addWidget(self.album_art_preview)

        top_layout = QHBoxLayout()
        top_layout.addLayout(left_column_layout)
        top_layout.addLayout(right_column_layout)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start)
        button_layout.addWidget(self.clear)
        button_layout.addWidget(self.quit)

        album_art_size = 120
        self.album_art_preview.setFixedHeight(album_art_size)
        self.album_art_preview.setFixedWidth(album_art_size)

        self.wait_message.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        window_layout = QVBoxLayout()
        window_layout.addLayout(top_layout)
        window_layout.addWidget(self.tracks)
        window_layout.addWidget(self.wait_message)
        window_layout.addLayout(button_layout)

        self.window.setLayout(window_layout)

    def run(self) -> int:
        """Executes the application."""
        self._layout()
        self.window.show()
        return self.exec()


def get_file_metadata(file: str) -> dict:
    """Returns the metadata of a given file."""
    tags = mutagen.id3.ID3(file)
    artists = [tag.text[0] for tag in tags.getall("TPE2")]
    title = tags.getall("TIT2")
    genre = tags.getall("TCON")
    return {
        "artist": "; ".join(artists),
        "title": title[0].text[0] if title else "",
        "genre": genre[0].text[0] if genre else "",
    }


def create_text_frame(kind: type, text: str) -> mutagen.id3.TextFrame:
    """Creates a text frame with the given data."""
    return kind(encoding=mutagen.id3.Encoding.UTF8, text=[text])


def create_id3(metadata: dict) -> mutagen.id3.ID3:
    """Creates ID3 tags from a metadata dictionary."""
    tags = mutagen.id3.ID3()

    if "cover" in metadata.keys() and metadata["cover"] != "":
        with open(metadata["cover"], "rb") as file:
            image_contents = file.read()

        image_type = "jpeg"
        if metadata["cover"].endswith(".png"):
            image_type = "png"

        frame = mutagen.id3.APIC(
            encoding=mutagen.id3.Encoding.UTF8,
            mime=f"image/{image_type}",
            type=mutagen.id3.PictureType.COVER_FRONT,
            desc="Front Cover",
            data=image_contents,
        )

        tags.add(frame)

    def add_simple_text_frame(kind: type, key: str):
        if key in metadata.keys():
            frame = create_text_frame(kind, metadata[key])
            tags.add(frame)

    add_simple_text_frame(mutagen.id3.TPE1, "album_artist")
    add_simple_text_frame(mutagen.id3.TPE2, "artist")
    add_simple_text_frame(mutagen.id3.TALB, "album")
    add_simple_text_frame(mutagen.id3.TIT2, "title")
    add_simple_text_frame(mutagen.id3.TDRC, "year")
    add_simple_text_frame(mutagen.id3.TCON, "genre")
    add_simple_text_frame(mutagen.id3.TRCK, "track")

    return tags


def main() -> typing.NoReturn:
    """Entry point of the program."""
    application = AlbumTaggerApplication()
    sys.exit(application.run())


if __name__ == "__main__":
    main()

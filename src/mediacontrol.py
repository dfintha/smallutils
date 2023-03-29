#!/usr/bin/env python
"""A simple program, which can track the currently played media."""

# Exception handling is not critical in this use case, we'll want to just
# proceed everytime.
# pylint: disable=W0702

import argparse
import asyncio
import ctypes
import datetime
import json
import http.server
import os
import sys
import typing
import unidecode
import urllib.request

if sys.platform == "linux":  # --- Linux Implementation: DBus (dbus-python) -- #

    import dbus

    async def get_current_media_info() -> typing.Optional[dict]:
        """Queries information about the currently played media."""
        session_bus = dbus.SessionBus()
        instance = ""
        for name in session_bus.list_names():
            if "org.mpris.MediaPlayer2" in name:
                instance = name
                break
        proxy = session_bus.get_object(instance, "/org/mpris/MediaPlayer2")
        iface = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        properties = iface.GetAll("org.mpris.MediaPlayer2.Player")

        if properties["PlaybackStatus"] not in ("Playing",  "Paused"):
            return {"Playing": False}
        paused = properties["PlaybackStatus"] == "Paused"

        title = "Unknown"
        artist = ""
        length = 0
        position = 0
        for field in properties["Metadata"]:
            if "title" in field or "Title" in field:
                title = properties["Metadata"][field]
            elif "artist" in field or "Artist" in field:
                artist = properties["Metadata"][field]
                if isinstance(artist, dbus.Array):
                    artist = artist[0]
            elif "length" in field or "Length" in field:
                length = properties["Metadata"][field] // 1000000
                if ("Position" in properties):
                    position = properties["Position"] // 1000000
        return {
            "Playing": True,
            "Paused": paused,
            "Artist": artist,
            "Title": title,
            "Position": position,
            "Length": length
        }

    async def go_to_previous() -> None:
        """Jumps to the previous track."""
        call_dbus_command("Previous")

    async def toggle_play_pause() -> None:
        """Plays or pauses the current track."""
        call_dbus_command("PlayPause")

    async def go_to_next() -> None:
        """Jumps to the next track."""
        call_dbus_command("Next")

    async def seek_backward_5sec() -> None:
        """Seeks forward 5 seconds, if available."""
        call_dbus_command("Seek", -5000000)

    async def seek_forward_5sec() -> None:
        """Seeks forward 5 seconds, if available."""
        call_dbus_command("Seek", +5000000)

    def call_dbus_command(command: str, argument: typing.Any = None) -> None:
        """Calls a single DBus command."""
        session_bus = dbus.SessionBus()
        instance = ""
        for name in session_bus.list_names():
            if "org.mpris.MediaPlayer2" in name:
                instance = name
                break
        proxy = session_bus.get_object(instance, "/org/mpris/MediaPlayer2")
        method = proxy.get_dbus_method(
            command, dbus_interface="org.mpris.MediaPlayer2.Player"
        )
        method(argument) if argument is not None else method()

    def set_console_title(title: str) -> None:
        """Sets the console title of the terminal."""
        print(f"\33]0;{title}\a", end="", flush=True)


elif sys.platform == "win32":  # --- Windows Implementation: WinRT (winsdk) -- #

    # This module is only available on Windows.
    # pylint: disable-next=E0401
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    )

    async def get_current_media_info() -> typing.Optional[dict]:
        """Queries information about the currently played media."""
        sessions = await MediaManager.request_async()
        session = sessions.get_current_session()
        if session:
            media = await session.try_get_media_properties_async()
            media = {
                attribute: media.__getattribute__(attribute)
                for attribute in dir(media)
                if attribute[0] != "_"
            }
            timeline = session.get_timeline_properties()
            timeline =  {
                attribute: timeline.__getattribute__(attribute)
                for attribute in dir(timeline)
                if attribute[0] != "_"
            }
            playback = session.get_playback_info()
            playback =  {
                attribute: playback.__getattribute__(attribute)
                for attribute in dir(playback)
                if attribute[0] != "_"
            }
            now = datetime.datetime.now(datetime.timezone.utc)
            position = now - timeline["last_updated_time"] + timeline["position"]
            if playback["playback_status"] not in (4, 5):
                return {"Playing": False}
            return {
                "Playing": True,
                "Paused": playback["playback_status"] == 5,
                "Artist": media["artist"],
                "Title": media["title"],
                "Position": int(position.total_seconds()),
                "Length": int(timeline["end_time"].total_seconds()),
            }
        return {"Playing": False}

    async def go_to_previous() -> None:
        """Jumps to the previous track."""
        sessions = await MediaManager.request_async()
        session = sessions.get_current_session()
        if session:
            await session.try_skip_previous_async()

    async def toggle_play_pause() -> None:
        """Plays or pauses the current track."""
        sessions = await MediaManager.request_async()
        session = sessions.get_current_session()
        if session:
            await session.try_toggle_play_pause_async()

    async def go_to_next() -> None:
        """Jumps to the next track."""
        sessions = await MediaManager.request_async()
        session = sessions.get_current_session()
        if session:
            await session.try_skip_next_async()

    async def seek_backward_5sec() -> None:
        """Seeks forward 5 seconds, if available."""
        await relative_seek(datetime.timedelta(seconds=-5))

    async def seek_forward_5sec() -> None:
        """Seeks forward 5 seconds, if available."""
        await relative_seek(datetime.timedelta(seconds=+5))

    async def relative_seek(delta: datetime.timedelta) -> None:
        """Does relative seeking."""
        sessions = await MediaManager.request_async()
        session = sessions.get_current_session()
        if session:
            timeline = session.get_timeline_properties()
            timeline =  {
                attribute: timeline.__getattribute__(attribute)
                for attribute in dir(timeline)
                if attribute[0] != "_"
            }
            now = datetime.datetime.now(datetime.timezone.utc)
            position = now - timeline["last_updated_time"] + timeline["position"]
            position += delta
            ticks = int(position.total_seconds()) * 10000000
            await session.try_change_playback_position_async(ticks)

    def set_console_title(title: str) -> None:
        """Sets the console title of the terminal."""
        ctypes.windll.kernel32.SetConsoleTitleW(title)


BUILTIN_HTML_PAGE = (
    "<!doctype html>\n"
    '<html lang="en" dir="ltr">\n'
    "  <head>\n"
    '    <meta charset="utf-8" />\n'
    "    <title>mediacontrol Client</title>\n"
    '    <link rel="icon" href="https://fav.farm/🎸" />\n'
    '    <link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,400;0,700" />\n'
    '    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@1,400;1,700" />\n'
    '    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto+Mono:ital,wght@0,400" />\n'
    '    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.3.0/css/all.min.css" />\n'
    "    <style>\n"
    "      body {\n"
    '        font-family: "Montserrat", sans-serif;\n'
    "        background-color: #222222;\n"
    "        color: #93A1A1;\n"
    "      }\n"
    "      body.light {\n"
    "        background-color: #AAAAAA;\n"
    "      }\n"
    "      main {\n"
    "        margin: 20pt auto 20pt auto;\n"
    "        padding: 10pt;\n"
    "        width: 80%;\n"
    "        min-width: 800px;\n"
    "        background-color: #333333;\n"
    "        text-align: center;\n"
    "        border-radius: 20pt;\n"
    "      }\n"
    "      body.light main {\n"
    "        background-color: #DDDDDD;\n"
    "        color: #333333;\n"
    "      }\n"
    "      footer {\n"
    "        font-style: italic;\n"
    "        font-size: 10pt;\n"
    "        color: #666666;\n"
    "      }\n"
    "      footer a {\n"
    "        text-decoration: none;\n"
    "        font-weight: bold;\n"
    "        color: #666666;\n"
    "      }\n"
    "      .button {\n"
    "        padding-top: 8pt;\n"
    "        vertical-align: middle;\n"
    "        width: 40pt;\n"
    "        height: 32pt;\n"
    "        display: inline-block;\n"
    "        background: #222222;\n"
    "        border-radius: 20pt;\n"
    "        margin: 5pt;\n"
    "        text-decoration: none;\n"
    "        font-size: 20pt;\n"
    "        color: #93A1A1;\n"
    "      }\n"
    "      .button:hover {\n"
    "        background: #161616;\n"
    "      }\n"
    "      .button:active {\n"
    "        background: #444444;\n"
    "      }\n"
    "      body.light .button {\n"
    "        background: #AAAAAA;\n"
    "        color: #333333;\n"
    "      }\n"
    "      body.light .button:hover {\n"
    "        background: #888888;\n"
    "      }\n"
    "      body.light .button:active {\n"
    "        background: #CCCCCC;\n"
    "      }\n"
    "      #current {\n"
    "        font-size: 30pt;\n"
    "        font-weight: bold;\n"
    "      }\n"
    "      #lyrics {\n"
    "        background-color: #222222;\n"
    "        border-radius: 10pt;\n"
    "        padding: 10pt;\n"
    '        font-family: "Roboto Mono", monospace;\n'
    "        margin: 10pt;\n"
    "      }\n"
    "      body.light #lyrics {\n"
    "        background-color: #AAAAAA;\n"
    "      }\n"
    "      #progress {\n"
    "        display: inline-block;\n"
    "        width: calc(95% - 2 * 60pt);\n"
    "        margin: 10pt auto 10pt auto;\n"
    "        appearance: none;\n"
    "        -webkit-appearance: none;\n"
    "        -moz-appearance: none;\n"
    "      }\n"
    "      .timestamp {\n"
    "        height: 8pt;\n"
    "        width: 60pt;\n"
    "        display: inline-block;\n"
    "        margin: 10pt 5pt 10pt 5pt;\n"
    "        position: relative;\n"
    "        bottom: 11pt;\n"
    "      }\n"
    "      #position.timestamp {\n"
    "        text-align: right;\n"
    "      }\n"
    "      #length.timestamp {\n"
    "        text-align: left;\n"
    "      }\n"
    "      #progress::-webkit-progress-bar {\n"
    "        height: 8pt;\n"
    "        border-radius: 4pt;\n"
    "      }\n"
    "      #progress::-webkit-progress-value {\n"
    "        background-color: #555;\n"
    "        height: 8pt;\n"
    "        border-radius: 4pt;\n"
    "      }\n"
    "    </style>\n"
    "  </head>\n"
    "  <body>\n"
    "    <main>\n"
    '      <p id="current"></p>\n'
    '      <span class="timestamp" id="position">0:00</span>\n'
    '      <progress id="progress"></progress>\n'
    '      <span class="timestamp" id="length">0:00</span>\n'
    '      <br />\n'
    "      <a\n"
    '        class="button"\n'
    '        id="previous-button"\n'
    '        title="Previous Track"\n'
    '        href="#"\n'
    "        onclick=\"command('previous')\">\n"
    '        <i class="fa fa-fast-backward"></i>\n'
    "      </a>\n"
    "      <a\n"
    '        class="button"\n'
    '        id="seek-back-button"\n'
    '        title="Rewind 5 Seconds"\n'
    '        href="#"\n'
    "        onclick=\"command('seekback')\">\n"
    '        <i class="fa fa-rotate-left"></i>\n'
    "      </a>\n"
    "      <a\n"
    '        class="button"\n'
    '        id="playpause-button"\n'
    '        href="#"\n'
    '        title="Toggle Play/Pause"\n'
    "        onclick=\"command('playpause')\">\n"
    '        <i class="fa fa-play"></i>\n'
    "      </a>\n"
    "      <a\n"
    '        class="button"\n'
    '        id="seek-forward-button"\n'
    '        href="#"\n'
    '        title="Fast-Forward 5 Seconds"\n'
    "        onclick=\"command('seekforward')\">\n"
    '        <i class="fa fa-rotate-right"></i>\n'
    "      </a>\n"
    "      <a\n"
    '        class="button"\n'
    '        id="next-button"\n'
    '        href="#"\n'
    '        title="Next Track"\n'
    "        onclick=\"command('next')\">\n"
    '        <i class="fa fa-fast-forward"></i>\n'
    "      </a>\n"
    "      <a\n"
    '        class="button"\n'
    '        id="toggle-dark-mode-button"\n'
    '        href="#"\n'
    '        title="Toggle Dark/Light Mode"\n'
    "        onclick=\"toggleDarkMode()\">\n"
    '        <i class="fa fa-sun"></i>\n'
    "      </a>\n"
    '      <div id="lyrics">\n'
    "      </div>\n"
    "      <footer>\n"
    '        Lyrics are ripped from <a href="https://www.azlyrics.com/">AZLyrics</a>.\n'
    "        The website uses the\n"
    '        <a href="https://fonts.google.com/specimen/Montserrat">Montserrat</a>\n'
    "        and\n"
    '        <a href="https://fonts.google.com/specimen/Roboto+Mono">Roboto Mono</a>\n'
    "        fonts, hosted on\n"
    '        <a href="https://fonts.google.com/">Google Fonts</a>, and the\n'
    '        <a href="https://fontawesome.com/">Font Awesome</a>\n'
    '        font. The interface and backend is provided by the\n'
    "        <b>mediacontrol</b> software. For the best experience, use a\n"
    "        WebKit-based web browser. For private use only.\n"
    "      </footer>\n"
    "      <script>\n"
    "        function updateLyrics() {\n"
    "          let request = new XMLHttpRequest();\n"
    '          request.open("GET", "/lyrics");\n'
    '          request.addEventListener("load", function () {\n'
    '            let lyrics = document.getElementById("lyrics");\n'
    "            lyrics.innerHTML = this.responseText;\n"
    "          });\n"
    "          request.send();\n"
    "        }\n"
    "        function update() {\n"
    '          let title = document.getElementsByTagName("title")[0];\n'
    '          let progress = document.getElementById("progress");\n'
    '          let position = document.getElementById("position");\n'
    '          let length = document.getElementById("length");\n'
    '          let playpause = document.getElementById("playpause-button");\n'
    "          let request = new XMLHttpRequest();\n"
    '          request.open("GET", "/get");\n'
    '          request.addEventListener("load", function () {\n'
    '            let current = document.getElementById("current");\n'
    "            let status = JSON.parse(this.responseText);\n"
    "            if (status.Playing) {\n"
    '              let text = "";\n'
    '              if (status.Artist !== "")\n'
    '                text = status.Artist + " - " + status.Title;\n'
    "              else {\n"
    "                text = status.Title;\n"
    "              }\n"
    "              if (text !== current.innerHTML) {\n"
    '                title.innerHTML = status.Title;\n'
    "                current.innerHTML = text;\n"
    "                length.innerHTML = formatTime(status.Length);\n"
    "                updateLyrics();\n"
    "              }\n"
    "              if (status.Paused) {\n"
    '                playpause.children[0].classList.add("fa-play");\n'
    '                playpause.children[0].classList.remove("fa-pause");\n'
    "              } else {\n"
    '                playpause.children[0].classList.add("fa-pause");\n'
    '                playpause.children[0].classList.remove("fa-play");\n'
    "              }\n"
    "              position.innerHTML = formatTime(status.Position);\n"
    "              progress.value = status.Position;\n"
    "              progress.max = status.Length;\n"
    "            } else {\n"
    '              current.innerHTML = "Not Playing";\n'
    '              title.innerHTML = "mediacontrol Client";\n'
    '              playpause.children[0].classList.add("fa-play");\n'
    '              playpause.children[0].classList.remove("fa-pause");\n'
    "            }\n"
    "          });\n"
    "          request.send();\n"
    "        }\n"
    "        function command(verb) {\n"
    "          let request = new XMLHttpRequest();\n"
    '          request.open("GET", "/" + verb);\n'
    "          request.send();\n"
    "          update();\n"
    "        }\n"
    "        function formatTime(seconds) {\n"
    "          let addZeroes = function (number) {\n"
    '            if (number === 0) return "00";\n'
    '            if (number < 10) return "0" + number;\n'
    '            return "" + number;\n'
    "          };\n"
    "          let minutes = Math.floor(seconds / 60);\n"
    "          seconds = seconds % 60;\n"
    "          let hours = Math.floor(minutes / 60);\n"
    "          minutes = minutes % 60;\n"
    "          if (hours === 0) {\n"
    '            return minutes + ":" + addZeroes(seconds);\n'
    "          } else {\n"
    '            return hours + ":" + addZeroes(minutes) + ":" + addZeroes(seconds);\n'
    "          }\n"
    "        };\n"
    "        function toggleDarkMode() {\n"
    '          let body = document.getElementsByTagName("body")[0];\n'
    '          body.classList.toggle("light");\n'
    '          let button = document.getElementById("toggle-dark-mode-button");\n'
    "          let logo = button.children[0];\n"
    '          logo.classList.toggle("fa-moon");\n'
    '          logo.classList.toggle("fa-sun");\n'
    '          let isLightMode = logo.classList.contains("fa-moon");\n'
    '          localStorage.setItem("isLightMode", isLightMode ? 1 : 0);\n'
    "        };\n"
    '        if (localStorage.getItem("isLightMode") == 1)\n'
    "          toggleDarkMode();\n"
    "        update();\n"
    "        let autoUpdate = setInterval(update, 1000);\n"
    "      </script>\n"
    "    </main>\n"
    "  </body>\n"
    "</html>\n"
)


class MediaQueryHandler(http.server.BaseHTTPRequestHandler):
    """Handler for media queries through HTTP."""

    def _send_status(self, code: int, description: str) -> None:
        head = f"HTTP/1.1 {str(code)} {description}\n".encode("utf-8")
        try:
            self.wfile.write(head)
            self.wfile.write(b"Server: Media Query Service\n")
            self.wfile.write(b"Connection: close\n\n")
        except:
            pass

    def _send_content(self, content: str):
        header = (
            "HTTP/1.1 200 OK\n"
            "Server: Media Query Service\n"
            f"Content-Type: text/html\n"
            f"Content-Length: {len(content)}\n"
            "Connection: close\n"
            "\n"
        )
        try:
            self.wfile.write(header.encode("utf-8"))
            self.wfile.write(content.encode("utf-8"))
        except:
            pass

    # This method name is fixed as it is an overridden callback function.
    # pylint: disable-next=C0103
    def do_HEAD(self) -> None:
        """Handles HEAD requests."""
        self._send_status(404, "Not Found")

    # This method name is fixed as it is an overridden callback function.
    # pylint: disable-next=C0103
    def do_GET(self) -> None:
        """Handles GET requests."""
        if self.server.verbose:
            print(f" --- Incoming request; path='{self.path}'")

        if self.path == "/get":
            content = parse_artist_and_title(
                asyncio.run(get_current_media_info())
            )
            if self.server.verbose:
                print(f" --- Fetched current media info; info='{content}'")
            self._send_content(json.dumps(content))
        elif self.path == "/previous":
            asyncio.run(go_to_previous())
            self._send_status(200, "OK")
        elif self.path == "/seekback":
            asyncio.run(seek_backward_5sec())
            self._send_status(200, "OK")
        elif self.path == "/playpause":
            asyncio.run(toggle_play_pause())
            self._send_status(200, "OK")
        elif self.path == "/seekforward":
            asyncio.run(seek_forward_5sec())
            self._send_status(200, "OK")
        elif self.path == "/next":
            asyncio.run(go_to_next())
            self._send_status(200, "OK")
        elif self.path == "/lyrics":
            content = get_lyrics_for_track(
                parse_artist_and_title(asyncio.run(get_current_media_info())),
                self.server.verbose
            )
            self._send_content(content)
        elif self.path == "/":
            self._send_content(BUILTIN_HTML_PAGE)
        else:
            self._send_status(404, "Not Found")


def main() -> None:
    """Entry point of the program."""
    try:
        program = "mediacontrol"
        description = "server for media control through http"
        parser = argparse.ArgumentParser(description=description, prog=program)
        parser.add_argument(
            "-p",
            "--port",
            type=int,
            default=42069,
            metavar="PORT",
            help="define a custom port number (default is 42069)",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            default=False,
            help="verbose mode, debug messages are emitted",
        )

        duck_bw = (
            "                                \n"
            "                                \n"
            "            ▓▓▓▓▓▓▓▓▓▓          \n"
            "          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓        \n"
            "          ▓▓▓▓▓▓  ▒▒▓▓▓▓░░░░░░  \n"
            "          ▓▓▓▓▓▓    ▓▓░░░░░░░░  \n"
            "          ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░    \n"
            "          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒      \n"
            "  ▓▓▓▓      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒    \n"
            "  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▓▓▒▒▒▒  \n"
            "  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒▒  \n"
            "  ▒▒▓▓▓▓▒▒▓▓▓▓▓▓▓▓▓▓▓▓░░▒▒▒▒▒▒  \n"
            "    ▒▒▓▓▒▒▓▓▓▓▓▓▓▓░░░░▒▒▒▒▒▒▒▒  \n"
            "    ▒▒▒▒▒▒░░░░░░░░▒▒▒▒▒▒▒▒▒▒    \n"
            "      ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒      \n"
            "          ▒▒▒▒▒▒▒▒▒▒▒▒          \n"
            "                                \n"
            "                                \n"
        )

        duck_color = (
            "\n"
            "            \x1B[33;1m▓▓▓▓▓▓▓▓▓▓\x1B[0m\n"
            "          \x1B[33;1m▓▓▓▓▓▓▓▓▓▓▓▓▓▓\x1B[0m\n"
            "          \x1B[33;1m▓▓▓▓▓▓\x1B[0m  \x1B[37;1m▓▓"
            "\x1B[33;1m▓▓▓▓\x1B[33;2m▒▒▒▒▒▒\x1B[0m\n"
            "          \x1B[33;1m▓▓▓▓▓▓\x1B[0m    "
            "\x1B[33;1m▓▓\x1B[33;2m▒▒▒▒▒▒▒▒\x1B[0m\n"
            "          \x1B[33;1m▓▓▓▓▓▓▓▓▓▓▓▓\x1B[33;2m▒▒▒▒▒▒\x1B[0m\n"
            "          \x1B[33;1m▓▓▓▓▓▓▓▓▓▓▓▓▓▓\x1B[33m▒▒\x1B[0m\n"
            "  \x1B[33;1m▓▓▓▓\x1B[0m      \x1B[33;1m▓▓▓▓▓▓▓▓▓▓▓▓▓▓"
            "\x1B[33m▒▒\x1B[0m\n"
            "  \x1B[33;1m▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\x1B[33m▒▒\x1B[33;1m▓▓"
            "\x1B[33m▒▒▒▒\x1B[0m\n"
            "  \x1B[33;1m▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\x1B[33m▒▒▒▒▒▒\x1B[0m\n"
            "  \x1B[33m▒▒\x1B[33;1m▓▓▓▓\x1B[33m▒▒\x1B[33;1m▓▓▓▓▓▓▓▓▓▓▓▓"
            "\x1B[33;2m▒▒\x1B[0m\x1B[33m▒▒▒▒▒▒\x1B[0m\n"
            "    \x1B[33m▒▒\x1B[33;1m▓▓\x1B[33m▒▒\x1B[33;1m▓▓▓▓▓▓▓▓"
            "\x1B[33;2m▒▒▒▒\x1B[0m\x1B[33m▒▒▒▒▒▒▒▒\x1B[0m\n"
            "    \x1B[33m▒▒▒▒▒▒\x1B[33;2m▒▒▒▒▒▒▒▒\x1B[0m"
            "\x1B[33m▒▒▒▒▒▒▒▒▒▒\x1B[0m\n"
            "      \x1B[33m▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒\x1B[0m\n"
            "          \x1B[33m▒▒▒▒▒▒▒▒▒▒▒▒\x1B[0m\n"
            "\n"
        )

        selected_duck = duck_bw
        if "TERM" in os.environ and "color" in os.environ["TERM"]:
            selected_duck = duck_color
        if "WT_SESSION" in os.environ:
            selected_duck = duck_color

        arguments = vars(parser.parse_args())
        set_console_title("mediacontrol Server")
        port = arguments["port"]
        server = http.server.HTTPServer(("", port), MediaQueryHandler)
        server.verbose = arguments["verbose"]
        print(
            selected_duck +
            " >>> Media control server started! Quack!\n"
            f" >>> Listening on port {port}!"
        )
        server.serve_forever()
    except KeyboardInterrupt:
        print("")
        print(" >>> Goodbye!")


def parse_artist_and_title(state: dict) -> dict:
    """Parses artist and title from the metadata."""
    if not state["Playing"]:
        return state
    if state["Artist"] == "" and '•' in state["Title"]:
        state["Artist"] = state["Title"].split('•')[1].strip()
        state["Title"] = state["Title"].split('•')[0].strip()
    elif state["Artist"] == "" and " - " in state["Title"]:
        state["Artist"] = state["Title"].split(" - ")[0].strip()
        state["Title"] = state["Title"].split(" - ")[1].strip()
    if "," in state["Artist"]:
        state["Artist"] = state["Artist"].split(",")[0]
    if " - " in state["Title"]:
        state["Title"] = state["Title"].split(" - ")[0].strip()
    if state["Artist"].endswith(" - Topic"):
        state["Artist"] = state["Artist"][:-8]
    return state


def get_lyrics_for_track(state: dict, verbose: bool) -> str:
    """Retrieves the lyrics of a song from AZLyrics."""

    def replace_known_artist(field: str) -> str:
        """Replaces known artists."""
        known = {
            "ELO": "Electric Light Orchestra",
            "Jimi Hendrix Experience": "Jimi Hendrix",
        }
        return known[field] if field in known else field

    def replace_known_title(field: str) -> str:
        """Replaces known titles."""
        known = {
            "B********": "Bückstabü",
            "Why Don't You Do Right": "Why Don't You Do Right (Get Me Some Money Too)",
            "I-E-A-I-E-I-O": "I-E-A-I-A-I-O",
            "Foxy Lady": "Foxey Lady",
        }
        return known[field] if field in known else field

    def filter_special(field: str) -> str:
        """Filters special characters from a string."""
        specials = "/'\" (),.?!-_äáëéóöőúüűß[*]"
        return "".join(c for c in field if c not in specials).lower()

    try:
        artist = state["Artist"]
        title = state["Title"]
        if artist.startswith("The "):
            artist = artist[4:]
        artist = filter_special(replace_known_artist(unidecode.unidecode(artist)))
        title = filter_special(replace_known_title(title))
        url = f"http://www.azlyrics.com/lyrics/{str(artist)}/{str(title)}.html"
        if verbose:
            print(
                f" --- Fetching lyrics for current track; "
                f"artist='{state['Artist']}' "
                f"title='{state['Title']}' "
                f"url='{url}' "
            )
        with urllib.request.urlopen(url) as page:
            content = page.read().decode("utf-8")
        content = content[content.find("<div>\r\n<!--") :]
        content = content[content.find("-->") + 3 :]
        content = content[: content.find("</div>")]
        return content
    except:
        if verbose:
            print(f" --- Failed to fetch lyrics for current track; url='{url}'")
        return "<i>Lyrics are unavailable for this track.</i>"


if __name__ == "__main__":
    main()

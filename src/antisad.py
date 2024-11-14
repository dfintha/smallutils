#!/usr/bin/env python3

"""Small tool to mute the computer while Spotify plays advertisements."""

import asyncio
import datetime
import subprocess
import sys
import time


def _log(message: str) -> None:
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
    print(f"{timestamp}{message}")


def _check(artist: str, title: str) -> bool:
    blacklist = {"Spotify", "Advertisement"}
    return artist in blacklist or title in blacklist


# --- Linux: D-Bus and PulseAudio -------------------------------------------- #
if sys.platform.startswith("linux"):
    import dbus

    def _greet() -> None:
        _log("Started; platform='linux', backend='dbus+pactl'")

    async def _fetch() -> tuple:
        session_bus = dbus.SessionBus()
        instance = ""
        for name in session_bus.list_names():
            if "org.mpris.MediaPlayer2" in name:
                instance = name
                break

        proxy = session_bus.get_object(instance, "/org/mpris/MediaPlayer2")
        interface = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        properties = interface.GetAll("org.mpris.MediaPlayer2.Player")

        title = None
        artist = None
        for field in properties["Metadata"]:
            if "title" in field or "Title" in field:
                title = properties["Metadata"][field]
            elif "artist" in field or "Artist" in field:
                artist = properties["Metadata"][field]
                if isinstance(artist, dbus.Array):
                    artist = ", ".join(artist)
        return (artist, title)

    def _mute(mute: bool) -> None:
        process = subprocess.run(
            ["pactl", "get-default-sink"],
            capture_output=True,
            check=False,
            encoding="utf-8",
        )

        if process.returncode != 0:
            _log(f"Failed to query default sink; code='{process.returncode}'")
            return

        sink = process.stdout.strip()

        process = subprocess.run(
            ["pactl", "set-sink-mute", sink, "1" if mute else "0"],
            capture_output=True,
            check=False,
            encoding="utf-8",
        )

        if process.returncode != 0:
            _log(f"Failed to mute default sink; code='{process.returncode}'")


# --- macOS: OSAScript ------------------------------------------------------- #
elif sys.platform.startswith("darwin"):
    import os

    def _greet() -> None:
        _log("Started; platform='macos', backend='osascript'")

    async def _fetch() -> tuple:

        def _ask(what: str) -> str:
            command = (
                "osascript -e "
                "'tell application \"Spotify\" to if player state is playing "
                f"then {what} of current track'"
            )
            return os.popen(command).read().strip()

        artist = _ask("artist")
        title = _ask("name")
        if artist == "" and title == "":
            return (None, None)

        return (artist, title)

    def _mute(mute: bool) -> None:
        mode = "with" if mute else "without"
        os.popen(f"osascript -e 'set volume {mode} output muted'")

# --- Unknown Platform: No-Op ------------------------------------------------ #
else:

    def _greet() -> None:
        _log("Started; platform='unknown', backend='noop'")

    def _fetch() -> tuple:
        return (None, None)

    def _mute(_: bool) -> None:
        pass


# --- End of Platform Code --------------------------------------------------- #


def _main() -> None:
    try:
        _greet()

        ad = False
        previous_artist = None
        previous_title = None

        while True:
            artist, title = asyncio.run(_fetch())
            if not artist and not title:
                continue

            if artist != previous_artist or title != previous_title:
                _log(f"Media changed; artist='{artist}', title='{title}'")
                previous_artist = artist
                previous_title = title

            if _check(artist, title):
                if not ad:
                    _log("Advertisement started, muting;")
                    _mute(True)
                    ad = True
            elif ad:
                _log("Advertisement stopped, unmuting;")
                _mute(False)
                ad = False

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("")
        _log("Interrupted, exiting;")


if __name__ == "__main__":
    _main()

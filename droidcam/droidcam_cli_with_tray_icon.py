import asyncio
import sys
import signal

from PIL import Image
from subprocess import Popen
from time import sleep
from os.path import abspath, join, dirname

try:
    from pystray import Icon, Menu, MenuItem
except ImportError:
    PYSTRAY_AVAILABLE = False
else:
    PYSTRAY_AVAILABLE = True

TRAY_ICON_TITLE = "droidcam-tray-icon"


def get_icon_image():
    here = abspath(__file__)
    icon_path = join(dirname(here), "icon.png")
    return Image.open(icon_path)


def run_tray_icon(exit_callback):
    menu = Menu(MenuItem("Exit", exit_callback))
    icon_image = get_icon_image()
    icon = Icon(TRAY_ICON_TITLE, icon_image, menu=menu)
    icon.run()


if __name__ == "__main__":
    droidcam_process = Popen(["droidcam-cli", *sys.argv[1:]])

    def exit_handler(*args):
        droidcam_process.terminate()
        sys.exit()

    signal.signal(signal.SIGTERM, exit_handler)

    # Wait a second before checking if we've terminated early
    # due to bad arguments or similar
    sleep(0.5)
    droidcam_returncode = droidcam_process.poll()

    if not droidcam_returncode:

        if PYSTRAY_AVAILABLE:
            run_tray_icon(exit_handler)
        else:
            loop = asyncio.get_event_loop()
            try:
                loop.run_forever()
            finally:
                loop.close()

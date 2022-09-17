import operator
import os
import time
from functools import reduce


class console:
    # Helper class

    def info(*args, colour_rgb="0094c8", sep="", end="\n") -> None:
        print(console.__getColourANSICodeFromHexRGB(colour_rgb) + "[INFO] ", end="")
        print(*args, "\033[39m", sep=sep, end=end)

    def warn(*args, colour_rgb="fcc800", sep="", end="\n") -> None:
        print(console.__getColourANSICodeFromHexRGB(colour_rgb) + "[WARN] ", end="")
        print(*args, "\033[39m", sep=sep, end=end)

    def err(*args, colour_rgb="ba2636", sep="", end="\n") -> None:
        print(console.__getColourANSICodeFromHexRGB(colour_rgb) + "[ERR!] ", end="")
        print(*args, "\033[39m", sep=sep, end=end)

    def ok(*args, colour_rgb="67a70c", sep="", end="\n") -> None:
        print(console.__getColourANSICodeFromHexRGB(colour_rgb) + "[ OK ] ", end="")
        print(*args, "\033[39m", sep=sep, end=end)

    def sublog(*args, colour_rgb="000000", sep="", end="\n"):
        print(console.__getColourANSICodeFromHexRGB(colour_rgb) + "       ", end="")
        print(*args, "\033[39m", sep=sep, end=end)

    def clear() -> None:
        print("\033c")

    def wait(seconds: float) -> None:
        time.sleep(seconds)

    def getWidth() -> int:
        return os.get_terminal_size().columns

    def getHeight() -> int:
        return os.get_terminal_size().lines

    def __getColourANSICodeFromHexRGB(colour_rgb: str) -> str:
        if colour_rgb[0] == "#":
            colour_rgb = colour_rgb[1:]

        return "\033[38;2" + reduce(
            operator.add, [";" + str(int(colour_rgb[i:i + 2], base=16)) for i in [0, 2, 4]]
        ) + "m"

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

try:
    DEBUG: int = int(os.environ.get("DEBUG", "0"))
    """The debugging level.

    Supported debugging levels:
        - ``0``: No debugging.
        - ``1``: Renders debbuging information onto the screen and prints some basic statistics to stdout.
        - ``2``: Profiles the AI's minimax algorithm.
        - ``3``: Dumps data for each visited node in the AI's minimax algorithm.
    """
except:
    DEBUG = 1

try:
    TARGET_TIME: int = int(os.environ.get("TARGET_TIME", "1500"))
    """How long the AI should calculate for, in milliseconds, per turn.

    This is used to determine the search depth. Note that this will be the average time taken up by the AI.
    The amount of time taken up by each computation will vary somewhat.
    """
except:
    TARGET_TIME = 1500

try:
    MINIMUM_DEPTH: int = int(os.environ.get("MINIMUM_DEPTH", "7"))
    """The minimum depth to search to.

    This is also used as the initial search depth. Every search will be at least this deep (unless the game ends before reach this depth).
    """
except:
    MINIMUM_DEPTH = 7

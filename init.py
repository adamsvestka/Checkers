import os
import sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
try:
    if len(sys.argv) > 1:
        DEBUG = int(sys.argv[1])
    else:
        DEBUG = int(os.environ.get("DEBUG", "0"))
except:
    DEBUG = 1
os.environ["DEBUG"] = str(DEBUG)
import pygame
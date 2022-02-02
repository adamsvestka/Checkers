import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

# 0: normal, 1: timing, 2: profiling, 3: minimax dump
try:
    DEBUG = int(os.environ.get("DEBUG", "0"))
except:
    DEBUG = 1

try:
    TARGET_TIME = int(os.environ.get("TARGET_TIME", "1500"))
except:
    TARGET_TIME = 1500

try:
    MINIMUM_DEPTH = int(os.environ.get("MINIMUM_DEPTH", "7"))
except:
    MINIMUM_DEPTH = 7

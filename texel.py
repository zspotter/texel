import curses
import math
from time import time, sleep
import random
import noise

from fonts import Font

# Makes a binary tree out of dict's
def make_btree(layers):
    if layers <= 0:
        return None
    return {
        False: make_btree(layers - 1),
        True: make_btree(layers - 1)
    }

# 2x2 groups of pixels can be rendered as 1 block character in the terminal:
#
#                             / Invert for right-half block
#  [█] [▗] [▖] [▛] [▜] [▞] [▌]
#
#  [ ] [▝] [▘] [▙] [▟] [▚] [▄]
#                             \ Invert for top-half block
#

# TEX (terminal-pixel) is a 4-layer binary tree, where each leaf is a character.
# Characters for a 2x2 group of pixels are looked up like so:
#   TEX[topleft][topright][bottomleft][bottomright]
TEX = make_btree(4)
TEX[False][False][False][False] = ' ' # 0000
TEX[False][False][False][True ] = '▗' # 0001
TEX[False][False][True ][False] = '▖' # 0010
TEX[False][False][True ][True ] = '▄' # 0011
TEX[False][True ][False][False] = '▝' # 0100
TEX[False][True ][False][True ] = '▌' # 0101 invert
TEX[False][True ][True ][False] = '▞' # 0110
TEX[False][True ][True ][True ] = '▟' # 0111
TEX[True ][False][False][False] = '▘' # 1000
TEX[True ][False][False][True ] = '▚' # 1001
TEX[True ][False][True ][False] = '▌' # 1010
TEX[True ][False][True ][True ] = '▙' # 1011
TEX[True ][True ][False][False] = '▄' # 1100 invert
TEX[True ][True ][False][True ] = '▜' # 1101
TEX[True ][True ][True ][False] = '▛' # 1110
TEX[True ][True ][True ][True ] = '█' # 1111
TEX_INVERT = {
    (False, True , False, True ),
    (True , True , False, False)
}

def draw_texel(tl, tr, bl, br, stdscr, y, x):
    c = TEX[tl][tr][bl][br]
    if (tl, tr, bl, br) in TEX_INVERT:
        stdscr.addch(y, x, c, curses.A_REVERSE)
    else:
        stdscr.addch(y, x, c)

def draw_win(stdscr, pixel, fps=None):
    (height, width) = stdscr.getmaxyx()
    height -= 1 # curses can't write to bottom right corner
    frame_s = 1.0/fps if fps else None

    t = 0
    start = None
    elapsed = None
    while True:
        start = time()
        for y in range(0, height * 2, 2):
            for x in range(0, width * 2, 2):
                draw_texel(
                    pixel(y, x, t),
                    pixel(y, x + 1, t),
                    pixel(y + 1, x, t),
                    pixel(y + 1, x + 1, t),
                    stdscr, int(y/2), int(x/2))
        stdscr.refresh()
        elapsed = time() - start
        if frame_s and elapsed < frame_s:
            # Max FPS
            sleep(frame_s - elapsed)
            elapsed = time() - start
        # else :
        #     # Skip frame
        #     sleep(elapsed - frame_s)
        #     t += 1
        stdscr.addstr(height, 0, f'[{1/elapsed:.2f} FPS]')
        t += 1


# Size of features
SX = 400
SY = 50
# Delta position per frame
DX = 0.05
DY = 0.1
DZ = 0.005
def simp(y, x, t):
    n = 1 + noise.snoise3((t * DX + x) / SX, (t * DY + y) / SY, t * DZ)
    return int(n * 100) % 100 < (math.sin(t/30) / 2.0 + 1) * 25 + 40

def mask(y, x, t):
    return simp(y, x, t) and (x % 2 == 0 or simp(y + 1000, x, t + 15))

def waves(y, x, t):
    return int(x + t + 1000.0 * math.sin(t/100.0) * math.sin(y/50.0)) % 50 < 20

def make_text(stdscr, text):
    (scr_h, scr_w) = stdscr.getmaxyx()
    height = 2 * scr_h
    width = 2 * scr_w
    font = Font('/System/Library/Fonts/Monaco.dfont', min(height, 50))
    text_bitmap = font.render_text(text)
    x_off = (width - text_bitmap.width) // 2
    y_off = (height - text_bitmap.height) // 2
    def pixel(y, x, t):
        text_x = x - x_off
        text_y = y - y_off
        text_p = None
        if text_y < 0 or text_x < 0 or text_y >= text_bitmap.height or text_x >= text_bitmap.width:
           text_p = False
        else:
            text_p = text_bitmap.get(text_x, text_y)
        return text_p != (not simp(y, x, t/2.0) and y % 2 == 0)
    return pixel

def main(stdscr):
    draw_win(stdscr, make_text(stdscr, '12:33a'), 60)
    # draw_win(stdscr, mask, 30)

curses.wrapper(main)


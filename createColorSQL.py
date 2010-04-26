#!/usr/bin/python
import colorsys

# This script builds the store_color table, it uses the names based on the
# color wheel from the imagescan.py script. Rename them to something you
# think is better aftwards (color info is normalized). The last bit prints
# out a lookup dict for the imagescan file to use to generate SQL output

bin_width = 30 # size of hue slices (degress)
max_bin = 360

SATURATION = 0.7

COLOR = ['RED', 'ORANGE', 'YELLOW',
    'LIME', 'GREEN', 'TURQUOISE',
    'CYAN', 'OCEAN', 'BLUE',
    'VIOLET', 'MAGENTA', 'RASPBERRY',
    ]
TONE = ['DARK', None, 'BRIGHT']

CNT = 1

NAME_TO_SQLID = dict()

for h in range(0, int(max_bin/bin_width)):
    for t in TONE:
        hue = float(h*bin_width)/max_bin
        val = float((TONE.index(t)+1)*33)/100
        rgb = ''.join(['%X' % int(x*255) for x in colorsys.hsv_to_rgb(hue, SATURATION, val)])
        if t:
            name = ' '.join([t, COLOR[h]])
        else:
            name = COLOR[h]
        print ','.join([str(CNT), repr(name), str(0), repr(rgb)])
        NAME_TO_SQLID.update({name : CNT})
        CNT += 1

print repr(NAME_TO_SQLID)


#!/usr/bin/python
# -*- coding: utf-8 -*-

# A color analysis script to help you label your store's products with color data
# automagically. It will take either a single file or scour an entire folder for
# folders of images and do each one individually printing a summary of what it
# thinks is the correct color value. A work in progress...
#
#    ~jaymz | @jaymzcampbell | jaymz.eu
#
#
# MIT Licesnsed for what its worth, copy: http://www.opensource.org/licenses/mit-license.php

import Image
import ImageFilter
import os
import glob
import sys
import colorsys
import re
from copy import copy
from operator import itemgetter
from decimal import Decimal

output = open('colors.csv', 'w')

# Pixels will be first compared to these values before being
# added to the data list of color information on the first pass
LBOUND = 0
UBOUND = 255

MIN_SATURATION = 30 # avoid washed out pixels influencing counts

# Base folder for the processFolder function, it'll iterate over here on subfolders
FOLDER = '/home/jaymz/documents/crooked-docs/data-export/store-migration/product-images/'

# Meh, i need to flip between these two, you can probably tweak this :)
SUMMARY_FORMAT, SQL_FORMAT = True, True

# Names based off: http://bluelobsterart.com/wordpress/wp-content/uploads/2009/03/rgb-color-wheel-lg.jpg
COLOR = ['RED', 'ORANGE', 'YELLOW',
    'LIME', 'GREEN', 'TURQUOISE',
    'CYAN', 'OCEAN', 'BLUE',
    'VIOLET', 'MAGENTA', 'RASPBERRY',
    ]
TONE = ['DARK', '', 'BRIGHT']

# via the createColorSQL.py file , addition added in GRAY/BLACK/WHITE to after this
SQL_IDS = {'DARK YELLOW': 7, 'DARK ORANGE': 4, 'BRIGHT GREEN': 15, 'BRIGHT ORANGE': 6, 'DARK RED': 1, 'BRIGHT OCEAN': 24, 'BRIGHT RED': 3, 'DARK OCEAN': 22, 'YELLOW': 8, 'OCEAN': 23, 'BRIGHT YELLOW': 9, 'RASPBERRY': 35, 'GREEN': 14, 'BRIGHT TURQUOISE': 18, 'CYAN': 20, 'MAGENTA': 32, 'RED': 2, 'ORANGE': 5, 'BLUE': 26, 'TURQUOISE': 17, 'LIME': 11, 'BRIGHT LIME': 12, 'DARK MAGENTA': 31, 'DARK LIME': 10, 'BRIGHT MAGENTA': 33, 'BRIGHT VIOLET': 30, 'DARK VIOLET': 28, 'DARK BLUE': 25, 'BRIGHT BLUE': 27, 'VIOLET': 29, 'BRIGHT RASPBERRY': 36, 'DARK TURQUOISE': 16, 'DARK CYAN': 19, 'BRIGHT CYAN': 21, 'DARK GREEN': 13, 'DARK RASPBERRY': 34}

pcnt = 0

def trimFloat(val, places=2):
    return float(repr(val)[0:places+2])

def withinBounds(allowance, _rgb):
    rgb = copy(_rgb)
    diff = 0
    allowance = Decimal(repr(allowance))
    for c in rgb:
        for d in rgb:
            dec_d = Decimal(repr(d)).quantize(allowance)
            dec_c = Decimal(repr(c)).quantize(allowance)

            diff = abs(dec_d-dec_c)

            if (d != c) and diff>allowance:
                return False
    return True

def processImage(i, name=None):
  """ Scales down the image, blurs it to ease the blending of the color values
  and reduce spikes from anomolies. It then samples pixels creating a list of
  colors. This list is then looped over to build counts which are placed into
  bins of 30° hue's seperated into three based on their value. Pixels less than
  a certain saturation are discarded. """

  global pcnt

  i = i.resize((200,200))
  i = i.convert("RGB")
  i = i.filter(ImageFilter.BLUR)
  d = i.getdata()
  cnt = 0

  h = [] #holds the hsv info
  grays = [] #holds just gray content
  black_count = 0
  white_count = 0
  total_samples = 0

  for p in d:
      cnt = cnt + 1
      if cnt == 8: #take every 4th pixel
        if p[0]>LBOUND and p[1]>LBOUND and p[2]>LBOUND and p[0]<UBOUND and p[1]<UBOUND and p[2]<UBOUND:
            r = trimFloat(float(p[0])/255)
            g = trimFloat(float(p[1])/255)
            b = trimFloat(float(p[2])/255)

            if not withinBounds(0.02, (r,g,b)):
                h.append(colorsys.rgb_to_hsv(r,g,b))
            else:
                if (r+g+b)/3>0.94:
                    white_count += 1
                elif (r+g+b)/3<0.3:
                    black_count += 1
                else:
                    grays.append(colorsys.rgb_to_hsv(r,g,b))
            total_samples += 1
        cnt = 0 #reset sample counter

  h.sort()
  grays.sort()
  bin_width = 30 # size of hue slices (degress)
  max_bin = 360

  darks = [0] * int(max_bin/bin_width)
  mids = [0] * int(max_bin/bin_width)
  lites = [0] * int(max_bin/bin_width)

  for p in h[::]:
      hue = p[0]*360
      sat = p[1]*100
      val = p[2]*100
      if sat >= MIN_SATURATION:
        bin_number = ((int(hue)+15)/bin_width)%(max_bin/bin_width)
        if val<33:
            darks[bin_number] += 1
        elif val>33 and val < 66:
            mids[bin_number] += 1
        else:
            lites[bin_number] += 1
        #print "HUE BIN: %s VALUE : %d" % (int(hue)/bin_width, int(hue))

  c = 0
  data = zip(darks, mids, lites)

  if SUMMARY_FORMAT:
    for x in data:
        print '%d %s : %s %d°' % (c, COLOR[c], x, c*bin_width)
        c += 1

  # the following area needs a rework. the index technique works alright as long
  # as counts and values dont all match up, then it starts picking the first one
  # so this needs re-writing to better order the list data

  darks_sort, mids_sort, lites_sort = darks[::], mids[::], lites[::]
  darks_sort.sort()
  mids_sort.sort()
  lites_sort.sort()

  sorted_counts = (darks_sort, mids_sort, lites_sort)

  primary_idx = (darks.index(sorted_counts[0][-1]), mids.index(sorted_counts[1][-1]), lites.index(sorted_counts[2][-1]))
  primary_cnts = (darks[primary_idx[0]], mids[primary_idx[1]], lites[primary_idx[2]])
  tone = primary_cnts.index(max(primary_cnts))
  max_hbin = primary_idx[tone]

  pcnt += 1

  if SUMMARY_FORMAT:
    print "\nDominant Hue: %s %s" % (TONE[tone], COLOR[max_hbin])

  if SQL_FORMAT and name and max(primary_cnts) > 30:
    output.write('%d, %s, %s\n' % (pcnt, name, SQL_IDS[' '.join([TONE[tone], COLOR[max_hbin]]).strip()]))

  sorted_counts[0][-1], sorted_counts[1][-1], sorted_counts[2][-1] = (0, 0, 0) # kind of reset the primary to null
  for l in sorted_counts:
      l.sort()

  primary_idx = (darks.index(sorted_counts[0][-1]), mids.index(sorted_counts[1][-1]), lites.index(sorted_counts[2][-1]))
  primary_cnts = (darks[primary_idx[0]], mids[primary_idx[1]], lites[primary_idx[2]])
  tone = primary_cnts.index(max(primary_cnts))
  max_hbin = primary_idx[tone]

  if SUMMARY_FORMAT:
    print "Secondary Hue: %s %s" % (TONE[tone], COLOR[max_hbin])

  if SQL_FORMAT and name and max(primary_cnts) > 30:
    pcnt += 1
    output.write('%d, %s, %s\n' % (pcnt, name, SQL_IDS[' '.join([TONE[tone], COLOR[max_hbin]]).strip()]))

  # area to rewrite ends...

  gray_total = [(g[0]+g[1]+g[2])/3 for g in grays]
  gray_average = reduce(lambda x,y : x+y, gray_total)/len(gray_total)

  black_percent = black_count/float(total_samples)*100
  gray_percent = len(gray_total)/float(total_samples)*100
  white_percent = white_count/float(total_samples)*100

  if SUMMARY_FORMAT:
    print "\nAverage Gray: %s (samples: %0.1f%%), White count: %s (%0.1f%%), Black count: %s (%0.1f%%)" % (gray_average, gray_percent, white_count, white_percent, black_count, black_percent)
    print "Total samples taken: %s\n\n" % total_samples

  if SQL_FORMAT:
    if black_percent > 10:
        pcnt += 1
        output.write('%d, %s, %d\n' % (pcnt, name, 38))
    if gray_percent > 10:
        pcnt += 1
        output.write('%d, %s, %d\n' % (pcnt, name, 37))
    if white_percent > 30:
        pcnt += 1
        output.write('%d, %s, %d\n' % (pcnt, name, 39))

# Helper functions follow along with __main__ def

def processFolder(folder):
    for image_folder in glob.glob(folder+'*'):
        try:
            folder_images = []
            for image in os.listdir(image_folder):
                if "jpg" in image and "._" not in image:
                    folder_images.append(image)
            folder_images.sort()
            j = os.path.join(image_folder, folder_images[1])
            if SUMMARY_FORMAT:
                print "working: "+j
            i = Image.open(j)
            processImage(i, image_folder.split('/')[-1])
        except:
            pass

def processFile(_file):
    i = Image.open(_file)
    processImage(i)

if __name__ == "__main__":
    try:
        if 'product-images' not in sys.argv[1]:
            processFile('product-images/'+sys.argv[1])
        else:
            processFile(sys.argv[1])
    except IndexError:
        processFolder(FOLDER)
    output.close()




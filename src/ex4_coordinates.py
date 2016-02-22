#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
We read a FITS file, find the clusters,
and convert their centroid coordinates to WCS coordinates.
Then we display the WCS coordinates on the image,
following the mouse movement.
:Author: LAL npac09 <laudrain@ipno.in2p3.fr>
:Date:   February 2016
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import mylib
import library

# pylint: disable=E1101
# 'numpy' has indeed an 'histogram' member, this error is not relevant

# pylint: disable=R0914
# Only 17 local variables, and the code is already simple enough

# TODO possible upgrade : also display the info 'on_click'. Remove the last text on the screen
def event_handler(fig, header, pixels):
    """
    Event handler
    :param fig: the canvas to draw into
    :param my_wcs: The conversion tool for coordinates
    :param pixels: The image to display
    :return:
    """
    # create a WCS object to make unit conversions
    my_wcs = library.WCS(header)

    def move(event):
        """
        Action on mouse movement
        :param event: the event
        :return:
        """
        if event.xdata >= len(pixels) or event.xdata < 0 \
                or event.ydata >= len(pixels) or event.ydata < 0:
            return
        pads = event.inaxes     #event.inaxes renvoie le pad courant
        text_id = pads.text(event.xdata, event.ydata,
                            "%f, %f" % my_wcs.convert_to_radec(event.xdata, event.ydata),
                            fontsize=14, color='white')
        event.canvas.draw()
        text_id.remove()

    fig.canvas.mpl_connect('motion_notify_event', move)


def main():
    """
    We read a FITS file, find the clusters,
    and convert their centroid coordinates to WCS coordinates.
    Then we display the WCS coordinates on the image,
    following the mouse movement.
    """

    input_file_path = "/Users/npac09/PycharmProjects/npac09/data/specific.fits"
    output_file_path = "/Users/npac09/PycharmProjects/npac09/src/ex4.txt"

    # open file and retrieve data and header
    header, pixels = mylib.open_fits(input_file_path)

    # creation of the histogram from the data
    bin_number = 200
    bin_values, bin_boundaries = np.histogram(pixels.ravel(), bin_number)

    # apply the fit (no need for the amplitude (first parameter))
    _, background, dispersion = mylib.gaussian_fit(bin_boundaries[:-1], bin_values)
    # We define the threshold at 6 standard deviations above the mean bkg value
    threshold = background + (6.0 * dispersion)

    # plot
    fig, pads = plt.subplots()

    # visualization of the image after bkg removal
    pads.imshow(mylib.remove_background(pixels, background, threshold))

    # find the clusters.
    cluster_list, cluster_dico = mylib.find_clusters(header, pixels, threshold)

    # find the maximum-integral cluster
    max_integral_key = mylib.find_max_integral_cluster(cluster_list)

    # call the event handler
    event_handler(fig, header, pixels)

    # display
    plt.show()

    # write result to output file
    try:
        with open(output_file_path, 'w') as output_file:
            output_file.write('right ascension: %.3f, declination: %.3f' \
                              % (cluster_dico[max_integral_key][0].centroid_wcs))

    except IOError:
        print "File not found :", output_file_path
        return 2

    return 0

if __name__ == '__main__':
    sys.exit(main())

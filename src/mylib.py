#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Personal functions
"""

# pylint: disable=E1101
# 'numpy' has indeed an 'exp' member, this error is not relevant

from astropy.io import fits
from scipy.optimize import curve_fit
import numpy as np
import library
import Cluster

##########
### For exercice 1
##########
def open_fits(input_file_path):
    """
    Open a FITS file and retrieve the header and the data of the first block.
    :param input_file_path: FITS file path to be opened
    :return: header, data of the first block [0]
    """
    try:
        with fits.open(input_file_path) as data_blocks:
            data_blocks.info()
            return data_blocks[0].header, data_blocks[0].data

    except IOError:
        print "File not found :", input_file_path
        return 1

##########
### For exercice 2
##########
def gaussian(x, amplitude, mean, sigma):
    """
    compute a gaussian function:
    """
    return amplitude * np.exp(- (x - mean) * (x - mean) / (2 * sigma * sigma))

def gaussian_fit(xdata, ydata):
    """
    Fit a set of data with a gaussian function.
    :param xdata: bin boundaries values
    :param ydata: bin contents (values)
    :return:    The fit parameters array 'fit_param',
                and the covariant matrix 'covariant'.
    """

    # normalization parameters
    m_x = np.float(np.max(xdata))
    m_y = np.float(np.max(ydata))

    # apply the fit, normalize the data to help the fitting program (no need for covariant matrix)
    fit_param, _ = curve_fit(gaussian, \
                       xdata / m_x, \
                       ydata / m_y)

    # get back the un-normalized parameters
    amplitude = fit_param[0] * m_y
    background = fit_param[1] * m_x
    dispersion = fit_param[2] * m_x

    return amplitude, background, dispersion

def remove_background(pixels, background, threshold):
    """
    :param pixels: original image matrix
    :param background: mean value of the gaussian fit on the pixel distribution
    :param threshold:
    :return: an image, similar to 'pixels', with the background removed
    """
    mask = pixels >= background + threshold
    # mask is a 2D-array of booleans, 'True' if value is above bkg
    return mask * (pixels - background)

##########
### For exercice 3
##########
def explore_cluster(pixels_visited, pixels, row, col, threshold):
    """
    The image is assumed to be a matrix
    with first coordinate going from top to bottom
    and second coordinate going from right to left

    :param pixels_visited: boolean matrix of visited pixels (1 = visited)
    :param pixels: original image matrix
    :param row: x coordinate of the seed to begin the search
    :param col: y coordinate of the seed to begin the search
    :param threshold: detection threshold, usually "mean + 6*sigma"
    :return: the list of pixels in the cluster
    """

    # boundary conditions
    if row < 0 or row >= len(pixels) \
            or col < 0 or col >= len(pixels[0]):
        return []
    # if already tested
    elif pixels_visited[row, col]:
        return []
    elif pixels[row, col] < threshold:
        pixels_visited[row, col] = 1  # this pixel has been tested
        return []
    else:
        pixels_visited[row, col] = 1  # this pixel has been tested
        return [(row, col)] + \
               explore_cluster(pixels_visited, pixels, row, col-1, threshold) + \
               explore_cluster(pixels_visited, pixels, row+1, col, threshold) + \
               explore_cluster(pixels_visited, pixels, row, col+1, threshold) + \
               explore_cluster(pixels_visited, pixels, row-1, col, threshold)

def find_clusters(header, pixels, threshold, search_radius=0.003):
    """
    Find all the clusters in a FITS image, given a threshold
    :param header: header of the FITS image
    :param pixels: original image matrix
    :param threshold:
    :return: list of clusters in the image, dictionary of clusters indexed by centroid coordinates
    """
    # We define an array of pixels visited: 1 if visited, 0 elsewise
    pixels_visited = np.zeros_like(pixels)
    cluster_list = []
    cluster_dico = {}
        # access key : string with centroid x and y
        # value : doublet (the cluster, the cluster name (from Simbad request and sorting))

    # WARNING : pixels[row, col]: row corresponds to x and col to y
    for row in range(len(pixels[0])):
        for col in range(len(pixels)):
            if pixels_visited[row, col]:
                continue # If pixel visited, go to next pixel (next step of the loop)
            if pixels[row, col] < threshold:
                pixels_visited[row, col] = 1 # visited
            else: # add the new cluster to the list
                cluster = Cluster.Cluster(explore_cluster(
                    pixels_visited, pixels, row, col, threshold), pixels, header)
                cluster_list.append(cluster)
                # we don't give the name for now
                pixels_visited[row, col] = 1 # visited
    # at this point, the cluster list is build

    # now build the dico
    # we have to build it apart since tuple are non modifiable internally
    for cluster in cluster_list:
        celestial_objects = library.get_objects(cluster.centroid_wcs[0], \
                                                cluster.centroid_wcs[1],
                                                search_radius)
        if not celestial_objects: # empty dictionary = False
            cluster_dico['%f %f' % cluster.centroid] = (cluster, 'Not found')
            continue
        # now, there is at least one name available
        # find the first name in alphabetical order, skipping the 'Unknown'
        first_key = celestial_objects.keys()[0] # initialize
        for key in celestial_objects.keys():
            if celestial_objects[key] == 'Unknown':
                continue
            if key < first_key: # if before in alphabetic order
                first_key = key
        cluster_dico['%f %f' % cluster.centroid] = (cluster, first_key)

    return cluster_list, cluster_dico

def find_max_integral_cluster(cluster_list):
    """
    :param cluster_list: list of cluster objects
    :return: the dictionary key of the cluster with maximal integral
            (string with coordinates of the centroid)
    """
    max_integral = 0
    max_integral_key = ''
    for cluster in cluster_list:
        if cluster.integral > max_integral:
            max_integral = cluster.integral
            max_integral_key = '%f %f' % cluster.centroid
    return max_integral_key

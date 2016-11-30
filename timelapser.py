#!/usr/bin/env python

import sys
import argparse
import os
from os.path import expanduser, normpath
from shutil import copy2
from shutil import move
from glob import glob
from clint.textui import puts, progress, colored, indent
from wand.image import Image
from wand.color import Color
import subprocess


#
# Creating a timelapse from a sequence of images
# The program should be launched in the directory containing all the pictures
#

def get_params(argv):
    """
    Function called to read and parse command line arguments

    Arguments
    ----------
    argv: Command line arguments as passed by sys.argv[1:]

    Returns
    --------
    params: Namespace object returned by `argparse`
        Contains the values for all necessary parameters
        angle, width, height, framerate, crop, vertical

    Possible flags
    ----------------
    -r = alpha ; --rotation = alpha
    -w = width ; --width = width
    -t = height ; --height = height
    -f = framerate ; --framerate = framerate
    -c = crop (?) ; --crop

    Default values
    ---------------
    r = 0 ; w = 1080 ; h = 720 ; f = 7 ; c = ""
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='Folder containing the pictures',
                        default='.')
    parser.add_argument('-e', '--extension', help='File extension to look for',
                        default='jpg')
    parser.add_argument('-r', '--rotation', help='Rotation angle to apply',
                        default=0, type=float)
    parser.add_argument('-w', '--width', help='New width of pictures',
                        default=1080, type=int)
    parser.add_argument('-t', '--height', help='New height of pictures',
                        default=720, type=int)
    parser.add_argument('-f', '--framerate', help='Framerate of the timelapse',
                        default=7, type=int)
    parser.add_argument('-c', '--crop', help='Crop window. Not implemented.')

    params = parser.parse_args(argv)
    params.path = normpath(expanduser(params.path))

    return params


def create_dir(dir_name):
    """
    Create a directory - Fail if impossible (e.g. already exists)

    Argument
    --------
    dirName: str
        Name / path of the new directory
    """
    try:
        os.mkdir(dir_name)
    except:
        sys.exit("Could not create directory " + dir_name)


def check_args(params, image):
    """
    Check/Optimize the parameters retrieved from the command line

    Arguments:
    ---------
    params: Namespace object returned by `argparse`
        Parameters as returned by :py:func:`get_params`
    image: str
        File name of one example image used for the checking

    Return:
    -------
    params: Namespace object
        Eventually updated parameters

    """
    with Image(filename=image) as img:
        native_aspect_ratio = float(img.width) / img.height
        # If image is vertical
        if img.width < img.height:
            puts(colored.green('Pictures are vertical'))
            # Store the desired width for side bars width calculation
            params.tot_width = params.width
            # The width is fixed by the aspect ratio.
            # Black side bars will be added1
            params.width = int(native_aspect_ratio * params.height)
            params.vertical = True
        else:
            params.vertical = False
        # Check that the aspect ratio is respected
        if native_aspect_ratio - (
                    float(params.width) / params.height) < .01:
            puts(colored.green('Aspect ratio is conserved. OK'))
        else:
            puts(colored.yellow('Aspect ratio not conserved.'))
            params.height = int(params.width / native_aspect_ratio)
            with indent(5, quote=colored.yellow('>')):
                puts(colored.yellow(
                    'Height changed to : {}'.format(params.height)))

    return params


def processing_pic(operation, params, pic_list):
    """
    Apply an operation on all the pictures in the 'processed' directory
    according to the parameters retrieved from the command line

    Arguments:
    ----------
    operation: str
        Which operation to perform ('Resizing', 'Rotating')
    params: Namespace object
        Parameters as retrieved from :py:func:`get_params`
    pic_list: list
        List of all the pictures to resize (file names)
    """
    puts(colored.cyan(operation + ' pictures'))
    op_bar = progress.Bar(label=operation, expected_size=len(pic_list))
    # Open and transform all pictures
    for i, pic in enumerate(pic_list):
        with Image(filename=pic) as img:
            if operation == 'Resizing':
                img.resize(params.width, params.height)
            elif operation == 'Rotating':
                img.rotate(params.rotation)
            img.save(filename=pic)
            op_bar.show(i + 1)
    puts('\n')


def side_bars(params, pic_list):
    """
    Add black side bars to vertical pictures

    Arguments:
    ----------
    params: Namespace object
        Parameters as retrieved from :py:func:`get_params`
    picList: list
        List of all the pictures to resize (file names)
    """
    puts(colored.cyan('Adding side bars'))
    sb_bar = progress.Bar(label='Sidebars', expected_size=len(pic_list))
    side_bars_width = int((params.tot_width - params.width) / 2)
    # Open and transform all pictures
    for i, pic in enumerate(pic_list):
        with Image(filename=pic) as img:
            img.border(Color('black'), side_bars_width, 0)
            img.save(filename=pic)
            sb_bar.show(i + 1)
    puts('\n')


if __name__ == "__main__":
    # Parse the command line arguments
    prms = get_params(sys.argv[1:])
    # Pattern to search files
    pattern = "*.{}".format(prms.extension)
    # Get to the proper folder
    os.chdir(prms.path)
    # Check if original and processed folders already exist
    lstDirs = os.listdir('.')
    tidy = 'original' in lstDirs and 'processed' in lstDirs
    # If not, organize the files
    if not tidy:
        puts(colored.cyan('Organizing pictures in different folders'))
        # Create two folders to organize original and processed pictures
        create_dir('original')
        create_dir('processed')
        # Copy pictures to processed folder
        # Get a list of all the images in the folder
        pic_list = glob(pattern)
        copyBar = progress.Bar(label="Organizing files ",
                               expected_size=len(pic_list))
        for i, pic in enumerate(pic_list):
            copy2(pic, "processed")
            # Move pictures to original folder
            move(pic, "original")
            copyBar.show(i + 1)
        puts('\n')
    # Change the current directory to 'processed'
    os.chdir('processed')
    if tidy:
        # Get a list of all the images in the folder
        pic_list = glob(pattern)
    # Check the parameters
    prms = check_args(prms, pic_list[0])
    if not tidy:
        # Resize the pictures
        processing_pic('Resizing', prms, pic_list)
    if prms.rotation != 0:
        # Rotate them
        processing_pic('Rotating', prms, pic_list)

    # If images are vertical then put black rectangles on the side
    if prms.vertical:
        side_bars(prms, pic_list)

    # Assemble the timelapse using mencoder
    tlFilename = 'timelapse_{}x{}_{}fps.avi'.format(
        prms.width, prms.height, prms.framerate)

    # Remove potentially conflicting files if they have the same name
    if os.path.isfile('../' + tlFilename):
        os.remove('../' + tlFilename)
    if os.path.isfile(tlFilename):
        os.remove(tlFilename)

    command = ('mencoder',
               'mf://'+pattern,
               '-mf',
               'type=jpg:w={}:h={}:fps={}'.format(prms.width, prms.height,
                                      prms.framerate),
               '-ovc',
               'lavc',
               '-lavcopts',
               'vcodec=mjpeg',
               '-oac',
               'copy',
               '-o',
               tlFilename)
    puts(colored.cyan('Assembling the time lapse'))
    subprocess.check_call(command)

    move(tlFilename, '..')

    puts(colored.green('\nAll Done!\n'))

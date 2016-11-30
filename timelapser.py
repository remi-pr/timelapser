#!/usr/bin/env python

import sys
import getopt
import os
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
    params: Dictionary containing values for all necessary parameters
            angle, width, height, framerate, crop, vertical

    Possible flags
    ----------------
    -r = alpha ; --rotation = alpha
    -w = width ; --width = width
    -h = height ; --height = height
    -f = framerate ; --framerate = framerate
    -c = crop (?) ; --crop

    Default values
    ---------------
    r = 0 ; w = 1080 ; h = 720 ; f = 7 ; c = ""
    """
    # Default values for all parameters
    params = {
        'ext': 'jpg',
        'angle': 0,
        'width': 1080,
        'height': 720,
        'framerate': 7,
        'crop': ""
    }

    try:
        # Get all the valid arguments from the command line
        opts, args = getopt.getopt(argv, "e:r:w:h:f:c:v",
                                   ["extension=", "rotation=", "width=",
                                    "height=", "framerate=", "crop=",
                                    "vertical"])
    except:
        # In case one argument is not valid or if a value is missing
        # usage()
        sys.exit(2)
    # Go through all the options and get the corresponding values
    for opt, arg in opts:
        if opt in ("-r", "--rotation"):
            params['angle'] = int(arg)
        elif opt in ("-e", "--extension"):
            params['ext'] = str(arg)
        elif opt in ("-w", "--width"):
            params['width'] = float(arg)
        elif opt in ("-h", "--height"):
            params['height'] = float(arg)
        elif opt in ("-f", "--framerate"):
            params['framerate'] = int(arg)
        elif opt in ("-c", "--crop"):
            params['crop'] = arg
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
    """ Check/Optimize the parameters retrieved from the command line

    Arguments:
    ---------
    params: dict
        Dictionary of parameters as returned by getParams
    image: str
        File name of one example image used for the checking

    Return:
    -------
    params: dict
        Eventually updated dictionary

    """
    with Image(filename=image) as img:
        native_aspect_ratio = float(img.width) / img.height
        # If image is vertical
        if img.width < img.height:
            puts(colored.green('Pictures are vertical'))
            # Store the desired width for side bars width calculation
            params.update({'totWidth': params['width']})
            # The width is fixed by the aspect ratio.
            # Black side bars will be added1
            params['width'] = native_aspect_ratio * params['height']
            params.update({'vertical': True})
        else:
            params.update({'vertical': False})
        # Check that the aspect ratio is respected
        if native_aspect_ratio - (
                    float(params['width']) / params['height']) < .01:
            puts(colored.green('Aspect ratio is conserved. OK'))
        else:
            puts(colored.yellow('Aspect ratio not conserved.'))
            params['height'] = params['width'] / native_aspect_ratio
            with indent(5, quote=colored.yellow('>')):
                puts(colored.yellow(
                    'Height changed to : ' + str(params['height'])))

    return params


def processing_pic(operation, params, pic_list):
    """
    Apply an operation on all the pictures in the 'processed' directory
    according to the parameters retrieved from the command line

    Arguments:
    ----------
    operation: str
        Which operation to perform ('Resizing', 'Rotating')
    params: dict
        Dictionary of parameters as retrieved from getParams
    pic_list: list
        List of all the pictures to resize (file names)
    """
    puts(colored.cyan(operation + ' pictures'))
    op_bar = progress.Bar(label=operation, expected_size=len(pic_list))
    # Open and transform all pictures
    for i, pic in enumerate(pic_list):
        with Image(filename=pic) as img:
            if operation == 'Resizing':
                img.resize(int(params['width']), int(params['height']))
            elif operation == 'Rotating':
                img.rotate(params['angle'])
            img.save(filename=pic)
            op_bar.show(i + 1)
    puts('\n')


def side_bars(params, pic_list):
    """
    Add black side bars to vertical pictures

    Arguments:
    ----------
    params: Dictionary of parameters as retrieved from getParams
    picList: List of all the pictures to resize (file names)
    """
    puts(colored.cyan('Adding side bars'))
    sb_bar = progress.Bar(label='Sidebars', expected_size=len(pic_list))
    side_bars_width = int((params['totWidth'] - params['width']) / 2)
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
        picList = glob("*.jpg")
        copyBar = progress.Bar(label="Organizing files ",
                               expected_size=len(picList))
        for i, pic in enumerate(picList):
            copy2(pic, "processed")
            # Move pictures to original folder
            move(pic, "original")
            copyBar.show(i + 1)
        puts('\n')
    # Change the current directory to 'processed'
    os.chdir('processed')
    if tidy:
        # Get a list of all the images in the folder
        picList = glob("*.jpg")
    # Check the parameters
    prms = check_args(prms, picList[0])
    if not tidy:
        # Resize the pictures
        processing_pic('Resizing', prms, picList)
    if prms['angle'] != 0:
        # Rotate them
        processing_pic('Rotating', prms, picList)

    # If images are vertical then put black rectangles on the side
    if prms['vertical']:
        side_bars(prms, picList)

    # Assemble the timelapse using mencoder
    tlFilename = 'timelapse_' + str(prms['width']) + 'x' + str(
        prms['height']) + '_' + str(prms['framerate']) + 'fps' + '.avi'

    # Remove potentially conflicting files if they have the same name
    if os.path.isfile('../' + tlFilename):
        os.remove('../' + tlFilename)
    if os.path.isfile(tlFilename):
        os.remove(tlFilename)

    command = ('mencoder',
               'mf://*.JPG',
               '-mf',
               'type=jpg:w=' + str(prms['width']) + ':h=' + str(
                   prms['height']) + ':fps=' + str(prms['framerate']),
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

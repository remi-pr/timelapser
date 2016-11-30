# Timelapser

This little Python script assembles a collection of pictures into a timelapse 
movie. It takes care of some preprocessing (resizing, rotation, adding black 
borders to vertical pictures...) and then produces a video.

## Requirements

**Timelapser** depends on :
+ **Imagemagick** and its Python bindings 
[**Wand**](http://docs.wand-py.org/en/0.4.4/).
+ [**clint**](https://github.com/kennethreitz/clint) for an awesome 
commandline interface
+ **mencoder** for the video creation

## Documentation
**timelapser** is to be used at the command line by running:
```
python timelapser.py path/to/pictures
```
Different flags can be used to set some options:
```
-r --rotation=ALPHA
    Set a rotation angle applied to all pictures before assembling 
    
-w --width=WIDTH
    Set a new width. If height is not specified, then the original aspect 
    ratio is conserved. By default: 1080

-t --height=HEIGHT
    Set a new height. If width is not specified, preserve the original aspect 
    ratio. Is ignored if width and height are specified and violate the 
    aspect ratio too much. By default: 720

-f --framerate=FRAMERATE
    Set the video framerate

-h 
    Output help and exit

```
The code is extensively commented and documented but not tested (yet?).

## License

MIT License

    Copyright (c) 2016, Rémi Proville
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

## Contribute

If you'd like to contribute, simply fork the repository, commit your changes
to the master branch (or branch off of it), and send a pull request.

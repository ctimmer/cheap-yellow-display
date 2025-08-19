#
################################################################################
# The MIT License (MIT)
#
# Copyright (c) 2025 Curt Timmerman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
################################################################################
#
## SpriteHandler - extract raw images from raw sprite sheets for displays
#
# Notes:
#   o Images must contain only pixel data in RGB565 (16bit) format,
#     no extra information
#   o All images must be the same size
#   o Images are accessed via an index
#
# Example usage:
'''
#display = 480x320 display

raw_image = SpriteHandler ()
raw_image.load_raw_file ("tarot240x300.raw" ,
                        image_width = 40 ,
                        image_height = 75 ,
                        image_rows = 4)
#raw_image.buffer_images ()
#raw_image.store_all_images ("tarot")
for img_idx in range (0,11) :
    display.draw_sprite (raw_image[img_idx], x=5 + (img_idx * 42), y=10,w=40,h=75)
for img_idx in range (0,11) :
    display.draw_sprite (raw_image[img_idx+11], x=5 + (img_idx * 42), y=90,w=40,h=75)
'''

class SpriteHandler :
    def __init__ (self) :
        self.file_path = None        # Sprite image file input
        self.buffer = None           # Sprite images buffer
        self.image_count = 0         # number of images in buffer
        self.image_rows = None       # number of image rows
        self.image_columns = None    # number of image columns
        self.image_width = None      # individual image width
        self.image_height = None     # individual image height
        self.image_pixel_size = None # 1,2,4 bytes per pixel
        self.image_size = None       # image_width * image_height * 2
        self.image_buffers = None    # optional - stores individual sprite images
        self.index_dict = {}
        self.location_dict = {}

    ## load_row_sprite loads buffer from raw_image, saves image information
    def load_raw_sprite (self ,
                        sprite_buffer ,
                        image_width = None ,
                        image_height = None ,
                        image_rows = 1 ,
                        image_pixel_size = 2 ,
                        variable_size = False ,
                        buffer_width = None) :
        self.buffer = sprite_buffer
        self.image_count = 0
        self.image_pixel_size = image_pixel_size
        self.buffer_byte_width = None
        if variable_size :
            self.buffer_byte_width = buffer_width * self.image_pixel_size
            self.image_rows = 1
            self.image_columns = buffer_width
            return
        
        buf_len = len (sprite_buffer)
        self.image_buffers = None
        self.image_width = image_width
        self.image_height = image_height
        self.image_size = image_width * image_height * self.image_pixel_size
        if buf_len % self.image_size != 0 :
            #raise RuntimeError (f"raw_sprite: buffer length error ({buf_len})")
            return None
        self.image_count = buf_len // self.image_size
        self.image_rows = image_rows
        self.image_columns = self.image_count // self.image_rows
        self.buffer_byte_width = image_width * self.image_columns * self.image_pixel_size
 
    ## load_raw_file - reads raw sprite file and loads it to the buffer
    def load_raw_file (self ,
                        file_path ,
                        image_width = None ,
                        image_height= None ,
                        image_rows = 1 ,
                        image_pixel_size = 2 ,
                        variable_size = False ,
                        buffer_width = None) :
        #print (file_path)
        try :
            with open (file_path, "rb") as raw_file :
                buffer = raw_file.read ()
        except Exception as e :
            print (file_path, e)
            return
        self.file_path = file_path
        self.load_raw_sprite (bytes (buffer),
                                image_width,
                                image_height,
                                image_rows ,
                                image_pixel_size ,
                                variable_size,
                                buffer_width)

    ## __getitem__ returns the indexed sprite image
    def __getitem__(self, index) :
        if self.image_count <= 0 :
            return None
        if index < 0 \
        or index >= self.image_count :
            return None
        if self.image_buffers is None :
            return self.get_index_sprite (index)  # return image from buffer
        else :
            return self.image_buffers [index]  # return buffered image

    #def set_sprite_byte_width (self, sprite_byte_width) :
    #    self.buffer_byte_width = sprite_byte_width * self.image_pixel_size
    ## get_sprite
    def get_sprite (self,
                    x_pos ,
                    y_pos ,
                    width ,
                    height) :
        #print ("get_sprite:", x_pos,y_pos,width,height)
        sprite_image = bytearray (width * height * self.image_pixel_size) # returned image
        image_width = width * self.image_pixel_size
        buffer_offset = y_pos * image_width * self.image_columns
        buffer_offset += (x_pos * self.image_pixel_size)
        sprite_image_offset = 0
        for img_idx in range (0, height) :
            sprite_image [sprite_image_offset:(sprite_image_offset + image_width)] \
                = self.buffer [buffer_offset:(buffer_offset + image_width)]
            buffer_offset += self.buffer_byte_width     # Next image row in buffer
            sprite_image_offset += image_width          # Next sprite image row
        return bytes (sprite_image)

    ## get_sprite_inverted
    def get_sprite_inverted (self,
                            x_pos ,
                            y_pos ,
                            width ,
                            height) :
        #print ("get_sprite_inverted:", x_pos ,y_pos ,width ,height)
        sprite_image = bytearray (width * height * self.image_pixel_size) # returned image
        image_width = width * self.image_pixel_size
        buffer_offset = (y_pos + (height - 1)) * image_width * self.image_columns
        buffer_offset += (x_pos * self.image_pixel_size)
        sprite_image_offset = ((width) - 1) * self.image_pixel_size
        for img_idx in range (0, height) :
            buffer_pos = buffer_offset
            for _ in range (width) :
                for _ in range (self.image_pixel_size) :
                    sprite_image [sprite_image_offset] \
                        = self.buffer [buffer_pos] # + color_idx]
                    buffer_pos += 1
                    sprite_image_offset -= 1
                #sprite_image_offset -= self.image_pixel_size
            buffer_offset -= self.buffer_byte_width     # Previous image row in buffer
            sprite_image_offset += (width * 2) * self.image_pixel_size # next sprite row
        return bytes (sprite_image)

    ## index_to_xy - convert sprite index to x,y position in buffer
    def index_to_xy (self, index) :
        x_pos = (self.image_width * index) % (self.image_width * self.image_columns)
        y_pos = (index // self.image_columns) * self.image_height
        #print (f"i_to_xy:idx={index} x={x_pos} y={y_pos}")
        return x_pos, y_pos

    def get_index_sprite_data (self, index) :
        x, y = self.index_to_xy (index)
        return {
            "x" : x ,
            "y" : y ,
            "w" : self.image_width ,
            "h" : self.image_height
            }
    ## get_index_sprite - return image via index
    def get_index_sprite (self, index, inverted = False) :
        if self.image_count <= 0 :
            return None
        if index < 0 \
        or index >= self.image_count :
            return None
        if self.image_buffers is None :
            x_pos, y_pos = self.index_to_xy (index)
            if not inverted :
                return self.get_sprite (x_pos, y_pos, self.image_width, self.image_height)
            else :
                return self.get_sprite_inverted (x_pos, y_pos, self.image_width, self.image_height)
        else :
            return self.image_buffers [index]  # return buffered image
    def load_index_id (self, idx_id, index) :
        self.index_dict [idx_id] = index
    def get_index_id_sprite (self, idx_id, inverted = False) :
        if idx_id not in self.index_dict :
            return None
        return self.get_index_sprite (self.index_dict [idx_id], inverted=inverted)
    def load_location_id (self, loc_id, x, y, w, h) :
        self.location_dict [loc_id] = [x, y, w, h]
    def get_location_id_sprite (self, loc_id, inverted = False) :
        if loc_id not in self.location_dict :
            return None
        if inverted :
            return self.get_sprite_inverted (*self.location_dict [loc_id])
        else :
            return self.get_sprite (*self.location_dict [loc_id])

    ## buffer_images extact all images to array
    # your device may not have enough memory to use this function
    # running garbage collect is recomended after calling
    def buffer_images (self, keep_image_buffer = False):
        if self.buffer is None :
            return
        image_buffers = []
        for index in range (0, self.image_count) :
            image_buffers.append (self.get_index_sprite (index))
        if not keep_image_buffer :
            self.buffer = None              # No longer needed
        self.image_buffers = image_buffers
                          

    ## store_all_images extract all images to files
    def store_all_images (self, path_base = "sprite_") :
        for index in range (0, self.image_count) :
            raw_image = self.__getitem__ (index)
            with open (f"{path_base}{index:04d}.raw", "wb") as raw_file :
                raw_file.write (raw_image)

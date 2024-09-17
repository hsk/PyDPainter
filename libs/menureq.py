#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os.path, colorsys

import libs.gadget
from libs.gadget import *

from libs.prim import *

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

config = None

def menureq_set_config(config_in):
    global config
    config = config_in

#Read in directory and return sorted list
def get_dir(path):
    filelist = []
    dirlist = [".. (parent dir)"]
    try:
        with os.scandir(path) as it:
            for entry in it:
                if not entry.name.startswith('.'):
                    if entry.is_file():
                        filelist.append(entry.name)
                    elif entry.is_dir():
                        dirlist.append("\x92\x93" + entry.name)
        filelist.sort(key=str.casefold)
        dirlist.sort(key=str.casefold)
    except FileNotFoundError:
        dirlist = ["<Not found>"]
    except:
        dirlist = ["<Error>"]
    return dirlist + filelist


def get_type(filename, filetype_list):
    retval = "type"
    ext = ""
    matches = re.search(r"\.([^.]+)$", filename)
    if matches:
        ext = matches.group(1).upper()
        if not filetype_list is None and ext in filetype_list[:,0]:
            retval = ext
        else:
            ext = ""
    return (ext, ("%-4s\x98" % (retval)))

def pick_file_type(screen, req, file_typeg, ext, filetype_list):
    retval = -1
    req_backup = screen.copy()
    rx,ry,rw,rh = file_typeg.rect
    fontx = req.font.xsize
    fonty = req.font.ysize
    lx = fontx*2
    ly = ry-(fonty*len(filetype_list)+fonty//2)
    lw = rx+rw-lx
    lh = ry-ly
    pickg = PPtypelist(Gadget.TYPE_CUSTOM, "#", (lx,ly,lw,lh), filetype_list=filetype_list)
    pickg.value = -1
    req.gadgets.append(pickg)
    req.draw(screen)
    config.recompose()

    running = 1
    wait_for_mouseup = 0

    while running:
        event = config.xevent.wait()
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            x,y = req.mouse_pixel_mapper(event)
            if pickg.pointin((x,y), pickg.screenrect):
                retval = pickg.value
            running = 0
        else:
            gevents = req.process_event(screen, event)

        if event.type == KEYDOWN:
            running = 0

        req.draw(screen)
        config.recompose()

    req.gadgets.remove(pickg)
    screen.blit(req_backup, (0,0))
    config.recompose()
    return retval

class PPtypelist(Gadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None, filetype_list=None):
        self.filetype_list = filetype_list
        super(PPtypelist, self).__init__(type, label, rect, value, maxvalue, id)
        
    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        px = font.xsize//8
        py = font.ysize//8
        self.offsetx = xo
        self.offsety = yo
        fontx = font.xsize
        fonty = font.ysize
        self.fontw = fontx
        self.fonth = fonty
        self.screenrect = (x+xo,y+yo,w,h)
        srx,sry,srw,srh = self.screenrect

        if self.type == Gadget.TYPE_CUSTOM:
            if not self.need_redraw:
                return

            self.need_redraw = False

            if self.label == "#":
                screen.set_clip(self.screenrect)
                screen.fill(bgcolor)
                pygame.draw.rect(screen, fgcolor, self.screenrect, 0)
                pygame.draw.rect(screen, bgcolor, (srx+px,sry+py,srw-px-px,srh-py-py), 0)
                for i in range(len(self.filetype_list)):
                    (label,desc) = self.filetype_list[i]
                    if self.value == i:
                        bg = fgcolor
                        fg = bgcolor
                    else:
                        bg = bgcolor
                        fg = fgcolor
                    font.blitstring(screen, (x+xo+px+px,y+yo+py+py+i*fonty), "%-5s%-22s"%(label,desc), fg, bg)
                pygame.draw.rect(screen, hcolor, (x+xo,y+yo, w-px, py), 0)
                pygame.draw.rect(screen, hcolor, (x+xo,y+yo, px, h), 0)
                
        else:
            super(PPtypelist, self).draw(screen, font, offset)

    def process_event(self, screen, event, mouse_pixel_mapper):
        ge = []
        x,y = mouse_pixel_mapper()
        g = self
        gx,gy,gw,gh = g.screenrect
        py = g.fonth // 8

        #disabled gadget
        if not g.enabled:
            return ge

        if self.type == Gadget.TYPE_CUSTOM:
            if g.pointin((x,y), g.screenrect):
                if g.label == "#":
                    g.value = (y-gy-py-py)//g.fonth
                    g.need_redraw = True
        return ge

def ask_dir_req(screen):
    # save previous requestor
    prr = config.pixel_req_rect
    prc = config.pixel_req_canvas.copy()
    oldcursor = config.cursor.shape
    config.cursor.shape = config.cursor.NORMAL
    retval = ""

    req = str2req("Create Directory", """

Dir Name: ______________________

[Cancel][OK]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    dirnameg = req.gadget_id("10_1")
    dirnameg.value = ""
    dirnameg.maxvalue = 255

    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    retval = dirnameg.value
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0 

        if not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    # restore previous requestor
    config.pixel_req_rect = prr
    config.pixel_req_canvas.blit(prc, (0,0))
    config.cursor.shape = oldcursor

    return retval

def file_req(screen, title, action_label, filepath, filename, filetype_list=None):
    if filetype_list is None:
        has_type = False
    else:
        has_type = True
    req = str2req(title, """
Path:_________________________
############################^^
############################@@
############################@@
############################@@
############################@@
############################@@
############################@@
############################@@
############################@@
############################^^
File:___________________%s
[%s][Cancel]  [Make Dir]
"""%("[type\x98]" if has_type else "______", action_label), "#^@", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=ListGadget, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    retval = ""
    ext = ""

    #list items
    list_itemsg = req.gadget_id("0_1")
    list_itemsg.items = get_dir(filepath)
    list_itemsg.top_item = 0
    list_itemsg.value = list_itemsg.top_item

    #list up/down arrows
    list_upg = req.gadget_id("28_1")
    list_upg.value = -1
    list_downg = req.gadget_id("28_10")
    list_downg.value = 1

    #list slider
    list_sliderg = req.gadget_id("28_2")
    list_sliderg.value = list_itemsg.top_item

    #all list item gadgets
    listg_list = [list_itemsg, list_upg, list_downg, list_sliderg]
    list_itemsg.listgadgets = listg_list
    list_upg.listgadgets = listg_list
    list_downg.listgadgets = listg_list
    list_sliderg.listgadgets = listg_list

    #File path
    file_pathg = req.gadget_id("5_0")
    file_pathg.value = filepath
    file_pathg.maxvalue = 255

    #File name
    filename = os.path.basename(filename)
    file_nameg = req.gadget_id("5_11")
    file_nameg.value = filename
    file_nameg.maxvalue = 255

    #File type
    if has_type:
        file_typeg = req.gadget_id("24_11")
    else:
        # Create dummy gadget
        file_typeg = Gadget(Gadget.TYPE_BOOL, "", (0,0,0,0))

    #Initialize file type
    ext, file_typeg.label = get_type(filename, filetype_list)
    file_typeg.need_redraw = True

    #take care of non-square pixels
    fontmult = 1
    if config.aspectX != config.aspectY:
        fontmult = 2

    req.draw(screen)
    config.recompose()

    last_click_ms = pygame.time.get_ticks()

    running = 1
    wait_for_mouseup = 0

    while running or wait_for_mouseup:
        string_enter = False
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == action_label:
                    if file_nameg.value != "":
                        retval = os.path.join(filepath, file_nameg.value)
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0
                elif ge.gadget.label == "Make Dir":
                    newdir = ask_dir_req(screen)
                    if newdir != "":
                        newdirpath = os.path.join(filepath, newdir)
                        try:
                            os.mkdir(newdirpath)
                            list_itemsg.items = get_dir(filepath)
                            list_itemsg.need_redraw = True
                            list_sliderg.need_redraw = True
                        except:
                            libs.menus.io_error_req("Directory Error", "Unable to create directory:\n%s", newdirpath)
                            running = 0
                elif ge.gadget == file_typeg:
                    picki = pick_file_type(screen, req, file_typeg, ext, filetype_list)
                    if picki >=0 and picki < len(filetype_list):
                        filename = file_nameg.value
                        if filename != "":
                            if filename.find(".") >= 0:
                                filename = re.sub(r"\.[^.]*$", "."+filetype_list[picki][0].lower(), filename)
                            else:
                                filename += "." + filetype_list[picki][0].lower()
                        file_nameg.value = filename
                        file_nameg.need_redraw = True
                    ext, file_typeg.label = get_type(filename, filetype_list)
                    file_typeg.need_redraw = True
            if ge.gadget.type == Gadget.TYPE_STRING:
                if ge.type == ge.TYPE_GADGETUP and ge.gadget == file_pathg:
                    filepath = file_pathg.value
                    list_itemsg.items = get_dir(filepath)
                    list_itemsg.top_item = 0
                    list_itemsg.value = list_itemsg.top_item
                    list_itemsg.need_redraw = True
                    list_sliderg.need_redraw = True
                if ge.type == ge.TYPE_GADGETUP and event.type == KEYDOWN and event.key == K_RETURN:
                    string_enter = True
                ext, file_typeg.label = get_type(file_nameg.value, filetype_list)
                file_typeg.need_redraw = True

        if not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            if event.type == MOUSEBUTTONDOWN and event.button == 1 and list_itemsg.pointin(config.get_mouse_pixel_pos(event), list_itemsg.screenrect):
                filename = list_itemsg.items[list_itemsg.value]
                if len(filename) > 2 and (filename[0:2] == "\x92\x93" or filename[0:2] == ".."):
                    if filename[0:2] == "\x92\x93":
                        filepath = os.path.join(filepath, filename[2:])
                    elif filename[0:2] == "..":
                        filepath = os.path.abspath(os.path.join(filepath, ".."))
                    list_itemsg.items = get_dir(filepath)
                    list_itemsg.top_item = 0
                    list_itemsg.value = list_itemsg.top_item
                    list_itemsg.need_redraw = True
                    file_pathg.value = filepath
                    file_pathg.need_redraw = True
                    list_sliderg.need_redraw = True
                    file_typeg.need_redraw = True
                else:
                    file_nameg.value = filename
                    file_nameg.need_redraw = True
                    ext, file_typeg.label = get_type(filename, filetype_list)
                    file_typeg.need_redraw = True
                    if pygame.time.get_ticks() - last_click_ms < 500:
                        if file_nameg.value != "":
                            retval = os.path.join(filepath, file_nameg.value)
                        running = 0
                        wait_for_mouseup = 1
                    else:
                        last_click_ms = pygame.time.get_ticks()
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                wait_for_mouseup = 0
            elif event.type == KEYDOWN:
                if event.key in [K_DOWN, K_UP, K_PAGEDOWN, K_PAGEUP]:
                    filename = list_itemsg.items[list_itemsg.value]
                    if len(filename) > 2 and (filename[0:2] == "\x92\x93" or filename[0:2] == ".."):
                        file_nameg.value = ""
                        ext, file_typeg.label = get_type("", filetype_list)
                    else:
                        file_nameg.value = filename
                        ext, file_typeg.label = get_type(filename, filetype_list)

                    file_nameg.state = 0
                    file_nameg.need_redraw = True
                    file_typeg.need_redraw = True
                elif event.key == K_RETURN and list_itemsg.items[0][0] != "<" and not string_enter:
                    filename = list_itemsg.items[list_itemsg.value]
                    if len(filename) > 2 and (filename[0:2] == "\x92\x93" or filename[0:2] == ".."):
                        if filename[0:2] == "\x92\x93":
                            filepath = os.path.join(filepath, filename[2:])
                        elif filename[0:2] == "..":
                            filepath = os.path.abspath(os.path.join(filepath, ".."))
                        list_itemsg.items = get_dir(filepath)
                        list_itemsg.top_item = 0
                        list_itemsg.value = list_itemsg.top_item
                        list_itemsg.need_redraw = True
                        file_pathg.value = filepath
                        file_pathg.need_redraw = True
                        list_sliderg.need_redraw = True
                    else:
                        if file_nameg.value != "":
                            retval = os.path.join(filepath, file_nameg.value)
                        running = 0

            req.draw(screen)
            config.recompose()

    config.filepath = filepath

    config.pixel_req_rect = None
    config.recompose()

    return retval


def screen_format_req(screen, new_clicked=False):
    req = str2req("Choose Screen Format", """
                     Number of
      Format:         Colors:
[Lo-Res     000x000] [  2][ 32]
[Med-Res    000x000] [  4][ 64]
[Interlace  000x000] [  8][128]
[Hi-Res     000x000] [ 16][256]
                      Out of:
[NTSC~PAL~VGA]       [4096~16M]

Resize Page: [Yes~No]

[Cancel][OK][Make Default]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)

    display_names = ["VGA","NTSC","PAL"]

    #Get PAL/NTSC from current display mode
    global aspect
    if config.display_mode & config.MONITOR_ID_MASK == config.PAL_MONITOR_ID:
        aspect = 2
    elif config.display_mode & config.MONITOR_ID_MASK == config.NTSC_MONITOR_ID:
        aspect = 1
    else:
        aspect = 0

    #Get color depth (16 = 4096 colors and 256 = 16M colors)
    global cdepth
    cdepth = config.color_depth

    #Get bitplane depth from current number of colors
    global bdepth
    bdepth = int(math.log(config.NUM_COLORS,2))

    #Gather bitplane depth gadgets and sort in numeric order
    gDepth = []
    for g in req.gadgets:
        if g.label.lstrip() in ['2','4','8','16','32','64','128','256']:
            gDepth.append(g)
    gDepth.sort(key=lambda g: g.label)

    #Gather NTSC/PAL gadgets
    gNTSC = req.gadget_id("0_7")
    gPAL = req.gadget_id("5_7")
    gVGA = req.gadget_id("9_7")

    #Gather (OCS)ECS/AGA gadgets
    g12bit = req.gadget_id("21_7")
    g24bit = req.gadget_id("26_7")

    #Get resolution from current screen mode
    modes = config.display_info.get_display(display_names[aspect])
    res = 0
    while modes[res].mode_id != config.display_mode & ~config.MODE_EXTRA_HALFBRIGHT:
        res += 1

    #Gather screen mode gadgets
    gres = []
    for g in req.gadgets:
        if re.search(r'\dx\d\d\d$', g.label):
            gres.append(g)

    gDepth[bdepth-1].state = 1

    #Gather page resize gadgets
    resize_page = False
    gResize = [None, None]
    gResize[1] = req.gadget_id("13_9") #Yes
    gResize[0] = req.gadget_id("17_9") #No
    if new_clicked:
        gResize[0].enabled = False
        gResize[1].enabled = False

    for i in range(0,2):
        gResize[i].state = (resize_page == (i == 1))
        gResize[i].need_redraw = True

    def apply_cdepth():
        if cdepth == 16:
            g12bit.state = 1
            gDepth[5].label = "EHB"
            gDepth[5].need_redraw = True
            gDepth[6].enabled = False
            gDepth[6].need_redraw = True
            gDepth[7].enabled = False
            gDepth[7].need_redraw = True
        else:
            g24bit.state = 1
            gDepth[4].enabled = True
            gDepth[4].need_redraw = True
            gDepth[5].enabled = True
            gDepth[5].need_redraw = True
            gDepth[5].label = " 64"
            gDepth[5].need_redraw = True
            gDepth[6].enabled = True
            gDepth[6].need_redraw = True
            gDepth[7].enabled = True
            gDepth[7].need_redraw = True

    def apply_aspect():
        global cdepth
        if aspect == 0:
            gVGA.state = 1
            g12bit.enabled = False
            g12bit.need_redraw = True
            if cdepth == 16:
                cdepth = 256
                apply_cdepth()
        elif aspect == 1:
            gNTSC.state = 1
            g12bit.enabled = True
            g12bit.need_redraw = True
        else:
            gPAL.state = 1
            g12bit.enabled = True
            g12bit.need_redraw = True


        modes = config.display_info.get_display(display_names[aspect])
        i=0
        for g in gres:
            g.label = "%-10s%4dx%d" % (modes[i].name, modes[i].x, modes[i].y)
            g.need_redraw = True
            i += 1

    apply_aspect()
    apply_cdepth()

    def apply_bdepth():
        gDepth[bdepth-1].state = 1
        gDepth[bdepth-1].need_redraw = True

    def apply_mode():
        global bdepth
        #Apply limits to screen mode/bitplane depth
        if cdepth == 16 and res in [1,3]:
            if bdepth > 4:
                bdepth = 4
                apply_bdepth()
            gDepth[4].enabled = False
            gDepth[4].need_redraw = True
            gDepth[5].enabled = False
            gDepth[5].need_redraw = True
        elif cdepth == 16 and res in [0,2]:
            if bdepth > 6:
                bdepth = 6
                apply_bdepth()
            gDepth[4].enabled = True
            gDepth[4].need_redraw = True
            gDepth[5].enabled = True
            gDepth[5].need_redraw = True
        gres[res].state = 1

    apply_mode()

    def get_top_colors(num_colors):
        surf_array = pygame.surfarray.pixels2d(config.pixel_canvas)
        #find unique color indexes and counts of color indexes in pic
        unique_colors, counts_colors = np.unique(surf_array, return_counts=True)
        surf_array = None
        #put counts and color indexes into matrix together into histogram
        hist_array = np.asarray((unique_colors, counts_colors)).transpose()
        #print(hist_array)
        #sort histogram descending by frequency
        sorted_hist_array = hist_array[np.argsort(-hist_array[:, 1])]
        #print(sorted_hist_array)
        #take first num_colors indexes
        colorlist = np.sort(sorted_hist_array[0:num_colors, 0])
        #make sure to preserve color 0
        if colorlist[0] != 0:
            colorlist = np.sort(sorted_hist_array[0:num_colors-1, 0])
            colorlist = np.insert(colorlist, 0, 0)
        #print(colorlist)
        return colorlist

    def get_top_pal(pal, colorlist, num_colors, halfbright):
        num_top_colors = num_colors
        if halfbright:
            num_top_colors = 32

        #assign top colors to new palette
        newpal = []
        for i in range(0,num_top_colors):
            if i < len(colorlist):
                newpal.append(pal[colorlist[i]])
            else:
                newpal.append(pal[i])

        #adjust halfbright colors
        if halfbright:
            for i in range(0,32):
                newpal.append(((newpal[i][0] & 0xee) // 2,
                               (newpal[i][1] & 0xee) // 2,
                               (newpal[i][2] & 0xee) // 2))

        #fill in upper palette with background color
        for i in range(num_colors,256):
            newpal.append(newpal[0])

        return newpal

    def get_max_color_index():
        max_color_index = 0
        for y in range(config.pixel_canvas.get_height()):
            for x in range(config.pixel_canvas.get_width()):
                color_index = config.pixel_canvas.get_at_mapped((x,y))
                if max_color_index < color_index:
                    max_color_index = color_index
        return max_color_index

    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()
    req.draw(screen)
    config.recompose()

    running = 1
    reinit = False
    ok_clicked = False
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        for ge in gevents:
            if ge.gadget == gNTSC:
                aspect = 1
                apply_aspect()
            elif ge.gadget == gPAL:
                aspect = 2
                apply_aspect()
            elif ge.gadget == gVGA:
                aspect = 0
                apply_aspect()
            elif ge.gadget in gres:
                for i in range(len(gres)):
                    if ge.gadget == gres[i]:
                        res = i
                apply_mode()
            elif ge.gadget in gDepth:
                for i in range(len(gDepth)):
                    if ge.gadget == gDepth[i]:
                        bdepth = i+1
            elif ge.gadget == g12bit:
                cdepth = 16
                apply_cdepth()
                apply_mode()
            elif ge.gadget == g24bit:
                cdepth = 256
                apply_cdepth()
                apply_mode()
            elif ge.gadget in gResize:
                resize_page = (gResize.index(ge.gadget) == 1)
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label in ["OK","Make Default"] and not req.has_error():
                    ok_clicked = True
                    num_colors = 2**bdepth
                    if bdepth == 6 and cdepth == 16:
                        halfbright = True
                    else:
                        halfbright = False

                    if new_clicked and config.anim.num_frames > 1:
                        #Get rid of animation
                        config.anim = libs.animation.Animation()

                    config.color = 1
                    config.bgcolor = 0

                    for frame_no in config.anim:
                        if new_clicked:
                            reinit = True
                        elif num_colors < config.NUM_COLORS:
                            #reduce palette to highest frequency color indexes
                            reinit = False

                            num_top_colors = num_colors
                            if halfbright:
                                num_top_colors = 32

                            if get_max_color_index() < num_colors:
                                config.truepal = config.truepal[0:num_colors]
                                config.pal = config.pal[0:num_colors]
                            else:
                                colorlist = get_top_colors(num_top_colors)

                                newpal = get_top_pal(config.pal, colorlist, num_colors, halfbright)

                                #convert colors to reduced palette using blit
                                new_pixel_canvas = pygame.Surface((config.pixel_width, config.pixel_height),0,8)
                                new_pixel_canvas.set_palette(newpal)
                                new_pixel_canvas.blit(config.pixel_canvas, (0,0))

                                #substitute new canvas for the higher color one
                                config.pixel_canvas = new_pixel_canvas
                                config.truepal = get_top_pal(config.truepal, colorlist, num_colors, halfbright)[0:num_colors]
                                config.truepal = config.quantize_palette(config.truepal, cdepth)
                                config.pal = list(config.truepal)
                                config.pal = config.unique_palette(config.pal)

                            config.backuppal = list(config.pal)
                            config.pixel_canvas.set_palette(config.pal)
                            for frame in config.anim.frame:
                                frame.is_pal_key = True
                            config.anim.global_palette = False
                        elif num_colors == config.NUM_COLORS:
                            reinit = False
                        elif num_colors > config.NUM_COLORS:
                            reinit = False

                            config.truepal = config.quantize_palette(config.truepal, cdepth)
                            newpal = config.get_default_palette(num_colors)
                            config.truepal.extend(newpal[config.NUM_COLORS:num_colors])
                            if halfbright:
                                for i in range(0,32):
                                    config.truepal[i+32] = \
                                              ((config.truepal[i][0] & 0xee) // 2,
                                               (config.truepal[i][1] & 0xee) // 2,
                                               (config.truepal[i][2] & 0xee) // 2)
                            config.pal = list(config.truepal)
                            config.pal = config.unique_palette(config.pal)
                            config.backuppal = list(config.pal)
                            config.pixel_canvas.set_palette(config.pal)

                        sm = config.display_info.get_display(display_names[aspect])[res]
                        dmode = sm.mode_id
                        px = sm.x
                        py = sm.y

                        if halfbright:
                            dmode |= config.MODE_EXTRA_HALFBRIGHT

                        if not new_clicked and resize_page and (px != config.pixel_width or py != config.pixel_height):
                            new_pixel_canvas = pygame.transform.scale(config.pixel_canvas, (px, py))
                            new_pixel_canvas.set_palette(config.pal)
                            config.pixel_canvas = new_pixel_canvas
                            reinit = False

                    config.display_mode = dmode
                    config.pixel_width = px
                    config.pixel_height = py
                    config.color_depth = cdepth
                    config.NUM_COLORS = num_colors
                    config.pal = list(config.truepal)
                    config.pal = config.unique_palette(config.pal)
                    config.set_all_palettes(config.pal, config.truepal)
                    if ge.gadget.label == "Make Default":
                        config.saveConfig()
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0 

        apply_bdepth()

        if aspect == 0:
            gVGA.state = 1
        elif aspect == 1:
            gNTSC.state = 1
        else:
            gPAL.state = 1

        gres[res].state = 1

        if cdepth == 16:
            g12bit.state = 1
        else:
            g24bit.state = 1

        if resize_page:
            gResize[1].state = 1
        else:
            gResize[0].state = 1

        if running and not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    if ok_clicked:
        config.initialize_surfaces(reinit=reinit)
        config.anim.show_curr_frame()
    else:
        config.recompose()

    return ok_clicked


def page_size_req(screen):
    req = str2req("Set Page Size", """
Type in size:
 Width:_____ Height:_____

Or select one:
 [Standard   xxxx x yyyy]
 [Full Page  xxxx x yyyy]
 [Overscan   xxxx x yyyy]

Resize: [Yes~No]

[Cancel][OK]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    widthg = req.gadget_id("7_1")
    heightg = req.gadget_id("20_1")
    standardg = req.gadget_id("1_4")
    fullpageg = req.gadget_id("1_5")
    overscang = req.gadget_id("1_6")

    pageg = [standardg, fullpageg, overscang]

    sm = config.display_info.get_id(config.display_mode)
    page_size = [[sm.x,sm.y],[sm.x,int(sm.y*1.7)],[sm.max_x,sm.max_y]]

    widthg.value = str(config.pixel_width)
    widthg.numonly = True
    heightg.value = str(config.pixel_height)
    heightg.numonly = True

    # Populate buttons from page_size array
    for i in range(0,3):
        pageg[i].label = pageg[i].label.replace("xxxx", "%4d"%(page_size[i][0]))
        pageg[i].label = pageg[i].label.replace("yyyy", "%d"%(page_size[i][1]))

    #Gather page resize gadgets
    resize_page = False
    gResize = [None, None]
    gResize[1] = req.gadget_id("8_8") #Yes
    gResize[0] = req.gadget_id("12_8") #No

    for i in range(0,2):
        gResize[i].state = (resize_page == (i == 1))
        gResize[i].need_redraw = True

    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.size_canvas(int(widthg.value), int(heightg.value), resize_page)
                    running = 0
                elif ge.gadget in gResize:
                    resize_page = (gResize.index(ge.gadget) == 1)
                elif ge.gadget.label == "Cancel":
                    running = 0
                elif ge.gadget in pageg:
                    i = pageg.index(ge.gadget)
                    widthg.value = str(page_size[i][0])
                    widthg.need_redraw = True
                    heightg.value = str(page_size[i][1])
                    heightg.need_redraw = True

        if resize_page:
            gResize[1].state = 1
        else:
            gResize[0].state = 1

        if not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.initialize_surfaces()
    config.anim.show_curr_frame()

    return

class PreviewPic(Gadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        self.pic = config.layers.get_flattened(exclude=["R"]).convert()
        super(PreviewPic, self).__init__(type, label, rect, value, maxvalue, id)
 
    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo
        self.screenrect = (x+xo,y+yo,w,h)

        if self.type == Gadget.TYPE_CUSTOM:
            if not self.need_redraw:
                return

            self.need_redraw = False

            if self.label == "#":
                if config.pixel_width / w > config.pixel_height / h:
                    # Scale to max width and center height
                    newh = int(config.pixel_height * w / config.pixel_width)
                    yo += (h - newh) // 2
                    h = newh
                else:
                    # Scale to max height and center width
                    neww = int(config.pixel_width * h / config.pixel_height)
                    xo += (w - neww) // 2
                    w = neww
                screen.set_clip(self.screenrect)
                screen.blit(pygame.transform.smoothscale(self.pic, (w, h)), (x+xo,y+yo))
        else:
            super(PreviewPic, self).draw(screen, font, offset)

def page_preview_req(screen):
    req = str2req("Page Preview", """
###############################
###############################
###############################
###############################
###############################
###############################
###############################
###############################
###############################
###############################
###############################
###############################
              [OK]
""", "#", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=PreviewPic, font=config.font)

    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()
    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK":
                    running = 0

        if running and not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return


class PPpic(Gadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        self.pic = imgload('logo.png')
        super(PPpic, self).__init__(type, label, rect, value, maxvalue, id)
        
    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo
        self.screenrect = (x+xo,y+yo,w,h)

        if self.type == Gadget.TYPE_CUSTOM:
            if not self.need_redraw:
                return

            self.need_redraw = False

            if self.label == "#":
                screen.set_clip(self.screenrect)
                screen.blit(pygame.transform.smoothscale(self.pic, (w, h)), (x+xo,y+yo))
        else:
            super(PPpic, self).draw(screen, font, offset)

def about_req(screen):
    req = str2req("About", """
PyDPainter           ############
%-20.20s ############
Version %-12.12s ############
                     ############
Licensed under GPL 3 ############
or later. See LICENSE############
for more details.    ############
                     ############
             [OK]
""" % (config.copyright,config.version), "#", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=PPpic, font=config.font)

    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()
    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK":
                    running = 0 

        if running and not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return

class PPprogress(Gadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        self.pic = imgload('logo.png')
        super(PPprogress, self).__init__(type, label, rect, value, maxvalue, id)

    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo
        px = font.xsize//8
        py = font.ysize//8
        self.screenrect = (x+xo,y+yo,w,h)

        if self.type == Gadget.TYPE_CUSTOM:
            if not self.need_redraw:
                return

            self.need_redraw = False

            if self.label == "#":
                screen.set_clip(self.screenrect)
                pygame.draw.rect(screen, bgcolor, self.screenrect)
                pygame.draw.rect(screen, hcolor, (x+xo,y+yo,int(w*self.value),h))
                progress_str = "%d%%"%(self.value*100)
                font.blitstring(screen, (x+xo+(w-len(progress_str)*font.xsize)//2,y+yo+2*py), progress_str, fgcolor)
                screen.set_clip(None)
        else:
            super(PPprogress, self).draw(screen, font, offset)

def open_progress_req(screen, title):
    req = str2req(title, """
#############################
""", "#", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=PPprogress, font=config.font)

    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()
    progressg = req.gadget_id("0_0")
    progressg.value = 0
    config.cursor.shape = config.cursor.BUSY
    req.draw(screen)
    config.recompose()
    return req

def update_progress_req(req, screen, progress):
    progressg = req.gadget_id("0_0")
    progressg.value = progress
    progressg.need_redraw = True
    config.xevent.get()
    req.draw(screen)
    config.recompose()

def close_progress_req(req):
    config.pixel_req_rect = None
    config.cursor.shape = config.cursor.NORMAL
    config.recompose()

palette_page = 0

class PPstencil(Gadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        if label == "#":
            self.is_stencil_color = np.copy(config.stencil.is_color)
        elif label == "^":
            scaleX = rect[2] // 16
            scaleY = rect[3] // 8
            scaledown = 4 // min(scaleX,scaleY)
            self.crng_arrows = imgload('crng_arrows.png', scaleX=scaleX, scaleY=scaleY, scaledown=scaledown)
            value = 0
        super(PPstencil, self).__init__(type, label, rect, value, maxvalue, id)

    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo
        self.screenrect = (x+xo,y+yo,w,h)
        px = font.xsize//8
        py = font.ysize//8

        if self.type == Gadget.TYPE_CUSTOM:
            if not self.need_redraw:
                return

            self.need_redraw = False

            if self.label == "#":
                # Draw color palette
                numcolors = len(config.pal)
                if numcolors >= 32:
                    color_cols = 4
                elif numcolors == 16:
                    color_cols = 2
                elif numcolors == 8:
                    color_cols = 2
                elif numcolors <= 4:
                    color_cols = 1
                    
                colors_shown = 32
                if numcolors < colors_shown:
                    colors_shown = numcolors

                color_rows = colors_shown // color_cols
                color_spacing = w // color_cols
                color_width = w // color_cols * 3 // 4
                color_height = int(round(h*1.0 / color_rows))

                if self.value == None:
                    self.value = 1

                screen.set_clip(self.screenrect)
                screen.fill(bgcolor)
                curcolor = palette_page
                self.palette_bounds = []
                for j in range(0,color_cols):
                    for i in range(0,color_rows):
                        self.palette_bounds.append((x+xo+1+j*color_spacing,y+yo+1+i*color_height,color_spacing-1,color_height, curcolor))
                        pygame.draw.rect(screen, config.pal[curcolor], (x+xo+1+j*color_spacing,y+yo+1+i*color_height,color_width-1,color_height), 0)
                        #Draw selected colors
                        if self.is_stencil_color[curcolor]:
                            pygame.draw.rect(screen, fgcolor, (x+xo+j*color_spacing+color_width,y+yo+py+1+i*color_height,px*2,color_height-py-py), 0)
                            pygame.draw.rect(screen, fgcolor, (x+xo+j*color_spacing+color_width,y+yo+py+py+1+i*color_height,px*3,color_height-(4*py)), 0)
                        curcolor += 1
                screen.set_clip(None)
            elif self.label == "^": # direction arrow
                pygame.draw.rect(screen, bgcolor, self.screenrect, 0)
                if self.state == 0:
                    pygame.draw.rect(screen, fgcolor, (x+xo+1,y+yo,w-1,h), 1)
                    pygame.draw.line(screen, hcolor, (x+xo+1,y+yo), (x+xo+w-2,y+yo))
                    pygame.draw.line(screen, hcolor, (x+xo+1,y+yo), (x+xo+1,y+yo+h-1))
                else:
                    pygame.draw.rect(screen, hcolor, (x+xo+1,y+yo,w-1,h), 1)
                    pygame.draw.line(screen, fgcolor, (x+xo+1,y+yo), (x+xo+w-2,y+yo))
                    pygame.draw.line(screen, fgcolor, (x+xo+1,y+yo), (x+xo+1,y+yo+h-1))

                ah = self.crng_arrows.get_height()
                aw = self.crng_arrows.get_width() // 4

                if self.value == 1:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (aw*0,0,aw,ah))
                elif self.value == -1:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (aw*1,0,aw,ah))
                elif self.value == -2:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (aw*2,0,aw,ah))
                elif self.value == 2:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (aw*3,0,aw,ah))

                if not self.enabled:
                    for i in range(x+xo, x+xo+w+1, 2):
                        for j in range(y+yo, y+yo+h+1, 4):
                            pygame.draw.rect(screen, bgcolor, (i,j,1,1), 0)
                    for i in range(x+xo+1, x+xo+w+1, 2):
                        for j in range(y+yo+2, y+yo+h+1, 4):
                            pygame.draw.rect(screen, bgcolor, (i,j,1,1), 0)
                    fadesurf = pygame.Surface((w,h), SRCALPHA)
                    fadesurf.fill((bgcolor[0],bgcolor[1],bgcolor[2],128))
                    screen.blit(fadesurf, self.screenrect)
                screen.set_clip(None)
        else:
            super(PPstencil, self).draw(screen, font, offset)

    def process_event(self, screen, event, mouse_pixel_mapper):
        global palette_page
        ge = []
        x,y = mouse_pixel_mapper()
        g = self
        gx,gy,gw,gh = g.screenrect

        #disabled gadget
        if not g.enabled:
            return ge

        if self.type == Gadget.TYPE_CUSTOM:
            if g.pointin((x,y), g.screenrect):
                #handle left button
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if g.label == "#":
                        for i in range(len(self.palette_bounds)):
                            x1,y1,x2,y2,colorindex = self.palette_bounds[i]
                            if x >= x1 and x <= x1+x2-1 and y >= y1 and y <= y1+y2-1:
                                g.need_redraw = True
                                self.is_stencil_color[colorindex] = not self.is_stencil_color[colorindex]
                                ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
                    elif g.label == "^":
                        g.state = 1
                        g.need_redraw = True
            if event.type == MOUSEBUTTONUP and event.button == 1:
                if g.label == "^":
                    if g.pointin((x,y), g.screenrect) and g.state == 1:
                        if abs(g.value) == 1:
                            g.value = -g.value
                        elif g.value == -2:
                            palette_page -= 32
                            if palette_page < 0:
                                palette_page = 0
                        elif g.value == 2:
                            palette_page += 32
                            if palette_page >= config.NUM_COLORS:
                                palette_page = config.NUM_COLORS - 32
                    g.state = 0
                    g.need_redraw = True
                    ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
        else:
            ge.extend(super(PPstencil, self).process_event(screen, event, mouse_pixel_mapper))
        return ge

def stencil_req(screen):
    req = str2req("Make Stencil", """
[Clear ]    Locked:
[Invert]##############
        ##############
        ##############
        ##############
        ##############
        ##############
[ Make ]##############
[Cancel]    ^^ A^^
""", "#^", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=PPstencil, font=config.font)

    (rx,ry,rw,rh) = req.rect
    rx += 20
    ry += int(config.menubar.rect[3] * 1.5)
    req.rect = (rx,ry,rw,rh)
    config.pixel_req_rect = req.get_screen_rect()
    req.draggable = True
    config.stop_cycling()

    #palette page
    palpageg = req.gadget_id("15_8")
    ppx,ppy,ppw,pph = palpageg.rect
    palpageg.rect = (ppx-(config.fontx//2),ppy,ppw,pph)
    palpage_lg = req.gadget_id("12_8")
    palpage_lg.value = -2
    palpage_rg = req.gadget_id("16_8")
    palpage_rg.value = 2

    if len(config.pal) > 32 and not config.display_mode & config.MODE_EXTRA_HALFBRIGHT:
        palpageg.enabled = True
        palpage_lg.enabled = True
        palpage_rg.enabled = True
    else:
        palpageg.enabled = False
        palpage_lg.enabled = False
        palpage_rg.enabled = False

    req.draw(screen)
    config.recompose()

    colorsg = req.gadget_id("8_1")

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        #Get color from pixel canvas
        buttons = config.get_mouse_pressed(event)
        if event.type in [MOUSEBUTTONDOWN, MOUSEMOTION] and True in buttons:
            x,y = config.get_mouse_pixel_pos(event)
            if x < rx or y < ry or x > rx+rw or y > ry+rh:
                x1,y1 = config.get_mouse_pixel_pos(event, ignore_req=True)
                if x1 >= 0 and y1 >= 0 and \
                   x1<config.pixel_canvas.get_width() and \
                   y1<config.pixel_canvas.get_height():
                    colorindex = config.pixel_canvas.get_at_mapped((x1,y1))
                    colorsg.need_redraw = True
                    if buttons[0]:
                        colorsg.is_stencil_color[colorindex] = True
                    elif buttons[2]:
                        colorsg.is_stencil_color[colorindex] = False

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "Cancel":
                    running = 0 
                elif ge.gadget.label == "Clear ":
                    colorsg.is_stencil_color[:] = False
                    colorsg.need_redraw = True
                elif ge.gadget.label == "Invert":
                    colorsg.is_stencil_color = np.invert(colorsg.is_stencil_color)
                    colorsg.need_redraw = True
                if ge.gadget.label == " Make ":
                    config.stencil.make(config.pixel_canvas, colorsg.is_stencil_color)
                    running = 0 
            elif ge.gadget.type == Gadget.TYPE_CUSTOM:
                if ge.gadget.label == "^":
                    palpageg.label = chr(65+(palette_page//32))
                    palpageg.need_redraw = True
                    colorsg.need_redraw = True

        if running and not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            #keep requestor within screen
            (rx,ry,rw,rh) = req.rect
            if ry < 14:
                ry = 14
            if ry > screen.get_height()-20:
                ry = screen.get_height()-20
            if rx < -rw+20:
                rx = -rw+20
            if rx > screen.get_width()-40:
                rx = screen.get_width()-40
            req.rect = (rx,ry,rw,rh)
            config.pixel_req_rect = req.get_screen_rect()
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return

def question_req(screen, title, text, buttons, hotkeys=[]):
    dummy_text = re.sub(r'[^\n]', "A", text) #replace text with "A"s so characters aren't interpreted
    all_text = dummy_text + "\n"
    for button_text in buttons:
        all_text += "[" + button_text + "]"

    req = str2req(title, all_text, "",
          mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)

    #Replace dummy text with actual text
    textlines = text.splitlines()
    textrow = 0
    for textline in textlines:
        labelg = req.gadget_id("0_%d" % (textrow))
        labelg.label = textline
        textrow += 1

    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()
    req.draw(screen)
    config.recompose()

    button_clicked = -1
    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key in hotkeys:
            button_clicked = hotkeys.index(event.key)
            running = 0 
        elif event.type == KEYDOWN:
            for bstr in buttons:
                if bstr[0].lower() == event.unicode.lower():
                    button_clicked = buttons.index(bstr)
                    running = 0

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                button_clicked = buttons.index(ge.gadget.label)
                running = 0 

        if running and not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return button_clicked

init -1700 python in _editor:
    from store import config, style
    import os
    import re
    from time import time
    import pygame
    import pyperclip # to use external copy buffer
    from pygments import highlight
    from pygments.styles import monokai
    from RVRE import *


    class RenPyBuffer(ReadWriteBuffer):
        """ layer formatting to display a text buffer in a ren'py screen """
        def __init__(self, language='en', style='monokai'):
            # lst=[{"sbc": {"lnr": None, "cx": None, "cy": None}}]
            # past = LogList(logger=devlog, lst=lst)
            # super(RenPyBuffer, self).__init__(fname=Editor.fname, past=past)
            self.style = style
            super(RenPyBuffer, self).__init__(fname=Editor.fname)
            self.set_format(language, style=style)
            self.lexer = RenPyLexer(stripnl=False)

        def set_format(self, language=None, style=None, **kwargs):
            language = self.language = language or self.language
            style = self.style = style or self.style
            self.formatter = RenPyFormatter(language=language, style=style, **kwargs)

        def parse(self, force=False):
            """ If changes were not yet parsed, check for errors; create colored_buffer for view on screen """
            if self.history.changed or force:
                document = os.linesep.join(self.data)
                renpy.parser.parse_errors = []
                renpy.parser.parse(self.fname, document)
                escaped = re.sub(r'(?<!\{)(\{(\{\{)*)(?!\{)', r'{\1', re.sub(r'(?<!\[)(\[(\[\[)*)(?!\[)', r'[\1', document))

                # NOTE: must split on newline here, not os.linesep, or it won't work in windows
                self.colored_buffer = highlight(escaped, self.lexer, self.formatter).split('\n')

        def get_color(self, arg):
            return self.formatter.get_style_defs(arg)


    class TextView(object):

        """keeps track of horizontal position in text. Wrapping is not taken into account for position."""
        def __init__(self, console, data, font_name="Inconsolata-Regular", font_size=30, lnr=0, wheel_scroll_lines=3):
            self.data = data
            self.lnr = lnr
            self.console = console
            self.show_errors = ""
            self.wheel_scroll_lines = wheel_scroll_lines
            self.keymap = set(['mousedown_4', 'mousedown_5'])
            self._add_km(['UP', 'DOWN', 'PAGEUP', 'PAGEDOWN'], ['repeat_', 'shift_', 'repeat_shift_', ''])
            self._add_km(['HOME', 'END'], ['ctrl_'])
            self.wrapped_buffer = []
            self.wrap2buf = {}
            self.set_font(name=font_name, size=font_size)

        def set_font(self, **kwargs):
            self.font = Font(**kwargs)
            self.cbuflines = self.font.max_lines
            self.parse()

        def _add_km(self, km, mod):
            self.keymap.update([m+'K_'+k for k in km for m in mod])

        def get_char_width_height(self, w, h=None):
            return (w/self.font.max_char_per_line, h/self.font.max_lines_per_screen)

        @property
        def line(self):
            return self.wrapped_buffer[Editor.cy]

        def nr_of_lines(self):
            return len(self.wrapped_buffer)

        @property
        def coords(self):
            return {"lnr": self.lnr, "cx": Editor.cx, "cy": Editor.cy, "CX": Editor.CX, "CY": Editor.CY}

        def rewrap(self):
            """ a copy of the buffer in view that is wrapped as shown in view """
            atline = 0
            tot = 0
            self.wrapped_buffer.clear()
            for line in self.data[self.lnr:min(self.lnr + self.font.max_lines, len(self.data))]:
                wrap = renpy.text.extras.textwrap(line, self.font.max_char_per_line) or ['']

                offs = 0
                for l in wrap:
                    offs += line.index(l, offs) - offs
                    self.wrap2buf[tot]=(offs, atline)
                    tot += 1
                    if tot > self.font.max_lines:
                        return
                    offs += len(l)
                    self.wrapped_buffer.append(l)
                atline += 1
                self.cbuflines = atline
                if offs != len(line):
                    renpy.error(os.linesep.join(["rewrap() discrepancy", line, str(offs), str(len(line)), str(wrap)]))

        def parse(self, force=False):
            self.data.parse(force)
            self.rewrap()
            if self.show_errors is not None:
                err = renpy.parser.parse_errors
                self.show_errors = ""
                if err:
                    self.show_errors = re.sub(r'(?<!\{)(\{(\{\{)*)(?!\{)', r'{\1', re.sub(r'(?<!\[)(\[(\[\[)*)(?!\[)', r'[\1', os.linesep.join(err)))

        def update_cursor(self, force=False):
            mouse = "; mouse: {0}, {1}".format(Editor.mousex, Editor.mousey) if hasattr(Editor, "mousey") else ""
            config.window_title = Editor.fname + ": line %d+%d, char %d%s" % (self.lnr, Editor.cy, Editor.cx, mouse)
            self.data.history.update_cursor(self.console, force)

        def UP(self, sub=1, new_history_entry=True):
            if new_history_entry:
                self.update_cursor()

            sub = min(Editor.cy + self.lnr, sub)
            cursor_movement = min(Editor.cy, sub)
            Editor.cy -= cursor_movement
            self.lnr -= sub - cursor_movement
            if cursor_movement == 0: # then view moved
                self.rewrap()
                # either suggestion screen positions needs to be updated or closed
                end_all_screens_with_name("_editor_menu")

        def DOWN(self, add=1, new_history_entry=True):
            if new_history_entry:
                self.update_cursor()
            cursor_movement = min(self.nr_of_lines() - Editor.cy - 1, add)
            add -= cursor_movement
            if cursor_movement:
                Editor.cy += cursor_movement
            elif self.lnr + add < len(self.data): # view movement
                end_all_screens_with_name("_editor_menu")
                self.lnr += add
                self.rewrap()
                while Editor.cy >= self.nr_of_lines():
                    Editor.cy -= 1
                    self.parse()
            else:
                 Editor.CY = Editor.cy

        def PAGEUP(self):
            self.UP(self.nr_of_lines())

        def PAGEDOWN(self):
            self.DOWN(self.nr_of_lines())

        def ctrl_HOME(self):
            self.update_cursor(self.console)
            Editor.cy = self.lnr = 0

        def ctrl_END(self):
            self.update_cursor()
            Editor.cy = self.nr_of_lines() - 1
            self.lnr = len(self.data) - Editor.cy - 1

        def mousedown_4(self): self.UP(self.wheel_scroll_lines)
        def mousedown_5(self): self.DOWN(self.wheel_scroll_lines)


    class EditView(TextView):

        def __init__(self, **kwargs):
            super(EditView, self).__init__(**kwargs)

            self._add_km(['BACKSPACE', 'DELETE', 'RETURN'], ['repeat_', ''])
            self._add_km(['HOME', 'END'], ['shift_', 'ctrl_', 'ctrl_shift_', ''])
            self._add_km(['LEFT', 'RIGHT'], ['shift_', 'ctrl_', 'ctrl_shift_', 'repeat_ctrl_shift_', '', 'repeat_shift_', 'repeat_ctrl_', 'repeat_'])
            self._add_km(['UP', 'DOWN'], ['shift_', 'repeat_shift_'])
            Editor.max = 0xffff
            # FIXME: this is QWERTY keyboard specific.
            self.nrSymbol = ")!@#$%^&*("
            self.oSymName = [ "BACKQUOTE", "MINUS", "EQUALS", "LEFTBRACKET", "RIGHTBRACKET",
                               "BACKSLASH", "SEMICOLON", "QUOTE", "COMMA", "PERIOD", "SLASH"]
            self.oSymLow = r"`-=[]\;',./"
            self.oSymUpp = r'~_+{}|:"<>?'
            self.copied = ""
            self.show_search = False
            self.search_string = ""
            self.find_upstream = None
            self.find_downstream = None

        def get_selected(self):
            cx, cy, CX, CY, selection = self.console.ordered_cursor_coordinates()
            if not selection:
                return ""
            sx, sy, ex, ey = self.cursor2buf_coords(cx, cy, CX, CY)
            copy = ""
            for y in xrange(sy, ey):
                copy += self.data[y][sx:len(self.data[y])] + os.linesep
                sx = 0
            return copy+self.data[ey][sx:ex]

        def LEFT(self, sub=1, new_history_entry=True):
            if new_history_entry:
                self.update_cursor()

            while Editor.cx < sub and self.wrap2buf[Editor.cy][0]:
                sub -= Editor.cx + 1
                self.UP()
                Editor.cx = len(self.line)
            Editor.max = max(Editor.cx - sub, 0)

        def RIGHT(self, add=1, new_history_entry=True):
            if new_history_entry:
                self.update_cursor()

            bx, by = self.wrap2buf[Editor.cy]
            while Editor.cx + add > len(self.line) and bx+Editor.cx <= len(self.data[self.lnr+by]):
                add -= len(self.line) - Editor.cx + 1
                self.DOWN()
                Editor.cx = 0
            Editor.cx = min(Editor.cx + add, len(self.line))
            Editor.max = Editor.cx

        def ctrl_LEFT(self):
            bx, by = self.wrap2buf[Editor.cy]
            m = re.compile(r'\w*\W*$').search(self.data[self.lnr+by][:bx+Editor.cx])
            if m:
                self.LEFT(len(m.group(0)))

        def ctrl_RIGHT(self):
            bx, by = self.wrap2buf[Editor.cy]
            m = re.compile(r'^\w*\W*').match(self.data[self.lnr+by][bx+Editor.cx:])
            if m:
                self.RIGHT(len(m.group(0)))

        def HOME(self):
            self.update_cursor()
            Editor.max = 0

        def END(self):
            self.update_cursor()
            Editor.max = 0xffff

        def RETURN(self): self.insert(['',''])

        def BACKSPACE(self):
            self.update_cursor(force=True)
            if Editor.cx == Editor.CX and Editor.cy == Editor.CY:
                if Editor.cx or self.wrap2buf[Editor.cy][0]:
                    self.LEFT(new_history_entry=False)
                elif self.lnr + Editor.cy != 0:
                    self.UP(new_history_entry=False)
                    Editor.max = len(self.line)
                else:
                    return
                Editor.cx = Editor.max
            self.DELETE(force=False)

        def cursor2buf_coords(self, cx, cy, CX, CY, _selection=None):
            sx, sy = self.wrap2buf[cy]
            ex, ey = self.wrap2buf[CY]
            return (sx+cx, sy+self.lnr, ex+CX, ey+self.lnr)

        def DELETE(self, force=True):
            self.update_cursor(force=force)
            cx, cy, CX, CY, selection = self.console.ordered_cursor_coordinates()
            sx, sy, ex, ey = self.cursor2buf_coords(cx, cy, CX, CY)

            if sx != len(self.data[sy]) or selection:
                ex += 0 if selection else 1 # then delete the one right of the cursor
                start = self.data[sy][:sx]
                del self.data[sy:ey]
                self.data[sy] = start + self.data[sy][ex:]
            elif sy < len(self.data) - 1:
                Editor.max = len(self.data[sy])
                self.data[sy] += self.data[sy+1]
                del self.data[sy+1]
            self.parse()
            Editor.cy = Editor.CY = cy
            if cx > len(self.line):
                # fix cursor placement if space was deleted causing a word at the end of the line to wrap to the next line
                cx -= len(self.line) + 1
                self.DOWN(new_history_entry=False)
            elif sx < self.wrap2buf[cy][0]:
                # fix cursor placement when word at start of line was shortened and now wraps
                dx = self.wrap2buf[cy][0] - sx
                self.UP(new_history_entry=False)
                cx = len(self.line) + 1 - dx
            Editor.max = Editor.cx = Editor.CX = cx

        def copy(self):
            selection = self.get_selected()
            if selection is not "":
                pyperclip.copy(selection)

        def cut(self):
            if Editor.CX != Editor.cx or Editor.CY != Editor.cy:
                self.copy()
                self.handlekey("DELETE")

        def insert(self, entries=None):
            """ entries: string, linesep split or pyperclipboard is used """
            self.update_cursor(force=True)

            if entries == None: # paste in absences of entries
                entries = pyperclip.paste().split(os.linesep)
            elif isinstance(entries, basestring):
                entries = entries.split(os.linesep)

            cx, cy, CX, CY, selection = self.console.ordered_cursor_coordinates()

            if cx != CX or cy != CY:
                self.DELETE(force=False)

            cx, cy = Editor.cx, Editor.cy

            offs, atline = self.wrap2buf[cy]
            cx += offs
            by = atline + self.lnr

            end = self.data[by][cx:]
            self.data[by] = self.data[by][:cx] + entries[0]
            for l in entries[1:]:
                by += 1
                self.data.insert(by, l)
            self.data[by] += end
            self.parse()

            # distinction required to prevent cursor jump when pasting/inserting on first line.
            if len(entries) <= 1 and cx + len(entries[0]) - self.wrap2buf[Editor.cy][0] < len(self.line):
                Editor.cx = cx + len(entries[0])
            else:
                self.UP(new_history_entry=False)
                for e in entries:
                    self.DOWN(new_history_entry=False)
                    Editor.cx = cx + len(e)
                    while Editor.cx - self.wrap2buf[Editor.cy][0] > len(self.line):
                        self.DOWN(new_history_entry=False)
                        if not self.wrap2buf[Editor.cy][0]:
                            break
                    cx = 0
                Editor.CY = Editor.cy

            Editor.cx -= self.wrap2buf[Editor.cy][0]
            Editor.max = Editor.CX = Editor.cx
            renpy.redraw(self.console, 0)

        def handlekey(self, keystr):
            """ repeat keys are handled as normal keys; unless shift is provided selection is discarded and cursor is redrawn """
            getattr(self, re.sub(r'^(?:repeat_)?(ctrl_|meta_|alt_|)(?:shift_)?K_', r'\1', keystr))()
            Editor.cx = min(Editor.max, len(self.line))
            if "shift_" not in keystr:
                Editor.CX, Editor.CY = Editor.cx, Editor.cy
            renpy.redraw(self.console, 0)

        def colorize(self, txt, at_start, at_end):
            return ('{color=#000000}' if at_start else '') + txt + ('{/color}' if at_end else '')

        def display(self):
            ll = min(self.lnr + self.cbuflines, len(self.data))
            section = os.linesep.join(self.data.colored_buffer[self.lnr:ll])
            section = self.colorize(section, self.lnr != 0, ll != len(self.data))
            return re.sub(r'(\{/color\}[^{}]*)\{/color\}$', r'\1', section)

        def ctrl_z(self):
            self.data.history.undo(self)

        def ctrl_y(self):
            self.data.history.redo(self)

        def search_init(self, search):
            self.search_string = search
            renpy.show_screen("_editor_find")

        def search(self):
            """ Regex multiline search. `^' and `$' replaced so they also allow newline at start/end """
            if self.search_string is not "":
                self.search_string = re.sub(r'(?!\\)(\\\\)*\$$', r'$1(:?(?=\\n)|$)', self.search_string)
                self.search_string = re.sub(r'^\^', r'(:?(?<=\\n)|^)', self.search_string)
                sx, sy, ex, ey = self.cursor2buf_coords(*self.console.ordered_cursor_coordinates())
                self.find_downstream = re.finditer(self.search_string, "\n".join(self.data[:sy-1]) + "\n" + self.data[sy][:(sx + len(self.search_string) - 1)])
                self.find_upstream = re.finditer(self.search_string, self.data[sy][sx:] + "\n" + "\n".join(self.data[sy+1:]))
                self.search_next()

        def search_next(self):
            chars = None
            had_selection = (abs(Editor.cx - Editor.CX) + 1) * (abs(Editor.cy - Editor.CY) + 1)
            try:
                while True:
                    m = next(self.find_upstream)
                    if m.start() != 0: # do not return exact same match
                        break
                chars = m.start()
            except StopIteration:
                try:
                    while True:
                        m = next(self.find_downstream)
                        if m.start() != 0:
                            break
                    chars = m.start()
                except StopIteration:
                    renpy.notify("Not found")
                    pass
                if chars is not None:
                    Editor.CY = Editor.CX = self.lnr = 0
                    self.PAGEUP()
                    self.HOME()
                    self.rewrap()
            if chars is None:
                renpy.notify("Not found")
            else:
                Editor.cx, Editor.cy = Editor.CX, Editor.CY
                # move to found text and place cursor(s) there
                self.RIGHT(chars)
                Editor.CX, Editor.CY = Editor.cx, Editor.cy
                # place in middle of view
                self.DOWN(self.font.half_a_screen)
                self.UP(self.font.half_a_screen)
                #correct cursor
                Editor.CY, Editor.cx = Editor.cy, Editor.CX
                # move to select searched text
                self.RIGHT(m.end()-m.start())
                renpy.redraw(self.console, 0)

        def suggestions_for_selected(self):
            return self.data.formatter.lang.candidates(self.get_selected())

        def set_spellcheck_modus(self, value):
            if not value:
                renpy.hide_screen("_editor_menu", layer="transient")
            self.data.formatter.do_check = value
            self.parse(force=True)
            renpy.redraw(self.console, 0)

    class Editor(renpy.Displayable):
        mousex = mousey = fname = view = None
        buffer = {}
        timer = time()
        is_mouse_pressed = False
        max = cx = cy = CX = CY = 0 # last two are meant for dragging
        suggestion_menu = None #TODO: make this a hashmap per word?
        original_title = None

        def __init__(self, *a, **b):
            self.context_options = []
            super(Editor, self).__init__(a, b)
            self.is_visible = False

        @staticmethod
        def ordered_cursor_coordinates():
            cx, cy = Editor.cx, Editor.cy
            CX, CY = Editor.CX, Editor.CY

            selection = True

            if cy > CY:
                Editor.cy, Editor.CY = CY, cy
                Editor.cx, Editor.CX = CX, cx

            elif cy == CY:
                if cx > CX:
                    Editor.cx, Editor.CX = CX, cx
                elif cx == CX:
                    selection = False
            return (Editor.cx, Editor.cy, Editor.CX, Editor.CY, selection)

        def setup_default_context_menu(self):
            self.context_options = []
            inconsolata = {"name": "Inconsolata-Regular", "submenu": [20,30,40]}
            proggy = {"name": "ProggyClean", "submenu": [20,30,40]}
            scpro = {"name": "SourceCodePro-Regular", "submenu": [20,30,40]}
            self.context_options.append({"name": "font", "submenu": [inconsolata, proggy, scpro]})
            self.context_options.append({ "name": "language", "submenu": ["de", "en", "es", "fr", "pt", "ru"] })
            self.context_options.append({"name": "style", "submenu": ["abap", "algol_nu", "arduino", "autumn", "borland", "colorful", "default", "emacs", "friendly", "fruity", "igor", "inkpot", "lovelace", "manni", "monokai", "murphy", "native", "pastie", "perldoc", "rainbow_dash", "rrt", "sas", "tango", "vim", "vs", "xcode"] })
            # also present but problematic styles:
            # "paraiso_dark", "paraiso_light", "stata_dark", "stata_light", "solarized", "trac", "bw", "algol", 
            def context_menu_handler(pick):
                if pick != "":
                    if pick[0] == "language":
                        self.view.data.set_format(language=pick[1])
                    elif pick[0] == "style":
                        self.view.data.set_format(style=pick[1])
                    elif pick[0] == "font":
                        self.view.set_font(name=pick[1], size=pick[2])
                    self.view.parse(force=True)
                    renpy.redraw(self, 0)
                return ""
            self.context_menu_handler = context_menu_handler

        def render(self, width, height, st, at):
            """ draw the cursor or the selection """
            R = renpy.Render(width, height)
            C = R.canvas()
            dx, dy = self.view.get_char_width_height(width, height)
            selection = self.view.data.get_color("highlight")
            if Editor.cy == Editor.CY:
                if Editor.CX == Editor.cx:
                    C.line((255,255,255,255),(Editor.cx*dx,Editor.cy*dy),(Editor.cx*dx, (Editor.cy+1.0)*dy))
                else:
                    C.rect(selection,(Editor.cx*dx, Editor.cy*dy, (Editor.CX-Editor.cx)*dx, dy))
            elif Editor.cy < Editor.CY:
                x = Editor.cx
                for y in xrange(Editor.cy, Editor.CY):
                    C.rect(selection, (x*dx, y*dy, (len(self.view.wrapped_buffer[y])-x)*dx, dy))
                    x = 0
                C.rect(selection, (0, Editor.CY*dy, Editor.CX*dx, dy))
            else:
                x = Editor.CX
                for y in xrange(Editor.CY, Editor.cy):
                    C.rect(selection, (x*dx, y*dy, (len(self.view.wrapped_buffer[y])-x)*dx, dy))
                    x = 0
                C.rect(selection, (0, Editor.cy*dy, Editor.cx*dx, dy))
            return R

        def show_debug_messages(self, do_show):
            self.view.show_errors = "" if do_show else None
            self.view.parse()

        def get_screen_char_width_height(self):
            w, h = (config.screen_width, config.screen_height)
            return self.view.get_char_width_height(w, h)

        def _screen_to_cursor_coordinates(self, x, y):
            cw, ch = self.get_screen_char_width_height()
            Editor.max = int(x / cw)
            cy = int(y / ch)

            if cy >= self.view.nr_of_lines():
                cy = self.view.nr_of_lines() - 1
            return (min(Editor.max, len(self.view.wrapped_buffer[cy])), cy)

        def sbc(self, lnr=None, cx=None, cy=None, CX=None, CY=None):
            """set buffer coordinates"""
            self.view.lnr = self.view.lnr if lnr is None else lnr
            Editor.cx = Editor.cx if cx is None else cx
            Editor.cy = Editor.cy if cy is None else cy
            Editor.CX = Editor.cx if CX is None else CX
            Editor.CY = Editor.cy if CY is None else CY
            self.view.rewrap()

        def select_word(self):
            bx, by = self.view.wrap2buf[Editor.cy]
            m = re.compile(r'\w*$').search(self.view.data[self.view.lnr+by][:bx+Editor.cx])
            if m:
                Editor.cx -= len(m.group(0))
            m = re.compile(r'^\w*').match(self.view.data[self.view.lnr+by][bx+Editor.cx:])
            if m:
                Editor.max = Editor.CX = min(Editor.cx+len(m.group(0)), len(self.view.line))
        def select_none(self):
            self.sbc()

        def event(self, ev, x, y, st):
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                Editor.cx, Editor.cy = self._screen_to_cursor_coordinates(x, y)
                self.view.update_cursor()
                if time() - Editor.timer < 0.5:
                    self.select_word()
                else:
                    Editor.timer = time()
                    Editor.CX, Editor.CY = Editor.cx, Editor.cy
                renpy.redraw(self, 0)
                Editor.is_mouse_pressed = True
            elif ev.type == pygame.MOUSEMOTION: # Updates the position of the mouse every time the player moves it
                Editor.mousex = x
                Editor.mousey = y
                if Editor.is_mouse_pressed:
                    Editor.CX, Editor.CY = self._screen_to_cursor_coordinates(x, y)
                renpy.redraw(self, 0)
            elif Editor.is_mouse_pressed and ev.type == pygame.MOUSEBUTTONUP:
                renpy.redraw(self, 0)
                if ev.type == pygame.MOUSEBUTTONUP:
                    Editor.CX, Editor.CY, Editor.cx, Editor.cy = Editor.cx, Editor.cy, Editor.CX, Editor.CY
                    Editor.is_mouse_pressed = False

        def start(self, ctxt, offset=2, search=None, context_menu=None):
            (fname, lnr) = ctxt
            if fname: # no fname indicates failure
                renpy.loadsave.force_autosave()
                if context_menu is None:
                    self.setup_default_context_menu()
                else:
                    self.context_options = [];
                    for opt in context_menu[0]:
                        self.context_options.append(opt)
                    self.context_menu_handler = context_menu[1]
                lnr = lnr - 1
                Editor.fname = os.path.join(renpy.config.basedir, fname)

                if fname not in Editor.buffer:
                    Editor.buffer[fname] = EditView(console=self, data=RenPyBuffer(), lnr=lnr)
                else:
                    self.view.lnr = lnr
                    self.view.handlekey("END") # NB. call via handlekey triggers cursor redraw.
                self.view = Editor.buffer[fname]
                self.is_visible = True
                self.view.rewrap()
                if Editor.original_title is None:
                    Editor.original_title = config.window_title
                if search is not None:
                    self.view.search_string=search
                    self.view.search()
                renpy.redraw(self, 0)

        def exit(self, discard=False, apply=False):
            """ unless discarded, changes are kept in store. Applied changes are not visible until reload (shift+R). """
            self.is_visible = False
            Editor.max = Editor.cx = Editor.cy = Editor.CX = Editor.CY = 0 # last two are meant for dragging
            if Editor.original_title is not None:
                config.window_title = Editor.original_title
            if discard:
                #reload from disk
                self.view.data.load()
                self.view.parse()
            elif apply:
                self.view.data.save()
                renpy.reload_script()
                renpy.loadsave.load(renpy.loadsave.newest_slot())

        def add_suggestion_menu(self):
            self.select_word()
            choices = self.view.suggestions_for_selected()
            renpy.redraw(self, 0)
            Editor.is_mouse_pressed = False

            cw, ch = self.get_screen_char_width_height()

            x = int(Editor.cx * cw)
            if Editor.cy + 1 + len(choices) <= self.view.font.max_lines or Editor.cy - len(choices) < 0:
                y = int((1 + Editor.cy) * ch)
            else:
                y = int((Editor.cy - len(choices)) * ch)

            coords = self.ordered_cursor_coordinates()
            def replacer(pick):
                if pick:
                    self.sbc(cx=coords[0], cy=coords[1], CX=coords[2], CY=coords[3])
                    self.view.insert([pick])
                return pick

            Editor.suggestion_menu=SelectionMenu(x=x, y=y, cw=cw, ch=ch, font=self.view.font, choices=choices, layer="transient", handler=replacer, options={'timeout':(1.5, 0.2)})
            renpy.restart_interaction()

        def add_context_menu(self, **kwargs):

            # TODO/FIXME: context menu doesn't have to follow screen/view font parameters
            cw, ch = self.get_screen_char_width_height()
            if 'type' in kwargs:
                if kwargs['type'] == "editor":
                    choices=self.context_options
                    handler=self.context_menu_handler
            else:
                handler=None
                choices=None

            Editor.context_menu=SelectionMenu(x=Editor.mousex, y=Editor.mousey,
                                              cw=cw, ch=ch, font=self.view.font,
                                              choices=choices, layer="master",
                                              handler=handler, options={'timeout':(1.5, 0.2)})


init 1701 python in _editor:

    def hyperlink_styler_wrap(target):
        global editor
        if len(target) <= 8 or target[0:8] != "_editor:":
            return hyperlink_styler(target)

        editor_error = renpy.style.Style(style.default)
        editor_error.font = editor.view.font.get_file()
        editor_error.size = editor.view.font.size
        editor_error.color = editor.view.data.get_color("error")
        editor_error.background = editor.view.data.get_color("error background")
        editor_error.hover_underline = True
        return editor_error

    def hyperlink_callback_wrap(target):
        if len(target) <= 8 or target[0:8] != "_editor:":
            return hyperlink_callback(target)

        if not renpy.get_screen("_editor_menu", layer="transient"):
            editor.add_suggestion_menu()

    def end_all_screens_with_name(name):
        while renpy.get_screen(name):
            renpy.end_interaction("")

    editor = Editor()

    style.default.hyperlink_functions = (hyperlink_styler_wrap, hyperlink_callback_wrap, None)

    def dev_add_editor(pick):
        global editor
        if pick == "editor button":
            editor.view.insert("""
        if config.developer and _editor.editor:
            textbutton _("Edit") keysym "ctrl_K_e" action [Function("_editor.editor.start", renpy.get_filename_line()), ShowMenu('_editor_main')]
        """)

    def dev_jump_helper(file_line=None, label=None, search=None, in_editor=False, instructions=None, purpose=None, **kwargs):
        if file_line is None:
            if label is not None:
                renpy.jump(label)
        elif in_editor:
            global editor
            if purpose:
                renpy.say(who="narrator", what=instructions)
                kwargs['context_menu']=((purpose,), dev_add_editor)
            editor.start(file_line, **kwargs)
            renpy.call_screen("_editor_main")
        else:
            renpy.renpy.warp.warp_spec = "%s:%d" % file_line
            renpy.renpy.warp.warp()

    def renpy_jump_menu(*dev_jump_options):
        renpy.say(who="narrator", what="Develer menu", interact=False)
        dev_jump_result = renpy.display_menu(dev_jump_options)
        return dev_jump_result if isinstance(dev_jump_result, basestring) else dev_jump_helper(**dev_jump_result)

init 1702:
    style _editor_textbutton:
        font _editor.Font.file_for("Inconsolata-Regular")
        size 28
        color "#fff"
        hover_color "ff2"

screen _editor_main:
    layer "master"
    default editor = _editor.editor
    default view = editor.view
    frame:
        padding (0, 0)
        pos (0, 0)
        background view.data.get_color("background")
        add editor
        text view.display() font view.font.get_file() size view.font.size justify False kerning 0.0 line_leading 0 newline_indent False #adjust_spacing False
        if view.show_errors:
            window:
                align (0.5, 1.0)
                background Frame("gui/namebox.png", gui.namebox_borders, tile=gui.namebox_tile, xalign=gui.name_xalign)
                text view.show_errors font _editor.Font.file_for("Inconsolata-Regular") size 20 color "#f22"

        for keystr in sorted(view.keymap, key=len):
            key keystr action Function(view.handlekey, keystr)

        key "shift_K_RETURN" action [Function(editor.exit, apply = True), Return()]
        key "shift_K_KP_ENTER" action [Function(editor.exit, apply = True), Return()]

        key "K_ESCAPE" action [Function(editor.exit), Return()]

        key "K_TAB" action Function(view.insert, ["    "])
        key "K_SPACE" action Function(view.insert, [" "])
        key "repeat_K_SPACE" action Function(view.insert, [" "])

        for i in xrange(0, len(view.oSymName)):
            key "K_"+view.oSymName[i] action Function(view.insert, [view.oSymLow[i]])
            key "shift_K_"+view.oSymName[i] action Function(view.insert, [view.oSymUpp[i]])
            key "repeat_K_"+view.oSymName[i] action Function(view.insert, [view.oSymLow[i]])
            key "repeat_shift_K_"+view.oSymName[i] action Function(view.insert, [view.oSymUpp[i]])

        for nr in xrange(0, 10):
            key "K_"+str(nr) action Function(view.insert, [str(nr)])
            key "K_KP"+str(nr) action Function(view.insert, [str(nr)])
            key "repeat_K_"+str(nr) action Function(view.insert, [str(nr)])
            key "repeat_K_KP"+str(nr) action Function(view.insert, [str(nr)])
            key "shift_K_"+str(nr) action Function(view.insert, [view.nrSymbol[nr]])
            key "repeat_shift_K_"+str(nr) action Function(view.insert, [view.nrSymbol[nr]])

        for c in xrange(ord('a'), ord('z')+1):
            key "K_"+chr(c) action Function(view.insert, [chr(c)])
            key "shift_K_"+chr(c) action Function(view.insert, [chr(c).upper()])
            key "repeat_K_"+chr(c) action Function(view.insert, [chr(c)])
            key "repeat_shift_K_"+chr(c) action Function(view.insert, [chr(c).upper()])

        key "K_KP_PERIOD" action Function(view.insert, ["."])
        key "K_KP_DIVIDE" action Function(view.insert, ["/"])
        key "K_KP_MULTIPLY" action Function(view.insert, ["*"])
        key "K_KP_MINUS" action Function(view.insert, ["-"])
        key "K_KP_PLUS" action Function(view.insert, ["+"])
        key "K_KP_EQUALS" action Function(view.insert, ["="])

        key "ctrl_K_a" action [Function(view.handlekey, "ctrl_K_END"), Function(view.handlekey, "ctrl_shift_K_HOME")]
        key "ctrl_K_c" action Function(view.copy)
        key "ctrl_K_v" action Function(view.insert)
        key "ctrl_K_x" action Function(view.cut)
        for keystr in 'zy':
            key 'ctrl_K_'+keystr action Function(view.handlekey, 'ctrl_K_'+keystr)
            key 'repeat_ctrl_K_'+keystr action Function(view.handlekey, 'repeat_ctrl_K_'+keystr)

        # probably this should be a renpy.cal_screen or Call
        key "ctrl_K_f" action Show("_editor_find")

        if renpy.get_screen("_editor_menu"):
            key 'mousedown_1' action Function(_editor.end_all_screens_with_name, "_editor_menu")
        elif renpy.get_screen("_editor_find"):
            key 'mousedown_1' action Hide("_editor_find")
        else:
            key 'mouseup_3' action Function(editor.add_context_menu, type="editor")
        hbox:
            style_prefix "quick"
            align (0.5, 1.0)
            if view.data.changed:
                if not renpy.parser.parse_errors:
                    textbutton _("Apply") action [Function(editor.exit, apply = True), Return()]
                elif view.show_errors is None:
                    textbutton _("Debug") action Function(editor.show_debug_messages, True)
                else:
                    textbutton _("Hide") action Function(editor.show_debug_messages, False)
                textbutton _("Cancel") action [Function(editor.exit, discard = True), Return()]
            textbutton _("Visual") action [Function(editor.exit), Return()]
            if view.data.formatter.do_check:
                textbutton _("No check") action Function(view.set_spellcheck_modus, False)
            else:
                textbutton _("Suggest") action Function(view.set_spellcheck_modus, True)

# FIXME: should a call_screen and a reusable renpy.displayable that supports tabs among others.
screen _editor_find(layer="overlay"):
    #TODO Regex replace
    default editor = _editor.editor
    default view = editor.view
    frame:
        align (0.5, 0.5)
        background AlphaMask(Image("gui/frame.png", gui.confirm_frame_borders), mask="#000a")
        vbox:
            align (0.4, 0.5)
            text "Enter search string:\n":
                size 20
                color "#fff"

            add Input(hover_color="#3399ff",size=28, color="#afa", default=view.search_string, changed=view.search_init, length=256)
            hbox:
                textbutton "OK":
                    text_style "_editor_textbutton"
                    action Function(view.search)
                    keysym('K_RETURN', 'K_KP_ENTER')
                textbutton "Cancel":
                    text_style "_editor_textbutton"
                    action Hide("_editor_find", _layer=layer)
                    keysym('K_ESCAPE')




init -1700 python in _editor:
    from pygame import MOUSEBUTTONDOWN
    from time import time


    class SelectionMenu(renpy.Displayable):
        # https://renpy.org/doc/html/cdd.html
        # https://lemmasoft.renai.us/forums/viewtopic.php?p=374053#p374053
        #https://lemmasoft.renai.us/forums/viewtopic.php?t=11910
        required_init_args = {'x', 'y', 'cw', 'ch', 'font', 'font_size', 'choices', 'handler', 'layer'}
        def __init__(self, id="", base_menu=None, options=None, **kwargs):

            for arg in self.required_init_args:
                setattr(self, arg, kwargs[arg])
                del kwargs[arg]
            super(SelectionMenu, self).__init__(**kwargs)

            self.__dict__.update({"id": id, "base_menu": base_menu, "options": options if options else {}})

            wordlen_max = max(map(lambda x: len(str(x["name"] if isinstance(x, (dict, renpy.python.RevertableDict)) else x)) + 1, self.choices))
            self.area = (self.x, self.y, int(wordlen_max * self.cw), int(len(self.choices) * self.ch))
            self.nested_menu = []
            self.focus(keep=True)
            if renpy.get_screen("_editor_menu", layer=self.layer):
                renpy.end_interaction("")
            if base_menu:
                # XXX: for some reason not shown for overlay layer.
                renpy.show_screen("_editor_menu", self, _layer=self.layer)
            else:
                renpy.invoke_in_new_context(renpy.call_screen, "_editor_menu", self, _layer=self.layer)

        def focus(self, keep=False):
            if 'timeout' in self.options and keep is False:
                self.timeout = self.options['timeout'][0]
                self.polling = self.options['timeout'][1]
                self.last_focus = time()
            else:
                self.timeout = 0.0
            if self.base_menu:
                self.base_menu.focus(keep)

        def event(self, ev, x, y, st):
            if ev.type == MOUSEBUTTONDOWN:# and self.timeout != 0.0:
                renpy.end_interaction("")

        def end(self, pick):
            if pick != "" or self.timeout != 0.0:
                if self.base_menu:
                    renpy.hide_screen("_editor_menu", layer=self.layer)
                    self.base_menu.nested_menu.remove(self)
                    if isinstance(pick, (list, renpy.python.RevertableList)):
                        pick.insert(0, self.id)
                        self.base_menu.end(pick)
                    else:
                        self.base_menu.end("" if pick == "" else [self.id, pick])
                else:
                    renpy.end_interaction(self.handler(pick))

        def act(self, pick=None, hovered=None):
            """selection, (un)hover event or timeout"""
            if pick != None:
                self.timeout = 0.0
                for nested in self.nested_menu:
                    nested.end("")
                index, pick = pick
                if not isinstance(pick, (dict, renpy.python.RevertableDict)):
                    self.end(pick)
                elif 'submenu' in pick:
                    kwargs = dict((k, getattr(self, k)) for k in self.required_init_args)

                    # TODO/FIXME 1. could implement stacking as cards for menus
                    # TODO/FIXME 2. choose other side if there's no space right of the menu

                    kwargs['layer'] = config.layers[config.layers.index(self.layer)+1]
                    # if this errors, you're using too many side menus. use a
                    # different solution instead.

                    if renpy.get_screen("_editor_menu", layer=kwargs['layer']):
                        renpy.hide_screen("_editor_menu", layer=kwargs['layer'])

                    kwargs['choices'] = pick["submenu"]
                    kwargs['id'] = pick['name']
                    kwargs['y'] = int(kwargs['y'] + index * self.ch)
                    kwargs['x'] = int(kwargs['x'] + self.area[2])
                    self.nested_menu.append(SelectionMenu(base_menu=self, **kwargs))
            elif hovered is True:
                self.focus(keep=True)
            elif hovered is False:
                self.focus()
            elif self.timeout != 0.0 and time() - self.last_focus > self.timeout:
                 self.end("")

        def render(self, width, height, st, at):
            R = renpy.Render(width, height)
            renpy.redraw(self, 1)
            return R

        def visit(self):
            return self.nested_menu


screen _editor_menu(selection):
    # TODO 2: vertical scroll bar with buttons if too many options
    # TODO 3: do not always close for certain events
    # TODO 4: move menu when scrolling up/down
    if selection.timeout != 0.0:
        timer selection.polling action Function(selection.act) repeat True
    frame:
        padding (0, 0)
        background "#111a"
        area selection.area
        add selection
        vbox:
            for (index, pick) in enumerate(selection.choices):
                textbutton (pick["name"] if isinstance(pick, (dict, renpy.python.RevertableDict)) else str(pick)):
                    padding (0, 0)
                    minimum (0, 0)
                    text_font _editor.get_font(selection.font)
                    text_size selection.font_size
                    text_color "#fff"
                    text_hover_color "ff2"
                    hovered Function(selection.act, hovered=True)
                    unhovered Function(selection.act, hovered=False)
                    action Function(selection.act, pick=(index, pick))
        key "K_ESCAPE" action Function("renpy.hide_screen", "_editor_menu", layer=selection.layer)

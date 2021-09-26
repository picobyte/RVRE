init 1801 python in _editor:
    """
        This sets up up the editor button. The label main_menu below prevents showing the game menu, which can be useful for development.
        Also to test code, you could maybe set some variables here and add a jump statement to directly go to the code you are developing.
    """
    dev_jump_options = (
    # TODO: Remove this first option after the edit button was added
    ("Add editor button: right click (mouse) between the yalign line and the first textbutton in screen quick_menu().", {
        "file_line": ("game/screens.rpy", 1),
        "search": "^screen\s+quick_menu\(",
        "in_editor": True,
        "purpose": "Add editor button"
    }),
    ("Just jump to start in visual modus", {
        "label": "start"
    }),
    ("Edit the options in this development jump menu.", {
        "search": "^\s*dev_jump_options\s*=\s*\["
    }))

    def dev_menu():
        global dev_jump_options
        renpy.say(who="narrator", what="Development menu", interact=False)
        dev_jump_result = renpy.display_menu(dev_jump_options)
        dev_jump_helper(**dev_jump_result)

label main_menu:
    # with this label the main menu is not shown upon start
    # for development this is also a good location to set variables and jump to a certain location in your code.

    # this disables the quit confirmation (this could also be set in game/options.rpy)
    $ config.quit_action = Quit(confirm=False)

    $ _editor.dev_menu()

    return


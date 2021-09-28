label main_menu:
    # with this label the main menu is not shown upon start
    # for development this is a good spot to set variables and jump to a certain location in your code.

    python:
        # this disables the quit confirmation (this could also be set in game/options.rpy)
        #config.quit_action = Quit(confirm=False)

        _editor.renpy_jump_menu(
            # The first option is to set up the editor button. TODO: comment this first option after the edit button was added.
            ("Add editor button: right click (mouse) between the yalign line and the first textbutton in screen quick_menu().", {
                "file_line": ("game/screens.rpy", 1),
                "search": "^screen\s+quick_menu\(",
                "in_editor": True,
                "purpose": "Add editor button"
            }), # last line to comment.
            ("Show main menu", "exit loop"),
            ("Edit the options in this development jump menu.", {
                "search": "^\s*_editor\.renpy_jump_menu\(",
                "in_editor": True,
                "file_line": ("game/RVRE/bypass_main_menu.rpy", 1),
            })
        )

    return


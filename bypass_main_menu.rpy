label main_menu:
    # with this label the main menu is not shown upon start
    # for development this is a good spot to set variables and jump to a certain location in your code.

    python:
        # this disables the quit confirmation (this could also be set in game/options.rpy)
        #config.quit_action = Quit(confirm=False)

        _editor.renpy_jump_menu(
            ("Just start", "exit loop"),
            # Two options to enable the editor, you may want to remove these when done.
            ("Add editor button to screen quick_menu.", {
                "file_line": ("game/screens.rpy", 1),
                "instructions": "right click (mouse) between the yalign line and the first textbutton in screen quick_menu().",
                "search": "^screen\s+quick_menu\(",
                "in_editor": True,
                "purpose": "editor button"
            }), # last line to comment.
            ("Edit the options in this development menu.", {
                "search": "^\s*_editor\.renpy_jump_menu\(",
                "in_editor": True,
                "file_line": ("game/RVRE/bypass_main_menu.rpy", 1),
            })
        )

    return


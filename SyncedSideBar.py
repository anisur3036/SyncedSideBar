import sublime
import sublime_plugin

# assume sidebar is visible by default on every window (there's no way to check, unfortunately)
DEFAULT_VISIBILITY = True

pref_reveal = DEFAULT_VISIBILITY

sidebar_visible = DEFAULT_VISIBILITY
lastWindow = None
lastView = None

# Keep track of active windows so we remember sidebar_visible for each one
windows = {}

def plugin_loaded():
    s = sublime.load_settings('SyncedSideBar.sublime-settings')

    def read_pref():
        vis = s.get('reveal-on-activate')
        if vis is not None:
            global pref_reveal
            pref_reveal = vis

    # read initial setting
    read_pref()
    # listen for changes
    s.add_on_change("SyncedSideBar", read_pref)

# ST2 backwards compatibility
if (int(sublime.version()) < 3000):
    plugin_loaded()

def should_be_visible(view):
    viewSetting = view.settings().get('reveal-on-activate')
    return viewSetting if viewSetting is not None else pref_reveal


class SideBarListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        activeWindow = view.window()

        # don't even consider updating state if we don't have an activeWindow.
        # "goto anything" doesn't set activeWindow until the file is selected.
        # also, reveal in side bar is a window command only.
        if not activeWindow:
            return

        global lastView
        if lastView is not None and lastView.id() == view.id():
            # this view has already been processed, likely an alt-tab focus event
            return

        lastView = view

        if not activeWindow.id() in windows:
            # first activation in this window, use default
            windows[activeWindow.id()] = DEFAULT_VISIBILITY

        global sidebar_visible, lastWindow
        if lastWindow is None:
            # plugin just loaded
            lastWindow = activeWindow
        elif lastWindow.id() != activeWindow.id():
            # store the old window state
            windows[lastWindow.id()] = sidebar_visible
            # load the new window state
            sidebar_visible = windows[activeWindow.id()]
            lastWindow = activeWindow

        if sidebar_visible and should_be_visible(view) != False:
            def reveal():
                activeWindow.run_command('reveal_in_side_bar')

            # When using quick switch project, the view activates before the sidebar is ready.
            # This tiny delay is imperceptible but works around the issue.
            sublime.set_timeout(reveal, 100);

    # Sublime text v3 window command listener, safe to include unconditionally as it's simply ignored by v2.
    def on_window_command(self, window, command_name, args):
        if command_name == "toggle_side_bar":
            global sidebar_visible
            sidebar_visible = not sidebar_visible


class SideBarUpdateSync(sublime_plugin.ApplicationCommand):
    def run(self):
        pass

    def updateSync(self, value):
        # Load in user settings
        settings = sublime.load_settings("Preferences.sublime-settings")

        # Update the setting
        settings.set("reveal-on-activate", value)

        # Save our changes
        sublime.save_settings("Preferences.sublime-settings")


class SideBarEnableSync(SideBarUpdateSync):
    def run(self):
        self.updateSync(True)


class SideBarDisableSync(SideBarUpdateSync):
    def run(self):
        self.updateSync(False)

"""GTK 3 result tables used by the FSlint GUI.

The GtkBuilder file contains ordinary widgets so it can be edited in
Cambalache. This controller keeps file metadata separate from display text.
"""
import os
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gio, GLib


class DesktopAppearance:
    """Follow the desktop color scheme without modifying desktop settings."""
    def __init__(self):
        self.settings = Gtk.Settings.get_default()
        self.proxy = None
        self.desktop = None
        self.cancellable = Gio.Cancellable()
        self._proxy_handler = self._desktop_handler = None
        self._initial_dark = self.settings.get_property('gtk-application-prefer-dark-theme')
        # An explicit GTK_THEME is a user override, including during debugging.
        if os.environ.get('GTK_THEME'):
            return
        # GNOME fallback also provides the preference before the portal replies.
        if 'GNOME' in os.environ.get('XDG_CURRENT_DESKTOP', '').upper().split(':'):
            source = Gio.SettingsSchemaSource.get_default()
            schema = source.lookup('org.gnome.desktop.interface', True) if source else None
            if schema and schema.has_key('color-scheme'):
                self.desktop = Gio.Settings.new_full(schema, None, None)
                self._desktop_handler = self.desktop.connect('changed::color-scheme',
                                                             self._desktop_changed)
                self._desktop_changed(self.desktop, 'color-scheme')
        Gio.DBusProxy.new_for_bus(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.DO_NOT_AUTO_START | Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES,
            None, 'org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop',
            'org.freedesktop.portal.Settings', self.cancellable, self._proxy_ready)

    def _desktop_changed(self, settings, key):
        scheme = {'prefer-dark': 1, 'prefer-light': 2}.get(settings.get_string(key), 0)
        self._apply(scheme)

    def _proxy_ready(self, source, result):
        try:
            proxy = Gio.DBusProxy.new_for_bus_finish(result)
        except GLib.Error:
            return
        if self.cancellable.is_cancelled() or not proxy.get_name_owner():
            return
        self.proxy = proxy
        self._proxy_handler = proxy.connect('g-signal', self._setting_changed)
        self._read(False)

    def _read(self, legacy):
        self.proxy.call('Read' if legacy else 'ReadOne',
                        GLib.Variant('(ss)', ('org.freedesktop.appearance', 'color-scheme')),
                        Gio.DBusCallFlags.NONE, 2000, self.cancellable,
                        self._read_ready, legacy)

    def _read_ready(self, proxy, result, legacy):
        try:
            scheme = proxy.call_finish(result).unpack()[0]
        except GLib.Error:
            if not legacy and not self.cancellable.is_cancelled():
                self._read(True)  # Older portals do not implement ReadOne.
            return
        if not self.cancellable.is_cancelled():
            self._apply(scheme)

    def _setting_changed(self, proxy, sender, signal, parameters):
        if signal == 'SettingChanged':
            namespace, key, value = parameters.unpack()
            if namespace == 'org.freedesktop.appearance' and key == 'color-scheme':
                self._apply(value)

    def _apply(self, scheme):
        theme = self.settings.get_property('gtk-theme-name')
        # Adwaita-dark selects a fixed variant, overriding prefer-dark=False.
        # Use the base theme so GTK can choose its light or dark variant.
        adwaita = theme in ('Adwaita', 'Adwaita-dark')
        if scheme not in (1, 2):
            dark = False if adwaita else self._initial_dark
        else:
            dark = scheme == 1
        self.settings.freeze_notify()
        if adwaita:
            self.settings.set_property('gtk-theme-name', 'Adwaita')
        self.settings.set_property('gtk-application-prefer-dark-theme', dark)
        self.settings.thaw_notify()

    def close(self):
        self.cancellable.cancel()
        if self._proxy_handler is not None:
            self.proxy.disconnect(self._proxy_handler)
            self._proxy_handler = None
        if self._desktop_handler is not None:
            self.desktop.disconnect(self._desktop_handler)
            self._desktop_handler = None


def style_notebook_tabs(*notebooks):
    """Outline the tabs and join the selected tab to its content panel."""
    for notebook in notebooks:
        notebook.get_style_context().add_class('outlined-tabs')
    provider = Gtk.CssProvider()
    provider.load_from_data(b"""
        notebook.outlined-tabs > header {
            background-color: shade(@theme_bg_color, 0.94);
            border: none;
        }
        notebook.outlined-tabs > header.left {
            padding: 0 0 0 6px;
        }
        notebook.outlined-tabs > header.top {
            padding: 6px 0 0;
        }
        notebook.outlined-tabs > header.left > tabs {
            border-right: 1px solid alpha(@theme_fg_color, 0.30);
        }
        notebook.outlined-tabs > header.top > tabs {
            border-bottom: 1px solid alpha(@theme_fg_color, 0.30);
        }
        notebook.outlined-tabs > header > tabs > tab {
            background-color: shade(@theme_bg_color, 0.90);
            border: 1px solid alpha(@theme_fg_color, 0.30);
            box-shadow: none;
            padding: 7px 12px;
            min-height: 0;
            min-width: 0;
        }
        notebook.outlined-tabs > header.left > tabs > tab {
            border-right: none;
            border-radius: 5px 0 0 5px;
            margin: 2px 0;
        }
        notebook.outlined-tabs > header.top > tabs > tab {
            border-bottom: none;
            border-radius: 5px 5px 0 0;
            margin: 0 2px;
        }
        notebook.outlined-tabs > header > tabs > tab:hover {
            background-color: shade(@theme_bg_color, 1.08);
        }
        notebook.outlined-tabs > header > tabs > tab:checked {
            background-color: @theme_bg_color;
            color: @theme_fg_color;
            font-weight: bold;
        }
        notebook.outlined-tabs > header.left > tabs > tab:checked {
            margin-right: -1px;
            padding-right: 13px;
            box-shadow: inset 3px 0 @theme_selected_bg_color;
        }
        notebook.outlined-tabs > header.top > tabs > tab:checked {
            margin-bottom: -1px;
            padding-bottom: 8px;
            box-shadow: inset 0 3px @theme_selected_bg_color;
        }
        notebook.outlined-tabs > stack {
            background-color: @theme_bg_color;
            border: 1px solid alpha(@theme_fg_color, 0.30);
        }
        notebook.outlined-tabs > header.left + stack {
            border-left: none;
        }
        notebook.outlined-tabs > header.top + stack {
            border-top: none;
        }
    """)
    Gtk.StyleContext.add_provider_for_screen(notebooks[0].get_screen(), provider,
                                            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    return provider


class ResultList:
    def __init__(self, view):
        self.view = view
        self.columns = len(view.get_columns())
        n = self.columns
        self.model = Gtk.ListStore(*([str] * n + [GObject.TYPE_PYOBJECT, bool, str, str]))
        self.view.set_model(self.model)
        self.data = {}
        self.sort_column = 0
        self.sort_type = Gtk.SortType.ASCENDING
        selection = view.get_selection()
        selection.set_select_function(self._can_select)

    def _can_select(self, selection, model, path, selected, *args):
        return bool(model[path][self.columns + 1])

    def __getattr__(self, name):
        return getattr(self.view, name)

    @property
    def rows(self):
        return len(self.model)

    @property
    def selection(self):
        return [p.get_indices()[0] for p in self.view.get_selection().get_selected_rows()[1]]

    @property
    def focus_row(self):
        path = self.view.get_cursor()[0]
        return min(path.get_indices()[0] if path else 0, self.rows - 1)

    def append(self, values):
        values = list(values)
        values += [''] * (self.columns - len(values))
        self.model.append(values + [None, True, None, None])
        return self.rows - 1

    def clear(self):
        self.model.clear()
        self.data.clear()

    def remove(self, row):
        self.model.remove(self.model.get_iter(Gtk.TreePath.new_from_indices([row])))

    def get_text(self, row, column):
        return self.model[row][column]

    def set_text(self, row, column, text):
        self.model[row][column] = text

    def set_row_data(self, row, data):
        self.model[row][self.columns] = data

    def get_row_data(self, row):
        return self.model[row][self.columns]

    def find_row_from_data(self, data):
        for i, row in enumerate(self.model):
            if row[self.columns] == data:
                return i
        return -1

    def set_data(self, key, value):
        self.data[key] = value

    def get_data(self, key):
        return self.data.get(key)

    def set_selectable(self, row, selectable):
        self.model[row][self.columns + 1] = bool(selectable)
        if not selectable:
            self.unselect_row(row, 0)

    def get_selectable(self, row):
        return self.model[row][self.columns + 1]

    def set_foreground(self, row, color):
        self.model[row][self.columns + 2] = color

    def set_background(self, row, color):
        self.model[row][self.columns + 3] = color

    def select_row(self, row, column):
        if 0 <= row < self.rows:
            self.view.get_selection().select_path(Gtk.TreePath.new_from_indices([row]))

    def unselect_row(self, row, column):
        if 0 <= row < self.rows:
            self.view.get_selection().unselect_path(Gtk.TreePath.new_from_indices([row]))

    def select_all(self):
        self.view.get_selection().select_all()

    def unselect_all(self):
        self.view.get_selection().unselect_all()

    def get_selection_info(self, x, y):
        found = self.view.get_path_at_pos(x, y)
        if found:
            path, column, _, _ = found
            return path.get_indices()[0], self.view.get_columns().index(column)
        return None

    def moveto(self, row, column, row_align, col_align):
        if 0 <= row < self.rows:
            self.view.scroll_to_cell(Gtk.TreePath.new_from_indices([row]),
                                     self.view.get_column(column), True,
                                     row_align, col_align)

    def freeze(self):
        # Keep the model attached so selection and row indexes remain valid.
        self.view.freeze_notify()

    def thaw(self):
        self.view.thaw_notify()

    def columns_autosize(self):
        self.view.columns_autosize()

    def set_column_visibility(self, column, visible):
        self.view.get_column(column).set_visible(bool(visible))

    def set_column_justification(self, column, justification):
        col = self.view.get_column(column)
        col.set_alignment(1.0)
        for cell in col.get_cells():
            cell.set_property('xalign', 1.0)

    def set_sort_column(self, column):
        self.sort_column = column

    def set_sort_type(self, sort_type):
        self.sort_type = sort_type

    def sort(self):
        # Reorder the model once rather than enabling live sorting during edits.
        order = sorted(range(self.rows),
                       key=lambda i: self.model[i][self.sort_column],
                       reverse=self.sort_type == Gtk.SortType.DESCENDING)
        self.model.reorder(order)
        # GtkTreeSelection tracks rows across ListStore.reorder automatically.

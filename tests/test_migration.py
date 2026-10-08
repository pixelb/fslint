"""Migration regressions; GUI cases require a display (or xvfb-run)."""
import os
import hashlib
from pathlib import Path
import runpy
import shlex
import signal
import subprocess
import sys
import tempfile
import unittest
import warnings
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import fslint_gtk
old_argv = sys.argv
sys.argv = [str(ROOT / 'fslint-gui')]
GUI = runpy.run_path(str(ROOT / 'fslint-gui'), run_name='fslint_tests')
sys.argv = old_argv
Gtk = GUI['gtk']
HAS_DISPLAY = Gtk.init_check()[0]


def setUpModule():
    # PyGObject's event loop bridge emits Python 3.14 policy deprecations.
    warnings.filterwarnings('ignore', category=DeprecationWarning, module=r'gi\.events')


class PythonMigrationTests(unittest.TestCase):
    def command(self, source):
        return shlex.join([sys.executable, '-c', source])

    def test_pipe_output_preserves_filename_bytes(self):
        process = GUI['subProcess'](self.command(
            "import os; os.write(1,b'caf\\xc3\\xa9\\x00bad\\xff\\x00'); os.write(2,b'error\\n')"),
            bufsize=1)
        self.assertEqual(process.read(), 0)
        self.assertEqual(os.fsencode(process.outdata), b'caf\xc3\xa9\0bad\xff\0')
        self.assertEqual(process.errdata, 'error\n')
        self.assertEqual(process.read(), 0)
        self.assertEqual(process.cleanup(), 0)

    def test_both_pipes_are_drained_without_deadlock(self):
        process = GUI['subProcess'](self.command(
            "import os; os.write(1,b'x'*262144); os.write(2,b'y'*262144)"))
        process.read()
        self.assertEqual(len(process.outdata), 262144)
        self.assertEqual(len(process.errdata), 262144)
        self.assertEqual(process.cleanup(), 0)

    def test_process_group_pause_resume_and_cancel(self):
        process = GUI['subProcess']('sleep 30 & wait')
        self.assertEqual(os.getpgid(process.pid), process.pid)
        process.pause()
        self.assertEqual(process.read(timeout=0.01), 1)
        process.resume()
        process.kill()
        while process.read(timeout=0.1):
            pass
        self.assertEqual(process.cleanup(), -signal.SIGTERM)

    def test_display_text_is_safe_and_original_path_roundtrips(self):
        path = os.fsdecode(b'bad\xff\tname')
        self.assertEqual(os.fsencode(path), b'bad\xff\tname')
        text = GUI['I18N'].displayable_utf8(path)
        self.assertEqual(text, 'bad?\u2409name')
        text.encode('utf-8')
        self.assertEqual(GUI['I18N'].displayable_utf8('a\nb', '\n'), 'a\nb')

    def test_help_and_version(self):
        for option in ('--help', '--version'):
            result = subprocess.run([sys.executable, str(ROOT/'fslint-gui'), option],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout)

    def test_dupwaste(self):
        result = subprocess.run([str(ROOT/'fslint/fstool/dupwaste')],
                                input='3 x 100 bytes\n2 x 50 bytes\n',
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, 'Total wasted space: 250 bytes\n')

    def test_whitespace_scan_keeps_raw_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.fsencode(directory) + b'/bad\xff'
            with open(path, 'wb') as stream:
                stream.write(b'text   \n')
            result = subprocess.run([str(ROOT/'fslint/findrs'), '-w', '-f', directory],
                                    capture_output=True, check=True)
            self.assertEqual(result.stdout, path + b'\n')
            self.assertEqual(result.stderr, b'')

    def test_approximate_digest_reads_binary_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'binary'
            data = bytes(range(256)) * 4
            path.write_bytes(data)
            result = subprocess.run([str(ROOT/'fslint/supprt/md5sum_approx'), str(path)],
                                    capture_output=True, text=True, check=True)
            digest = hashlib.md5(data[:512], usedforsecurity=False).hexdigest()
            self.assertEqual(result.stdout, f'{digest}  {path}\n')

    def test_command_line_duplicate_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / 'first'
            second = Path(directory) / 'second'
            first.write_bytes(b'identical content\n')
            second.write_bytes(first.read_bytes())
            subprocess.run([str(ROOT/'fslint/findup'), '-m', directory],
                           capture_output=True, check=True)
            self.assertEqual(first.stat().st_ino, second.stat().st_ino)

    def test_hardlink_filter_preserves_raw_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            first = os.fsencode(directory) + b'/first\xff'
            second = os.fsencode(directory) + b'/second'
            linked = os.fsencode(directory) + b'/linked'
            for path in (first, second):
                with open(path, 'wb') as stream:
                    stream.write(b'identical content\n')
            os.link(first, linked)
            tool = str(ROOT/'fslint/supprt/rmlint/merge_hardlinks')
            data = first + b'\n' + second + b'\n'
            result = subprocess.run([tool, '--non-gui'], input=data,
                                    capture_output=True, check=True)
            self.assertEqual(result.stdout, data)
            result = subprocess.run([tool, '--non-gui'], input=first+b'\n'+linked+b'\n',
                                    capture_output=True, check=True)
            self.assertEqual(result.stdout, b'')


class AppearanceTests(unittest.TestCase):
    def follower(self, theme='Adwaita-dark', dark=False):
        values = {'gtk-theme-name': theme, 'gtk-application-prefer-dark-theme': dark}
        settings = Mock()
        settings.get_property.side_effect = values.__getitem__
        settings.set_property.side_effect = values.__setitem__
        follower = fslint_gtk.DesktopAppearance.__new__(fslint_gtk.DesktopAppearance)
        follower.settings = settings
        follower._initial_dark = dark
        return follower, values

    def test_portal_light_dark_and_default(self):
        follower, values = self.follower()
        for scheme, dark in [(2, False), (1, True), (0, False), (42, False)]:
            follower._setting_changed(None, None, 'SettingChanged',
                fslint_gtk.GLib.Variant('(ssv)', ('org.freedesktop.appearance',
                                                'color-scheme',
                                                fslint_gtk.GLib.Variant('u', scheme))))
            self.assertEqual(values['gtk-theme-name'], 'Adwaita')
            self.assertEqual(values['gtk-application-prefer-dark-theme'], dark)

    def test_no_preference_preserves_custom_theme(self):
        follower, values = self.follower('CustomTheme', True)
        follower._apply(2)
        self.assertFalse(values['gtk-application-prefer-dark-theme'])
        follower._apply(0)
        self.assertTrue(values['gtk-application-prefer-dark-theme'])
        self.assertEqual(values['gtk-theme-name'], 'CustomTheme')

    def test_explicit_gtk_theme_override(self):
        settings = Mock()
        with patch.dict(os.environ, {'GTK_THEME': 'Adwaita:dark'}), \
             patch.object(fslint_gtk.Gtk.Settings, 'get_default', return_value=settings), \
             patch.object(fslint_gtk.Gio.DBusProxy, 'new_for_bus') as connect:
            follower = fslint_gtk.DesktopAppearance()
            settings.set_property.assert_not_called()
            connect.assert_not_called()
            follower.close()

    def test_old_portal_read_fallback(self):
        follower, values = self.follower()
        follower.cancellable = fslint_gtk.Gio.Cancellable()
        follower._read = Mock()
        proxy = Mock()
        proxy.call_finish.side_effect = fslint_gtk.GLib.Error('ReadOne is unavailable')
        follower._read_ready(proxy, None, False)
        follower._read.assert_called_once_with(True)


@unittest.skipUnless(HAS_DISPLAY, 'GTK 3 needs a graphical display')
class GtkMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.old_cwd = os.getcwd()
        GUI['lArgs'][:] = [str(self.directory)]
        self.app = GUI['fslint'](str(ROOT/'fslint.ui'), 'fslint')
        self.app.pwd = self.old_cwd
        self.app.chk_sn_path.set_active(False)
        self.app.chk_ns_path.set_active(False)

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.app.dlgPath.GtkWindow.destroy()
        self.app.GtkWindow.destroy()
        self.temp.cleanup()

    def pump(self):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)

    def scan(self, mode):
        self.app.fslint_functions.set_current_page(mode)
        self.pump()
        self.app.on_find_clicked(None)
        buffer = self.app.errors.get_buffer()
        errors = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        self.assertEqual(errors, '')
        return self.app.clists[mode]

    def test_all_search_tabs(self):
        for name in ('first', 'second'):
            (self.directory/name).write_text('same content   \n')
        (self.directory/'empty').mkdir()
        (self.directory/'broken').symlink_to('missing')
        for mode in range(10):
            table = self.scan(mode)
            if mode in (0, 5, 7, 9):
                self.assertGreater(table.rows, 0, f'No results in tab {mode}')

    def test_group_selection_keeps_one_duplicate(self):
        for name in ('first', 'second', 'third'):
            (self.directory/name).write_text('identical\n')
        table = self.scan(0)
        self.assertEqual(table.rows, 4)
        table.select_all()
        self.assertEqual(table.selection, [1, 2, 3])
        self.app.on_select_all_but_one_in_each_group_activate('first')
        self.assertEqual(table.selection, [2, 3])
        self.app.on_select_all_but_one_in_each_group_activate('newest')
        self.assertEqual(len(table.selection), 2)

    def test_sort_preserves_package_metadata_and_selection(self):
        table = self.app.clist_pkgs
        for name, size in [('z', '0000000020'), ('a', '0000000100')]:
            row = table.append([name, size, size, '0'])
            table.set_row_data(row, name)
        table.select_row(0, 0)
        table.set_sort_column(2)
        table.set_sort_type(Gtk.SortType.DESCENDING)
        table.sort()
        self.assertEqual(table.get_row_data(0), 'a')
        self.assertEqual(table.get_row_data(table.selection[0]), 'z')
        table.remove(0)
        self.assertEqual(table.get_row_data(0), 'z')

    def test_dialog_response_and_entry(self):
        dialog = GUI['dlgUserInteraction'](str(ROOT/'fslint.ui'), 'UserInteraction')
        dialog.init(self.app, 'Rename:', ('Cancel', 'Ok'), 'new name', again=True)
        GUI['GLib'].idle_add(lambda: (dialog.button_clicked(
            dialog.buttons[-1]), False)[1])
        dialog.show()
        self.assertEqual(dialog.response, 'Ok')
        self.assertEqual(dialog.input, 'new name')
        self.assertTrue(dialog.again)

    def test_invalid_utf8_results_and_export(self):
        path = os.fsencode(self.directory) + b'/bad\xff'
        with open(path, 'wb') as stream:
            stream.write(b'text   \n')
        self.app.chk_findu8.set_active(True)
        table = self.scan(2)
        self.assertEqual(table.rows, 1)
        self.assertEqual(os.fsencode(table.get_data('row_data')[0][:-1]), path)
        table.select_row(0, 0)
        selected = self.app.get_selected_path()
        self.assertIn('%FF', selected)
        output = self.directory/'results.txt'
        chooser = self.app.dlgPath
        chooser.show = lambda **kwargs: None
        chooser.canceled = False
        chooser.GtkWindow.get_filename = lambda: str(output)
        self.app.on_saveAs_clicked(None)
        self.assertEqual(output.read_bytes(), path + b'\n')

    def test_live_appearance_refreshes_group_headers(self):
        for name in ('first', 'second'):
            (self.directory/name).write_text('identical\n')
        table = self.scan(0)
        follower = self.app.appearance
        # Simulate portal events locally; never change the user's desktop settings.
        follower.close()
        settings = follower.settings
        theme = settings.get_property('gtk-theme-name')
        dark = settings.get_property('gtk-application-prefer-dark-theme')
        try:
            colors = []
            for scheme in (2, 1):
                follower._setting_changed(None, None, 'SettingChanged',
                    fslint_gtk.GLib.Variant('(ssv)', ('org.freedesktop.appearance',
                                                    'color-scheme',
                                                    fslint_gtk.GLib.Variant('u', scheme))))
                loop = GUI['GLib'].MainLoop()
                GUI['GLib'].timeout_add(100, lambda: (loop.quit(), False)[1])
                loop.run()
                self.assertEqual(settings.get_property('gtk-application-prefer-dark-theme'),
                                 scheme == 1)
                color = self.app.bg_colour
                self.assertEqual(table.model[0][table.columns + 3], color)
                colors.append(color)
            self.assertNotEqual(*colors)
        finally:
            settings.set_property('gtk-theme-name', theme)
            settings.set_property('gtk-application-prefer-dark-theme', dark)

    def test_rename_delete_and_merge_temporary_files(self):
        for name in ('first', 'second', 'third'):
            (self.directory/name).write_text('identical\n')
        table = self.scan(0)
        self.app.msgbox = lambda *args, **kwargs: ('Yes',)
        self.app.on_autoMerge(symlink=False)
        self.assertEqual(len({p.stat().st_ino for p in self.directory.iterdir()}), 1)
        # Scan an ordinary path tab for rename and delete.
        odd = self.directory/' bad name '
        odd.write_text('different\n')
        table = self.scan(2)
        index = next(i for i, p in enumerate(table.get_data('row_data')) if str(odd) == p[:-1])
        table.select_row(index, 0)
        self.app.msgbox = lambda *args, **kwargs: ('Ok', 'renamed')
        self.app.on_rename_activate(None)
        renamed = self.directory/'renamed'
        self.assertTrue(renamed.exists())
        # Supply this fixture as a result to exercise deletion without rescanning.
        table.clear(); table.set_data('row_data', [str(renamed)+'\n'])
        table.append(['renamed', str(self.directory)])
        table.select_row(0, 0)
        self.app.confirm_delete = False
        self.app.confirm_delete_group = False
        self.app.on_delSelected_clicked(None)
        self.assertFalse(renamed.exists())


if __name__ == '__main__':
    unittest.main()

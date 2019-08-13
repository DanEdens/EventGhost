# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright Â© 2005-2016 EventGhost Project <http://www.eventghost.org/>
#
# EventGhost is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# EventGhost is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with EventGhost. If not, see <http://www.gnu.org/licenses/>.

import eg


eg.RegisterPlugin(
    name=u'WindowsVirtualDesktop',
    author=u'Kevin Schlosser',
    version=u'0.1.0a',
    description=u'Control of the Windows 10 Virtual Desktop',
    kind=u'other',
    canMultiLoad=False,
    createMacrosOnAdd=True,
    guid=u'{04A19D5E-0C69-4E58-BF7B-DD128A6F6EF6}',
)

import wx # NOQA
import sys # NOQA
import os # NOQA

pyWinVirtualDesktop = None

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

if 'MakeIDEHappy' in os.environ:
    import pyWinVirtualDesktop as _pyWinVirtualDesktop

    pyWinVirtualDesktop = _pyWinVirtualDesktop


class Text:
    # add variables with string that you want to be able to have translated
    # using the language editor in here

    window_label = 'Window Name:'
    name_label = 'Desktop Name:'
    number_label = 'Desktop Number:'

    class GetDesktopNameFromNumber:
        name = u'Get Desktop Name From Number'
        description = 'Get Desktop Name From Number'


    class SetDesktopNameFromNumber:
        name = u'Set Desktop Name From Number'
        description = 'Set Desktop Name From Number'


    class LeftDesktop:
        name = u'Left Desktop'
        description = 'Left Desktop'


    class RightDesktop:
        name = u'Right Desktop'
        description = 'Right Desktop'


    class GetDesktopId:
        name = u'Get Desktop Id'
        description = 'Get Desktop Id'


    class MoveWindowToDesktop:
        name = u'Move Window To Desktop'
        description = 'Action Move Window To Desktop'


    class DesktopHasWindow:
        name = u'Desktop Has Window'
        description = 'Desktop Has Window'


    class IsDesktopActive:
        name = u'Is Desktop Active'
        description = 'Is Desktop Active'


    class DestroyDesktop:
        name = u'Destroy Desktop'
        description = 'Destroy Desktop'


    class GetDesktopWindows:
        name = u'Get Desktop Windows'
        description = 'Get Desktop Windows'


    class GetDesktops:
        name = u'Get Desktops'
        description = 'Get Desktops'


    class IsAppPinned:
        name = u'Is App Pinned'
        description = 'Is App Pinned'


    class PinApp:
        name = u'Pin App'
        description = 'Pin App'

    class UnPinApp:
        name = u'Unpin App'
        description = 'Unpin App'


    class ShowAppInSwitchers:
        name = u'Show App In Switchers'
        description = 'Show App In Switchers'


    class IsAppShownInSwitchers:
        name = u'Is App Shown In Switchers'
        description = 'Is App Shown In Switchers'


    class IsAppInTray:
        name = u'Is App In Tray'
        description = 'Is App In Tray'


    class CanAppReceiveInput:
        name = u'Can App Receive Input'
        description = 'Can App Receive Input'


    class IsAppMirrored:
        name = u'Is App Mirrored'
        description = 'Action Is App Mirrored'


    class IsAppSplashScreenPresented:
        name = u'Is App Splash Screen Presented'
        description = 'Is App Splash Screen Presented'


    class FlashApp:
        name = u'Flash App'
        description = 'Flash App'


    class ActivateApp:
        name = u'Activate App'
        description = 'Activate App'


    class AppHasFocus:
        name = u'App Has Focus'
        description = 'App Has Focus'


    class SetAppFocus:
        name = u'Set App Focus'
        description = 'Set App Focus'


    class IsAppVisible:
        name = u'Is App Visible'
        description = 'Is App Visible'


class WindowsVirtualDesktop(eg.PluginBase):
    text = Text

    # you want to add any variables that can be access from anywhere inside of
    # your plugin here
    def __init__(self):
        eg.PluginBase.__init__(self)

        self.AddAction(GetDesktopNameFromNumber)
        self.AddAction(SetDesktopNameFromNumber)
        self.AddAction(LeftDesktop)
        self.AddAction(RightDesktop)
        self.AddAction(GetDesktopId)
        self.AddAction(MoveWindowToDesktop)
        self.AddAction(DesktopHasWindow)
        self.AddAction(IsDesktopActive)
        self.AddAction(DestroyDesktop)
        self.AddAction(GetDesktopWindows)
        self.AddAction(GetDesktops)
        self.AddAction(IsAppPinned)
        self.AddAction(PinApp)
        self.AddAction(ShowAppInSwitchers)
        self.AddAction(IsAppShownInSwitchers)
        self.AddAction(IsAppInTray)
        self.AddAction(CanAppReceiveInput)
        self.AddAction(IsAppMirrored)
        self.AddAction(IsAppSplashScreenPresented)
        self.AddAction(FlashApp)
        self.AddAction(ActivateApp)
        self.AddAction(AppHasFocus)
        self.AddAction(SetAppFocus)
        self.AddAction(IsAppVisible)

    def __start__(self, *args):
        if BASE_PATH not in sys.path:
            sys.path.insert(0, BASE_PATH)
            
        global pyWinVirtualDesktop

        import pyWinVirtualDesktop as _pyWinVirtualDesktop

        pyWinVirtualDesktop = _pyWinVirtualDesktop

    def __stop__(self):
        if BASE_PATH not in sys.path:
            sys.path.remove(BASE_PATH)


def h_sizer(*ctrls):
    sizer = wx.BoxSizer(wx.HORIZONTAL)

    for ctrl in ctrls:
        sizer.Add(ctrl, 0, wx.ALL | wx.EXPAND, 5)
    return sizer


class NameBase(eg.ActionBase):

    def Configure(self, desktop_name=''):
        panel = eg.ConfigPanel()

        choices = sorted(
            list(desktop.name for desktop in pyWinVirtualDesktop)
        )

        name_label = panel.StaticText(Text.name_label)
        name_ctrl = wx.Choice(self, -1, choices=choices)

        if desktop_name in choices:
            name_ctrl.SetStringSelection(desktop_name)
        else:
            name_ctrl.SetSelection(0)

        panel.sizer.Add(h_sizer(name_label, name_ctrl), 0)

        while panel.Affirmed():
            panel.SetResult(name_ctrl.GetStringSelection())


class WindowBase(eg.ActionBase):

    def Configure(self, desktop_name='', window_name=''):
        panel = eg.ConfigPanel()

        choices = sorted(
            list(desktop.name for desktop in pyWinVirtualDesktop)
        )

        name_label = panel.StaticText(Text.name_label)
        name_ctrl = wx.Choice(self, -1, choices=choices)

        if desktop_name in choices:
            name_ctrl.SetStringSelection(desktop_name)
        else:
            name_ctrl.SetSelection(0)

        window_label = panel.StaticText(Text.window_label)

        choices = []
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                choices += [window.text]

        window_ctrl = wx.Choice(self, -1, choices=sorted(choices))

        if window_name in choices:
            window_ctrl.SetStringSelection(window_name)
        else:
            window_ctrl.SetSelection(0)

        panel.sizer.Add(h_sizer(name_label, name_ctrl), 0)
        panel.sizer.Add(h_sizer(window_label, window_ctrl), 0)

        while panel.Affirmed():
            panel.SetResult(
                name_ctrl.GetStringSelection(),
                window_ctrl.GetStringSelection()
            )


class JustWindowBase(eg.ActionBase):

    def Configure(self, window_name=''):
        panel = eg.ConfigPanel()

        window_label = panel.StaticText(Text.window_label)

        choices = []
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                choices += [window.text]

        window_ctrl = wx.Choice(self, -1, choices=sorted(choices))

        if window_name in choices:
            window_ctrl.SetStringSelection(window_name)
        else:
            window_ctrl.SetSelection(0)

        panel.sizer.Add(h_sizer(window_label, window_ctrl), 0)

        while panel.Affirmed():
            panel.SetResult(
                window_ctrl.GetStringSelection()
            )


class GetDesktopNameFromNumber(eg.ActionBase):

    def __call__(self, desktop_number):
        for desktop in pyWinVirtualDesktop:
            if desktop.number == desktop_number:
                break

        else:
            eg.PrintError('Desktop ' + str(desktop_number) + ' not found.')
            return

        return desktop.name

    def Configure(self, desktop_number=1):
        panel = eg.ConfigPanel()

        number_label = panel.StaticText(Text.number_label)
        number_ctrl = panel.SpinIntCtrl(desktop_number, min=1)

        panel.sizer.Add(h_sizer(number_label, number_ctrl), 0)

        while panel.Affirmed():
            panel.SetResult(number_ctrl.GetValue())


class SetDesktopNameFromNumber(eg.ActionBase):

    def __call__(self, desktop_number, desktop_name):
        for desktop in pyWinVirtualDesktop:
            if desktop.number == desktop_number:
                break

        else:
            eg.PrintError('Desktop ' + str(desktop_number) + ' not found.')
            return

        desktop.name = desktop_name

    def Configure(self, desktop_number=1, desktop_name=''):
        panel = eg.ConfigPanel()

        number_label = panel.StaticText(Text.number_label)
        number_ctrl = panel.SpinIntCtrl(desktop_number, min=1)

        name_label = panel.StaticText(Text.name_label)
        name_ctrl = panel.TextCtrl(desktop_name)

        panel.sizer.Add(h_sizer(number_label, number_ctrl), 0)
        panel.sizer.Add(h_sizer(name_label, name_ctrl), 0)

        while panel.Affirmed():
            panel.SetResult(number_ctrl.GetValue(), name_ctrl.GetValue())


class LeftDesktop(NameBase):

    def __call__(self, desktop_name):
        for desktop in pyWinVirtualDesktop:
            if desktop.name == desktop_name:
                break
        else:
            eg.PrintError('Desktop ' + desktop_name + ' not found.')
            return

        return desktop.desktop_to_left


class RightDesktop(NameBase):

    def __call__(self, desktop_name):
        for desktop in pyWinVirtualDesktop:
            if desktop.name == desktop_name:
                break
        else:
            eg.PrintError('Desktop ' + desktop_name + ' not found.')
            return

        return desktop.desktop_to_right


class GetDesktopId(NameBase):

    def __call__(self, desktop_name):
        for desktop in pyWinVirtualDesktop:
            if desktop.name == desktop_name:
                break
        else:
            eg.PrintError('Desktop ' + desktop_name + ' not found.')
            return

        return desktop.id


class MoveWindowToDesktop(WindowBase):

    def __call__(self, desktop_name, window_name):
        found_desktop = None
        found_window = None

        for desktop in pyWinVirtualDesktop:
            if desktop.name == desktop_name:
                found_desktop = desktop

            for window in desktop:
                if window.text == window_name:
                    found_window = window

        if found_desktop is None:
            eg.PrintNotice('Desktop ' + desktop_name + ' not found.')
            return

        if found_window is None:
            eg.PrintNotice('Window ' + window_name + ' not found.')
            return

        found_desktop.add_window(found_window)


class DesktopHasWindow(WindowBase):

    def __call__(self, desktop_name, window_name):
        for desktop in pyWinVirtualDesktop:
            if desktop.name == desktop_name:
                break
        else:
            eg.PrintError('Desktop ' + desktop_name + ' not found.')
            return False

        for window in desktop:
            if window.text == window_name:
                return True

        return False


class IsDesktopActive(NameBase):

    def __call__(self, desktop_name):
        for desktop in pyWinVirtualDesktop:
            if desktop.name == desktop_name:
                break
        else:
            eg.PrintError('Desktop ' + desktop_name + ' not found.')
            return False

        return desktop.is_active


class DestroyDesktop(NameBase):

    def __call__(self, desktop_name):
        for desktop in pyWinVirtualDesktop:
            if desktop.name == desktop_name:
                break
        else:
            eg.PrintError('Desktop ' + desktop_name + ' not found.')
            return

        desktop.destroy()


class GetDesktopWindows(NameBase):

    def __call__(self, desktop_name):
        for desktop in pyWinVirtualDesktop:
            if desktop.name == desktop_name:
                break
        else:
            eg.PrintError('Desktop ' + desktop_name + ' not found.')
            return []

        return list(window for window in desktop)


class GetDesktops(eg.ActionBase):

    def __call__(self):
        return list(desktop for desktop in pyWinVirtualDesktop)


class IsAppPinned(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return False

        return window.view.pinned


class PinApp(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return

        window.view.pinned = True


class UnPinApp(JustWindowBase):
    def __call__(self, app_name):

        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue

            break

        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return

        window.view.pinned = False


class ShowAppInSwitchers(eg.ActionBase):

    def __call__(self, *args):
        pass

    def Configure(self, *args):
        text = self.text
        panel = eg.ConfigPanel()

        while panel.Affirmed():
            panel.SetResult()


class IsAppShownInSwitchers(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return False

        return window.view.show_in_switchers


class IsAppInTray(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return False

        return window.view.is_tray


class CanAppReceiveInput(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return False

        return window.view.can_receive_input


class IsAppMirrored(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return False

        return window.view.is_mirrored


class IsAppSplashScreenPresented(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return False

        return window.view.is_splash_screen_presented


class FlashApp(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return

        return window.view.flash()


class ActivateApp(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return

        return window.view.activate()


class AppHasFocus(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return False

        return window.view.has_focus


class SetAppFocus(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return

        return window.view.set_focus()


class IsAppVisible(JustWindowBase):

    def __call__(self, app_name):
        for desktop in pyWinVirtualDesktop:
            for window in desktop:
                if window.text == app_name:
                    break
            else:
                continue
            break
        else:
            eg.PrintError('App ' + app_name + ' not found.')
            return False

        return window.view.is_visible

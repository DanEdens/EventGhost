# -*- coding: utf-8 -*-

version="1.0.1"

#
# plugins/MouseEvent/__init__.py
#
# Copyright (C) 2012 by Daniel Brugger
#
# Version history (newest on top):
# 1.0.1    Fix: StopMouseEventListener was broken in 1.0.0
#          Fix: After several suspend-resume cycles, the MouseListener stopped producing mouse events.
#          Fix: MouseEventListener instantiation on __start__(), not on __init__()
#          Impr: Code cleanup and maintenance
# 1.0.0    First official release
# 0.1.3    Option "Filter move events by distance" improved. The initial events are now filtered until minDistance reached.
#          On some systems I got ghost events (i.e. events without moving the mouse) after start and I want to suppress them.
# 0.1.2    Fix: Restore event configuration after system resume
#          Impr: new option to filter move events with a distance smaller than a configurable value
# 0.1.1    Fix: trigger move events even if coalesce == False
#          Unnecessary imports removed, URL added
#          Impr: filter ghost move events, i.e. events with same position as previous one
# 0.1.0    Initial version
#
# This file is part of EventGhost.
#
# EventGhost is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# EventGhost is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EventGhost; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import eg

eg.RegisterPlugin(
    name="Mouse Event",
    author="Daniel Brugger",
    version=version,
    kind="remote",
    guid="{CBF73261-23E4-452A-8B3C-4EE7DD19930F}",
    createMacrosOnAdd = True,
    url="http://www.eventghost.net/forum/viewtopic.php?f=9&t=3720",
    description=(
        'Fires mouse events on mouse actions like moves, clicks and wheel.'
    ),
    icon = (
        "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAMAAABhq6zVAAAAFHRFWHRDcmVhdGlvbiBU"
        "aW1lAAfcAgcKCzhrrOQAAAAHdElNRQfcAgcMHAiviTEmAAAACXBIWXMAAArwAAAK8AFC"
        "rDSYAAADAFBMVEVaGAhrQjFzMRhzOSmEQimUKQiUUjmlKQi9MQi9Wjm9jHu9lITG/8bO"
        "SiHOUinOWjHOY0LOY0rOa0rWUinWUjHWpZTWrZzeOQjehGvelITeta3nUiHne1rnvbXv"
        "xr33OQD3Win3c0r3c1L3hGP3zsb31sb33t7359735+f/Qgj/ShD/WiH/azn/a0L/c0r/"
        "e1L/hFr/hGP/jGP/jGv/1s7/3tb/9+//9/f/////////////////////////////////"
        "////////////////////////////////////////////////////////////////////"
        "////////////////////////////////////////////////////////////////////"
        "////////////////////////////////////////////////////////////////////"
        "////////////////////////////////////////////////////////////////////"
        "////////////////////////////////////////////////////////////////////"
        "////////////////////////////////////////////////////////////////////"
        "////////////////////////////////////////////////////////////////////"
        "////////////////////////////////////////////////////////////////////"
        "////////////////////////////////////////////////////////////////////"
        "////////////////////////////////////////////////////////////////////"
        "////////////////////////////////////////////////////////////////////"
        "//////////////////+fdX+GAAAADXRSTlP///////////////8APegihgAAAHBJREFU"
        "eNpj4FEXU+OBAgYedU4+STM4R0BfgV8OxhEy1NMWlzCDcowNdLTk+VTAHEFjY31tTXkO"
        "UbAeA2NDXXYGRm4Qh19PyUhf2gSih5+XSdlQVwbCYWFWMzHQl4YYIKXOw2OkyMoF5oCs"
        "M2WTBZIAIcwNqtwIphAAAAAASUVORK5CYII="
    )
)

# This plugin requires the additional pyHook library which is currently not part of EventGhost (as of 4.1)
# It can be downloaded from http://sourceforge.net/apps/mediawiki/pyhook
# It has to be installed under EventGhost\lib26\site-packages\pyHook

import wx
import pyHook
import math
from threading import Lock


class MouseEvent(eg.PluginBase):
    class Text:
        header = "Hint: Call action 'Start Mouse Event Listener' in order to start receiving mouse events."
        notStarted = "Plugin is not started, event was ignored"
    
    @eg.LogIt
    def __init__(self):
        self.AddAction(StartMouseEventListener)
        self.AddAction(StopMouseEventListener)
        self.AddAction(GetLastMouseEvent)
        self.AddAction(GetLastMoveEvent)
        self.AddAction(GetLastLeftClickEvent)
        self.AddAction(GetLastMiddleClickEvent)
        self.AddAction(GetLastRightClickEvent)
        self.AddAction(GetLastWheelEvent)
        self.started = False
        
    @eg.LogIt
    def __start__(self):
        eg.PrintDebugNotice("MouseEvent " + version)
        self.mouseListener = MouseEventListener(self)
        self.started = True
        
    @eg.LogItWithReturn
    def __stop__(self):
        self.started = False
        self.mouseListener.Stop()
        del self.mouseListener
        
    def __close__(self):
        pass
        
    @eg.LogIt
    def __del__(self):
        if self.started:
            self.__stop__()
        
    @eg.LogIt
    def Configure(self):
        panel = eg.ConfigPanel()
        gridSizer = wx.GridBagSizer(10, 5)
        gridSizer.Add(wx.StaticText(panel, -1, self.Text.header), (0, 0), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        panel.sizer.Add(gridSizer)
        while panel.Affirmed():
            panel.SetResult()

    @eg.LogIt
    def OnComputerSuspend(self, suspendType):
        if self.started:
            self.mouseListener.Stop()

    @eg.LogIt
    def OnComputerResume(self, suspendType):
        if self.started:
            self.mouseListener.Restart()


class StartMouseEventListener(eg.ActionBase):
    name = "Start Mouse Event Listener"
    description = "Start listening on mouse events"

    class Text:
        header = "Fire mouse events for"
        allEvents = "All mouse actions"
        mMove = "Mouse move"
        mLeftClick = "Mouse left click"
        mMiddleClick = "Mouse middle click"
        mRightClick = "Mouse right click"
        mWheel = "Mouse wheel"
        coalesce1 = "Coalesce move events: Fire not more than"
        coalesce2 = "events per second."
        filter1 = "Filter move events with a distance smaller or equal than"
        filter2 = "pixel."

    @eg.LogIt
    def __call__(self,
        mouseLeftClick=True, 
        mouseMiddleClick=True, 
        mouseRightClick=True, 
        mouseWheel=True, 
        mouseMove=True, 
        coalesce=True, 
        repeatRate=2.0,
        minDistFilter=True,
        minDistance=2
    ):
        plugin = self.plugin

        if not plugin.started:
            self.PrintError(plugin.text.notStarted)
            return False
        
        plugin.mouseListener.Start(
            mouseLeftClick, 
            mouseMiddleClick, 
            mouseRightClick, 
            mouseWheel, 
            mouseMove,
            coalesce, 
            repeatRate,
            minDistFilter,
            minDistance
        )

    @eg.LogIt
    def Configure(self, 
        mouseLeftClick=True, 
        mouseMiddleClick=True, 
        mouseRightClick=True, 
        mouseWheel=True, 
        mouseMove=True, 
        coalesce=True, 
        repeatRate=2.0,
        minDistFilter=True,
        minDistance=1
    ):
        def onAllEventsCheckBox(event):
            selected = allEventsCheckBoxCtrl.GetValue()
            mLeftClickCheckBoxCtrl.SetValue(selected)
            mMiddleClickCheckBoxCtrl.SetValue(selected)
            mRightClickCheckBoxCtrl.SetValue(selected)
            mWheelCheckBoxCtrl.SetValue(selected)
            mMoveCheckBoxCtrl.SetValue(selected)
            onGuiChange(event)
            event.Skip()
            
        def onGuiChange(event):
            allEventsCheckBoxCtrl.SetValue(
                mLeftClickCheckBoxCtrl.GetValue() 
                and mMiddleClickCheckBoxCtrl.GetValue() 
                and mRightClickCheckBoxCtrl.GetValue() 
                and mWheelCheckBoxCtrl.GetValue() 
                and mMoveCheckBoxCtrl.GetValue() )
            enable = mMoveCheckBoxCtrl.GetValue()
            coalesceCheckBoxCtrl.Enable(enable)
            repeatRateNumCtrl.Enable(enable and coalesceCheckBoxCtrl.GetValue())
            minDistCheckBoxCtrl.Enable(enable)
            minDistNumCtrl.Enable(enable and minDistCheckBoxCtrl.GetValue())
            event.Skip()

        def onCoalesceCheckBox(event):
            repeatRateNumCtrl.Enable(coalesceCheckBoxCtrl.GetValue())
            event.Skip()
            
        def onMinDistCheckBox(event):
            minDistNumCtrl.Enable(minDistCheckBoxCtrl.GetValue())
            event.Skip()

        panel = eg.ConfigPanel(self)
        text = self.Text
        
        allEventsCheckBoxCtrl = wx.CheckBox(panel, -1, text.allEvents)
        allEventsCheckBoxCtrl.SetValue(mouseLeftClick and mouseMiddleClick and mouseRightClick and mouseWheel and mouseMove)
        allEventsCheckBoxCtrl.Bind(wx.EVT_CHECKBOX, onAllEventsCheckBox)
        
        mLeftClickCheckBoxCtrl = wx.CheckBox(panel, -1, text.mLeftClick)
        mLeftClickCheckBoxCtrl.SetValue(mouseLeftClick)
        mLeftClickCheckBoxCtrl.Bind(wx.EVT_CHECKBOX, onGuiChange)

        mMiddleClickCheckBoxCtrl = wx.CheckBox(panel, -1, text.mMiddleClick)
        mMiddleClickCheckBoxCtrl.SetValue(mouseMiddleClick)
        mMiddleClickCheckBoxCtrl.Bind(wx.EVT_CHECKBOX, onGuiChange)

        mRightClickCheckBoxCtrl = wx.CheckBox(panel, -1, text.mRightClick)
        mRightClickCheckBoxCtrl.SetValue(mouseRightClick)
        mRightClickCheckBoxCtrl.Bind(wx.EVT_CHECKBOX, onGuiChange)

        mWheelCheckBoxCtrl = wx.CheckBox(panel, -1, text.mWheel)
        mWheelCheckBoxCtrl.SetValue(mouseWheel)
        mWheelCheckBoxCtrl.Bind(wx.EVT_CHECKBOX, onGuiChange)
        
        mMoveCheckBoxCtrl = wx.CheckBox(panel, -1, text.mMove)
        mMoveCheckBoxCtrl.SetValue(mouseMove)
        mMoveCheckBoxCtrl.Bind(wx.EVT_CHECKBOX, onGuiChange)

        coalesceCheckBoxCtrl = wx.CheckBox(panel, -1, text.coalesce1)
        coalesceCheckBoxCtrl.SetValue(coalesce)
        coalesceCheckBoxCtrl.Bind(wx.EVT_CHECKBOX, onCoalesceCheckBox)
        repeatRateNumCtrl = panel.SpinNumCtrl(repeatRate, min=0, max=999.999, fractionWidth=3, integerWidth=3)

        minDistCheckBoxCtrl = wx.CheckBox(panel, -1, text.filter1)
        minDistCheckBoxCtrl.SetValue(minDistFilter)
        minDistCheckBoxCtrl.Bind(wx.EVT_CHECKBOX, onMinDistCheckBox)
        minDistNumCtrl = panel.SpinNumCtrl(minDistance, min=1, max=9999, fractionWidth=0, integerWidth=4)
        
        gridSizer = wx.GridBagSizer(10, 5)

        rowCount = 0
        gridSizer.Add(wx.StaticText(panel, -1, text.header), (rowCount, 0),flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        rowCount += 1
        gridSizer.Add(allEventsCheckBoxCtrl, (rowCount, 0), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        rowCount += 1
        gridSizer.Add(mLeftClickCheckBoxCtrl, (rowCount, 0), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        rowCount += 1
        gridSizer.Add(mMiddleClickCheckBoxCtrl, (rowCount, 0), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        rowCount += 1
        gridSizer.Add(mRightClickCheckBoxCtrl, (rowCount, 0), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        rowCount += 1
        gridSizer.Add(mWheelCheckBoxCtrl, (rowCount, 0), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        rowCount += 1
        gridSizer.Add(mMoveCheckBoxCtrl, (rowCount, 0), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        rowCount += 1
        gridSizer.Add(coalesceCheckBoxCtrl, (rowCount, 0), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(repeatRateNumCtrl, (rowCount, 1), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(wx.StaticText(panel, -1, text.coalesce2), (rowCount, 2),flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        rowCount += 1
        gridSizer.Add(minDistCheckBoxCtrl, (rowCount, 0), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(minDistNumCtrl, (rowCount, 1), flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(wx.StaticText(panel, -1, text.filter2), (rowCount, 2),flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)

        panel.sizer.Add(gridSizer)
        onGuiChange(wx.CommandEvent())

        while panel.Affirmed():
            if repeatRateNumCtrl.GetValue() <= 0.00001:
                repeatRate = 0.0
                coalesce = False
            else:
                repeatRate = repeatRateNumCtrl.GetValue()
                coalesce = coalesceCheckBoxCtrl.GetValue()
            panel.SetResult(
                mLeftClickCheckBoxCtrl.GetValue(), 
                mMiddleClickCheckBoxCtrl.GetValue(), 
                mRightClickCheckBoxCtrl.GetValue(), 
                mWheelCheckBoxCtrl.GetValue(), 
                mMoveCheckBoxCtrl.GetValue(), 
                coalesce, 
                repeatRate,
                minDistCheckBoxCtrl.GetValue(),
                minDistNumCtrl.GetValue()
            )


class StopMouseEventListener(eg.ActionBase):
    name = "Stop Mouse Event Listener"
    description = "Stop listening on mouse events"

    @eg.LogIt
    def __call__(self):
        if not self.plugin.started:
            self.PrintError(self.plugin.text.notStarted)
            return False
        self.plugin.mouseListener.Stop()


class GetLastMouseEvent(eg.ActionBase):
    name = "Get last Mouse Event"
    description = "Gets the event details of the last mouse event regardless of its type. Provides result in 'eg.result'."

    @eg.LogIt
    def __call__(self):
        if not self.plugin.started:
            self.PrintError(self.plugin.text.notStarted)
            return False
        return self.plugin.mouseListener.GetLastEvent()


class GetLastMoveEvent(eg.ActionBase):
    name = "Get last Mouse Move Event"
    description = "Gets the event details of the last mouse move event. Provides result in 'eg.result'."

    @eg.LogIt
    def __call__(self):
        if not self.plugin.started:
            self.PrintError(self.plugin.text.notStarted)
            return False
        return self.plugin.mouseListener.GetLastMoveEvent()


class GetLastLeftClickEvent(eg.ActionBase):
    name = "Get last Mouse Left Click Event"
    description = "Gets the event details of the last mouse left click event. Provides result in 'eg.result'."

    @eg.LogIt
    def __call__(self):
        if not self.plugin.started:
            self.PrintError(self.plugin.text.notStarted)
            return False
        return self.plugin.mouseListener.GetLastLeftClickEvent()


class GetLastMiddleClickEvent(eg.ActionBase):
    name = "Get last Mouse Middle Click Event"
    description = "Gets the event details of the last mouse middle click event. Provides result in 'eg.result'."

    @eg.LogIt
    def __call__(self):
        if not self.plugin.started:
            self.PrintError(self.plugin.text.notStarted)
            return False
        return self.plugin.mouseListener.GetLastMiddleClickEvent()


class GetLastRightClickEvent(eg.ActionBase):
    name = "Get last Mouse Right Click Event"
    description = "Gets the event details of the last mouse right click event. Provides result in 'eg.result'."

    @eg.LogIt
    def __call__(self):
        if not self.plugin.started:
            self.PrintError(self.plugin.text.notStarted)
            return False
        return self.plugin.mouseListener.GetLastRightClickEvent()


class GetLastWheelEvent(eg.ActionBase):
    name = "Get last Mouse Wheel Event"
    description = "Gets the event details of the last mouse wheel event. Provides result in 'eg.result'."

    @eg.LogIt
    def __call__(self):
        if not self.plugin.started:
            self.PrintError(self.plugin.text.notStarted)
            return False
        return self.plugin.mouseListener.GetLastWheelEvent()


class MouseEventListener(object):
    """Basic listener for all mouse events.
    """
    @eg.LogIt
    def __init__(
        self,
        plugin,
    ):
        self.plugin = plugin
        self.lock = Lock() # thread synchronization
        self._resetEventData()
        self.listenerStarted = False

    def _resetEventData(self):
        self.lastLeftClickEvent = None
        self.lastMiddleClickEvent = None
        self.lastRightClickEvent = None
        self.lastMoveEvent = None
        self.lastWheelEvent = None
        self.lastEvent = None
        self.lastTriggeredMoveEvent = None

    @eg.LogIt
    def Start(self,
        mouseLeftClick, 
        mouseMiddleClick, 
        mouseRightClick, 
        mouseWheel, 
        mouseMove,
        coalesce, 
        repeatRate,
        minDistFilter,
        minDistance
    ):
        if self.listenerStarted:
            self.Stop()

        self.lock.acquire()
        try:

            self.hm = pyHook.HookManager()
            self._resetEventData()
            self.listenerStarted = True
    
            self.mouseLeftClick   = mouseLeftClick 
            self.mouseMiddleClick = mouseMiddleClick
            self.mouseRightClick  = mouseRightClick 
            self.mouseWheel       = mouseWheel 
            self.mouseMove        = mouseMove
            self.coalesce         = coalesce 
            self.repeatRate       = repeatRate
            self.minDistFilter    = minDistFilter
            self.minDistance      = minDistance

            self.minTimeDiff = 1000 / repeatRate
            
            if not minDistFilter:
                self.minDistance = -1
            
            if mouseLeftClick:
                self.hm.MouseLeftUp = self.OnMouseEvent
            else:
                self.hm.MouseLeftUp = None
                
            if mouseMiddleClick:
                self.hm.MouseMiddleUp = self.OnMouseEvent
            else:
                self.hm.MouseMiddleUp = None
                
            if mouseRightClick:
                self.hm.MouseRightUp = self.OnMouseEvent
            else:
                self.hm.MouseRightUp = None
                
            if mouseWheel:
                self.hm.MouseWheel = self.OnMouseEvent
            else:
                self.hm.MouseWheel = None
                
            if mouseMove:
                self.hm.MouseMove = self.OnMouseEvent
            else:
                self.hm.MouseMove = None
    
            # start listening events
            wx.CallAfter(self.hm.HookMouse)
        finally:
            self.lock.release()

    @eg.LogIt
    def Stop(self):
        if self.listenerStarted:
            self.lock.acquire()
            try:
                wx.CallAfter(self.hm.UnhookMouse)
                del self.hm
                self.listenerStarted = False
            finally:
                self.lock.release()

    @eg.LogIt
    def Restart(self):
        if self.listenerStarted:
            self.Start(
                self.mouseLeftClick, 
                self.mouseMiddleClick, 
                self.mouseRightClick, 
                self.mouseWheel, 
                self.mouseMove, 
                self.coalesce, 
                self.repeatRate, 
                self.minDistFilter, 
                self.minDistance)
        
    def OnMouseEvent(self, event):
        self.lock.acquire()
        try:
            #self._printEvent(event)
            self._handleEvent(event)
        finally:
            self.lock.release()
        return True

    def _printEvent(self, event):
        print 'MessageName:',event.MessageName
        print 'Message:',event.Message
        print 'Time:',event.Time
        print 'Window:',event.Window
        print 'WindowName:',event.WindowName
        print 'Position:',event.Position
        print 'Wheel:',event.Wheel
        print 'Injected:',event.Injected
        print '---'
        
    def _handleEvent(self, event):
        if event.Message == pyHook.HookConstants.WM_LBUTTONUP:
            self.plugin.TriggerEvent("MouseLeftClick", event.Position)
            self.lastLeftClickEvent = event
        elif event.Message == pyHook.HookConstants.WM_MBUTTONUP:
            self.plugin.TriggerEvent("MouseMiddleClick", event.Position)
            self.lastMiddleClickEvent = event
        elif event.Message == pyHook.HookConstants.WM_RBUTTONUP:
            self.plugin.TriggerEvent("MouseRightClick", event.Position)
            self.lastRightClickEvent = event
        elif event.Message == pyHook.HookConstants.WM_MOUSEWHEEL:
            self.plugin.TriggerEvent("MouseWheel", event.Position)
            self.lastWheelEvent = event

        elif event.Message == pyHook.HookConstants.WM_MOUSEMOVE:
            trigger = False

            # the very first move event
            if self.lastMoveEvent == None:
                self.firstMoveEvent = event
                if self.minDistance <= 0: # feature disabled
                    trigger = True

            # following events, still untriggered
            elif self.lastTriggeredMoveEvent == None:
                # Filter by pixel distance (initial events)
                # The initial events are filtered until minDistance is reached.
                # The reason for that is that on some systems I got ghost events, i.e. events without mouse move
                if self.minDistance > 0:
                    a = abs(event.Position[0] - self.firstMoveEvent.Position[0])
                    b = abs(event.Position[1] - self.firstMoveEvent.Position[1])
                    c = math.sqrt(a*a + b*b)
                    if c > self.minDistance:
                        trigger = True
                else:
                    trigger = True

            # following events
            else:
                # Filter by pixel distance (following events)
                if self.minDistance > 0:
                    a = abs(event.Position[0] - self.lastTriggeredMoveEvent.Position[0])
                    b = abs(event.Position[1] - self.lastTriggeredMoveEvent.Position[1])
                    c = math.sqrt(a*a + b*b)
                    if c > self.minDistance:
                        trigger = True
                
                # Filter by time
                if trigger and self.coalesce:
                    diff = event.Time - self.lastTriggeredMoveEvent.Time
                    if diff < self.minTimeDiff:
                        trigger = False
                
            if trigger:
                self.plugin.TriggerEvent("MouseMove", event.Position)
                self.lastTriggeredMoveEvent = event
            elif eg.debugLevel:
                #print "No trigger for MouseMove ", event.Position
                pass
                
            self.lastMoveEvent = event
            
        self.lastEvent = event

    def GetLastEvent(self):
        return self._fillEventData(self.lastEvent)
    
    def GetLastMoveEvent(self):
        return self._fillEventData(self.lastMoveEvent)
    
    def GetLastLeftClickEvent(self):
        return self._fillEventData(self.lastLeftClickEvent)

    def GetLastMiddleClickEvent(self):
        return self._fillEventData(self.lastMiddleClickEvent)

    def GetLastRightClickEvent(self):
        return self._fillEventData(self.lastRightClickEvent)

    def GetLastWheelEvent(self):
        return self._fillEventData(self.lastWheelEvent)
    
    def _fillEventData(self, event):
        self.lock.acquire()
        try:
            data = {}
            if event != None:
                data['MessageName'] = event.MessageName
                data['Message'] = event.Message
                data['Time'] = event.Time
                data['Window'] = event.Window
                data['WindowName'] = event.WindowName
                data['Position'] = event.Position
                data['Wheel'] = event.Wheel
                data['Injected'] = event.Injected
        finally:
            self.lock.release()
        return data


# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright © 2005-2016 EventGhost Project <http://www.eventghost.org/>
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

from fnmatch import fnmatchcase
import threading
from time import clock
from collections import deque

# Local imports
import eg

# some shortcuts to speed things up
#pylint: disable-msg=C0103
actionThread = eg.actionThread
LogEvent = eg.log.LogEvent
RunProgram = eg.RunProgram
GetItemPath = eg.EventItem.GetPath
config = eg.config
#pylint: enable-msg=C0103


class EventMeta(type):

    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)
        cls._instances = {}

    def __call__(cls, suffix="", payload=None, prefix="Main", source=eg):
        string = prefix + "." + suffix

        if string not in cls._instances:
            cls._instances[string] = (
                super(EventMeta, cls).__call__(suffix, payload, prefix, source)
            )

        event = cls._instances[string]
        event.queue(payload, source)
        return event


def iter_dict(in_dict):
    out_dict = {}

    for key, value in in_dict.iteritems():
        if isinstance(value, dict):
            out_dict[key] = iter_dict(value)
        elif isinstance(value, list):
            out_dict[key] = iter_list(value)
        else:
            out_dict[key] = value

    return out_dict


def iter_list(in_list):
    out_list = []

    for item in in_list:
        if isinstance(item, dict):
            out_list += [iter_dict(item)]
        elif isinstance(item, list):
            out_list += [iter_list(item)]

        else:
            out_list += [item]
    return out_list


def copy(obj):
    if isinstance(obj, list):
        return iter_list(obj)
    if isinstance(obj, dict):
        return iter_dict(obj)

    return obj


class EventThread(threading.Thread):

    def __init__(self, suffix, payload, prefix, source):
        self.string = prefix + "." + suffix

        self.prefix = prefix
        self.suffix = suffix
        self.payload = payload
        self.source = source
        self.time = clock()
        self.isEnded = False
        self.shouldEnd = threading.Event()
        self.upFuncList = []
        self.programCounter = None
        self.programReturnStack = []
        self.indent = 0
        self.result = None
        self.stopExecutionFlag = False
        self.lastFoundWindows = []
        self.skipEvent = False
        self.__exit_event = threading.Event()
        self.__queue = deque()
        self.has_run = False

        threading.Thread.__init__(self, name=self.string)

    def queue(self, payload, source):
        self.__queue.append((payload, source))
        if self.is_alive():
            return True

        return False

    @property
    def run_count(self):
        return len(self.__queue)

    def AddUpFunc(self, func, *args, **kwargs):
        if self.isEnded:
            func(*args, **kwargs)
        else:
            self.upFuncList.append((func, args, kwargs))

    def DoUpFuncs(self):
        for func, args, kwargs in self.upFuncList:
            func(*args, **kwargs)
        del self.upFuncList[:]
        self.isEnded = True

    def run(self):
        def check_listeners():
            if self.string in eg.notificationHandlers:
                for callback in eg.notificationHandlers[self.string].listeners:
                    if callback(self) is True:
                        return False
            return True

        while not self.__exit_event.is_set():

            if not len(self.__queue):
                self.has_run = True
                break

            while len(self.__queue):
                if self.__exit_event.is_set():
                    break

                self.payload, self.source = self.__queue.popleft()
                self.isEnded = False
                self.shouldEnd.clear()
                self.programCounter = None
                self.programReturnStack = []
                self.indent = 0
                self.result = None
                self.stopExecutionFlag = False
                self.lastFoundWindows = []

                # start = clock()
                if check_listeners():
                    eg.event = self

                    eventHandlerList = []
                    for key, val in eg.eventTable.iteritems():
                        if (
                            self.string == key or
                            (("*" in key or "?" in key) and fnmatchcase(self.string, key))
                        ):
                            eventHandlerList += val

                    activeHandlers = set()
                    for eventHandler in eventHandlerList:
                        obj = eventHandler
                        while obj:
                            if not obj.isEnabled:
                                break
                            obj = obj.parent
                        else:
                            activeHandlers.add(eventHandler)

                    for listener in eg.log.eventListeners:
                        listener.LogEvent(self)

                    if config.onlyLogAssigned and len(activeHandlers) == 0:
                        self.SetStarted()
                        return

                    # show the event in the logger
                    LogEvent(self)

                    activeHandlers = sorted(activeHandlers, key=GetItemPath)

                    eg.SetProcessingState(2, self)
                    for eventHandler in activeHandlers:
                        try:
                            self.programCounter = (eventHandler.parent, None)
                            self.indent = 1
                            RunProgram()
                        except:
                            eg.PrintTraceback()
                        if self.skipEvent:
                            break

                    self.SetStarted()
                    eg.SetProcessingState(1, self)

    def stop(self):
        self.__exit_event.set()
        if self.is_alive() and threading.current_thread() != self:
            self.join(3.0)

            if self.is_alive():
                eg.PrintDebugNotice('Event shutdown timeout: ' + self.string)

    def SetShouldEnd(self):
        if not self.shouldEnd.isSet():
            self.shouldEnd.set()
            eg.SetProcessingState(0, self)
            actionThread.Call(self.DoUpFuncs)

    def SetStarted(self):
        if self.shouldEnd.isSet():
            self.DoUpFuncs()


class EventGhostEvent(object):
    """
    .. attribute:: string

        This is the full qualified event string as you see it inside the
        logger, with the exception that if the payload field
        (that is explained below) is not None the logger will also show it
        behind the event string, but this is not a part of the event string
        we are talking about here.

    .. attribute:: payload

        A plugin might publish additional data related to this event.
        Through payload you can access this data. For example the 'Network
        Event Receiver' plugin returns also the IP of the client that has
        generated the event. If there is no data, this field is ``None``.

    .. attribute:: prefix

        This is the first part of the event string till the first dot. This
        normally identifies the source of the event as a short string.

    .. attribute:: suffix

        This is the part of the event string behind the first dot. So you
        could say:

        event.string = event.prefix + '.' + event.suffix

    .. attribute:: time

        The time the event was generated as a floating point number in
        seconds (as returned by the clock() function of Python's time module).
        Since most events are processed very quickly, this is most likely
        nearly the current time. But in some situations it might be more
        clever to use this time, instead of the current time, since even
        small differences might matter (for example if you want to determine
        a double-press).

    .. attribute:: isEnded

        This boolean value indicates if the event is an enduring event and is
        still active. Some plugins (e.g. most of the remote receiver plugins)
        indicate if a button is pressed longer. As long as the button is
        pressed, this flag is ``False`` and in the moment the user releases the
        button the flag turns to ``True``. So you can poll this flag to see, if
        the button is still pressed.

    """

    __metaclass__ = EventMeta

    skipEvent = False

    def __init__(self, suffix="", payload=None, prefix="Main", source=eg):
        self.string = prefix + "." + suffix
        self.prefix = prefix
        self.suffix = suffix

        self.__pending_queue = deque()
        self.__thread = EventThread(suffix, payload, prefix, source)
        self.__lock = threading.Lock()

    @property
    def payload(self):
        return self.__thread.payload

    @payload.setter
    def payload(self, value):
        self.__thread.payload = value

    @property
    def source(self):
        return self.__thread.source

    @source.setter
    def source(self, value):
        self.__thread.source = value

    @property
    def lastFoundWindows(self):
        return self.__thread.lastFoundWindows

    @lastFoundWindows.setter
    def lastFoundWindows(self, value):
        self.__thread.lastFoundWindows = value

    @property
    def stopExecutionFlag(self):
        return self.__thread.stopExecutionFlag

    @stopExecutionFlag.setter
    def stopExecutionFlag(self, value):
        self.__thread.stopExecutionFlag = value

    @property
    def result(self):
        return self.__thread.result

    @result.setter
    def result(self, value):
        self.__thread.result = value

    @property
    def indent(self):
        return self.__thread.indent

    @indent.setter
    def indent(self, value):
        self.__thread.indent = value

    @property
    def programReturnStack(self):
        return self.__thread.programReturnStack

    @programReturnStack.setter
    def programReturnStack(self, value):
        self.__thread.programReturnStack = value

    @property
    def programCounter(self):
        return self.__thread.programCounter

    @programCounter.setter
    def programCounter(self, value):
        self.__thread.programCounter = value

    @property
    def upFuncList(self):
        return self.__thread.upFuncList

    @upFuncList.setter
    def upFuncList(self, value):
        self.__thread.upFuncList = value

    @property
    def shouldEnd(self):
        return self.__thread.shouldEnd

    @property
    def isEnded(self):
        return self.__thread.isEnded

    @isEnded.setter
    def isEnded(self, value):
        self.__thread.isEnded = value

    @property
    def time(self):
        return self.__thread.time

    @property
    def run_count(self):
        return self.__thread.run_count

    def AddUpFunc(self, func, *args, **kwargs):
        self.__thread.AddUpFunc(func, *args, **kwargs)

    def DoUpFuncs(self):
        self.__thread.DoUpFuncs()

    def is_alive(self):
        return self.__thread.is_alive()

    def id(self):
        if self.__thread is not None:
            return self.__thread.ident

    def stop(self):
        self.__thread.stop()

    def queue(self, payload, source):
        self.__pending_queue.append((copy(payload), source))

    def Execute(self):
        payload, source = self.__pending_queue.popleft()

        with self.__lock:
            if self.__thread.has_run or not self.__thread.is_alive():
                self.__thread = EventThread(self.suffix, payload, self.prefix, source)
                self.__thread.queue(payload, source)
                self.__thread.start()
            else:
                self.__thread.queue(payload, source)

    def SetShouldEnd(self):
        self.__thread.SetShouldEnd()

    def SetStarted(self):
        self.__thread.SetStarted()

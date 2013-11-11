#! /usr/bin/env python
# -*- coding: utf8 -*-

###################################################################################################
# RuleUser
# threads.py
# 
# Copyright (C) 2012,2013 Andrey Burbovskiy <xak-altsp@yandex.ru>
#
# Developed specially for ALT Linux School.
# http://www.altlinux.org/LTSP
#
# Computer management and monitoring of users:
# - LTSP servers
# - Linux standalone clients
# - Windows standalone clients(only VNC)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################################

import gtk, gobject, threading, time
import gettext
_ = gettext.gettext

####################################################################################################

# поток для комманд
class thread_command(threading.Thread):
    def __init__(self, command):
	threading.Thread.__init__(self)

	self.stopthread = threading.Event()
	self.cond = threading.Condition()
	# список комманд
	self.command = command

    def run(self):
	self.cond.acquire()
    	for line in self.command:
	    os.system(line)
    	self.cond.notify()
    	self.cond.release()

    def stop(self):
        self.stopthread.set()

####################################################################################################

# поток для функции + gobject
class thread_gfunc(threading.Thread, gobject.GObject):

    __gsignals__ = {
	"completed": ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [] ),
	"data": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,(gobject.TYPE_PYOBJECT,))
	}

    def __init__(self, cfg, cursor, sensitive, func, *args):
	threading.Thread.__init__(self)
	gobject.GObject.__init__(self)

	self.cond = threading.Condition()
	self.stopthread = threading.Event()

	self.func = func
	self.args = args

	self.cfg = cfg
	self.cursor = cursor
	self.sensitive = sensitive

    def run(self):

	if ( self.cursor ):
	    from util import cursor_wait
	    cursor_wait(self.cfg, True)
	if ( self.sensitive == False ):
	    self.cfg.window.set_sensitive(False)

	self.cond.acquire()
    	self.emit("data", self.run_func())
    	self.emit('completed')
    	# sleep на всякий случай
    	time.sleep(0.1)
    	self.cond.notify()
    	self.cond.release()

	if ( self.cursor ):
	    cursor_wait(self.cfg, False)
	if ( self.sensitive == False ):
	    self.cfg.window.set_sensitive(True)

    def run_func(self):
	self.func(*self.args)

    def stop(self):
        self.stopthread.set()

####################################################################################################

class _IdleObject(gobject.GObject):

    def __init__(self):
        gobject.GObject.__init__(self)

    def emit(self, *args):
        gobject.idle_add(gobject.GObject.emit,self,*args)

####################################################################################################

# поток для функции
class thread_func(threading.Thread):

    def __init__(self, cfg, cursor, func, *args):
	threading.Thread.__init__(self)

	self.cond = threading.Condition()
	self.stopthread = threading.Event()

	self.func = func
	self.args = args

	self.cfg = cfg
	self.cursor = cursor

    def run(self):

	if ( self.cursor ):
	    from util import cursor_wait
	    cursor_wait(self.cfg, True)

	self.cond.acquire()
	self.run_func()
    	self.cond.notify()
    	self.cond.release()

	if ( self.cursor ):
	    cursor_wait(self.cfg, False)
    
    def run_func(self):
	self.func(*self.args)

    def stop(self):
        self.stopthread.set()

####################################################################################################

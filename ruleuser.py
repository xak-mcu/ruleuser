#! /usr/bin/env python
# -*- coding: utf8 -*-

###################################################################################################
# RuleUser
# ruleuser.py
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

from __future__ import with_statement
try:
    import pango
    import gtk, gobject
    import os, socket, threading
    import re, string, shlex, ConfigParser, gettext, shutil
    import datetime, time, sys
    #import gc, weakref
except:
    print "Required python modules gtk,gobject,pango,os,socket,shutil,threading,re,string,shlex,\
	ConfigParser,gettext,datetime,time,sys,gc,weakref"
    raise SystemExit

if ( os.getuid() == 0 ):
    print "Cannot be run under root"    
    raise SystemExit

python_version = sys.version_info[0:2]

if python_version < (2, 5):
    print "Python 2.5.0 or later required"
    raise SystemExit

if gtk.pygtk_version < (2, 4, 0):
    print "PyGtk 2.4.0 or later required"
    raise SystemExit

# gtkvnc
#try:
#    if ( python_version == (2, 5) ):
#	module_path = os.path.expanduser("lib/2.5")
#	sys.path.insert(0, module_path)
#    elif ( python_version == (2, 6) ):
#	module_path = os.path.expanduser("lib/2.6")
#	sys.path.insert(0, module_path)
#except:
#    pass

try:
    import gtkvnc
except:
    print "python-module-gtkvnc not found. Program is run in reduced functionality."
    gtkvnc = False

# program modules
from config import *
from dialogs import *
from widget import *
from command import *
from window2 import *
from tree import *
from util import *
from timers import timers
from threads import *
from vnc import *

locale_path = os.path.expanduser("locale")
gettext.bindtextdomain('ruleuser', locale_path)
gettext.textdomain('ruleuser')
_ = gettext.gettext

debug_enable = False
if ( len(sys.argv) != 0 ):
    for x in sys.argv:
	if ( "--debug" in x ):
	    debug_enable = True

###########################################################################################################################
############################################################################################################################
class Program():

    def __init__(self):
	
        self.cfg = cfg()
        self.cfg.read()
        self.cfg.read_icons()
        
        if ( debug_enable ):
    	    self.cfg.debug_enable = True
    	else:
    	    self.cfg.debug_enable = False

        if ( gtk.pygtk_version < (2, 12, 0) ):
	    self.cfg.tooltips = gtk.Tooltips()
	else:
	    self.cfg.tooltips = gtk.Tooltip()
	    
	self.cfg.gtkvnc = False
	self.cfg.gtkvnc_depth = False
	self.cfg.gtkvnc_encoding = False
	if ( gtkvnc ):
	    self.cfg.gtkvnc = True
	    for method in dir(gtkvnc.Display):
		if ( method == "set_depth" ):
		    self.cfg.gtkvnc_depth = True
		if ( method == "set_encoding" ):
		    self.cfg.gtkvnc_encoding = True

	# gtkvnc
    	self.cfg.vnc_box = []
        self.colVnc = -1
	self.cfg.tt_size = 30
	self.cfg.tt_border = 10
        self.cfg.vnc_count = 0
        self.cfg.vnc_active = False
        self.cfg.vnc_active_open = False
        self.cfg.vnc_close_active = False
        self.cfg.vnc_local_active = False

	self.cfg.tree_motion_select_row = None
	self.cfg.thumbnails_resize_item = None

	self.window = self.cfg.window
	self.cfg.maximized = False
	self.cfg.fullscreen = False
	self.cfg.bg_color = self.window.get_style().copy().bg[gtk.STATE_NORMAL]
	self.window.set_title(" RuleUser ")
	self.window.connect('check-resize', self.window_resize_event)
	self.window.connect("window-state-event", self.window_state_event)
	self.window.connect('key-press-event', self.window_key_press_event)
	self.window.connect("event", self.window_event)
	self.window.connect("destroy", self.program_exit)
	self.mainUi()

    ##############################################

    def program_exit(self, data=None):
	save_userList(self.cfg)
	save_demoList(self.cfg)
	save_timersList(self.cfg)
	self.close_gtkvnc()
	self.cfg.timers.stop()
    	self.cfg.status(_("Quit"))
	umount_point(self.cfg)
	gtk.main_quit()
    
    ##############################################

    def callback(self, widget, data1=None ,data2=None, data3=None):
	# data2=row(path) thumbnails_vnc_event
	# data2=position scale, data3=event
	#print data1, data2, data3

	if (data1 == "screenshot" ):
	    label_text = ""
	    toolbar = data2[2].get_children()[0]
	    for w in toolbar.get_children():
		if ( type(w) == gtk.ToolItem ):
		    label_text = w.get_child().get_text()
		    break
	    vnc = data2[3]
	    time = datetime.datetime.now()
	    pix = vnc.get_pixbuf()
	    if ( os.path.exists(self.cfg.vncShotFolder) ):
    	    	pix.save(self.cfg.vncShotFolder+"/"+label_text+"_"+time.strftime("%d.%m.%Y_%H:%M:%S")+".png", "png", {})
    	    	self.cfg.status(_("The screenshot is saved to a file")+" "+label_text+"_"+time.strftime("%d.%m.%Y_%H:%M:%S")+".png")
    	    else:
    	    	self.cfg.status(_("The screenshot folder")+" "+_("not found")+" - "+self.cfg.vncShotFolder)
    	    	return

	if (data1 == "screenshot_all" ):
	    for p in self.cfg.vnc_box:
		label_text = ""
		toolbar = p[2].get_children()[0]
		for w in toolbar.get_children():
		    if ( type(w) == gtk.ToolItem ):
			label_text = w.get_child().get_text()
			break
		vnc = p[3]
		time = datetime.datetime.now()
		pix = vnc.get_pixbuf()
		if ( os.path.exists(self.cfg.vncShotFolder) ):
    	    	    pix.save(self.cfg.vncShotFolder+"/"+label_text+"_"+time.strftime("%d.%m.%Y_%H:%M:%S")+".png", "png", {})
    	    	    self.cfg.status(_("The screenshot is saved to a file")+" "+label_text+"_"+time.strftime("%d.%m.%Y_%H:%M:%S")+".png")
    		else:
    	    	    self.cfg.status(_("The screenshot folder")+" "+_("not found")+" - "+self.cfg.vncShotFolder)
    	    	    return

	if (data1 == "remove_tree_item" ):
	    remove_tree_item(self.cfg, self.cfg.treeView)
	if (data1 == "edit_tree_item" ):
	    userUi(self.cfg, "edit", get_selected_tree(self.cfg, self.cfg.treeView, "edit"))
	if (data1 == "create_standalone" ):
	    userUi(self.cfg, "standalone")
	if (data1 == "create_group" ):
	    userUi(self.cfg, "new_group")
	if (data1 == "create_server" ):
	    userUi(self.cfg, "server")
	    
	if (data1 == "client_info" ):
	    userUi(self.cfg, "client_info", get_selected_tree(self.cfg, self.cfg.treeView, "first"))

	if (data1 == "settings" ):
	    settings(self.cfg)

	if (data1 == "refresh" ):
	    self.cfg.timers.timer_userList("restart")

	if (data1 == "close_gtkvnc" ):
	    if ( self.cfg.vnc_active or self.cfg.vnc_local_active ):
		return
	    self.view_vnc_close()
    	    
	if (data1 == "demo" ):
	    self.cfg.demoUi.createUi()
	    
	if (data1 == "timers" ):
	    self.timersUi.createUi()
	    
	if (data1 == "process" ):
	    processUi(self.cfg, get_selected_tree(self.cfg, self.cfg.treeView))
	    
	if (data1 == "hwinfo" ):
	    hwinfoUi(self.cfg, get_selected_tree(self.cfg, self.cfg.treeView))

	if (data1 == "folder_user" ):
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView, "first")
	    if ( user_list != [] ):
		folderUi(self.cfg, user_list)

	if (data1 == "log" ):
	    hwinfoUi(self.cfg, get_selected_tree(self.cfg, self.cfg.treeView), "log")
	    
	if (data1 == "run" ):
	    if ( self.view_message_box(state="state") == False ):
		self.view_message_box()
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		if ( self.cfg.messageBox.get_active_text() != "" ):
		    if ( message_dialog(self.window, _("Run command")+" ?\n", user_list, True) == True ):
	    		run_command(self.cfg, user_list, self.cfg.messageBox.get_active_text(), _("Run command"))
	    	else:
	    	    entry_error(self.cfg, self.cfg.messageBox)
	        
	if (data1 == "run_root" ):
	    if ( self.view_message_box(state="state") == False ):
		self.view_message_box()
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		# Только стац. клиенты
		for z in user_list:
		    d = {}
		    for key, value in zip(self.cfg.z, z):
			d[key] = value
		    if ( d['client'] != "standalone" ):
			name = get_name(d)
			self.cfg.status(name+' "'+_("Run as root")+'" '+_("only for standalone clients"))
			return
		if ( self.cfg.messageBox.get_active_text() != "" ):
		    if ( message_dialog(self.window, _("Run as root")+" ?\n", user_list, True) == True ):
	    		run_command(self.cfg, user_list, self.cfg.messageBox.get_active_text(), _("Run as root"))
	    	else:
	    	    entry_error(self.cfg, self.cfg.messageBox)
	        
	if (data1 == "send_message" ):
	    if ( self.view_message_box(state="state") == False ):
		self.view_message_box()
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		if ( self.cfg.messageBox.get_active_text() != "" ):
		    if ( message_dialog(self.window, _("Send message")+" ?\n", user_list, True) == True ):
	    		run_command(self.cfg, user_list, self.cfg.messageBox.get_active_text(), _("Send message"))
	    	else:
	    	    entry_error(self.cfg, self.cfg.messageBox)

	if (data1 == "send_file" ):
	    if ( self.view_message_box(state="state") == False ):
		self.view_message_box()
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		if ( self.cfg.messageBox.get_active_text() != "" ):
		    if ( message_dialog(self.window, _("Send file")+" ?\n", user_list, True) == True ):
	    		send_file(self.cfg, user_list, self.cfg.messageBox.get_active_text())
	    	else:
	    	    entry_error(self.cfg, self.cfg.messageBox)

	if (data1 == "console_server" ): 
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView, "first")
	    if ( user_list != [] ):
		run_command(self.cfg, user_list, "", "console_server")
	    
	if (data1 == "console_host" ): 
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView, "first")
	    if ( user_list != [] ):
		run_command(self.cfg, user_list, "", "console_host")
	    
	if (data1 == "console_root" ): 
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView, "first")
	    if ( user_list != [] ):
		# Только стац. клиенты
		for z in user_list:
		    d = {}
		    for key, value in zip(self.cfg.z, z):
			d[key] = value
		    if ( d['client'] != "standalone" ):
			name = get_name(d)
			self.cfg.status(name+' "'+_("Console")+"(root)"+'" '+_("only for standalone clients"))
			return
		run_command(self.cfg, user_list, "", "console_root")
	    
	if (data1 == "lock" ):
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		if ( message_dialog(self.window, _("Lock screen")+" ?\n", user_list, True) == True ):
		    run_command(self.cfg, user_list, "", _("Lock screen"))

	if (data1 == "unlock" ):
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		if ( message_dialog(self.window, _("Unlock screen")+" ?\n", user_list, True) == True ):
		    run_command(self.cfg, user_list, "", _("Unlock screen"))
	    
	if (data1 == "block" ):
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		if ( message_dialog(self.window, _("Lock the input")+" ?\n", user_list, True) == True ):
		    run_command(self.cfg, user_list, "", "block")

	if (data1 == "unblock" ):
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		if ( message_dialog(self.window, _("Unlock the input")+" ?\n", user_list, True) == True ):
		    run_command(self.cfg, user_list, "", "unblock")
	    
	if ( data2 == "logout" or data2 == "logout" ):
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		if ( message_dialog(self.window, _("Logout")+" ?\n", user_list, True) == True ):
		    run_command(self.cfg, user_list, "", _("Logout"))

	if ( data1 == "reboot" or data2 == "reboot" ):
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		if ( message_dialog(self.window, _("Reboot")+" ?\n", user_list, True) == True ):
		    run_command(self.cfg, user_list, "", _("Reboot"))

	if ( data1 == "wake_on_lan" or data2 == "wake_on_lan" ):
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		if ( message_dialog(self.window, _("Turn On")+" ?\n", user_list, True) == True ):
		    run_command(self.cfg, user_list, "", _("Turn On"))

	if ( data1 == "shutdown" or data2 == "shutdown" ):
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list != [] ):
		if ( message_dialog(self.window, _("Shutdown")+" ?\n", user_list, True) == True ):
		    run_command(self.cfg, user_list, "", _("Shutdown"))

	if (data1 == "view" or data1 == "control"):
	    mode = data1
	    if ( self.cfg.vnc_active or self.cfg.vnc_local_active ):
		return
	    if ( self.cfg.vncGtk == "y" and self.cfg.gtkvnc != False ):
		user_list = get_selected_tree(self.cfg, self.cfg.treeView, "first")
		if ( user_list == [] ):
		    return
		(new, param) = self.thumbnails_vnc_pre(user_list, mode)
		if ( new ):
		    thread = thread_gfunc(self.cfg, True, True, self.thumbnails_vnc, user_list, param)
		    thread.start()
		    gobject.timeout_add(1000+len(user_list)*200, self.thumbnails_vnc_post, param)
		    gobject.timeout_add(7000+len(user_list)*200, self.thumbnails_vnc_active)
	    else:
		if ( mode == "view" ):
		    create_vnc_viewer(self.cfg, get_selected_tree(self.cfg, self.cfg.treeView, "first"), "-viewonly")
		else:
		    create_vnc_viewer(self.cfg, get_selected_tree(self.cfg, self.cfg.treeView, "first"), "")
		
	if (data1 == "thumbnails" ):
	    if ( self.cfg.vnc_active or self.cfg.vnc_local_active ):
		return
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView)
	    if ( user_list == [] ):
		return
	    if ( self.cfg.gtkvnc == False ):
		return    
	    (new, param) = self.thumbnails_vnc_pre(user_list, "thumbnails")
	    if ( new ):
		thread = thread_gfunc(self.cfg, True, True, self.thumbnails_vnc, user_list, param)
		thread.start()
		gobject.timeout_add(1000+len(user_list)*200, self.thumbnails_vnc_post, param)
		gobject.timeout_add(7000+len(user_list)*200, self.thumbnails_vnc_active)
	    #thread = threading.Thread(target=self.thumbnails_vnc)
	    #thread.start()
	    #self.thumbnails_vnc()

    ##############################################

    def window_state_event(self, widget=None, event=None):
	state = event.changed_mask
	if ( state == gtk.gdk.WINDOW_STATE_MAXIMIZED or state == gtk.gdk.WINDOW_STATE_FULLSCREEN ):
	    new_state = event.new_window_state
	    if ( new_state == gtk.gdk.WINDOW_STATE_MAXIMIZED ):
		self.cfg.maximized = True
	    else:
		self.cfg.maximized = False
	    if ( new_state == gtk.gdk.WINDOW_STATE_FULLSCREEN or new_state == gtk.gdk.WINDOW_STATE_MAXIMIZED|gtk.gdk.WINDOW_STATE_FULLSCREEN ):
		self.cfg.fullscreen = True
	    else:
		self.cfg.fullscreen = False

    ##############################################

    def window_event(self, widget=None, event=None):
	pass

    ##############################################
    
    def window_key_press_event(self, widget=None, event=None):
	if ( event.keyval == gtk.keysyms.F1 ):
	    about_dialog()
	if ( event.keyval == gtk.keysyms.F2 ):
	    self.view_list()
	if ( event.keyval == gtk.keysyms.F3 ):
	    self.view_vnc_minimize()
	if ( event.keyval == gtk.keysyms.F4 ):
	    self.view_vnc_close()
	if ( event.keyval == gtk.keysyms.F9 ):
	    self.view_message_box()
	if ( event.keyval == gtk.keysyms.F10 ):
	    self.view_status()
	if ( event.keyval == gtk.keysyms.F11 ):
	    self.view_fullscreen()

    ##############################################

    def window_resize_event(self, data=None):
	# Размер окна программы
	(self.cfg.window_x, self.cfg.window_y) = self.window.get_size()
	# Реальный размер рабочего стола
	(self.cfg.screen_x, self.cfg.screen_y) = get_workspace(self.cfg)
	# если меньше, кривой интерфейс и виснет
	if ( self.cfg.screen_x < self.cfg.mainWindowX + self.cfg.panedWindowX ):
	    self.cfg.screen_x = self.cfg.mainWindowX + self.cfg.panedWindowX
	
    	if ( self.cfg.table2.get_children() == [] ): 
	    self.window.set_size_request(self.cfg.min_mainWindowX, self.cfg.min_mainWindowY)
	
    ##############################################

    def paned_tree_event(self, data1=None, data2=None):
	# удалить миниатуры
	if ( self.panedTree.get_position() == self.cfg.panedWindow.get_position() ):
	    if ( self.cfg.vnc_box != [] ):
		self.close_gtkvnc()
	# Кнопка
	if ( self.panedTree.get_position() < self.cfg.panedWindow.get_position() ):
	    self.close_button_gtkvnc.show_all()
	else:
	    self.close_button_gtkvnc.hide()
	
	if ( self.panedTree.get_position() == 0 ):
	    button = self.toolbarTree.get_children()[0]
    	    image = button.get_icon_widget()
    	    image.set_from_pixbuf(self.cfg.pixbuf_list_hide0_16)
    	else:
	    button = self.toolbarTree.get_children()[0]
    	    image = button.get_icon_widget()
    	    image.set_from_pixbuf(self.cfg.pixbuf_list_hide1_16)

	# Переместить миниатюры
	self.thumbnails_reorder()

    ##############################################

    def paned_window_event(self, data1=None, data2=None):
	# Ползунок разделения не передвинуть
    	if ( self.cfg.table2.get_children() != [] ): 
	    if ( self.cfg.panedWindow.get_position() < self.cfg.window_x-self.cfg.panedWindowX-self.cfg.phandle_size or\
		 self.cfg.panedWindow.get_position() > self.cfg.window_x-self.cfg.panedWindowX-self.cfg.phandle_size ):
    		self.cfg.panedWindow.set_position(self.cfg.window_x-self.cfg.panedWindowX-self.cfg.phandle_size)
    	else:
	    if ( self.cfg.panedWindow.get_position() < self.cfg.window_x-self.cfg.phandle_size ):
    	    	self.cfg.panedWindow.set_position(self.cfg.window_x-self.cfg.phandle_size)
	# Тащить за собой ползунок panedTree если нет миниатюр
	if( self.table_vnc.get_children() == [] and self.cfg.vnc_active == False ):
	    if ( self.panedTree.get_position() < self.cfg.panedWindow.get_position()-self.cfg.phandle_size ):
    	        self.panedTree.set_position(self.cfg.panedWindow.get_position()-self.cfg.phandle_size)
	# Переместить миниатюры
	self.thumbnails_reorder()

    ##############################################

    def thumbnails_vnc_event(self, data, event):
	# Проверка кнопок мыши для миниатюр
        if event.button == 3:
    	    # client_id и ссылки на объекты хранятся в self.cfg.vnc_box
    	    for line in self.cfg.vnc_box:
    		client_id = line[0]
    		vbox = line[2]
    		vnc_item = line[3]
    		if ( str(vbox).find(str(data)) != -1 ):
    	    	    # Поиск в дереве row(path) по alias,user
    	    	    row = find_tree(self.cfg, self.cfg.userList, client_id=client_id)
    	    	    if ( row == False ):
    	    		return
    		    # Раскрыть и выделить
    		    self.cfg.treeView.scroll_to_cell(row, None, use_align=True, row_align=0.5, col_align=0.0)
    		    self.cfg.treeView.expand_to_path(row)
    		    self.treeSelection.unselect_all()
    		    self.treeSelection.select_path(row)
		    self.context_menu(event, line)

    ##############################################

    def thumbnails_reorder(self, mode="", resize_vbox=None, data=None):
	if ( self.cfg.vnc_active_open == True and mode == "" ):
	    return
	if ( self.cfg.vnc_box == [] ):
	    return
	if ( mode == "all_minimize" and resize_vbox == None ):
	    self.cfg.vnc_box[0][13] = "min"
	    resize_vbox = self.cfg.vnc_box[0]
	y = 0
	if ( mode == "" or mode == "all" or mode == "resize" or mode == "all_minimize" ):
	    self.cfg.debug("thumbnails_reorder start, mode: "+mode)
	    for num in range(len(self.cfg.vnc_box)):
		# "empty" пустые освобождают место для новых, пропустить
		if ( self.cfg.vnc_box[num][0] != "empty" ):
		    # Если размер изменен
		    if ( (self.cfg.vnc_box[num][13] == "custom" and mode != "all_minimize") or \
			(self.cfg.vnc_box[num][13] == "custom" and mode == "all_minimize" and self.cfg.vnc_box[num][2] == resize_vbox[2] ) ):
			pass
		    elif ( (self.cfg.vnc_box[num][13] == "max" and mode != "all_minimize") or \
			(self.cfg.vnc_box[num][13] == "max" and mode == "all_minimize" and self.cfg.vnc_box[num][2] == resize_vbox[2]) ):
			self.cfg.vnc_box[num][4] = self.cfg.vnc_box[num][8]
			self.cfg.vnc_box[num][5] = self.cfg.vnc_box[num][9]
    		    else:
			self.cfg.vnc_box[num][4] = self.cfg.vnc_box[num][6]
			self.cfg.vnc_box[num][5] = self.cfg.vnc_box[num][7]
    			if ( mode == "all_minimize" ):
			    # Если размер не минимальный
			    if ( self.cfg.vnc_box[num][13] != "min" ):
    				self.cfg.vnc_box[num][13] = "min"
    				self.cfg.vnc_box[num][2].set_size_request(self.cfg.vnc_box[num][4], self.cfg.vnc_box[num][5])
	    		    # Кнопка просмотр/управления
	    		    if ( self.cfg.vnc_box[num][12] != "view" ):
	    			self.cfg.vnc_box[num][12] = "view"
		    		self.thumbnails_button(self.cfg.vnc_box[num], _("Viewer")+"/"+_("Control"))
		    # Кнопка размера
		    if ( mode == "all_minimize" or (mode == "resize" and resize_vbox[2] == self.cfg.vnc_box[num][2]) ):
		        self.thumbnails_button(self.cfg.vnc_box[num], _("Size"))

	    for num in range(len(self.cfg.vnc_box)):
		if ( num == 0 ):
		    self.cfg.vnc_box[num][27] = 0
		    self.cfg.vnc_box[num][28] = y
		    y = self.cfg.vnc_box[num][28] + self.cfg.vnc_box[num][5] + self.cfg.tt_border
		else:
		    if ( self.cfg.vnc_box[num-1][27]+self.cfg.vnc_box[num-1][4]+self.cfg.vnc_box[num][4]+self.cfg.tt_border < self.thumbnails_table_size()[0] ):
			self.cfg.vnc_box[num][27] = self.cfg.vnc_box[num-1][27] + self.cfg.vnc_box[num-1][4] + self.cfg.tt_border
			self.cfg.vnc_box[num][28] = self.cfg.vnc_box[num-1][28]
			if ( y < self.cfg.vnc_box[num][28] + self.cfg.vnc_box[num][5] + self.cfg.tt_border ):
			    y = self.cfg.vnc_box[num][28] + self.cfg.vnc_box[num][5] + self.cfg.tt_border
		    else:
			self.cfg.vnc_box[num][27] = 0
			self.cfg.vnc_box[num][28] = y
			y = self.cfg.vnc_box[num][28] + self.cfg.vnc_box[num][5] + self.cfg.tt_border
	    
	    for num in range(len(self.cfg.vnc_box)):
	    	if ( self.cfg.vnc_box[num][0] != "empty" ):
		    # Изменить размер
		    if ( (mode == "resize" or mode == "all_minimize") and resize_vbox[2] == self.cfg.vnc_box[num][2] ):
			self.cfg.vnc_box[num][2].set_size_request(self.cfg.vnc_box[num][4], self.cfg.vnc_box[num][5])
		    # Переместить
		    if ( self.cfg.vnc_box[num] != self.cfg.thumbnails_resize_item ):
			alloc = self.cfg.vnc_box[num][2].get_allocation()
			if ( alloc.x-self.cfg.tt_border != self.cfg.vnc_box[num][27] or alloc.y-self.cfg.tt_border != self.cfg.vnc_box[num][28] ):
			    self.table_vnc.move(self.cfg.vnc_box[num][2], self.cfg.vnc_box[num][27], self.cfg.vnc_box[num][28])
		# Прокрутка
		if ( (mode == "resize" or mode == "all_minimize") and self.cfg.read_config("vnc","vnc_thumbnails_scroll") == "y" and\
		    ((resize_vbox[2] and resize_vbox[2] == self.cfg.vnc_box[num][2]) or (not resize_vbox[2] and num == 0)) and\
		    (self.cfg.vnc_box[num][0] == "empty" or self.cfg.vnc_box[num][13] != "custom") ):
		    gobject.timeout_add(100, self.thumbnails_scroll, self.cfg.vnc_box[num][28])
	    # Проверка
	    #for num in range(len(self.cfg.vnc_box)):
	    #	print num, self.cfg.vnc_box[num][1], "width="+str(self.cfg.vnc_box[num][4]), "height="+str(self.cfg.vnc_box[num][5]),\
	    #	    "x="+str(self.cfg.vnc_box[num][27]), "y="+str(self.cfg.vnc_box[num][28])
	    #print "\n-------------------------------------------------------------------"
		    

    ##############################################
    
    def thumbnails_scroll(self, y):
	adj = self.swVnc.get_vadjustment()
	adj.set_value(min(y, adj.upper-adj.page_size))
	return False
    
    ##############################################

    def thumbnails_button(self, p, label, data=None):
	for w in p[2].get_children()[0].get_children():
	    if ( (type(w) == gtk.ToolButton or type(w) == gtk.ToggleToolButton) and w.get_label() == label ):
		if ( label == _("Size") ):
		    if ( p[13] == "custom" ):
    		        image = w.get_icon_widget()
    		        image.set_from_pixbuf(self.cfg.pixbuf_action_window_min_16)
		    elif ( p[13] == "min" ):
    		        image = w.get_icon_widget()
    		        image.set_from_pixbuf(self.cfg.pixbuf_action_window_max_16)
    		    else:
    		        image = w.get_icon_widget()
    		        image.set_from_pixbuf(self.cfg.pixbuf_action_window_min_16)
    		elif ( label == _("Viewer")+"/"+_("Control") ):
    		    if ( p[12] == "view" ):
    			w.set_active(False)
			if ( p[3] ):
			    p[3].set_read_only(True)
    		    else:
    		        w.set_active(True)
			if ( p[3] ):
			    p[3].set_read_only(False)
		break
    
    ##############################################

    def thumbnails_vnc_event_button(self, button, p, mode):
	if ( self.cfg.vnc_active_open ):
	    return
	if ( mode == "screenshot" ):
	    self.callback(None, "screenshot", p)
	
	elif ( mode == "control" ):
	    if ( button.get_active() == True ):
    	    	p[12] = "control"
		if ( p[3] ):
		    p[3].set_read_only(False)
	    else:
    		p[12] = "view"
		if ( p[3] ):
		    p[3].set_read_only(True)

	elif ( mode == "resize" ):
    	    # max
    	    if ( p[13] == "min"):
		p[13] = "max"
		(new_max_thumb_x, new_max_thumb_y, new_max_window_x, new_max_window_y) = self.vnc_thumbnails_size("max")[4:8]
		p[4] = p[8] = new_max_thumb_x
		p[5] = p[9] = new_max_thumb_y
		p[10] = new_max_window_x
		p[11] = new_max_window_y
		window_x = self.cfg.window_x
		window_y = self.cfg.window_y
		if ( window_x < p[10] ):
		    window_x = p[10]
		if ( window_y < p[11] ):
		    window_y = p[11]
		if ( window_x != self.cfg.window_x or window_y != self.cfg.window_y ):
		    self.window.resize(window_x, window_y)
	    # min
	    else:
		p[13] = "min"
	    self.thumbnails_reorder("resize", p)

	elif ( mode == "up" ):
	    self.cfg.vnc_box.remove(p)
	    self.cfg.vnc_box.insert(0, p)
	    self.thumbnails_reorder("all")

	elif ( mode == "connect" ):
    	    row = find_tree(self.cfg, self.cfg.userList, client_id=p[0])
    	    if ( row == False ):
    		self.cfg.status(p[1]+": "+_("not found"))
    	    	return
    	    # Раскрыть и выделить
    	    self.cfg.treeView.scroll_to_cell(row, None, use_align=True, row_align=0.5, col_align=0.0)
    	    self.cfg.treeView.expand_to_path(row)
    	    self.treeSelection.unselect_all()
    	    self.treeSelection.select_path(row)
	    user_list = get_selected_tree(self.cfg, self.cfg.treeView, "first")
	    z = check_user_list(self.cfg, user_list, "vnc")
	    if ( z == [] ):
	    	return
	    z = z[0]
	    (ip, vncport, vncviewer) = vnc_razrulit(self.cfg, z)
    	    if ( vncport == "0" ):
    		return
	    p[15] = ip
	    p[16] = vncport
    	    self.vnc_item(p, "reconnect")

	elif ( mode == "close" ):
	    if ( p[3] ):
		p[3].close()
		p[3].destroy()
		p[3] = None
	    self.table_vnc.remove(p[2])
	    self.cfg.vnc_box.remove(p)
	    self.thumbnails_reorder("all")
    	    #gc.collect()

    ##############################################

    def vnc_item_toolbar_drag_data_get(self, widget, drag_context, selection, target_type, time, p):
    	client_id = p[0]
	selection.set(selection.target, 8, client_id)
	
    def vnc_item_toolbar_drag_begin(self, widget, drag_context):
	alloc = widget.get_allocation()
	pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, alloc.width, alloc.height)
	snapshot = pixbuf.get_from_drawable(widget.window, widget.get_colormap(), alloc.x, alloc.y, 0, 0, alloc.width, alloc.height)
	drag_context.set_icon_pixbuf(snapshot, 0, 0)
	#x_pointer, y_pointer = widget.get_pointer()
	#if ( x_pointer < 0 ):
	#    x_pointer = 0
	#elif ( x_pointer > alloc.width ):
	#    x_pointer = alloc.width
	#if ( y_pointer < 0 ):
	#    y_pointer = 0
	#elif ( y_pointer > alloc.height ):
	#    y_pointer = alloc.height
	#drag_context.set_icon_pixbuf(snapshot, x_pointer, y_pointer)
	
    ##############################################

    def vnc_item(self, p, connect="connect"):
	self.cfg.debug("vnc_item: "+p[1])
	if ( connect == "empty" ):
	    vnc = gtk.Frame()
	elif ( connect == "connect" ):
	    vnc = p[3] = gtkvnc.Display()
	elif ( connect == "reconnect" ):
	    if ( p[3] ):
		p[3].close()
		p[3].destroy()
		p[3] = None
	    for x in p[2].get_children():
		p[2].remove(x)
	    vnc = p[3] = gtkvnc.Display()
    	    #gc.collect()
	
	name = p[1]
	vbox = p[2]
	xsize = p[4]
	ysize = p[5]
	mode = p[12]
	size = p[13]
	ip = p[15]
	vncport = p[16]
	password = p[17]
	color = p[18]
	lossy = p[19]
	pointer = p[20]
	pointer_grab = p[21]
	keyboard_grab = p[22]
	encoding = p[23]

	toolbar = gtk.Toolbar()
	
	TARGETS = [ ('TEXT', 0, 0) ]
	toolbar.connect("drag_data_get", self.vnc_item_toolbar_drag_data_get, p)
	toolbar.connect('drag_begin', self.vnc_item_toolbar_drag_begin)
        toolbar.drag_source_set(gtk.gdk.BUTTON1_MASK, TARGETS, gtk.gdk.ACTION_DEFAULT)

	toolbar.set_size_request(-1, self.cfg.tt_size)
	toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
	toolbar.set_style(gtk.TOOLBAR_ICONS)
	toolbar.set_border_width(0)
	toolbar.set_tooltips(True)

	label = gtk.Label(" "+name)
	label.set_alignment(0, 0.5)
	label.modify_font(pango.FontDescription(self.cfg.fontThumbnails))
	item = gtk.ToolItem()
	item.set_expand(gtk.EXPAND)
	item.add(label)
	toolbar.insert(item, -1)

    	if ( self.cfg.read_config("hide","hide_control") == "n" ):
	    button = toolbar_button(self.cfg.pixbuf_action_control_16, self.cfg.tooltips, _("Viewer")+"/"+_("Control"), True)
	    button.set_label(_("Viewer")+"/"+_("Control"))
	    button.connect("clicked", self.thumbnails_vnc_event_button, p, "control")
	    if ( mode == "control" ):
		button.set_active(True)
	    toolbar.insert(button,-1)

	if ( "screenshot" in self.cfg.vncThumbnailsToolbar ):
	    button = toolbar_button(self.cfg.pixbuf_action_screenshot_16, self.cfg.tooltips, _("Screenshot"))
	    button.set_label(_("Screenshot"))
	    button.connect("clicked", self.thumbnails_vnc_event_button, p, "screenshot")
	    toolbar.insert(button,-1)

	item = gtk.SeparatorToolItem()
	toolbar.insert(item,-1)
	
	if ( "up" in self.cfg.vncThumbnailsToolbar ):
	    button = toolbar_button(self.cfg.pixbuf_action_window_up_16, self.cfg.tooltips, _("Upstairs"))
	    button.connect("clicked", self.thumbnails_vnc_event_button, p, "up")
	    button.set_label(_("Upstairs"))
	    toolbar.insert(button,-1)
	
	button = toolbar_button(None, self.cfg.tooltips, _("Size"))
	if ( size == "min" ):
	    image = gtk.Image()
	    image.set_from_pixbuf(self.cfg.pixbuf_action_window_max_16)
	else:
	    image = gtk.Image()
	    image.set_from_pixbuf(self.cfg.pixbuf_action_window_min_16)
	button.set_icon_widget(image)
	button.set_label(_("Size"))
	button.connect("clicked", self.thumbnails_vnc_event_button, p, "resize")
	toolbar.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_action_window_close_16, self.cfg.tooltips, _("Close"))
	button.connect("clicked", self.thumbnails_vnc_event_button, p, "close")
	button.set_label(_("Close"))
	toolbar.insert(button,-1)
	
	vbox.pack_start(toolbar, expand=False, fill=True, padding=0)
	vbox.pack_start(vnc, expand=True, fill=True, padding=1)
	
	vnc.realize()
	vbox.show_all()

	button = toolbar_button(self.cfg.pixbuf_action_window_connect_16, self.cfg.tooltips, _("Connect"))
	button.connect("clicked", self.thumbnails_vnc_event_button, p, "connect")
	button.set_label(_("Connect"))
	toolbar.insert(button,0)
	if ( "connect" in self.cfg.vncThumbnailsToolbar ):
	    button.show_all()
	
	if ( connect == "empty" ):
	    self.vnc_item_error(p, _("Disconnect"))
	    return

	vnc.set_shared_flag(True)
	vnc.set_scaling(True)

    	if ( mode != "control" ):
	    vnc.set_read_only(True)
	if ( pointer == "True" ):
	    vnc.set_pointer_local(True)
	if ( lossy == "True" ):
	    vnc.set_lossy_encoding(True)
	if ( keyboard_grab == "True" ):
	    vnc.set_keyboard_grab(True)
	if ( pointer_grab == "True" ):
	    vnc.set_pointer_grab(True)
	    
	if ( self.cfg.gtkvnc_depth ):
	    if ( color == "default" ):
		vnc.set_depth("VNC_DISPLAY_DEPTH_COLOR_DEFAULT")
	    elif ( color == "full" ):
		vnc.set_depth("VNC_DISPLAY_DEPTH_COLOR_FULL")
	    elif ( color == "medium" ):
		vnc.set_depth("VNC_DISPLAY_DEPTH_COLOR_MEDIUM")
	    elif ( color == "low" ):
		vnc.set_depth("VNC_DISPLAY_DEPTH_COLOR_LOW")
	    elif ( color == "ultra-low" ):
		vnc.set_depth("VNC_DISPLAY_DEPTH_COLOR_ULTRA_LOW")
	    else:
		vnc.set_depth("VNC_DISPLAY_DEPTH_COLOR_DEFAULT")
	
	if ( self.cfg.gtkvnc_encoding ):
	    if ( encoding == "zrle" ):
		vnc.set_encoding("VNC_DISPLAY_ENCODING_ZRLE")
	    elif ( encoding == "hextile" ):
		vnc.set_encoding("VNC_DISPLAY_ENCODING_HEXTILE")
	    elif ( encoding == "raw" ):
		vnc.set_encoding("VNC_DISPLAY_ENCODING_RAW")
	    
	vnc.set_credential(gtkvnc.CREDENTIAL_PASSWORD, password)
	    
	vnc.connect("vnc-initialized", self.vnc_item_init, p)
	vnc.connect("vnc-disconnected", self.vnc_item_disconnect, p)
	vnc.connect("vnc_auth_failure", self.vnc_item_auth_failure, p)
	vnc.open_host(ip, vncport)

    ##############################################

    def vnc_item_init(self, vnc, p):
	self.cfg.debug("vnc_item_init: "+p[1])

    ##############################################

    def vnc_item_auth_failure(self, vnc, msg, p):
	self.cfg.debug("vnc_item_auth_failure: "+p[1])
	self.vnc_item_error(p, _("Authentication failure"))

    ##############################################

    def vnc_item_disconnect(self, vnc, p):
	self.cfg.debug("vnc_item_disconnect: "+p[1])
	self.vnc_item_error(p, _("Disconnect"))
	
    ##############################################

    def vnc_item_error(self, p, label_error):
	if ( self.cfg.vnc_close_active ):
	    return
	if ( p[3] ):
	    p[3].destroy()
	    p[3] = None
	if ( p[2] ):
	    if ( len(p[2].get_children()) == 2 and type(p[2].get_children()[1]) == gtk.Frame ):
	    	p[2].remove(p[2].get_children()[1])
	    if ( len(p[2].get_children()) == 1 ):
		frame = gtk.Frame()
		p[2].pack_start(frame, expand=True, fill=True, padding=0)
		label = gtk.Label(label_error)
		label.modify_font(pango.FontDescription(self.cfg.fontThumbnails))
		frame.add(label)
		frame.show_all()
	    toolbar = p[2].get_children()[0]
	    for w in toolbar.get_children():
		if ( type(w) == gtk.ToolButton or type(w) == gtk.ToggleToolButton ):
		    if ( w.get_label() != _("Connect") and \
			w.get_label() != _("Upstairs") and \
			w.get_label() != _("Size") and \
			w.get_label() != _("Close") ):
			w.set_sensitive(False)
		    if ( "connect" not in self.cfg.vncThumbnailsToolbar ):
			if ( w.get_label() == _("Connect") ):
		    	    w.show_all()
	    	    if ( p[12] != "view" ):
	    	    	p[12] = "view"
		    	self.thumbnails_button(p, _("Viewer")+"/"+_("Control"))

    ##############################################
	    
    def close_gtkvnc(self, data=None):
	# gtkvnc 0.4.3 - GtkWarning: IA__gdk_drawable_get_size: assertion `GDK_IS_DRAWABLE (drawable)' failed
	if ( self.cfg.vnc_box != [] ):
	    self.cfg.debug("close_gtkvnc start")
    	    self.cfg.vnc_close_active = True
    	    for p in self.cfg.vnc_box:
		if ( p[3] ):
		    p[3].close()
		    p[3] = None
		self.table_vnc.remove(p[2])
		p[2] = None
	    del self.cfg.vnc_box[:]
    	    #gc.collect()
	    self.cfg.debug("close_gtkvnc end")
    	    self.cfg.vnc_close_active = False

    ##############################################

    def thumbnails_vnc(self, user_list, param):
	# Функция заполнения vnc VBox-ами(миниатюрами)
	# Без модуля gtkvnc не работает
	self.cfg.debug("---thumbnails_vnc start---")
	self.cfg.vnc_active = True
	self.cfg.vnc_active_open = True

	new_thumb_x = param[0]
	new_thumb_y = param[1]
	size = param[15]
	thumbnails_col = param[16]
	insert = param[17]
	
	row = 0
	col = 0
	item = -1
        for z in user_list:

    	    item += 1
	    self.cfg.vnc_count += 1
	    
	    # Проверка повтора при добавлении
	    if ( insert ):
		rep = False
		for p in self.cfg.vnc_box:
		    if ( z[self.cfg.dn['client_id']] == p[0] ):
			rep = True
			break
	    	if ( rep ):
    	    	    col += 1
    	    	    if ( col >= thumbnails_col ): 
    	    		col = 0
    	    		row += 1
	    	    continue

	    
	    vbox = gtk.VBox(False, 0)
	    vbox.connect("motion-notify-event", self.thumbnails_motion_event)
	    vbox.set_size_request(new_thumb_x, new_thumb_y)
	    # Рамка
	    frame = gtk.Frame()
	    label = gtk.Label(_("Connecting")+"...")
	    label.modify_font(pango.FontDescription(self.cfg.fontThumbnails))
	    frame.add(label)
	    vbox.pack_start(frame, expand=True, fill=True, padding=0)
	    vbox.show_all()
	    vbox.connect("button-press-event", self.thumbnails_vnc_event)
    	    self.table_vnc.put(vbox, col*(int(new_thumb_x)+self.cfg.tt_border), row*(new_thumb_y+self.cfg.tt_border))
    	    
    	    col += 1
    	    if ( col >= thumbnails_col ): 
    	    	col = 0
    	    	row += 1
	    # Отдельный поток на каждую миниатюру, без курсора
	    thread = thread_gfunc(self.cfg, False, True, self.thumbnails_vnc_item, vbox, z, param, item)
	    thread.start()
	    # sleep, иначе некоторые не открываются
	    time.sleep(0.1)

	self.colVnc = thumbnails_col

    	# sleep, иначе зависание(P5/P6). Курсор ожидания.
	time.sleep(2+len(user_list)*0.1)
	self.cfg.vnc_active_open = False
	self.cfg.debug("---thumbnails_vnc count---: "+str(self.cfg.vnc_count))
	self.cfg.debug("---thumbnails_vnc end---")

    ##############################################
    
    def thumbnails_vnc_active(self):
	self.cfg.vnc_active = False

    ##############################################

    def thumbnails_table_size(self):
	x = self.cfg.panedWindow.get_position() - self.panedTree.get_position() - self.cfg.slider_size - 2*self.cfg.tt_border - 20
	y = self.cfg.window_y - self.widget_view()
	return x, y
	
    ##############################################

    def thumbnails_resize_press(self, widget, event, p):
	if ( event.button == 1 ):
	    self.cfg.thumbnails_resize_item = p
	    if ( p[3] ):
		p[3].hide()

    ##############################################

    def thumbnails_resize_release(self, widget, event, p):
	self.cfg.thumbnails_resize_item = None
	if ( p[3] ):
	    p[3].show()
	if ( p[4] == p[6] and p[5] == p[7] ):
	    p[13] = "min"
	    self.thumbnails_button(p, _("Size"))
	if ( p[2] ):
	    new_window_x = self.cfg.window_x
	    new_window_y = self.cfg.window_y
	    vbox_alloc = p[2].get_allocation()
	    if ( p[4] > self.thumbnails_table_size()[0] ):
		new_window_x = self.panedTree.get_position() + self.cfg.slider_size + 2*self.cfg.tt_border + 20 + p[4]
	    if ( p[5] + vbox_alloc.y - self.cfg.tt_border > self.thumbnails_table_size()[1] ):
		new_window_y = self.widget_view() + p[5] + vbox_alloc.y - self.cfg.tt_border
	    if ( new_window_x != self.cfg.window_x or new_window_y != self.cfg.window_y ):
		self.window.resize(new_window_x, new_window_y)

    ##############################################

    def table_vnc_motion_event(self, widget, event):
	p = self.cfg.thumbnails_resize_item
	if ( p and p[2] and p[25] and p[26] ):
	    x, y = widget.get_pointer()
	    vbox_alloc = p[2].get_allocation()
	    frame_alloc = p[25].get_allocation()
	    
	    # Нельзя передвинуть правее области просмотра, меньше мин размера, больше макс рамера.
	    if ( x-vbox_alloc.x-int(self.cfg.tt_border*0.5) > self.thumbnails_table_size()[0]-vbox_alloc.x+int(self.cfg.tt_border*0.5) ):
		thumb_x = self.thumbnails_table_size()[0]-vbox_alloc.x+int(self.cfg.tt_border*0.5)
		frame_x = thumb_x+self.cfg.tt_border
	    elif ( p[6] < x-vbox_alloc.x-int(self.cfg.tt_border*0.5) < p[8] ):
		thumb_x = x-vbox_alloc.x-int(self.cfg.tt_border*0.5)
		frame_x = thumb_x+self.cfg.tt_border
	    elif ( p[6] >= x-vbox_alloc.x-int(self.cfg.tt_border*0.5) ):
		thumb_x = p[6]
		frame_x = thumb_x+self.cfg.tt_border
	    elif ( p[8] <= x-vbox_alloc.x-int(self.cfg.tt_border*0.5) ):
		thumb_x = p[8]
		frame_x = thumb_x+self.cfg.tt_border
		
	    # Нельзя передвинуть меньше мин размера, больше макс рамера.
	    if ( p[7] < y-vbox_alloc.y-int(self.cfg.tt_border*0.5) < p[9] ):
		thumb_y = y-vbox_alloc.y-int(self.cfg.tt_border*0.5)
		frame_y = thumb_y+self.cfg.tt_border
	    elif ( p[7] >= y-vbox_alloc.y-int(self.cfg.tt_border*0.5) ):
		thumb_y = p[7]
		frame_y = thumb_y+self.cfg.tt_border
	    elif ( p[9] <= y-vbox_alloc.y-int(self.cfg.tt_border*0.5) ):
		thumb_y = p[9]
		frame_y = thumb_y+self.cfg.tt_border
		
	    if ( thumb_x == p[6] and thumb_y == p[7] ):
    	        p[13] = "min"
		self.thumbnails_button(p, _("Size"))
		p[13] = "custom"
	    else:
		p[13] = "custom"
		self.thumbnails_button(p, _("Size"))
	    p[2].set_size_request(thumb_x, thumb_y)
	    p[25].set_size_request(frame_x, frame_y)
	    p[4] = thumb_x
	    p[5] = thumb_y
	    self.table_vnc.move(p[26], vbox_alloc.x+thumb_x-int(self.cfg.tt_border*0.5)-9, vbox_alloc.y+thumb_y-int(self.cfg.tt_border*0.5)-9)
	    self.thumbnails_reorder("all")

    ##############################################

    def thumbnails_motion_event(self, widget=None, event=None):
	p = None
	for x in self.cfg.vnc_box:
	    if ( x[2] == widget ):
		p = x
		break
	if ( p and p[2] and not p[25] and not p[26] ):
	    frame = gtk.Frame()
	    frame.set_border_width(0)
	    frame.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("gray"))
	    vbox_alloc = p[2].get_allocation()
	    frame.set_size_request(vbox_alloc.width+self.cfg.tt_border, vbox_alloc.height+self.cfg.tt_border)
	    self.table_vnc.put(frame, vbox_alloc.x-int(self.cfg.tt_border*1.5), vbox_alloc.y-int(self.cfg.tt_border*1.5))
    	    frame.show_all()
    	    p[25] = frame
	    
	    ebox = gtk.EventBox()
	    ebox.set_visible_window(False)
	        
	    image = gtk.Image()
	    image.set_from_pixbuf(self.cfg.pixbuf_action_resize_12)
	    ebox.add(image)
	    ebox.connect("button-press-event", self.thumbnails_resize_press, p)
	    ebox.connect("button-release-event", self.thumbnails_resize_release, p)
	    self.table_vnc.put(ebox, vbox_alloc.x+vbox_alloc.width-int(self.cfg.tt_border*0.5)-9, vbox_alloc.y+vbox_alloc.height-int(self.cfg.tt_border*0.5)-9)
	    ebox.show_all()
    	    p[26] = ebox
    	    gobject.timeout_add(100, self.thumbnails_frame_destroy, p)
    
    ##############################################

    def thumbnails_frame_destroy(self, p, destroy=None):
	if ( self.cfg.thumbnails_resize_item ):
	    return True
	if ( p[2] and p[25] and p[26] and not destroy):
	    x_frame, y_frame = p[25].get_pointer()
	    frame_alloc = p[25].get_allocation()
	    x_vbox, y_vbox = p[2].get_pointer()
	    vbox_alloc = p[2].get_allocation()
	    x_button, y_button = p[26].get_pointer()
	    button_alloc = p[26].get_allocation()
	    if ( ((0 < x_button < button_alloc.width and 0 < y_button < button_alloc.height) or \
		(0 < x_frame < frame_alloc.width and 0 < y_frame < frame_alloc.height)) and \
		vbox_alloc.x == frame_alloc.x+int(self.cfg.tt_border*0.5) and vbox_alloc.y == frame_alloc.y+int(self.cfg.tt_border*0.5) and \
		vbox_alloc.width == frame_alloc.width-self.cfg.tt_border and vbox_alloc.height == frame_alloc.height-self.cfg.tt_border ):
		return True
	if ( p[25] ):
	    p[25].destroy()
	    p[25] = None
	if ( p[26] ):
	    p[26].destroy()
	    p[26] = None
	return False
    	    
    ##############################################
    
    def thumbnails_vnc_item(self, vbox, z, param, item):
	self.cfg.debug("-thumbnails_vnc_item start- "+z[0])
	new_thumb_x = param[0]
	new_thumb_y = param[1]
	new_min_thumb_x = param[2]
	new_min_thumb_y = param[3]
	new_max_thumb_x = param[4]
	new_max_thumb_y = param[5]
	window_x = param[6]
	window_y = param[7]
	new_window_x = param[8]
	new_window_y = param[9]
	new_min_window_x = param[10]
	new_min_window_y = param[11]
    	new_max_window_x = param[12]
    	new_max_window_y = param[13]
	mode = param[14]
	size = param[15]
	thumbnails_col = param[16]
	insert = param[17]
	
    	d = {}
	for key, value in zip(self.cfg.z, z):
	    d[key] = value
	    
	name = d['alias']

    	p = [
    	    d['client_id'], name, vbox, None, new_thumb_x,
    	    new_thumb_y, new_min_thumb_x, new_min_thumb_y, new_max_thumb_x, new_max_thumb_y,\
    	    new_max_window_x, new_max_window_y, mode, size, None,\
    	    None, None, d['vnc_pass'], d['vnc_gtk_color'], d['vnc_gtk_lossy'],\
    	    d['vnc_gtk_pointer'], d['vnc_gtk_pointer_grab'], d['vnc_gtk_keyboard_grab'], d['vnc_gtk_encoding'], None,\
    	    None, None, None, None, None
    	    ]

	self.cfg.vnc_box.insert(item, p)

	connect = "connect"
	z_check = check_user_list(self.cfg, [z], "vnc")
	if ( z_check == [] ):
	    connect = "empty"
	else:
	    z = z_check[0]
    	    
	if ( connect == "empty" ):
	    ip = "0"
	    vncport = "0"
	else:
	    (ip, vncport, vncviewer) = vnc_razrulit(self.cfg, z)
    	    if ( vncport == "0" ):
		connect = "empty"
	
    	p[15] = ip
    	p[16] = vncport
    	
    	# Удалить рамку
    	vbox.remove(vbox.get_children()[0])
    	
    	# только idle_add
        gobject.idle_add(self.vnc_item, p, connect)
    	# sleep, иначе зависание(P5/P6). Больше 3 секунд!
	time.sleep(7)
	self.cfg.debug("-thumbnails_vnc_item end- "+z[0])
    
    ##############################################

    def thumbnails_vnc_post(self, param):
	self.cfg.debug("--thumbnails_vnc_post start--")
	new_thumb_x = param[0]
	new_thumb_y = param[1]
	new_min_thumb_x = param[2]
	new_min_thumb_y = param[3]
	new_max_thumb_x = param[4]
	new_max_thumb_y = param[5]
	window_x = param[6]
	window_y = param[7]
	new_window_x = param[8]
	new_window_y = param[9]
	new_min_window_x = param[10]
	new_min_window_y = param[11]
    	new_max_window_x = param[12]
    	new_max_window_y = param[13]
	mode = param[14]
	size = param[15]
	thumbnails_col = param[16]
	insert = param[17]
    	# Изменить окно
	# Если открыто второе окно
	if ( self.cfg.table2.get_children() != [] ):
	    self.cfg.mainWindowLastX = new_window_x
	# Если сдвинут разделитель
	if ( self.panedTree.get_position() > self.cfg.treeX ):
	    self.panedTree.set_position(self.cfg.treeX)
	# Если размер окна изменен во время открытия
	if ( window_x != self.cfg.window_x or window_y != self.cfg.window_y ):
	    self.thumbnails_reorder("all")
	elif ( self.panedTree.get_position() != self.cfg.treeX ):
	    # Если сдвинут разделитель
	    self.thumbnails_reorder("all")
	    if ( (window_x < new_window_x or window_y < new_window_y) and self.cfg.maximized == False and self.cfg.fullscreen == False and size == "max" ):
		# Если размер меньше необходимого
		self.window.resize(new_window_x, new_window_y)
	elif ( (window_x < new_window_x or window_y < new_window_y) and self.cfg.maximized == False and self.cfg.fullscreen == False ):
	    # Если размер меньше необходимого
	    self.window.resize(new_window_x, new_window_y)
	self.cfg.debug("--thumbnails_vnc_post end--")

    ##############################################

    def vnc_thumbnails_size(self, size="min"):

    	if ( self.panedTree.get_position() > self.cfg.treeX ):
    	    self.panedTree.set_position(self.cfg.treeX)

	# Декорации окна + отступ vncBox
	window_x = self.cfg.window_x
	window_y = self.cfg.window_y
	real_x =  self.thumbnails_table_size()[0]
	real_y = self.thumbnails_table_size()[1]
	corr_x = window_x-real_x
	corr_y = window_y-real_y

	if ( size == "min" ):
	    thumb_x = self.cfg.vncThumbnailsX
	    thumb_y = self.cfg.vncThumbnailsY + self.cfg.tt_size
	else:
	    thumb_x = self.cfg.vncGtkX
	    thumb_y = self.cfg.vncGtkY + self.cfg.tt_size

	new_thumb_x = thumb_x
	new_thumb_y = thumb_y
	new_window_x = window_x
	new_window_y = window_y

	if ( real_x < thumb_x ):
	    new_window_x = window_x-real_x+thumb_x
	if ( real_y < thumb_y ):
	    new_window_y = window_y-real_y+thumb_y

	if ( new_window_x != window_x or new_window_y != window_y ):
	    if ( new_window_x > self.cfg.screen_x ):
	        new_window_x = self.cfg.screen_x
	        new_thumb_x = self.cfg.screen_x-corr_x
	    if ( new_window_y > self.cfg.screen_y ):
	        new_window_y = self.cfg.screen_y
	        new_thumb_y = self.cfg.screen_y-corr_y
	    if ( size == "max" and self.cfg.read_config("vnc","vnc_thumbnails_reduce") == "n" ):
		# Не подгонять под размер окна просмотра
		new_thumb_x = thumb_x
		new_thumb_y = thumb_y
	    else:
		# Если размер изменился
		# Использовать начальное соотношение сторон
		if ( new_thumb_x != thumb_x or new_thumb_y != thumb_y ):
		    ratio = float(thumb_x)/float(thumb_y)
		    if ( float(new_thumb_x)/float(new_thumb_y) < ratio ):
    			new_thumb_y = int(new_thumb_x/ratio)
		    else:
    			new_thumb_x = int(new_thumb_y*ratio)	
		# Изменить окно под новый размер
		new_window_x = new_thumb_x+corr_x
		new_window_y = new_thumb_y+corr_y
	return window_x, window_y, real_x, real_y, new_thumb_x, new_thumb_y, new_window_x, new_window_y

    ##############################################

    def thumbnails_vnc_pre(self, user_list, mode):
	self.cfg.debug("--thumbnails_vnc_pre start--")
	# Ширину главного окна под размер одной миниатюры
	# Максимум ширина экрана
	
	(window_x, window_y, real_x, real_y, new_min_thumb_x, new_min_thumb_y, new_min_window_x, new_min_window_y) = self.vnc_thumbnails_size("min")
	(window_x, window_y, real_x, real_y, new_max_thumb_x, new_max_thumb_y, new_max_window_x, new_max_window_y) = self.vnc_thumbnails_size("max")
	
	# mode - встроенный в интерфейс VNC
	if ( mode == "thumbnails" ):
	    mode = "view"
	    size = "min"
	    new_thumb_x = new_min_thumb_x
	    new_thumb_y = new_min_thumb_y
	    new_window_x = new_min_window_x
	    new_window_y = new_min_window_y
	else:
	    size = "max"
	    new_thumb_x = new_max_thumb_x
	    new_thumb_y = new_max_thumb_y
	    new_window_x = new_max_window_x
	    new_window_y = new_max_window_y
	
	# Сколько по ширине
	thumbnails_col = (real_x)/(int(new_thumb_x)+self.cfg.tt_border)
	
	# Добавление
	insert = False
	if ( self.cfg.vnc_box != [] and self.cfg.read_config("vnc","vnc_thumbnails_insert") != "y" ):
	    self.close_gtkvnc()
	elif ( self.cfg.vnc_box != [] ):
	    insert = True
	    # Проверка повтора и перенос позиций
	    item = -1
	    new = False
	    for x in user_list:
		item += 1
		rep = False
		for p in self.cfg.vnc_box:
		    if ( x[self.cfg.dn['client_id']] == p[0] ):
	    		rep = True
	    		if ( size == "max" ):
	    		    if ( p[13] != "max" ):
	    		        p[13] = "max"
	    		    # Кнопка просмотр/управления
	    		    if ( mode == "view" and p[12] != "view" ):
	    			p[12] = "view"
		    		self.thumbnails_button(p, _("Viewer")+"/"+_("Control"))
	    		    if ( mode == "control" and p[12] != "control" ):
	    			p[12] = "control"
		    		self.thumbnails_button(p, _("Viewer")+"/"+_("Control"))
	    		else:
	    		    if ( p[13] != "min" and p == self.cfg.vnc_box[0] ):
	    		    	p[13] = "min"
	    		self.cfg.vnc_box.remove(p)
	    		self.cfg.vnc_box.insert(item, p)
			break
		# Добавить пустые
		if ( rep == False ):
		    if ( not new ):
			new = True
		    self.cfg.vnc_box.insert(item, \
					    ["empty", "", "", "", new_thumb_x,\
					    new_thumb_y, new_min_thumb_x, new_min_thumb_y, new_max_thumb_x, new_max_thumb_y,\
					    None, None, None, None, None,\
					    None, None, None, None, None,\
					    None, None, None, None, None,\
					    None, None, None, None, None])
	    if ( new and self.cfg.read_config("vnc","vnc_thumbnails_minimize") == "y" ):
		self.thumbnails_reorder("all_minimize", self.cfg.vnc_box[0])
	    else:
		self.thumbnails_reorder("resize", self.cfg.vnc_box[0])
		
	    # Удалить пустые
	    temp = []
	    for x in self.cfg.vnc_box:
	        if ( x[0] == "empty" ):
	    	    temp.append(x)
	    for x in temp:
	        self.cfg.vnc_box.remove(x)
	
	# Проверка новых в user_list
	new = False
	# список ID
	temp = []
	for p in self.cfg.vnc_box:
	    temp.append(p[0])
	# поиск
	for x in user_list:
	    if ( x[self.cfg.dn['client_id']] not in temp ):
		new = True
	
	# размеры окна
	if ( size == "max" and new == False ):
	    if ( (window_x < new_max_window_x or window_y < new_max_window_y) and self.cfg.maximized == False and self.cfg.fullscreen == False ):
		self.window.resize(new_window_x, new_window_y)
		
	# параметры	
	param = [\
		new_thumb_x, new_thumb_y,\
		new_min_thumb_x, new_min_thumb_y,\
		new_max_thumb_x, new_max_thumb_y,\
		window_x, window_y,\
		new_window_x, new_window_y,
		new_min_window_x, new_min_window_y,\
    		new_max_window_x, new_max_window_y,\
    		mode, size, thumbnails_col, insert
    		]
	self.cfg.debug("--thumbnails_vnc_pre end--")
	return new, param

    ##############################################
		
    def context_menu(self, event, line_vnc_box=None):
	# line_vnc_box объекты из self.cfg.vnc_box
	menu = gtk.Menu()
	
	if ( not line_vnc_box ):
    	    if ( self.cfg.read_config("hide","hide_viewer") == "n" ):
		item = menu_image_button(self.cfg.pixbuf_action_viewer_16, _("Viewer"))
		item.connect('activate', self.callback, "view")
    		menu.append(item)

    	    if ( self.cfg.read_config("hide","hide_control") == "n" ):
		item = menu_image_button(self.cfg.pixbuf_action_control_16, _("Control"))
		item.connect('activate', self.callback, "control")
    		menu.append(item)

    	    if ( self.cfg.read_config("hide","hide_thumbnails") == "n" ):
		item = menu_image_button(self.cfg.pixbuf_action_thumbnails_16, _("Thumbnails"))
		item.connect('activate', self.callback, "thumbnails")
    		menu.append(item)

	# снимок экрана только на миниатюре
	if ( line_vnc_box ):
	    item = menu_image_button(self.cfg.pixbuf_action_screenshot_16, _("Screenshot"))
	    item.connect('activate', self.callback, "screenshot", line_vnc_box)
    	    menu.append(item)

	    item = menu_image_button(self.cfg.pixbuf_action_screenshot_16, _("All screenshots"))
	    item.connect('activate', self.callback, "screenshot_all")
    	    menu.append(item)

    	    item = gtk.SeparatorMenuItem() 
    	    menu.append(item)
	    
	    item = menu_image_button(self.cfg.pixbuf_action_window_min_16, _("Minimize all"))
	    item.connect('activate', self.view_vnc_minimize)
    	    menu.append(item)

	    item = menu_image_button(self.cfg.pixbuf_action_close_16, _("Close all"))
	    item.connect('activate', self.view_vnc_close)
    	    menu.append(item)

    	item = gtk.SeparatorMenuItem() 
    	menu.append(item)

    	if ( self.cfg.read_config("hide","hide_message") == "n" ):
	    item = menu_image_button(self.cfg.pixbuf_action_send_message_16, _("Send message"))
	    item.connect('activate', self.callback, "send_message")
    	    menu.append(item)

    	if ( self.cfg.read_config("hide","hide_command") == "n" ):
	    item = menu_image_button(self.cfg.pixbuf_action_run_16, _("Run command"))
	    item.connect('activate', self.callback, "run")
    	    menu.append(item)
        
    	if ( self.cfg.read_config("hide","hide_send_file") == "n" ):
	    item = menu_image_button(self.cfg.pixbuf_list_file_send_16,_("Send file"))
    	    item.connect("activate", self.callback, "send_file")
    	    menu.append(item)

    	if ( self.cfg.read_config("hide","hide_util") == "n" ):
    	    item = gtk.SeparatorMenuItem() 
    	    menu.append(item)
	
	    item = menu_image_button(self.cfg.pixbuf_home_16, _("Home folder"))
    	    item.connect("activate", self.callback, "folder_user")
    	    menu.append(item)

	    item = gtk.SeparatorMenuItem()
    	    menu.append(item)

    	    item = menu_image_button(self.cfg.pixbuf_console_16, _("Console"))
	    item.connect('activate', self.callback, "console_server")
    	    menu.append(item)
    	    
    	    item = menu_image_button(self.cfg.pixbuf_console_16, _("Console(host)"))
	    item.connect('activate', self.callback, "console_host")
    	    menu.append(item)

    	    item = menu_image_button(self.cfg.pixbuf_console_root_16, _("Console")+"(root)")
	    item.connect('activate', self.callback, "console_root")
    	    menu.append(item)
    	
	    item = menu_image_button(self.cfg.pixbuf_run_root_16, _("Run as root"))
	    item.connect('activate', self.callback, "run_root")
    	    menu.append(item)

    	    item = gtk.SeparatorMenuItem() 
    	    menu.append(item)

	    item = menu_image_button(self.cfg.pixbuf_process_16, _("View process"))
	    item.connect('activate', self.callback, "process")
    	    menu.append(item)

	    item = menu_image_button(self.cfg.pixbuf_hwinfo_16, _("Hardware Info"))
	    item.connect('activate', self.callback, "hwinfo")
    	    menu.append(item)

	    item = gtk.SeparatorMenuItem()
    	    menu.append(item)

	    item = menu_image_button(self.cfg.pixbuf_lock_16, _("Lock screen"))
	    item.connect('activate', self.callback, "lock")
    	    menu.append(item)

	    item = menu_image_button(self.cfg.pixbuf_unlock_16, _("Unlock screen"))
	    item.connect('activate', self.callback, "unlock")
    	    menu.append(item)
    	    
	    item = gtk.SeparatorMenuItem()
    	    menu.append(item)

	    item = menu_image_button(self.cfg.pixbuf_block_16, _("Lock the input"))
	    item.connect('activate', self.callback, "block")
    	    menu.append(item)

	    item = menu_image_button(self.cfg.pixbuf_unblock_16, _("Unlock the input"))
	    item.connect('activate', self.callback, "unblock")
    	    menu.append(item)
    	    
    	if ( self.cfg.read_config("hide","hide_system_util") == "n" ):
    	    item = gtk.SeparatorMenuItem() 
    	    menu.append(item)

	    menu_system = gtk.Menu()
    	    item = menu_image_button(self.cfg.pixbuf_menu_system_16, "")
    	    item.set_submenu(menu_system)
    	    menu.append(item)

	    item = menu_image_button(self.cfg.pixbuf_logout_16, _("Logout"))
	    item.connect("button-press-event", self.callback, "logout")
    	    menu_system.append(item)

	    item = menu_image_button(self.cfg.pixbuf_reboot_16, _("Reboot"))
	    item.connect("button-press-event", self.callback, "reboot")
    	    menu_system.append(item)

	    item = menu_image_button(self.cfg.pixbuf_turn_on_16, _("Turn On"))
	    item.connect("button-press-event", self.callback, "wake_on_lan")
    	    menu_system.append(item)

	    item = menu_image_button(self.cfg.pixbuf_shutdown_16, _("Shutdown"))
	    item.connect("button-press-event", self.callback, "shutdown")
    	    menu_system.append(item)
	

        menu.popup(None, None, self.context_menu_pos, event.button, event.time, event)
	menu.show_all()

    ##############################################

    def context_menu_pos(self, menu, event=None):
	x, y, mods = menu.get_root_window().get_pointer()
	ysize = len(menu.get_children())*16
	if ( y+ysize > self.cfg.screen_y ):
	    y = self.cfg.screen_y - ysize
	return (x, y, True)
	
    ##############################################

    def status_changed(self, widget, event, data=None):
	# Устанавливает видимым последнее(нижнее) сообщение status()
        adj = self.swStatus.get_vadjustment()
        adj.set_value(adj.upper - adj.page_size)
	
    ##############################################

    def tree_leave(self, widget, event):
	# Убрать выделение
    	self.cfg.tree_motion_select_row = None
    	# Подсказки
	self.tree_info.set_text("")

    ##############################################

    def tree_cell_data_func(self, column, renderer, model, iter, data):
	if ( self.cfg.tree_motion_select_row == model.get_path(iter) ):
    	    renderer.set_property("weight", pango.WEIGHT_BOLD)
    	    #renderer.set_property("underline", pango.UNDERLINE_LOW)
    	    #renderer.set_property("foreground", "blue")
    	    pass
        else:
    	    renderer.set_property("weight", pango.WEIGHT_NORMAL)
    	    #renderer.set_property("underline", pango.UNDERLINE_NONE)
    	    #renderer.set_property("foreground", "black")
    	    pass

    def tree_motion_event(self, treeView, event):
    	model = treeView.get_model()
	# motion select
    	if ( treeView.get_path_at_pos(int(event.x), int(event.y)) ):
    	    (row,col,x,y) = treeView.get_path_at_pos(int(event.x), int(event.y))
    	    self.cfg.tree_motion_select_row = row
    	else:
    	    self.cfg.tree_motion_select_row = None
    	# tooltip
	info = ""
	if ( self.cfg.treeInfo == "y"):
    	    if ( treeView.get_path_at_pos(int(event.x), int(event.y)) ):
    		(row,col,x,y) = treeView.get_path_at_pos(int(event.x), int(event.y))
    		if ( len(row) != 1 ):
    		    user = model[row][1]
    		    host = model[row][2]
    		    server = model[row][4]
    		    ip = model[row][3]
    		    if ( model[row][5] == "standalone" ):
    			info = user+"@"+host+"("+ip+")"
    		    else:
    			info = user+"@"+host+"("+ip+") "+server
	if ( self.cfg.treeInfoTooltip == "y"):
	    if ( self.tree_info.get_text() != "" ):
		self.tree_info.set_text("")
    	    if ( gtk.pygtk_version < (2, 12, 0) ):
    		# Отображается под treeView
    		#self.cfg.tooltips.set_tip(treeView, info)
    		#self.cfg.tooltips.enable()
		self.tree_info.set_text(info)
    	    else:
    		treeView.set_tooltip_text(info)
    	else:
    	    self.tree_info.set_text(info)

    ##############################################

    def tree_button_press(self, treeView, event):
	mouse_pos = treeView.get_path_at_pos(int(event.x),int(event.y))
	# Снять выделение
	if ( not mouse_pos ):
	    treeView.get_selection().unselect_all()
	    return
	# multiple
	elif ( event.button == 3 or event.button == 1 ):
	    model, rows = treeView.get_selection().get_selected_rows()
	    if ( rows == [] and event.button == 1 ):
    		return
    	    if ( mouse_pos[0] in rows ):
    		treeView.get_selection().unselect_all()
		for row in rows:
    		    treeView.get_selection().select_path(row)
		# Отлючить выделение
		tree_selection_enable(self.cfg.treeView, False)
		# Обратно включить
		# Можно через button-release-event, но после popup-menu надо лишнее нажатие кнопки
		gobject.timeout_add(10, tree_selection_enable, self.cfg.treeView, True)
        # Действия
        if ( event.type == gtk.gdk._2BUTTON_PRESS and self.cfg.read_config("hide","hide_tree_add_remove") == "n" ):
	    self.callback(None, "edit_tree_item")
	if ( event.button == 3 ):
	    self.context_menu(event)
		
    ##############################################

    def mainUi(self, data=None):

	self.vboxMain = gtk.VBox(False, 0)
	self.cfg.table2 = gtk.Table(42, 28, True)
	self.cfg.panedWindow = gtk.HPaned()
	self.cfg.panedWindow.pack1(self.vboxMain, resize=False, shrink=True)
	self.cfg.panedWindow.pack2(self.cfg.table2, resize=False, shrink=True)
        self.cfg.window.add(self.cfg.panedWindow)
        self.cfg.panedWindow.connect("notify::position", self.paned_window_event)

	#################
	# status
	#################
	self.swStatus = gtk.ScrolledWindow()
	self.swStatus.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
	self.textviewStatus = gtk.TextView(self.cfg.bufferStatus)
	self.textviewStatus.connect('size-allocate', self.status_changed)
	self.textviewStatus.set_property('editable', False)
	self.textviewStatus.set_cursor_visible(False)
	#self.textviewStatus.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("light gray"))
	self.textviewStatus.modify_base(gtk.STATE_NORMAL, self.cfg.bg_color)
	self.textviewStatus.modify_font(pango.FontDescription(self.cfg.fontStatus))
	self.swStatus.set_border_width(0)
	self.swStatus.add(self.textviewStatus)
	# Похож по цвету на gtk.StatusBar
	# без Viewport() цвет не изменить
	self.viewportStatus = gtk.Viewport()
	self.viewportStatus.add(self.swStatus)

	self.cfg.bufferStatus.insert(self.cfg.bufferStatus.get_end_iter(), "\n")
    	self.cfg.status(_("Starting"))

	self.cfg.treeView = gtk.TreeView(self.cfg.userList)
	self.cfg.treeView.set_rules_hint(True)
	self.cfg.treeView.set_enable_tree_lines(True)
	#self.cfg.treeView.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_VERTICAL)
	self.cfg.treeView.set_headers_visible(True)
	self.cfg.treeView.set_headers_clickable(False)
	self.cfg.treeView.modify_font(pango.FontDescription(self.cfg.fontTree))
	#self.cfg.treeView.modify_base(gtk.STATE_SELECTED, gtk.gdk.color_parse("black"))
	self.cfg.treeView.connect("button-press-event", self.tree_button_press)
	self.cfg.treeView.connect("motion-notify-event", self.tree_motion_event)
	self.cfg.treeView.set_events( gtk.gdk.POINTER_MOTION_MASK )
	
	# drag and drop
	TARGETS = [('TREE_MAIN', gtk.TARGET_SAME_WIDGET, 0), ('TEXT', 0, 0) ]
	self.cfg.treeView.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, TARGETS, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_MOVE)
	self.cfg.treeView.enable_model_drag_dest(TARGETS, gtk.gdk.ACTION_DEFAULT)
	self.cfg.treeView.connect("drag_data_received", tree_drag_data_received, self.cfg)
	self.cfg.treeView.connect("drag_data_get", tree_drag_data_get, self.cfg)
	self.cfg.treeView.connect("leave-notify-event", self.tree_leave)
	self.cfg.treeView.connect("drag_motion", tree_drag_data_motion)

	d = {}
        for x in range(len(self.cfg.z)):
    	    d[self.cfg.z[x]] = int(x)
	
	i = -1
	for x in self.cfg.z:
	    i += 1
	    if ( i == d['alias'] ):
    		column = gtk.TreeViewColumn(_("Alias"))
		column.set_expand(True)
		column.set_spacing(3)
		
    		cell = gtk.CellRendererPixbuf()
		column.pack_start(cell, expand=False)
    		column.set_attributes(cell, pixbuf=100)

    		cell = gtk.CellRendererText()
    		cell.connect('edited', self.rename_group)
		column.pack_start(cell, expand=True)
    		column.set_attributes(cell, text=i)
    		column.set_cell_data_func(cell, self.tree_cell_data_func, None)
    		for y in range(9):
    		    cell = gtk.CellRendererPixbuf()
		    column.pack_start(cell, expand=False)
    		    column.set_attributes(cell, pixbuf=101+y)
	    else:
		cell = gtk.CellRendererText()
		if ( i == d['user'] ):
    		    column = gtk.TreeViewColumn(_("User"), cell, text=i)
		elif ( i == d['host'] ):
    		    column = gtk.TreeViewColumn(_("Host"), cell, text=i)
		elif ( i == d['ip'] ):
    		    column = gtk.TreeViewColumn(_("IP"), cell, text=i)
		elif ( i == d['server'] ):
    		    column = gtk.TreeViewColumn(_("Server"), cell, text=i)
		elif ( i == d['mac'] ):
    		    column = gtk.TreeViewColumn(_("MAC"), cell, text=i)
		elif ( i == d['start_time'] ):
    		    column = gtk.TreeViewColumn(_("Time"), cell, text=i)
    		else:
    		    column = gtk.TreeViewColumn(x, cell, text=i)
    		column.set_expand(True)
	    self.cfg.treeView.append_column(column)
	
	#self.cfg.treeShow = "full"
	if ( self.cfg.treeShow == "full" ):
	    visible_columns = []
	else:
	    visible_columns = self.cfg.treeShow.split(",")

	for i in range(len(self.cfg.z)):
    	    column = self.cfg.treeView.get_column(i)
    	    if ( visible_columns == [] ):
		column.set_visible(True)
		continue
    	    if ( str(i) in visible_columns):
		column.set_visible(True)
	    else:
		column.set_visible(False)
    	
    	column = self.cfg.treeView.get_column(0)
	cell = column.get_cell_renderers()[1]
	cell.set_property("visible", True)
	

	self.treeSelection = self.cfg.treeView.get_selection()
	self.treeSelection.set_mode(gtk.SELECTION_MULTIPLE)
	self.sw = gtk.ScrolledWindow()
	self.sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
	self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
	self.sw.add(self.cfg.treeView)
	
	######################
	# fast messages and commands
	######################
	self.cfg.messageBox = gtk.ComboBoxEntry(self.cfg.messageList, column=0)
	#
    	self.fileButton = image_button(self.cfg.pixbuf_list_file_add_16, None, self.cfg.tooltips, _("Select the file"))
    	self.fileButton.connect("clicked", file_chooser_dialog, self.cfg.messageBox, _("Select the file"))

	ebox = gtk.EventBox()
	ebox.add(self.cfg.messageBox)
	if ( gtk.pygtk_version < (2, 12, 0) ):
	    self.cfg.tooltips.set_tip(ebox, _("The input field of the messages, commands and file selection"))
	else:
    	    self.cfg.messageBox.set_tooltip_text(_("The input field of the messages, commands and file selection"))

	self.hbox_entry = gtk.HBox(False, 0)
        self.hbox_entry.pack_start(ebox, expand=True, fill=True, padding=0)
        self.hbox_entry.pack_start(self.fileButton, expand=False, fill=False, padding=0)
	
	################
	# main toolbar
	################
	self.toolbarMain= gtk.Toolbar()
	self.toolbarMain.set_orientation(gtk.ORIENTATION_HORIZONTAL)
	self.toolbarMain.set_style(gtk.TOOLBAR_ICONS)
	self.toolbarMain.set_border_width(0)
	self.toolbarMain.set_tooltips(True)
	
	button = toolbar_button(self.cfg.pixbuf_action_refresh, self.cfg.tooltips, _("Refresh"))
	button.connect('clicked',self.callback, "refresh")
	self.toolbarMain.insert(button,-1)

	item = gtk.SeparatorToolItem()
	self.toolbarMain.insert(item,-1)

	button = toolbar_button(self.cfg.pixbuf_action_viewer, self.cfg.tooltips, _("Viewer"))
	button.connect('clicked',self.callback, "view")
    	if ( self.cfg.read_config("hide","hide_viewer") == "n" ):
	    self.toolbarMain.insert(button,-1)
	
	button = toolbar_button(self.cfg.pixbuf_action_control, self.cfg.tooltips, _("Control"))
	button.connect('clicked',self.callback, "control")
    	if ( self.cfg.read_config("hide","hide_control") == "n" ):
	    self.toolbarMain.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_action_thumbnails, self.cfg.tooltips, _("Thumbnails"))
	button.connect('clicked',self.callback, "thumbnails")
    	if ( self.cfg.read_config("hide","hide_thumbnails") == "n" ):
	    self.toolbarMain.insert(button,-1)

	item = gtk.SeparatorToolItem()
	self.toolbarMain.insert(item,-1)

	button = toolbar_button(self.cfg.pixbuf_action_vnc_servers, self.cfg.tooltips, _("Demo"))
	button.connect('clicked',self.callback, "demo")
    	if ( self.cfg.read_config("hide","hide_demo") == "n" ):
	    self.toolbarMain.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_action_timers, self.cfg.tooltips, _("Timers"))
	button.connect('clicked',self.callback, "timers")
    	if ( self.cfg.read_config("hide","hide_timer") == "n" ):
	    self.toolbarMain.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_action_user_info, self.cfg.tooltips, _("Client information"))
	button.connect('clicked',self.callback, "client_info")
    	if ( self.cfg.read_config("hide","hide_tree_add_remove") == "n" ):
	    self.toolbarMain.insert(button,-1)

	item = gtk.SeparatorToolItem()
	item.set_draw(False) 
	item.set_expand(gtk.EXPAND)
	self.toolbarMain.insert(item, -1)

	# toolbar menu util
	button = menu_tool_button(self.cfg.pixbuf_menu_util, self.cfg.tooltips)
    	if ( self.cfg.read_config("hide","hide_util") == "n" ):
	    self.toolbarMain.insert(button,-1)

	item = menu_image_button(self.cfg.pixbuf_home, _("Home folder"))
    	item.connect("activate", self.callback, "folder_user")
    	button.append(item)

	item = gtk.SeparatorMenuItem()
    	button.append(item)

    	item = menu_image_button(self.cfg.pixbuf_console, _("Console"))
	item.connect('activate', self.callback, "console_server")
    	button.append(item)
    	    
    	item = menu_image_button(self.cfg.pixbuf_console, _("Console(host)"))
	item.connect('activate', self.callback, "console_host")
    	button.append(item)
    	
    	item = menu_image_button(self.cfg.pixbuf_console_root, _("Console")+"(root)")
	item.connect('activate', self.callback, "console_root")
    	button.append(item)
    	
	item = menu_image_button(self.cfg.pixbuf_run_root, _("Run as root"))
	item.connect('activate', self.callback, "run_root")
    	button.append(item)

	item = gtk.SeparatorMenuItem()
    	button.append(item)

	item = menu_image_button(self.cfg.pixbuf_process, _("View process"))
	item.connect('activate', self.callback, "process")
    	button.append(item)

	item = menu_image_button(self.cfg.pixbuf_hwinfo, _("Hardware Info"))
	item.connect('activate', self.callback, "hwinfo")
    	button.append(item)

	item = gtk.SeparatorMenuItem()
    	button.append(item)

	item = menu_image_button(self.cfg.pixbuf_lock, _("Lock screen"))
	item.connect('activate', self.callback, "lock")
    	button.append(item)

	item = menu_image_button(self.cfg.pixbuf_unlock, _("Unlock screen"))
	item.connect('activate', self.callback, "unlock")
    	button.append(item)

	item = gtk.SeparatorMenuItem()
    	button.append(item)

	item = menu_image_button(self.cfg.pixbuf_block, _("Lock the input"))
	item.connect('activate', self.callback, "block")
    	button.append(item)

	item = menu_image_button(self.cfg.pixbuf_unblock, _("Unlock the input"))
	item.connect('activate', self.callback, "unblock")
    	button.append(item)

	# toolbar menu logout
	button = menu_tool_button(self.cfg.pixbuf_menu_system, self.cfg.tooltips)
    	if ( self.cfg.read_config("hide","hide_system_util") == "n" ):
	    self.toolbarMain.insert(button,-1)

	item = menu_image_button(self.cfg.pixbuf_logout, _("Logout"))
	item.connect('activate', self.callback, "logout")
    	button.append(item)

	item = menu_image_button(self.cfg.pixbuf_reboot, _("Reboot"))
	item.connect('activate', self.callback, "reboot")
    	button.append(item)

	item = menu_image_button(self.cfg.pixbuf_turn_on, _("Turn On"))
	item.connect('activate', self.callback, "wake_on_lan")
    	button.append(item)

	item = menu_image_button(self.cfg.pixbuf_shutdown, _("Shutdown"))
	item.connect('activate', self.callback, "shutdown")
    	button.append(item)
	
	##################
	# tree toolbar
	#################
	self.toolbarTree = gtk.Toolbar()
	self.toolbarTree.set_orientation(gtk.ORIENTATION_HORIZONTAL)
	self.toolbarTree.set_style(gtk.TOOLBAR_ICONS)
	self.toolbarTree.set_border_width(0)
	self.toolbarTree.set_tooltips(True)

	button = toolbar_button(self.cfg.pixbuf_list_hide1_16, self.cfg.tooltips, _("Show/Hide the list"))
	button.connect('clicked', self.view_list)
	self.toolbarTree.insert(button,-1)

	#item = gtk.SeparatorToolItem()
	#self.toolbarTree.insert(item,-1)
	
	# toolbar menu
    	if ( self.cfg.read_config("hide","hide_tree_add_remove") == "n" ):
	    button = menu_tool_button(self.cfg.pixbuf_list_add_16, self.cfg.tooltips, _("Add"))
	    button.show_all()
	    self.toolbarTree.insert(button,-1)

	    item = menu_image_button(self.cfg.pixbuf_list_add_16, _("Add standalone client"))
	    item.connect('activate', self.callback, "create_standalone")
    	    button.append(item)

	    item = menu_image_button(self.cfg.pixbuf_list_add_16, _("Add group"))
	    item.connect('activate', self.callback, "create_group")
    	    button.append(item)

	    item = menu_image_button(self.cfg.pixbuf_list_add_16, _("Add server"))
	    item.connect('activate', self.callback, "create_server")
    	    button.append(item)

	    button = toolbar_button(self.cfg.pixbuf_list_remove_16, self.cfg.tooltips, _("Remove"))
	    button.connect('clicked', self.callback, "remove_tree_item")
	    self.toolbarTree.insert(button,-1)

	    button = toolbar_button(self.cfg.pixbuf_list_edit_16, self.cfg.tooltips, _("Edit"))
	    button.connect('clicked', self.callback, "edit_tree_item")
	    self.toolbarTree.insert(button,-1)

	    button_up = image_button(self.cfg.pixbuf_list_arrow_up_16, None, self.cfg.tooltips, _("Move above"))
	    button_up.props.relief = gtk.RELIEF_NONE
	    button_up.set_size_request(24, 12)
    	    button_up.connect("clicked", tree_move, self.cfg, self.cfg.treeView, "up")
	    button_down = image_button(self.cfg.pixbuf_list_arrow_down_16, None, self.cfg.tooltips, _("Move below"))
	    button_down.props.relief = gtk.RELIEF_NONE
	    button_down.set_size_request(24, 12)
    	    button_down.connect("clicked", tree_move, self.cfg, self.cfg.treeView, "down")
	    vbox = gtk.VBox(False, 0)
	    vbox.pack_start(button_up, expand=True, fill=False, padding=0)
	    vbox.pack_start(button_down, expand=True, fill=False, padding=0)
	    item = gtk.ToolItem()
	    item.add(vbox)
	    self.toolbarTree.insert(item, -1)

	self.tree_info = gtk.Label()
	item = gtk.ToolItem()
	item.set_expand(gtk.EXPAND)
	item.add(self.tree_info)
	self.toolbarTree.insert(item, -1)

    	if ( self.cfg.read_config("hide","hide_message") == "n" ):
	    # menu
	    button = toolbar_button(self.cfg.pixbuf_action_send_message_16, self.cfg.tooltips, _("Send message"))
	    button.connect('clicked', self.callback, "send_message")
	    self.toolbarTree.insert(button,-1)

    	if ( self.cfg.read_config("hide","hide_command") == "n" ):
	    button = toolbar_button(self.cfg.pixbuf_action_run_16, self.cfg.tooltips, _("Run command"))
	    button.connect('clicked', self.callback, "run")
	    self.toolbarTree.insert(button,-1)

    	if ( self.cfg.read_config("hide","hide_send_file") == "n" ):
	    button = toolbar_button(self.cfg.pixbuf_list_file_send_16, self.cfg.tooltips, _("Send file"))
    	    button.connect("clicked", self.callback, "send_file")
	    self.toolbarTree.insert(button,-1)

	self.close_button_gtkvnc = toolbar_button(self.cfg.pixbuf_action_close_16, self.cfg.tooltips, _("Thumbnails")+" - "+_("Close all"))
	self.close_button_gtkvnc.connect('clicked',self.callback, "close_gtkvnc")
	self.toolbarTree.insert(self.close_button_gtkvnc,-1)

        ############################
        # paned tree
        ############################
	self.panedTree = gtk.HPaned()
	self.panedTree.add1(self.sw)

	self.swVnc = gtk.ScrolledWindow()
	self.swVnc.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
	self.panedTree.add2(self.swVnc)
	
	self.table_vnc = gtk.Fixed()
	self.table_vnc.set_border_width(10)
	ebox = gtk.EventBox()
	ebox.add(self.table_vnc)
	ebox.connect("motion-notify-event", self.table_vnc_motion_event)

	TARGETS = [ ('TEXT', 0, 0) ]
	self.table_vnc.drag_dest_set(gtk.DEST_DEFAULT_ALL, TARGETS, gtk.gdk.ACTION_DEFAULT)
	self.table_vnc.connect("drag_data_received", self.table_vnc_drag_data_received)
	self.table_vnc.connect('drag_motion', self.table_vnc_drag_data_motion)
	self.table_vnc.connect('drag_drop', self.table_vnc_drag_data_drop)
	
	self.swVnc.add_with_viewport(ebox)
	self.panedTree.set_position(self.cfg.window_x-self.cfg.phandle_size)
        self.panedTree.connect("notify::position", self.paned_tree_event)

	#
    	self.fileButton = image_button(self.cfg.pixbuf_list_file_add_16, None, self.cfg.tooltips, _("Select the file"))
    	self.fileButton.connect("clicked", file_chooser_dialog, self.cfg.messageBox, _("Select the file"))
	
	##########
	# menu
	##########
	self.menuBar = gtk.MenuBar()
        #                             
	self.menuFile = gtk.Menu()
	self.itemFile = gtk.MenuItem(_("File"))
	self.itemFile.set_submenu(self.menuFile)
        self.menuBar.append(self.itemFile)

	item = gtk.MenuItem(_("Quit"))
	item.connect("activate", self.program_exit)
        self.menuFile.append(item)

        #                                                     
	self.menuTools = gtk.Menu()
	self.itemTools = gtk.MenuItem(_("Tools"))
	self.itemTools.set_submenu(self.menuTools)
        self.menuBar.append(self.itemTools)

	item = menu_image_button(self.cfg.pixbuf_action_refresh_16, _("Refresh"))
	item.connect("activate", self.callback, "refresh")
	self.menuTools.append(item)
	
    	if ( self.cfg.read_config("hide","hide_viewer") == "n" ):
	    item = menu_image_button(self.cfg.pixbuf_action_viewer_16, _("Viewer"))
	    item.connect('activate', self.callback, "view")
	    self.menuTools.append(item)

    	if ( self.cfg.read_config("hide","hide_control") == "n" ):
	    item = menu_image_button(self.cfg.pixbuf_action_control_16, _("Control"))
	    item.connect('activate', self.callback, "control")
	    self.menuTools.append(item)

    	if ( self.cfg.read_config("hide","hide_thumbnails") == "n" ):
	    item = menu_image_button(self.cfg.pixbuf_action_thumbnails_16, _("Thumbnails"))
	    item.connect('activate', self.callback, "thumbnails")
	    self.menuTools.append(item)

    	if ( self.cfg.read_config("hide","hide_demo") == "n" ):
	    item = menu_image_button(self.cfg.pixbuf_status_direct_16, _("Demo"))
	    item.connect("activate", self.callback, "demo")
	    self.menuTools.append(item)
	
    	if ( self.cfg.read_config("hide","hide_timer") == "n" ):
	    item = menu_image_button(self.cfg.pixbuf_status_timer_16, _("Timers"))
	    item.connect("activate", self.callback, "timers")
	    self.menuTools.append(item)
	
    	if ( self.cfg.read_config("hide","hide_tree_add_remove") == "n" ):
	    item = menu_image_button(self.cfg.pixbuf_action_user_info_16, _("Client information"))
	    item.connect("activate", self.callback, "client_info")
	    self.menuTools.append(item)

    	item = gtk.SeparatorMenuItem() 
    	self.menuTools.append(item)

	item = menu_image_button(None, _("Log"))
	item.connect("activate", self.callback, "log")
	self.menuTools.append(item)

    	if ( self.cfg.read_config("hide","hide_setting") == "n" ):
	    item = menu_image_button(None, _("Settings"))
	    item.connect("activate", self.callback, "settings")
	    self.menuTools.append(item)

	#self.itemLanguage = gtk.MenuItem(_("Language"))
	#self.itemLanguage.connect("activate", self.createLanguageWindow)
    	#self.menuConfig.append(self.itemLanguage)
    
	#                                                             
	self.menuView = gtk.Menu()
	self.itemView = gtk.MenuItem(_("View"))
	self.itemView.set_submenu(self.menuView)
        self.menuBar.append(self.itemView)
	
	self.itemHideToolbarMain = gtk.CheckMenuItem(_("The upper toolbar"))
    	self.itemHideToolbarMain.set_active(True)
	self.itemHideToolbarMain.connect("activate", self.view_toolbar_main)
        self.menuView.append(self.itemHideToolbarMain)
                                                             
	self.itemHideToolbarTree = gtk.CheckMenuItem(_("The lower toolbar"))
    	self.itemHideToolbarTree.set_active(True)
	self.itemHideToolbarTree.connect("activate", self.view_toolbar_tree)
        self.menuView.append(self.itemHideToolbarTree)
                                                             
	self.itemHideMessageBox = gtk.CheckMenuItem(_("Input field")+"\t\t\t\t\tF9")
    	self.itemHideMessageBox.set_active(True)
	self.itemHideMessageBox.connect("activate", self.view_message_box)
        self.menuView.append(self.itemHideMessageBox)
                                                             
	self.itemHideStatus = gtk.CheckMenuItem(_("Log")+"\t\t\t\t\t\tF10")
    	self.itemHideStatus.set_active(True)
	self.itemHideStatus.connect("activate", self.view_status)
        self.menuView.append(self.itemHideStatus)
                                                             
    	item = gtk.SeparatorMenuItem() 
    	self.menuView.append(item)

	self.itemFullscreen = gtk.CheckMenuItem(_("Full screen")+"\t\t\t\t\tF11")
	self.itemFullscreen.connect("activate", self.view_fullscreen)
        self.menuView.append(self.itemFullscreen)

    	item = gtk.SeparatorMenuItem() 
    	self.menuView.append(item)
	
	self.itemHideList = gtk.CheckMenuItem(_("Show/Hide the list")+"\t\t\tF2")
    	self.itemHideList.set_active(True)
	self.itemHideList.connect("activate", self.view_list)
        self.menuView.append(self.itemHideList)

    	item = gtk.SeparatorMenuItem() 
    	self.menuView.append(item)

	self.itemVncMinimize = menu_image_button(self.cfg.pixbuf_action_window_min_16, _("Thumbnails")+" - "+_("Minimize all")+"\tF3")
	self.itemVncMinimize.connect("activate", self.view_vnc_minimize)
        self.menuView.append(self.itemVncMinimize)

	self.itemVncClose = menu_image_button(self.cfg.pixbuf_action_close_16, _("Thumbnails")+" - "+_("Close all")+"\t\t\tF4")
	self.itemVncClose.connect("activate", self.view_vnc_close)
        self.menuView.append(self.itemVncClose)


	#	
	self.menuHelp = gtk.Menu()
	self.itemHelp = gtk.MenuItem(_("Help"))
	self.itemHelp.set_submenu(self.menuHelp)
        self.menuBar.append(self.itemHelp)

	self.itemHelpProgram = gtk.MenuItem(_("Help")+"\t\tF1")
	self.itemHelpProgram.connect("activate", about_dialog)
        self.menuHelp.append(self.itemHelpProgram)
	
	self.itemAbout = gtk.MenuItem(_("About"))
	self.itemAbout.connect("activate", about_dialog)
        self.menuHelp.append(self.itemAbout)
	
        ###########
	# attach
	###########
        self.vboxMain.pack_start(self.menuBar, expand=False, fill=False, padding=0)
        self.vboxMain.pack_start(self.toolbarMain, expand=False, fill=False, padding=0)
    	self.vboxMain.pack_start(self.panedTree, expand=True, fill=True, padding=0)
    	if ( self.cfg.read_config("hide","hide_command") == "n" or self.cfg.read_config("hide","hide_tree_add_remove") == "n" ):
    	    self.vboxMain.pack_start(self.toolbarTree, expand=False, fill=False, padding=0)
    	if ( self.cfg.read_config("hide","hide_command") == "n" ):
    	    self.vboxMain.pack_start(self.hbox_entry, expand=False, fill=False, padding=0)
    	self.vboxMain.pack_start(self.viewportStatus, expand=False, fill=False, padding=0)

	# таймеры
	self.timers_start()
	self.window.show_all()
	self.close_button_gtkvnc.hide()

    	if ( self.cfg.read_config("hide","hide_toolbar_main") == "y" ):
    	    self.view_toolbar_main()
    	if ( self.cfg.read_config("hide","hide_toolbar_tree") == "y" ):
    	    self.view_toolbar_tree()
    	if ( self.cfg.read_config("hide","hide_message_box") == "y" ):
    	    self.view_message_box()
    	if ( self.cfg.read_config("hide","hide_status") == "y" ):
    	    self.view_status()

    def widget_view(self, data1=None):
	# toolbar main
	self.toolbar_main_height = 0
	if ( self.itemHideToolbarMain.get_active() ):
	    self.toolbar_main_height = self.toolbarMain.get_allocation().height
	
	# toolbar tree
	self.toolbar_tree_height = 0
	if ( self.itemHideToolbarTree.get_active() ):
	    self.toolbar_tree_height = self.toolbarTree.get_allocation().height
	
	# messsageBox
	self.message_box_height = 0
	if ( self.itemHideMessageBox.get_active() ):
	    self.message_box_height = self.hbox_entry.get_allocation().height
	
	# status
	self.status_height = 0
	if ( self.itemHideStatus.get_active() ):
	    self.status_height = self.viewportStatus.get_allocation().height
	
	# Высота всех виджетов, для определения размера миниатюр
	window_border = 5 + 2*self.cfg.tt_border
	height = window_border + self.menuBar.get_allocation().height + self.toolbar_main_height + \
	    self.toolbar_tree_height + self.message_box_height + self.status_height
	return height
	
    ##############################################
    
    def view_toolbar_main(self, widget=None):
	# 
	if ( widget ):
	    if ( widget.get_active() ):
		self.toolbarMain.show()
		res="n"
	    else:
		self.toolbarMain.hide()
		res="y"
    	    self.cfg.write_config("hide","hide_toolbar_main", res)
	else:
	    if ( self.itemHideToolbarMain.get_active() ):
		self.itemHideToolbarMain.set_active(False)
	    else:
		self.itemHideToolbarMain.set_active(True)
	    
    ##############################################
    
    def view_toolbar_tree(self, widget=None):
	# 
	if ( widget ):
	    if ( widget.get_active() ):
		self.toolbarTree.show()
		res="n"
	    else:
		self.toolbarTree.hide()
		res="y"
    	    self.cfg.write_config("hide","hide_toolbar_tree", res)
	else:
	    if ( self.itemHideToolbarTree.get_active() ):
		self.itemHideToolbarTree.set_active(False)
	    else:
		self.itemHideToolbarTree.set_active(True)
	    
    ##############################################
    
    def view_message_box(self, widget=None, state=None):
	# entry
	if ( state ):
	    if ( self.itemHideMessageBox.get_active() ):
		return True
	    else:
		return False
	if ( widget ):
	    if ( widget.get_active() ):
		self.hbox_entry.show()
		res="n"
	    else:
		self.hbox_entry.hide()
		res="y"
    	    self.cfg.write_config("hide","hide_message_box", res)
	else:
	    if ( self.itemHideMessageBox.get_active() ):
		self.itemHideMessageBox.set_active(False)
	    else:
		self.itemHideMessageBox.set_active(True)
	    
    ##############################################
    
    def view_status(self, widget=None):
	# log
	if ( widget ):
	    if ( widget.get_active() ):
		self.viewportStatus.show()
		res="n"
	    else:
		self.viewportStatus.hide()
		res="y"
    	    self.cfg.write_config("hide","hide_status", res)
	else:
	    if ( self.itemHideStatus.get_active() ):
		self.itemHideStatus.set_active(False)
	    else:
		self.itemHideStatus.set_active(True)

    ##############################################
    
    def view_vnc_close(self, widget=None):
	self.panedTree.set_position(self.cfg.panedWindow.get_position()-self.cfg.phandle_size)
	#self.close_gtkvnc()

    ##############################################
    
    def view_vnc_minimize(self, widget=None):
	if ( self.cfg.vnc_box != [] ):
    	    self.thumbnails_reorder("all_minimize")

    ##############################################
    
    def view_list(self, widget=None):
    	if ( type(widget) == gtk.ToolButton or not widget ):
    	    if ( self.itemHideList.get_active() ):
		self.itemHideList.set_active(False)
	    else:
		self.itemHideList.set_active(True)
	else:
	    if ( self.panedTree.get_position() == 0 ):
		if ( self.cfg.vnc_box == [] ):
		    self.panedTree.set_position(self.cfg.panedWindow.get_position()-self.cfg.phandle_size)
		else:
    	    	    self.panedTree.set_position(self.cfg.treeX)
    	    else:
    		self.panedTree.set_position(0)

    ##############################################
    
    def view_fullscreen(self, widget=None):
	# full screen
	if ( widget ):
	    if ( widget.get_active() ):
		self.window.fullscreen()
	    else:
		self.window.unfullscreen()
	else:
	    if ( self.itemFullscreen.get_active() ):
		self.itemFullscreen.set_active(False)
	    else:
		self.itemFullscreen.set_active(True)
	    
    ##############################################

    def timers_start(self):
	self.cfg.timers = timers(self.cfg)
	# Формирование userList
	self.cfg.timers.timer_userList("start")
	#
        create_timersList(self.cfg)
        create_demoList(self.cfg)
	# 
	self.cfg.demoUi = demoUi(self.cfg)
	self.timersUi = timersUi(self.cfg)
	#
	gobject.timeout_add(3000, self.cfg.timers.start)

    ##############################################

    def rename_group(self, cell, path, new_text):
	cell.set_property('editable', False)
	self.cfg.treeView.get_selection().select_path(path)
	model, rows = self.cfg.treeView.get_selection().get_selected_rows()
	if ( new_text == model[rows[0]][0] ):
    	    return False
	self.cfg.userList[path][0] = new_text
	# Поменять группу у клиентов
	parent_iter = self.cfg.userList.get_iter(rows[0])
    	for client in range(self.cfg.userList.iter_n_children(parent_iter)):
	    path = (rows[0][0],client)
	    self.cfg.userList[path][self.cfg.dn['group']] = new_text
	save_userList(self.cfg)
    
    ##############################################

    def table_vnc_drag_data_drop(self, widget, drag_context, x, y, time):
	pass

    def table_vnc_drag_data_motion(self, widget, drag_context, x, y, time):
	if ( drag_context.get_source_widget() == self.cfg.treeView ):
	    drag_context.drag_status(gtk.gdk.ACTION_LINK, time)
	elif ( type(drag_context.get_source_widget()) == gtk.Toolbar ):
	    # При наведении на миниатюру
	    p_target = None
	    for p in self.cfg.vnc_box:
		alloc = p[2].get_allocation()
		if ( alloc.x < x < alloc.x+alloc.width+self.cfg.tt_border and alloc.y < y < alloc.y+alloc.height ):
		    p_target = p[2]
		    break
	    if ( p_target ):
		drag_context.drag_status(gtk.gdk.ACTION_MOVE, time)
		self.thumbnails_motion_event(widget=p_target)
	    else:
		drag_context.drag_status(gtk.gdk.ACTION_PRIVATE, time)
		return True
	else:
	    drag_context.drag_status(gtk.gdk.ACTION_PRIVATE, time)
	    return True

    def table_vnc_drag_data_received(self, widget, drag_context, x, y, selection, target_type, time):
	if ( drag_context.get_source_widget() == self.cfg.treeView ):
	    self.callback(None, "thumbnails")
	elif ( type(drag_context.get_source_widget()) == gtk.Toolbar ):
	    client_id = selection.data
	    p_source = None
	    p_source_index = None
	    p_target_index = None
	    for p in self.cfg.vnc_box:
		if ( p[0] == client_id ):
		    p_source = p
		    p_source_index = self.cfg.vnc_box.index(p_source)
		    break
	    # При наведении на миниатюру
	    for p in self.cfg.vnc_box:
		alloc = p[2].get_allocation()
		if ( alloc.x < x < alloc.x+alloc.width+self.cfg.tt_border and alloc.y < y < alloc.y+alloc.height ):
		    p_target_index = self.cfg.vnc_box.index(p)
		    break
	    if ( p_source and p_target_index != None and p_target_index != p_source_index ):
		self.cfg.vnc_box.remove(p_source)
		self.cfg.vnc_box.insert(p_target_index, p_source)
		self.thumbnails_reorder("all")

    ##############################################
    
############################################################################################################################
if __name__ == "__main__":
    gobject.threads_init()
    gtk.gdk.threads_init()
    base = Program()
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()

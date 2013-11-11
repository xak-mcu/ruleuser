#! /usr/bin/env python
# -*- coding: utf8 -*-

###################################################################################################
# RuleUser
# window2.py
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

import gtk, os, string, gettext, time, gobject, pango
_ = gettext.gettext

from util import *
from vnc import *
from tree import create_columns
from tree import find_tree
from tree import save_userList
from tree import save_demoList
from tree import save_timersList
from tree import save_aliasList
from tree import create_timersList
from widget import *
from threads import thread_gfunc

####################################################################################################

def create_window2(cfg):
    umount_point(cfg)
    if ( cfg.table2.get_children() == [] ): 
        cfg.mainWindowLastX = cfg.window_x
        if ( cfg.maximized == True or cfg.fullscreen == True ):
    	    gobject.timeout_add(50, paned_set_position, cfg, cfg.window_x-cfg.panedWindowX-cfg.phandle_size)
        elif ( cfg.screen_x < cfg.window_x+cfg.panedWindowX ):
    	    cfg.window.move(0, 0)
    	    cfg.window.resize(cfg.screen_x, cfg.window_y)
    	else:
	    cfg.window.resize(cfg.window_x+cfg.panedWindowX, cfg.window_y)
	gobject.timeout_add(100, window_size_request, cfg)
    else:
        # очистка таблицы
        for x in cfg.table2.get_children():
    	    cfg.table2.remove(x)

def close_window2(data, cfg):
    if ( cfg.cursor_wait_status ):
	return
    umount_point(cfg)
    # очистка таблицы
    for x in cfg.table2.get_children():
        cfg.table2.remove(x)
    if ( cfg.maximized == True or cfg.fullscreen == True ):
	cfg.panedWindow.set_position(cfg.window_x-cfg.phandle_size)
    else:
	cfg.window.set_size_request(cfg.min_mainWindowX, cfg.min_mainWindowY)
	gobject.timeout_add(50, paned_set_position, cfg, cfg.window_x-cfg.phandle_size)
	if ( cfg.mainWindowLastX < cfg.window_x - cfg.panedWindowX ):
	    cfg.window.resize(cfg.window_x-cfg.panedWindowX, cfg.window_y)
	else:
	    # -1 для открытого VNC после создания window2, чтобы закрыть ползунок
	    cfg.window.resize(cfg.mainWindowLastX-1, cfg.window_y)

def window_size_request(cfg):
    cfg.window.set_size_request(cfg.min_mainWindowX+cfg.panedWindowX, cfg.min_mainWindowY)
    return False

def paned_set_position(cfg, pos):
    if ( cfg.table2.get_children() != [] ): 
	cfg.panedWindow.set_position(pos)
	return False
    if ( cfg.panedWindow.get_position() == cfg.window_x-cfg.phandle_size ):
	return False
    return True

####################################################################################################

def umount_point(cfg):
    if ( cfg.mount_point != None ):
	try:
	    ismount = os.path.ismount(cfg.mount_point)
	except:
	    return
	if ( ismount ):    
	    cmd = "fusermount -uz "+cfg.mount_point
	    proc = popen_sub(cfg, shlex.split(cmd))
	    cfg.mount_point = None

####################################################################################################

class folderUi:
    def __init__(self, cfg, user_list):
	
	user_list = check_user_list(cfg, user_list, "command")
	if ( user_list == [] ):
	    return
	d = {}
	for key, value in zip(cfg.z, user_list[0]):
	    d[key] = value

	create_window2(cfg)

	cfg.mount_point = os.path.expanduser("~/.ruleuser/sshfs/")
	if (not os.path.exists(cfg.mount_point)):
	    os.makedirs(cfg.mount_point)
	else:
	    umount_point(cfg)
	    cfg.mount_point = os.path.expanduser("~/.ruleuser/sshfs/")
	
    	cmd = cfg.sshfs+" -o IdentityFile="+d['server_key']+" "+" -p "+d['server_port']+" "+\
    	    d['user']+"@"+d['server']+": "+cfg.mount_point
	proc = popen_sub(cfg, shlex.split(cmd))
	if ( proc == False ):
	    close_window2(None, cfg)
    	    return

	folder_name = d['user']+"@"+d['server']+":~/"
	vbox = file_browser(cfg, cfg.mount_point, folder_name)

	# button
        closeButton = image_button(cfg.pixbuf_action_close_16, _("Close"))
	closeButton.connect("clicked", close_window2, cfg)
	closeButton.set_size_request(120, 26)

	frame = gtk.Frame()
	frame2 = gtk.Frame()
        cfg.table2.attach(frame, 0, 28, 0, 39)
        cfg.table2.attach(frame2, 0, 28, 39, 42)
	cfg.table2.attach(vbox, 1, 27, 1, 39)
        cfg.table2.attach(closeButton, 21, 27, 40, 42, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

	cfg.table2.show_all()
	
####################################################################################################

class timersUi:
    def __init__(self, cfg):
	
	self.cfg = cfg
	self.treeView = self.cfg.treeView
	self.timers = self.cfg.timers
    
    def createUi(self, data=None):
	
	create_window2(self.cfg)

	self.treeTimer = gtk.TreeView(self.cfg.timersList)
	self.treeTimer.set_rules_hint(True)
	self.treeTimer.set_enable_tree_lines(True)
	self.treeTimer.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_VERTICAL)
	self.treeTimer.connect("button-press-event", self.tree_event)
	TARGETS = [('TREE_TIMER', gtk.TARGET_SAME_WIDGET, 0), ('TEXT', 0, 0),]
	#self.treeTimer.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, TARGETS, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_MOVE)
	self.treeTimer.enable_model_drag_dest(TARGETS, gtk.gdk.ACTION_DEFAULT)
	self.treeTimer.connect("drag_data_received", self.tree_timer_drag_data_received)
	self.treeTimer.connect('drag_motion', self.tree_timer_drag_data_motion)

	cell = gtk.CellRendererText()
	column = gtk.TreeViewColumn(_("№"), cell, text=0)
    	column.set_expand(True)
	self.treeTimer.append_column(column)
	
    	cell = gtk.CellRendererPixbuf()
	column = gtk.TreeViewColumn(_("Status"), cell, pixbuf=4)
	column.set_expand(False)
	self.treeTimer.append_column(column)

	cell = gtk.CellRendererText()
	column = gtk.TreeViewColumn(_("Action"), cell, text=1)
    	column.set_expand(True)
	self.treeTimer.append_column(column)

	cell = gtk.CellRendererText()
	column = gtk.TreeViewColumn(_("Time"), cell, text=2)
    	column.set_expand(True)
	self.treeTimer.append_column(column)

	cell = gtk.CellRendererText()
	column = gtk.TreeViewColumn(_("Message")+" / "+_("Command"), cell, text=3)
    	column.set_expand(True)
	self.treeTimer.append_column(column)


	self.treeTimerSelection = self.treeTimer.get_selection()
	self.treeTimerSelection.set_mode(gtk.SELECTION_MULTIPLE)

	swTimer = gtk.ScrolledWindow()
	swTimer.set_shadow_type(gtk.SHADOW_ETCHED_IN)
	swTimer.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
	swTimer.add(self.treeTimer)
	
	#######
	# Ui
	#######
	frame = gtk.Frame()

	self.cbAction = gtk.combo_box_new_text()
    	self.cbAction.append_text(_("Logout"))
    	self.cbAction.append_text(_("Reboot"))
    	self.cbAction.append_text(_("Turn On"))
    	self.cbAction.append_text(_("Shutdown"))
    	self.cbAction.append_text(_("Run command"))
    	self.cbAction.append_text(_("Send message"))
    	self.cbAction.set_active(0)
    	
    	# time
    	adj = gtk.Adjustment(0.0, 0.0, 23.0, 1.0, 5.0, 0.0)
    	self.sbHour = gtk.SpinButton(adj, 0, 0)
    	self.sbHour.set_wrap(True)
    	labelHour = gtk.Label(_("Hour"))
    	labelHour.set_alignment(0, 0.5)
	
    	adj = gtk.Adjustment(0.0, 0.0, 59.0, 1.0, 5.0, 0.0)
    	self.sbMin = gtk.SpinButton(adj, 0, 0)
    	self.sbMin.set_wrap(True)
    	labelMin = gtk.Label(_("Minute"))
    	labelMin.set_alignment(0, 0.5)

    	adj = gtk.Adjustment(0.0, 0.0, 59.0, 1.0, 5.0, 0.0)
    	self.sbSec = gtk.SpinButton(adj, 0, 0)
    	self.sbSec.set_wrap(True)
    	labelSec = gtk.Label(_("Second"))
    	labelSec.set_alignment(0, 0.5)
	
	# combobox
	textBox = gtk.ListStore(str)
	self.entryBox = gtk.ComboBoxEntry(textBox, column=0)
	textBox.append([""])
	for i in range(20):
	    if ( self.cfg.read_config("command","f"+str(i+1)) != "" ):
		textBox.append([self.cfg.read_config("command","f"+str(i+1))])
	
	# filechooser
	
        fileChooserButton = image_button(self.cfg.pixbuf_list_file_add_16, None, self.cfg.tooltips, _("Select the file"))
        fileChooserButton.set_size_request(25, 25)
        fileChooserButton.connect("clicked", file_chooser_dialog, self.entryBox, _("Select the file"))

	# toolbar
	toolbar = gtk.Toolbar()
	toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
	toolbar.set_style(gtk.TOOLBAR_ICONS)
	toolbar.set_border_width(0)
	toolbar.set_tooltips(True)
	
	button = toolbar_button(self.cfg.pixbuf_list_transfer_16, self.cfg.tooltips, _("Add"))
	button.connect('clicked',  self.add_client)
	toolbar.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_list_remove_16, self.cfg.tooltips, _("Remove"))
	button.connect('clicked',  self.remove_client)
	toolbar.insert(button,-1)

	space = gtk.SeparatorToolItem()
	space.set_draw(False) 
	space.set_expand(gtk.EXPAND)
	toolbar.insert(space,-1)
	
	button = toolbar_button(self.cfg.pixbuf_list_play_16, self.cfg.tooltips, _("Start"))
	button.connect('clicked',  self.timer_start)
	toolbar.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_list_stop_16, self.cfg.tooltips, _("Stop"))
	button.connect('clicked',  self.timer_stop)
	toolbar.insert(button,-1)

	space = gtk.SeparatorToolItem()
	toolbar.insert(space,-1)
	
	button = toolbar_button(self.cfg.pixbuf_list_save_16, self.cfg.tooltips, _("Save"))
	button.connect('clicked',  self.save_timer, "save")
	toolbar.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_list_add_16, self.cfg.tooltips, _("New"))
	button.connect('clicked',  self.save_timer, "create")
	toolbar.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_list_remove_16, self.cfg.tooltips, _("Remove"))
	button.connect('clicked',  self.remove_timer)
	toolbar.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_list_edit_16, self.cfg.tooltips, _("Edit"))
	button.connect('clicked',  self.edit_timer)
	toolbar.insert(button,-1)


        # button
        closeButton = image_button(self.cfg.pixbuf_action_close_16, _("Close"))
	closeButton.connect("clicked", close_window2, self.cfg)
	closeButton.set_size_request(120, 26)

	#
	frame = gtk.Frame()
	frame2 = gtk.Frame()
        self.cfg.table2.attach(swTimer, 0, 28, 0, 30)
        self.cfg.table2.attach(toolbar, 0, 28, 30, 32, yoptions=gtk.SHRINK)
	#
        self.cfg.table2.attach(frame, 0, 28, 32, 39)
        self.cfg.table2.attach(labelHour, 15, 18, 33, 34, yoptions=gtk.SHRINK)
        self.cfg.table2.attach(self.sbHour, 15, 18, 34, 36, yoptions=gtk.SHRINK)
        self.cfg.table2.attach(labelMin, 19, 22, 33, 34, yoptions=gtk.SHRINK)
        self.cfg.table2.attach(self.sbMin, 19, 22, 34, 36, yoptions=gtk.SHRINK)
        self.cfg.table2.attach(labelSec, 23, 27, 33, 34, yoptions=gtk.SHRINK)
        self.cfg.table2.attach(self.sbSec, 23, 26, 34, 36, yoptions=gtk.SHRINK)

        self.cfg.table2.attach(self.cbAction, 1, 14, 34, 36, yoptions=gtk.SHRINK)

        self.cfg.table2.attach(self.entryBox, 1, 24, 36, 38, yoptions=gtk.SHRINK)
        self.cfg.table2.attach(fileChooserButton, 24, 26, 36, 38, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
	#
        self.cfg.table2.attach(frame2, 0, 28, 39, 42)
        self.cfg.table2.attach(closeButton, 21, 27, 40, 42, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

	self.treeTimer.expand_all()
	self.cfg.table2.show_all()
	
    def remove_timer(self, data=None):
        model, rows = self.treeTimerSelection.get_selected_rows()
        if ( rows == [] ):
    	    return
        self.timer_stop()
        tree_iters = []
        for row in rows:
	    if ( len(row) == 1 ):
    	        tree_iters.append(model.get_iter(row))
	for iter in tree_iters:
    	    if ( iter != None ):
		model.remove(iter)
    	save_timersList(self.cfg)

    def remove_client(self, data=None):
	model, rows = self.treeTimerSelection.get_selected_rows()
	tree_iters = []
	for row in rows:
	    if ( len(row) == 1 ):
		continue
    	    tree_iters.append(model.get_iter(row))
    	    timer_path = (row[0],)
    	    # удаление из списка пользователей
    	    user_list = model[timer_path][5]
    	    for x in range(len(user_list)):
    		if ( user_list[x][0] == model[row][1] ):
    		    # Убрать иконки
		    userList_column_value(self.cfg, 54, None, [user_list[x]], False)
    		    del user_list[x]
    		    break
    	    model[timer_path][5] = user_list
    	# удаление
	for iter in tree_iters:
    	    if ( iter != None ):
		model.remove(iter)
    	save_timersList(self.cfg)
    
    def add_client(self, data=None, timer_path=None, user_list=None):
	# drag
	if ( timer_path and user_list ):
	    if ( user_list == [] ):
		return
	    model = self.cfg.timersList
	else:
    	    user_list = get_selected_tree(self.cfg, self.treeView)
	    if ( user_list == [] ):
		return
    	    model, rows = self.treeTimerSelection.get_selected_rows()
    	    if ( rows == [] ):
    		return
	    timer_path = (rows[0][0],)

	timer_iter = model.get_iter(timer_path)
        for z in user_list:
    	    # поиск пользователя, только в этом таймере
    	    for user in model[timer_path][5]:
    		if ( z[0] == user[0] ):
    	    	    return
	    model[timer_path][5].append(z)
    	    model.append(timer_iter, ["",z[0],"","",None,"",0])
    	self.treeTimer.expand_to_path(timer_path)
    	save_timersList(self.cfg)

    def edit_timer(self, data=None):
	self.clear_timer()
    	model, rows = self.treeTimerSelection.get_selected_rows()
    	if ( rows == [] or len(rows[0]) != 1 ):
    	    return
    	number = model[rows[0]][0]
    	action = model[rows[0]][1]
    	time = model[rows[0]][2]
    	command = model[rows[0]][3]

    	(hour,minute,second) = string.split(time, ":")
	if ( action != _("Turn On") and action != _("Logout") and action != _("Reboot") and action != _("Shutdown") ):
    	    self.entryBox.remove_text(0)
	    self.entryBox.insert_text(0,command)
	    self.entryBox.set_active(0)
	    
	model = self.cbAction.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == action ):
		self.cbAction.set_active(item)
		break
	self.sbHour.set_value(int(hour))
    	self.sbMin.set_value(int(minute))
    	self.sbSec.set_value(int(second))
    	self.treeTimer.expand_to_path(rows[0])

    def clear_timer(self, data=None):
        self.sbHour.set_value(0)
        self.sbMin.set_value(0)
        self.sbSec.set_value(0)
        self.entryBox.remove_text(0)
	self.entryBox.insert_text(0,"")
	self.entryBox.set_active(0)
    	self.cbAction.set_active(0)
	
    def save_timer(self, data, mode):
    	model, rows = self.treeTimerSelection.get_selected_rows()
	number = str(len(self.cfg.timersList)+1)
	action = self.cbAction.get_active_text()
	hour = str(int(self.sbHour.get_value()))
	if ( len(hour) == 1 ): hour = "0"+hour
	minute = str(int(self.sbMin.get_value()))
	if ( len(minute) == 1 ): minute = "0"+minute
	second = str(int(self.sbSec.get_value()))
	if ( len(second) == 1 ): second = "0"+second
	start = hour+":"+minute+":"+second
	
	if ( action == _("Logout") or action == _("Reboot") or action == _("Shutdown") ):
	    command = ""
	elif ( action == _("Turn On") ):
	    command = ""
	else:
	    command = self.entryBox.get_active_text()
	    if ( command == "" ):
		return

    	if ( mode == "save" ):
    	    if ( rows == [] or len(rows[0]) != 1 ):
    		return
	    timer_iter = model.get_iter(rows[0])
    	elif ( mode == "create" ):
    	    timer_iter = model.append(None)
    	    model.set(timer_iter, 0, str(number))
    	    model.set(timer_iter, 5, [])

    	model.set(timer_iter, 1, str(action))
    	model.set(timer_iter, 2, str(start))
    	model.set(timer_iter, 3, str(command))
    	if ( mode == "save" ):
    	    if ( model[rows[0]][6] != 0 ):
    		self.timer_stop()
    		self.timer_start()
    	self.clear_timer()
    	save_timersList(self.cfg)
    
    def tree_event(self, treeView, event, data=None):
	mouse_pos = treeView.get_path_at_pos(int(event.x),int(event.y))
	# Снять выделение
	if ( not mouse_pos ):
	    treeView.get_selection().unselect_all()
	    return
	# Действия
        if event.type == gtk.gdk._2BUTTON_PRESS:
	    self.edit_timer()

    def tree_timer_drag_data_motion(self, widget, drag_context, x, y, time):
	if ( drag_context.get_source_widget() == self.cfg.treeView ):
	    drag_context.drag_status(gtk.gdk.ACTION_LINK, time)
	else:
	    drag_context.drag_status(gtk.gdk.ACTION_PRIVATE, time)
	    return True
	drop_info = widget.get_dest_row_at_pos(x, y)
	if ( drop_info ):
	    dest_path, dest_pos = drop_info
	    if ( len(dest_path) == 2 ):
		if ( dest_pos == gtk.TREE_VIEW_DROP_BEFORE or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE ):
		    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_BEFORE)
		elif ( dest_pos == gtk.TREE_VIEW_DROP_AFTER or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER ):
		    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_AFTER)
	    else:
		if ( dest_pos == gtk.TREE_VIEW_DROP_BEFORE ):
	    	    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_BEFORE)
		elif ( dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE ):
	    	    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_INTO_OR_BEFORE)
		elif ( dest_pos == gtk.TREE_VIEW_DROP_AFTER and widget.row_expanded(dest_path) ):
	    	    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_INTO_OR_AFTER)
		elif ( dest_pos == gtk.TREE_VIEW_DROP_AFTER ):
	    	    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_AFTER)
		elif ( dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER ):
	    	    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_INTO_OR_AFTER)
	else:
	    widget.set_drag_dest_row((len(widget.get_model())-1,), gtk.TREE_VIEW_DROP_AFTER)
	return True

    def tree_timer_drag_data_received(self, treeview, context, x, y, selection, info, etime):
	# перетаскивание из основного дерева
        if ( not selection.data ):
    	    return
        data = selection.data.splitlines()
	user_list = []
	for z in data:
	    user_list.append(z.split(","))
        drop_info = treeview.get_dest_row_at_pos(x, y)
    	if ( drop_info ):
	    dest_path, dest_pos = drop_info
	    if ( len(dest_path) == 2 ):
		dest_path = (dest_path[0],)
	    self.add_client(None, dest_path, user_list)

    def timer_start(self, data=None, num=None):
    	if ( num ):
	    self.timers.timer_user("start", int(num)-1)
	else:
    	    model, rows = self.treeTimerSelection.get_selected_rows()
    	    if ( rows == [] ):
    		return
    	    for row in rows:
    		if (len(row) != 1 or model[row][5] == [] or model[row][5] == None ):
    		    continue
		self.timers.timer_user("start", row[0])

    def timer_stop(self, data=None, num=None):
    	if ( num ):
	    self.timers.timer_user("stop", int(num)-1)
	else:
    	    model, rows = self.treeTimerSelection.get_selected_rows()
    	    if ( rows == [] ):
    		return
    	    for row in rows:
    		if (len(row) != 1):
    		    continue
		self.timers.timer_user("stop", row[0])

    def timer_start_all(self, data=None):
	self.timers.timer_user("start")

    def timer_stop_all(self, data=None):
	self.timers.timer_user("stop")

####################################################################################################

class demoUi:
    def __init__(self, cfg):
	
	self.cfg = cfg
	self.treeView = self.cfg.treeView

	# toolbar, создать здесь, т.к. в timers запрос
	self.toolbarTree = gtk.Toolbar()

    def createUi(self, data=None):
	
	create_window2(self.cfg)

	# toolbar
	self.toolbarTree = gtk.Toolbar()
	self.toolbarTree.set_orientation(gtk.ORIENTATION_HORIZONTAL)
	self.toolbarTree.set_style(gtk.TOOLBAR_ICONS)
	self.toolbarTree.set_border_width(0)
	self.toolbarTree.set_tooltips(True)

	self.treeDemo = gtk.TreeView(self.cfg.demoList)
	self.treeDemo.set_rules_hint(True)
	self.treeDemo.set_enable_tree_lines(True)
	self.treeDemo.set_headers_visible(True)
	self.treeDemo.set_headers_clickable(True)
	#self.treeDemo.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_VERTICAL)
	#self.treeDemo.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
	self.treeDemo.modify_font(pango.FontDescription(self.cfg.fontTree))
	self.treeDemo.connect("button-press-event", self.tree_button_press)

	TARGETS = [('TREE_DEMO', gtk.TARGET_SAME_WIDGET, 0), ('TEXT', 0, 0)]
	self.treeDemo.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, TARGETS, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_MOVE)
	self.treeDemo.enable_model_drag_dest(TARGETS, gtk.gdk.ACTION_DEFAULT)
	#self.treeDemo.drag_dest_set(gtk.DEST_DEFAULT_ALL, TARGETS, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_MOVE)
	self.treeDemo.connect("drag_data_received", self.tree_demo_drag_data_received)
	self.treeDemo.connect("drag_motion", self.tree_demo_drag_data_motion)
	
	self.treeDemoSelection = self.treeDemo.get_selection()
	self.treeDemoSelection.set_mode(gtk.SELECTION_MULTIPLE)

	for i in range(len(self.cfg.z)):
	    if ( i == self.cfg.dn['demo_pixbuf'] ):
		column = gtk.TreeViewColumn(_("Status"))
		column.set_expand(False)
		column.set_spacing(3)
    		for y in range(3):
    		    cell = gtk.CellRendererPixbuf()
		    column.pack_start(cell, expand=False)
    		    column.set_attributes(cell, pixbuf=int(100)+y)
	    else:
		cell = gtk.CellRendererText()
		if ( i == self.cfg.dn['alias'] ):
		    column = gtk.TreeViewColumn(_("Alias"), cell, text=i)
		    column.set_expand(True)
		elif ( i == self.cfg.dn['demo_address'] ):
		    column = gtk.TreeViewColumn(_("Address"), cell, text=i)
		    column.set_expand(True)
		else:
    		    column = gtk.TreeViewColumn("", cell, text=i)
		    column.set_expand(False)
	    self.treeDemo.append_column(column)

        for i in range(len(self.cfg.z)):
    	    column = self.treeDemo.get_column(i)
    	    if ( i in [self.cfg.dn['alias'],self.cfg.dn['demo_address'],self.cfg.dn['demo_pixbuf']]):
	    	column.set_visible(True)
	    else:
	    	column.set_visible(False)

	swDemo = gtk.ScrolledWindow()
	swDemo.set_shadow_type(gtk.SHADOW_ETCHED_IN)
	swDemo.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
	swDemo.add(self.treeDemo)

	# toolbar menu
	for x in self.toolbarTree.get_children():
	    self.toolbarTree.remove(x)
	    
	button = menu_tool_button(self.cfg.pixbuf_list_transfer_16, self.cfg.tooltips, _("Add"))
	self.toolbarTree.insert(button,-1)

	item = menu_image_button(self.cfg.pixbuf_list_transfer_16, _("Add server"))
	item.connect('activate',  self.callback, "add_server")
	button.append(item)

	item = menu_image_button(self.cfg.pixbuf_list_transfer_16, _("Add clients"))
	item.connect('activate',  self.callback, "add_client")
	button.append(item)

	button = toolbar_button(self.cfg.pixbuf_list_remove_16, self.cfg.tooltips, _("Remove"))
	button.connect('clicked',  self.callback, "remove")
	self.toolbarTree.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_list_edit_16, self.cfg.tooltips, _("Edit"))
	button.connect('clicked', self.callback, "edit_tree_item")
	self.toolbarTree.insert(button,-1)

	button_up = image_button(self.cfg.pixbuf_list_arrow_up_16, None, self.cfg.tooltips, _("Move above"))
	button_up.props.relief = gtk.RELIEF_NONE
	button_up.set_size_request(24, 12)
    	button_up.connect("clicked", tree_move, self.cfg, self.treeDemo, "up")
	button_down = image_button(self.cfg.pixbuf_list_arrow_down_16, None, self.cfg.tooltips, _("Move below"))
	button_down.props.relief = gtk.RELIEF_NONE
	button_down.set_size_request(24, 12)
    	button_down.connect("clicked", tree_move, self.cfg, self.treeDemo, "down")
	vbox = gtk.VBox(False, 0)
	vbox.pack_start(button_up, expand=True, fill=False, padding=0)
	vbox.pack_start(button_down, expand=True, fill=False, padding=0)
	item = gtk.ToolItem()
	item.add(vbox)
	self.toolbarTree.insert(item, -1)

	space = gtk.SeparatorToolItem()
	space.set_draw(False) 
	space.set_expand(gtk.EXPAND)
	self.toolbarTree.insert(space,-1)

	button = toolbar_button(self.cfg.pixbuf_list_play_fullscreen_16, self.cfg.tooltips, _("Start")+" ("+_("in full screen")+")")
	button.connect('clicked',  self.callback, "start_fullscreen")
	self.toolbarTree.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_list_play_window_16, self.cfg.tooltips, _("Start")+" ("+_("in window")+")")
	button.connect('clicked',  self.callback, "start_window")
	self.toolbarTree.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_list_play_file_16, self.cfg.tooltips, _("Start")+" ("+_("file or stream, only for VLC")+")")
	button.connect('clicked',  self.callback, "start_file")
	self.toolbarTree.insert(button,-1)

	button = toolbar_button(self.cfg.pixbuf_list_stop_16, self.cfg.tooltips, _("Stop"))
	button.connect('clicked',  self.callback, "stop")
	self.toolbarTree.insert(button,-1)
	
	# file
	demoEntryList = gtk.ListStore(str)
    	for i in range(20):
    	    text = self.cfg.read_config("command","f"+str(i+1))
    	    if ( text != "" ):
    		demoEntryList.append([text])

	self.cfg.demoEntryBox = gtk.ComboBoxEntry(demoEntryList, column=0)
    	fileButton = image_button(self.cfg.pixbuf_list_file_add_16, None, self.cfg.tooltips, _("Select the file"))
    	fileButton.connect("clicked", file_chooser_dialog, self.cfg.demoEntryBox, _("Select the file"))

	hbox2 = gtk.HBox()
        hbox2.pack_start(self.cfg.demoEntryBox, expand=True, fill=True, padding=0)
        hbox2.pack_start(fileButton, expand=False, fill=False, padding=0)

        # button
        closeButton = image_button(self.cfg.pixbuf_action_close_16, _("Close"))
	closeButton.connect("clicked", close_window2, self.cfg)
	closeButton.set_size_request(120, 26)
	
	##########
	# attach
	##########
        self.cfg.table2.attach(swDemo, 0, 28, 0, 35)

	vbox = gtk.VBox(False, 0)
	vbox.pack_start(self.toolbarTree, expand=False, fill=False, padding=0)
	vbox.pack_start(hbox2, expand=False, fill=False, padding=0)
	self.cfg.table2.attach(vbox, 0, 28, 35, 39, yoptions=gtk.FILL)
	
        frame = gtk.Frame()
        self.cfg.table2.attach(frame, 0, 28, 35, 42)
        self.cfg.table2.attach(closeButton, 21, 27, 40, 42, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

	self.treeDemo.expand_all()
	self.cfg.table2.show_all()

    def add(self, mode=None, user_list=None, drop_info=None):
	model = self.cfg.demoList
	temp_select_iter = []
	# Перетаскивание
	if ( not mode and user_list ):

	    if ( drop_info ):
		dest_path, dest_pos = drop_info
		dest_iter = model.get_iter(dest_path)
	    else:
		dest_path = None
		dest_iter = None
		
	    if ( user_list == [] ):
		return
    	    for z in user_list:
    	    
		# Переместить группу в конец списка если нет назначения
    		if ( not dest_path ):
    		    new_iter = model.append(None)
    		else:
    		    if ( len(dest_path) == 1 ):
    			if ( dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER ):
			    new_iter = model.append(dest_iter)
			elif ( dest_pos == gtk.TREE_VIEW_DROP_BEFORE ):
    			    new_iter = model.insert_before(None, dest_iter, None)
			elif ( dest_pos == gtk.TREE_VIEW_DROP_AFTER ):
    			    new_iter = model.insert_after(None, dest_iter, None)
		    else:
    			if ( dest_pos == gtk.TREE_VIEW_DROP_BEFORE or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE ):
    			    new_iter = model.insert_before(None, dest_iter, None)
    			elif ( dest_pos == gtk.TREE_VIEW_DROP_AFTER or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER ):
    			    new_iter = model.insert_after(None, dest_iter, None)
    			
    		if ( new_iter ):
    		    for x in range(len(z)):
    			model.set(new_iter, int(x), z[int(x)])

		# Удалить если повтор в группе
    		if ( new_iter and check_demo_client_group(self.cfg, model, new_iter) ):
    		    model.remove(new_iter)
    		    new_iter = None

		if ( new_iter ):
	    	    temp_select_iter.append(new_iter)

	# Добавление кнопкой
    	else:
    	    user_list = get_selected_tree(self.cfg, self.treeView)
	    if ( user_list == [] ):
		return
		
    	    dest_path = None
    	    model, rows = self.treeDemoSelection.get_selected_rows()
    	    if ( mode == "add_client" ):
    		if ( rows == [] ):
    		    return
    	        dest_path = (rows[0][0],)
    	        
    	    for z in user_list:
    		
    		new_iter = None
    		
    		if ( mode == "add_server" ):
		    new_iter = self.cfg.demoList.append(None)
    		elif ( mode == "add_client" ):
    		    server_iter = model.get_iter(dest_path)
		    new_iter = model.append(server_iter)
		    
		if ( new_iter ):
    		    for x in range(len(z)):
    			model.set(new_iter, int(x), z[int(x)])
	
		# Удалить если повтор в группе
    		if ( new_iter and check_demo_client_group(self.cfg, model, new_iter) ):
    		    model.remove(new_iter)
    		    new_iter = None
    		    
		if ( new_iter ):
	    	    temp_select_iter.append(new_iter)
	    	    
	# раскрыть
    	if ( dest_path ):
	    self.treeDemo.expand_to_path(dest_path)

	# выделить
	if ( temp_select_iter != [] ):
	    self.treeDemo.get_selection().unselect_all()
	    for select_iter in temp_select_iter:
    		self.treeDemo.get_selection().select_iter(select_iter)
    	
	# сохранить после изменения
    	save_demoList(self.cfg)

    def stop(self, data=None):
    	model, rows = self.treeDemoSelection.get_selected_rows()
    	if ( rows == [] ):
    	    return
    	    
    	temp_iter = []
    	for row in rows:
    	    # Исключить клиентов выделенных групп
    	    if ( len(row) == 2 and (row[0],) in rows ):
    		continue
    	    iter = model.get_iter(row)
    	    temp_iter.append(iter)
    	    
    	for iter in temp_iter:
    	    if ( len(model.get_path(iter)) == 1 ):
    		self.stop_server(model, iter)
    	    elif ( len(model.get_path(iter)) == 2 ):
    		self.stop_client(model, iter)

    def stop_server(self, model, iter):
    	if ( self.check_start(model, iter) == False ):
    	    return
    	# Сперва остановить клиентов
	client_iter = self.cfg.demoList.iter_children(iter)
	while client_iter:
	    self.stop_client(model, client_iter)
	    client_iter = self.cfg.demoList.iter_next(client_iter)
	# Остановить сервер
	stop_demo_server(self.cfg, iter)
    	
    def stop_client(self, model, iter):
    	if ( self.check_start(model, iter) == False ):
    	    return
    	stop_demo_client(self.cfg, iter)

    def remove(self, data=None):
    	model, rows = self.treeDemoSelection.get_selected_rows()
    	if ( rows == [] ):
    	    return
	self.toolbarTree.set_sensitive(False)
	self.stop()
	self.toolbarTree.set_sensitive(True)
        parent_iters = []
        child_iters = []
	for row in rows:
	    if ( len(row) == 1 and row[0] == 0 ):
		    continue
	    if ( len(row) == 1 ):
    	    	parent_iters.append(model.get_iter(row))
    	    else:
    		child_iters.append(model.get_iter(row))
	for iter in child_iters:
    	    if ( iter != None ):
	        model.remove(iter)
	for iter in parent_iters:
    	    if ( iter != None ):
		model.remove(iter)
    	save_demoList(self.cfg)

    def start(self, mode):
    	model, rows = self.treeDemoSelection.get_selected_rows()
    	if ( rows == [] ):
    	    return

    	if ( mode == "file" ):
    	    if ( len(rows[0]) == 1 ):
    		rows = rows[0]
    	    else:
    		return

    	temp_iter = []
    	for row in rows:
    	    iter = model.get_iter(row)
    	    temp_iter.append(iter)
    	
    	for iter in temp_iter:
    	    if ( self.check_start(model, iter) == True ):
    		continue
    	    if ( self.check_start_all(model, iter) == True ):
    		continue
    	    model.set(iter, self.cfg.dn['demo_mode'], mode)
    	    if ( len(model.get_path(iter)) == 1 ):
		create_demo_server(self.cfg, iter)
		time.sleep(1)
    	    elif ( len(model.get_path(iter)) == 2 ):
    	    	thread = thread_gfunc(self.cfg, False, True, start_demo_client, self.cfg, iter)
		thread.start()
    		#start_demo_client(self.cfg, iter)

    def check_start(self, model, iter):
	# Если iter включен как сервер = True
    	if ( len(model.get_path(iter)) == 1 and \
    	    model.get_value(iter, self.cfg.dn['demo_server_pid']) not in self.cfg.null ):
    	    return True
	# Если iter включен как клиент = True
    	if ( len(model.get_path(iter)) == 2 and \
    	    model.get_value(iter, self.cfg.dn['demo_client_pid']) not in self.cfg.null ):
    	    return True
    	return False

    def check_start_all(self, model, iter):
    	# Если iter клиента и сервер не включен = True
    	if ( len(model.get_path(iter)) == 2 and \
    	    model.get_value(model.iter_parent(iter), self.cfg.dn['demo_server_pid']) in self.cfg.null ):
    	    return True
    	# Если включен любой сервер/клиент с этим id = True
	client_id = model.get_value(iter, self.cfg.dn["client_id"])
	server_iter = self.cfg.demoList.get_iter_first()
	while server_iter:
    	    if ( model.get_value(server_iter, self.cfg.dn["client_id"]) == client_id and \
    		model.get_value(server_iter, self.cfg.dn['demo_server_pid']) not in self.cfg.null ):
    		return True
	    client_iter = self.cfg.demoList.iter_children(server_iter)
	    while client_iter:
    		if ( model.get_value(client_iter, self.cfg.dn["client_id"]) == client_id ):
    		    if ( model.get_value(client_iter, self.cfg.dn['demo_client_pid']) not in self.cfg.null ):
    			return True
		client_iter = self.cfg.demoList.iter_next(client_iter)
	    server_iter = self.cfg.demoList.iter_next(server_iter)
    	return False

    def tree_button_press(self, treeView, event):
	path_at_pos = treeView.get_path_at_pos(int(event.x),int(event.y))
	# Снять выделение
	if ( not path_at_pos ):
	    treeView.get_selection().unselect_all()
	    return
	# Действия
	if ( event.button == 1 and (event.state & gtk.gdk.CONTROL_MASK or event.state & gtk.gdk.SHIFT_MASK) ):
	    # Нельзя выделить клиентов больше чем в одной группе
	    # Нельзя выделить несколько групп
	    model, rows = treeView.get_selection().get_selected_rows()
	    for row in rows:
		if ( row[0] != path_at_pos[0][0] ):
		    # Отлючить выделение
		    tree_selection_enable(self.treeDemo, False)
		    # Обратно включить
		    gobject.timeout_add(10, tree_selection_enable, self.treeDemo, True)
		    break
        elif ( event.type == gtk.gdk._2BUTTON_PRESS ):
    	    self.callback(None, "edit_tree_item" )
	
    def tree_demo_drag_data_motion(self, widget, drag_context, x, y, etime):
	if ( drag_context.get_source_widget() == widget ):
	    drag_context.drag_status(gtk.gdk.ACTION_MOVE, etime)
	elif ( drag_context.get_source_widget() == self.cfg.treeView ):
	    drag_context.drag_status(gtk.gdk.ACTION_LINK, etime)
	else:
	    drag_context.drag_status(gtk.gdk.ACTION_PRIVATE, etime)
	    return True
	drop_info = widget.get_dest_row_at_pos(x, y)
	if ( drop_info ):
	    dest_path, dest_pos = drop_info
	    if ( len(dest_path) == 2 ):
		if ( dest_pos == gtk.TREE_VIEW_DROP_BEFORE or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE ):
		    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_BEFORE)
		elif ( dest_pos == gtk.TREE_VIEW_DROP_AFTER or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER ):
		    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_AFTER)
	    else:
		if ( dest_pos == gtk.TREE_VIEW_DROP_BEFORE ):
	    	    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_BEFORE)
		elif ( dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE ):
	    	    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_INTO_OR_BEFORE)
		elif ( dest_pos == gtk.TREE_VIEW_DROP_AFTER and widget.row_expanded(dest_path) ):
	    	    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_INTO_OR_AFTER)
		elif ( dest_pos == gtk.TREE_VIEW_DROP_AFTER ):
	    	    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_AFTER)
		elif ( dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER ):
	    	    widget.set_drag_dest_row(dest_path, gtk.TREE_VIEW_DROP_INTO_OR_AFTER)
    	    # Нельзя вставить до первой группы
    	    if ( len(dest_path) == 1 and dest_path[0] == 0 and (dest_pos == gtk.TREE_VIEW_DROP_BEFORE or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE) ):
		drag_context.drag_status(gtk.gdk.ACTION_PRIVATE, etime)
	else:
	    widget.set_drag_dest_row((len(widget.get_model())-1,), gtk.TREE_VIEW_DROP_AFTER)
	return True

    def tree_demo_drag_data_received(self, treeView, context, x, y, selection, info, etime):
	if ( selection.target == "TREE_DEMO" ):
	    # Перетаскивание в списке
	    model, rows = treeView.get_selection().get_selected_rows()
	    if ( rows == [] ):
		return

	    drop_info = treeView.get_dest_row_at_pos(x, y)
	    if ( drop_info ):
		dest_path, dest_pos = drop_info
		dest_iter = model.get_iter(dest_path)
	    else:
		dest_path = None
		dest_iter = None

	    expand = False
	    temp_select_iter = []
	    temp_row_iter = []

	    for row in rows:
		# Исключить клиентов перемещаемых групп
		if ( len(row) == 2 and (row[0],) in rows ):
		    continue
		# Исключить клиентов если нет назначения
		if ( len(row) == 2 and not dest_path ):
		    continue
    		# Исключить первую группу
    		if ( len(row) == 1 and row[0] == 0 ):
    		    continue
    		# Исключить включенных клиентов
    		if ( len(row) == 2 and model[row][self.cfg.dn['demo_client_pid']] not in self.cfg.null ):
    		    continue
    		row_iter = model.get_iter(row)
    		temp_row_iter.append(row_iter)
    
	    for row_iter in temp_row_iter:
	
	    	temp_select_iter.append(row_iter)

		row = model.get_path(row_iter)
    		row_data = model[row]
    		new_iter = None
	
		if ( dest_path ):
    		    # Нельзя переместить группу в группу
    		    if ( len(row) == 1 and len(dest_path) == 2 ):
    			continue
    		    # Нельзя переместить группу в группу
    		    if ( len(row) == 1 and len(dest_path) == 1 and (dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER) ):
    			continue
    		
    		# Переместить группу в конец списка если нет назначения
		if ( len(row) == 1 and not dest_path ):
    		    new_iter = model.append(None, row_data)
		else:
    		    if ( len(dest_path) == 1 ):
    			if ( dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER ):
    			    new_iter = model.append(dest_iter, row_data)
			elif ( dest_pos == gtk.TREE_VIEW_DROP_BEFORE ):
    			    new_iter = model.insert_before(None, dest_iter, row_data)
			elif ( dest_pos == gtk.TREE_VIEW_DROP_AFTER ):
    			    new_iter = model.insert_after(None, dest_iter, row_data)
		    else:
    			if ( dest_pos == gtk.TREE_VIEW_DROP_BEFORE or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE ):
    			    new_iter = model.insert_before(None, dest_iter, row_data)
    			elif ( dest_pos == gtk.TREE_VIEW_DROP_AFTER or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER ):
    			    new_iter = model.insert_after(None, dest_iter, row_data)

		# Удалить если повтор в группе
    		if ( new_iter and check_demo_client_group(self.cfg, model, new_iter) ):
    		    model.remove(new_iter)
    		    new_iter = None

    		# Переместить клиентов группы
    		if ( new_iter and len(row) == 1 ):
    		    client_iter = model.iter_children(row_iter)
		    while client_iter:
    			client_data = model[model.get_path(client_iter)]
    			model.append(new_iter, client_data)
			client_iter = model.iter_next(client_iter)

    		if ( new_iter ):
    		    # Удалить
    		    model.remove(row_iter)
    		    # Добавить в список выделения
    		    temp_select_iter.remove(row_iter)
    		    temp_select_iter.append(new_iter)

	    if ( temp_row_iter != [] ):
		# раскрыть
		if ( expand ):
		    treeView.expand_to_path(dest_path)
	
		# выделить
		if ( temp_select_iter != [] ):
		    for select_iter in temp_select_iter:
    			treeView.get_selection().select_iter(select_iter)

		# сохранить после изменения
		save_demoList(self.cfg)
	else:
	    # перетаскивание из основного списка
    	    if ( not selection.data ):
    		return
    	    data = selection.data.splitlines()
	    user_list = []
	    for z in data:
		user_list.append(z.split(","))
	    drop_info = treeView.get_dest_row_at_pos(x, y)
	    self.add(None, user_list, drop_info)

    def toolbar_sens(self, thread):
	if thread.isAlive():
	    self.toolbarTree.set_sensitive(False)
	    return True
	else:
	    time.sleep(1)
	    self.toolbarTree.set_sensitive(True)
	    return False
    
    def callback(self, data1=None, data2=None, data3=None):
    	if (data2 == "edit_tree_item" ):
    	    if ( self.cfg.read_config("hide","hide_tree_add_remove") == "y" ):
    		return
    	    model, rows = self.treeDemo.get_selection().get_selected_rows()
    	    if ( rows == [] ):
		return
	    # Поиск в дереве row(path) по alias,user
	    client_id = model[rows[0]][self.cfg.dn['client_id']]
    	    row = find_tree(self.cfg, self.cfg.userList, client_id=client_id)
    	    if ( row == False ):
    	    	return
    	    # Раскрыть и выделить
    	    self.cfg.treeView.scroll_to_cell(row, None, use_align=True, row_align=0.5, col_align=0.0)
    	    self.cfg.treeView.expand_to_path(row)
    	    self.cfg.treeView.get_selection().unselect_all()
    	    self.cfg.treeView.get_selection().select_path(row)
    	    userUi(self.cfg, "edit", get_selected_tree(self.cfg, self.cfg.treeView, "edit"))

	if ( data2 == "add_server" ):
	    self.add("add_server")
	if ( data2 == "add_client" ):
	    self.add("add_client")
	if ( data2 == "remove" ):
	    self.remove()
	if ( data2 == "start_fullscreen" ):
	    thread = thread_gfunc(self.cfg, True, True, self.start, "fullscreen")
	    thread.start()
	    gobject.timeout_add(200, self.toolbar_sens, thread)
	if ( data2 == "start_window" ):
	    thread = thread_gfunc(self.cfg, True, True, self.start, "window")
	    thread.start()
	    gobject.timeout_add(200, self.toolbar_sens, thread)
	if ( data2 == "start_file" ):
	    if ( self.cfg.demoEntryBox.get_active_text() != "" ):
		thread = thread_gfunc(self.cfg, True, True, self.start, "file")
		thread.start()
		gobject.timeout_add(200, self.toolbar_sens, thread)
	    else:
		entry_error(self.cfg, self.cfg.demoEntryBox)
	if ( data2 == "stop" ):
	    thread = thread_gfunc(self.cfg, True, True, self.stop)
	    thread.start()
	    gobject.timeout_add(200, self.toolbar_sens, thread)

####################################################################################################

class userUi:

    def __init__(self, cfg, mode, user_list=None):
	# create standalone client

	self.cfg = cfg
	self.treeView = self.cfg.treeView
	self.table = self.cfg.table2
	self.mode = mode
	self.mode_edit = False
	self.user_list = user_list
	
	if ( user_list != None ):
	    if ( user_list == [] ):
		return
	    d = {}
	    for value, key in zip(user_list[0], cfg.z):
		d[key] = value
	
	if ( self.mode == "edit" ):
	    if ( d['server'] == "server" ):
		self.mode = "edit_server"
	    elif ( d['server'] == "" or d['server'] == None ):
		self.mode = "edit_group"
	    else:
		self.mode = "client_info"
	
	if ( self.mode == "new_group" ):
	    iter = self.cfg.userList.prepend(None)
	    row = self.cfg.userList.get_path(iter)
	    self.cfg.userList.set(iter, 0, _("New group"))
	    self.cfg.userList.set(iter, 100, self.cfg.pixbuf_status_group_16)
	    col = self.treeView.get_column(0)
	    cell = col.get_cell_renderers()[1]
    	    cell.set_property('editable', True)
	    self.treeView.set_cursor_on_cell(row, col, cell, start_editing=True)
    	    return
    	    
	if ( self.mode == "edit_group" ):
	    model, rows = self.treeView.get_selection().get_selected_rows()
	    row = rows[0]
	    col = self.treeView.get_column(0)
	    cell = col.get_cell_renderers()[1]
    	    cell.set_property('editable', True)
	    self.treeView.set_cursor_on_cell(row, col, cell, start_editing=True)
    	    return
    	    
	if ( self.mode == "server" ):
	    labelMode = gtk.Label(_("Add server"))
	    self.server = "server"
	    self.group = "server"
	    self.client = "server"
	    self.client_id = ""
	    #
	    ip = "localhost"
	    timeout = "100"
	    dhcp = "static"
	    dhcp_arp = "True"
	    #
	    show_local_sessions = "False"
	    dynamic_user = "False"
	    #
	    server_key = os.path.expanduser("~/.ssh/id_dsa")
	    server_port = "22"
	    server_user = ""
	    console_server = "mc"
	    #
	    host_key = os.path.expanduser("~/.ssh/id_dsa")
	    host_port = "22"
	    host_user = "root"
	    console_host = "mc"
	    folder_user = "/Рабочий стол/"
	    ssh_key_root = ""
	    #
	    vnc_nx_thin = "False"
	    vnc_nx_scan = "False"
	    vnc_nx_autostart = "True"
	    #
	    vncport = "5900"
	    vnc_normal = "False"
	    vnc_ssh = "True"
	    over_server = "False"
	    #
	    vnc_autostart = "True"
	    vnc_autostart_command = "x11vnc -noxdamage -defer 3000"
	    #
	    vnc_pass = ""
	    vnc_gtk_encoding = "default"
	    vnc_gtk_color = "default"
	    vnc_gtk_lossy = "True"
	    vnc_gtk_pointer = "False"
	    vnc_gtk_pointer_grab = "False"
	    vnc_gtk_keyboard_grab = "False"
	    #
	    vnc_pass_file = os.path.expanduser("~/.vnc/passwd")
	    vnc_command = "vncviewer -geometry 1024x768"
	    #
	    demo_ssh = "True"
	    vnc_server = "x11vnc -noxdamage -scale 1024x768"
	    vnc_client = "vncviewer -fullscreen -MenuKey none"
	    vnc_server_window = "x11vnc -noxdamage -scale 640x480"
	    vnc_client_window = "vncviewer -MenuKey none "
	    demo_vlc = "True"
	    demo_vlc_rtp = "False"
	    demo_vlc_audio = "False"
	    demo_vlc_fps = "10"
	    demo_vlc_vcodec = "mpgv"
	    demo_vlc_scale_full = "800x600"
	    demo_vlc_scale_window = "640x480"
	    demo_vlc_caching = "300"
	    demo_vlc_client = "False"
	    demo_vlc_client_command = "vlc --network-caching=100 --qt-minimal-view --no-qt-error-dialogs --no-qt-privacy-ask"
	elif ( self.mode == "edit_server" ):
	    labelMode = gtk.Label(_("Server information"))
	    self.mode = "server"
	    self.mode_edit = "server"
	    self.server = d['server']
	    self.group = d['group']
	    self.client = d['client']
	    self.client_id = ""
	    #
	    ip = d['alias']
	    timeout = d['timeout']
	    dhcp = d['dhcp']
	    dhcp_arp = d['dhcp_arp']
	    #
	    show_local_sessions = d['show_local_sessions']
	    dynamic_user = d['dynamic_user']
	    #
	    server_key = d['server_key']
	    server_port = d['server_port']
	    server_user = d['server_user']
	    console_server = d['console_server']
	    #
	    host_key = d['host_key']
	    host_port = d['host_port']
	    host_user = d['host_user']
	    console_host = d['console_host']
	    folder_user = d['folder_user']
	    ssh_key_root = d['ssh_key_root']
	    #
	    vnc_nx_thin = d['vnc_nx_thin']
	    vnc_nx_scan = d['vnc_nx_scan']
	    vnc_nx_autostart = d['vnc_nx_autostart']
	    #
	    vncport = d['vncport']
	    vnc_normal = d['vnc_normal']
	    vnc_ssh = d['vnc_ssh']
	    over_server = d['over_server']
	    #
	    vnc_autostart = d['vnc_autostart']
	    vnc_autostart_command = d['vnc_autostart_command']
	    #
	    vnc_pass = d['vnc_pass']
	    vnc_gtk_encoding = d['vnc_gtk_encoding']
	    vnc_gtk_color = d['vnc_gtk_color']
	    vnc_gtk_lossy = d['vnc_gtk_lossy']
	    vnc_gtk_pointer = d['vnc_gtk_pointer']
	    vnc_gtk_pointer_grab = d['vnc_gtk_pointer_grab']
	    vnc_gtk_keyboard_grab = d['vnc_gtk_keyboard_grab']
	    #
	    vnc_pass_file = d['vnc_pass_file']
	    vnc_command = d['vnc_command']
	    #
	    demo_ssh = d['demo_ssh']
	    vnc_server = d['vnc_server']
	    vnc_client = d['vnc_client']
	    vnc_server_window = d['vnc_server_window']
	    vnc_client_window = d['vnc_client_window']
	    demo_vlc = d['demo_vlc']
	    demo_vlc_rtp = d['demo_vlc_rtp']
	    demo_vlc_audio = d['demo_vlc_audio']
	    demo_vlc_fps = d['demo_vlc_fps']
	    demo_vlc_vcodec = d['demo_vlc_vcodec']
	    demo_vlc_scale_full = d['demo_vlc_scale_full']
	    demo_vlc_scale_window = d['demo_vlc_scale_window']
	    demo_vlc_caching = d['demo_vlc_caching']
	    demo_vlc_client = d['demo_vlc_client']
	    demo_vlc_client_command = d['demo_vlc_client_command']
	elif ( self.mode == "standalone" ):
	    labelMode = gtk.Label(_("Add standalone client"))
	    self.server = "standalone"
	    self.group = "standalone"
	    self.client = "standalone"
	    #
	    self.alias = ""
	    user = ""
	    host = ""
	    ip = ""
	    mac = ""
	    display = ":0"
	    timeout = "100"
	    desktop = "linux"
	    dhcp = "static"
	    dhcp_arp = "False"
	    #
	    show_local_sessions = "False"
	    dynamic_user = "False"
	    #
	    server_key = os.path.expanduser("~/.ssh/id_dsa")
	    #
	    host_key = os.path.expanduser("~/.ssh/id_dsa")
	    host_port = "22"
	    host_user = ""
	    console_host = "mc"
	    folder_user = "/Рабочий стол/"
	    ssh_key_root = ""
	    #
	    vnc_nx_thin = "False"
	    vnc_nx_scan = "False"
	    vnc_nx_autostart = "True"
	    #
	    vncport = "5900"
	    vnc_normal = "False"
	    vnc_ssh = "True"
	    over_server = "False"
	    #
	    vnc_autostart = "True"
	    vnc_autostart_command = "x11vnc -noxdamage -defer 3000"
	    #
	    vnc_pass = ""
	    vnc_gtk_encoding = "default"
	    vnc_gtk_color = "default"
	    vnc_gtk_lossy = "True"
	    vnc_gtk_pointer = "False"
	    vnc_gtk_pointer_grab = "False"
	    vnc_gtk_keyboard_grab = "False"
	    #
	    vnc_pass_file = os.path.expanduser("~/.vnc/passwd")
	    vnc_command = "vncviewer -geometry 1024x768"
	    #
	    demo_ssh = "True"
	    vnc_server = "x11vnc -noxdamage -scale 1024x768"
	    vnc_client = "vncviewer -fullscreen -MenuKey none"
	    vnc_server_window = "x11vnc -noxdamage -scale 640x480"
	    vnc_client_window = "vncviewer -MenuKey none"
	    demo_vlc = "True"
	    demo_vlc_rtp = "False"
	    demo_vlc_audio = "False"
	    demo_vlc_fps = "10"
	    demo_vlc_vcodec = "mpgv"
	    demo_vlc_scale_full = "800x600"
	    demo_vlc_scale_window = "640x480"
	    demo_vlc_caching = "300"
	    demo_vlc_client = "False"
	    demo_vlc_client_command = "vlc --network-caching=100 --qt-minimal-view --no-qt-error-dialogs --no-qt-privacy-ask"
	elif ( self.mode == "client_info" ):
	    labelMode = gtk.Label(_("Client information"))
	    self.server = d['server']
	    self.group = d['group']
	    self.client = d['client']
	    self.client_id = d['client_id']
	    #
	    self.alias = d['alias']
	    user = d['user']
	    host = d['host']
	    ip = d['ip']
	    mac = d['mac']
	    display = d['display']
	    timeout = d['timeout']
	    desktop = d['desktop']
	    dhcp = d['dhcp']
	    dhcp_arp = d['dhcp_arp']
	    #
	    show_local_sessions = d['show_local_sessions']
	    dynamic_user = d['dynamic_user']
	    #
	    server_key = d['server_key']
	    server_port = d['server_port']
	    server_user = d['server_user']
	    console_server = d['console_server']
	    #
	    host_key = d['host_key']
	    host_port = d['host_port']
	    host_user = d['host_user']
	    console_host = d['console_host']
	    folder_user = d['folder_user']
	    ssh_key_root = d['ssh_key_root']
	    #
	    vnc_nx_thin = d['vnc_nx_thin']
	    vnc_nx_scan = d['vnc_nx_scan']
	    vnc_nx_autostart = d['vnc_nx_autostart']
	    #
	    vncport = d['vncport']
	    vnc_normal = d['vnc_normal']
	    vnc_ssh = d['vnc_ssh']
	    over_server = d['over_server']
	    #
	    vnc_autostart = d['vnc_autostart']
	    vnc_autostart_command = d['vnc_autostart_command']
	    #
	    vnc_pass = d['vnc_pass']
	    vnc_gtk_encoding = d['vnc_gtk_encoding']
	    vnc_gtk_color = d['vnc_gtk_color']
	    vnc_gtk_lossy = d['vnc_gtk_lossy']
	    vnc_gtk_pointer = d['vnc_gtk_pointer']
	    vnc_gtk_pointer_grab = d['vnc_gtk_pointer_grab']
	    vnc_gtk_keyboard_grab = d['vnc_gtk_keyboard_grab']
	    #
	    vnc_pass_file = d['vnc_pass_file']
	    vnc_command = d['vnc_command']
	    #
	    demo_ssh = d['demo_ssh']
	    vnc_server = d['vnc_server']
	    vnc_client = d['vnc_client']
	    vnc_server_window = d['vnc_server_window']
	    vnc_client_window = d['vnc_client_window']
	    demo_vlc = d['demo_vlc']
	    demo_vlc_audio = d['demo_vlc_audio']
	    demo_vlc_rtp = d['demo_vlc_rtp']
	    demo_vlc_fps = d['demo_vlc_fps']
	    demo_vlc_vcodec = d['demo_vlc_vcodec']
	    demo_vlc_scale_full = d['demo_vlc_scale_full']
	    demo_vlc_scale_window = d['demo_vlc_scale_window']
	    demo_vlc_caching = d['demo_vlc_caching']
	    demo_vlc_client = d['demo_vlc_client']
	    demo_vlc_client_command = d['demo_vlc_client_command']

	create_window2(self.cfg)
	
	vbox = gtk.VBox(False, 0)
	layout = gtk.Layout()
	vbox.pack_start(layout, expand=False, fill=False, padding=5)

	if ( self.group == "server" and  self.mode != "server" ):
	    editable = False
	else:
	    editable = True
	
	if ( self.mode != "server" ):
	    self.entryAlias = label_entry(_("Alias"), self.alias, 24, 24, 20, 210, True)
	    vbox.pack_start(self.entryAlias, expand=False, fill=False, padding=0)

	    self.entryUser = label_entry(_("User"), user, 24, 24, 20, 210, editable)
	    vbox.pack_start(self.entryUser, expand=False, fill=False, padding=0)

	    self.entryHost = label_entry(_("Host"), host, 24, 24, 20, 210, editable)
	    vbox.pack_start(self.entryHost, expand=False, fill=False, padding=0)

	self.entryIp = label_entry("IP "+_("address"), ip, 24, 15, 20, 210, editable)
	vbox.pack_start(self.entryIp, expand=False, fill=False, padding=0)
	if ( self.mode == "server" ):
	    self.entryIp.entry.connect("changed", self.callback, "server_changed")
	
	if ( self.mode != "server" ):
	    self.entryMac = label_entry("MAC "+_("address"), mac, 24, 24, 20, 210, editable)
	    vbox.pack_start(self.entryMac, expand=False, fill=False, padding=0)

	    if ( self.client != "standalone" ):
		self.entryUser.set_editable(False)
		self.entryServer = label_entry(_("Server"), self.server, 24, 24, 20, 210, False)
		vbox.pack_start(self.entryServer, expand=False, fill=False, padding=0)

	    self.entryDisplay = label_entry(_("Display number"), display, 24, 24, 20, 210, editable)
	    vbox.pack_start(self.entryDisplay, expand=False, fill=False, padding=0)
	
	self.entryTimeout = label_entry(_("Nmap timeout"), timeout, 24, 5, 20, 210, editable)
	vbox.pack_start(self.entryTimeout, expand=False, fill=False, padding=0)
	
	if ( self.mode != "server" ):
	    # desktop
	    label = gtk.Label(_("Desktop"))
	    label.set_alignment(0, 0.5)
	    self.comboDesktop = gtk.combo_box_new_text()
	    self.comboDesktop.set_size_request(175, 26)
	    for i in cfg.known_desktop:
    		self.comboDesktop.append_text(i)
    	    fixed = gtk.Fixed()
    	    fixed.put(label, 20, 0)
	    fixed.put(self.comboDesktop, 210, 0)
	    vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	    model = self.comboDesktop.get_model()
	    for item in range(len(model)):
		if ( model[item][0] == desktop ):
		    self.comboDesktop.set_active(item)
		    break
		elif ( model[item][0] == "unknown" ):
		    self.comboDesktop.set_active(item)
		    break
	    if ( self.group == "server" ):
		self.comboDesktop.set_sensitive(False)
	
	# dhcp
	label = gtk.Label(_("DHCP"))
	label.set_alignment(0, 0.5)
	self.comboDhcp = gtk.combo_box_new_text()
	self.comboDhcp.set_size_request(175, 26)
    	self.comboDhcp.append_text("dynamic")
    	self.comboDhcp.append_text("static")
	model = self.comboDhcp.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == dhcp or model[item][0] == "static" ):
		self.comboDhcp.set_active(item)
		break
    	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.comboDhcp, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	if ( self.group == "server" and self.mode != "server" ):
	    self.comboDhcp.set_sensitive(False)
	self.comboDhcp.connect("changed", self.callback, "dhcp_changed")

    	label = gtk.Label(_("IP address from ARP table"))
    	self.buttonDhcpArp = gtk.CheckButton(" ")
    	self.buttonDhcpArp.unset_flags(gtk.CAN_FOCUS)
	self.buttonDhcpArp.set_sensitive(editable)
	if ( dhcp_arp == "True" ):
	    self.buttonDhcpArp.set_active(True)
	if ( self.comboDhcp.get_active_text() == "static" ):
    	    self.buttonDhcpArp.set_sensitive(False)
	if ( self.client != "standalone" ):
	    fixed = gtk.Fixed()
	    fixed.set_size_request(175, 20)
	    fixed.put(label, 20, 1)
	    fixed.put(self.buttonDhcpArp, 210, 0)
	    vbox.pack_start(fixed, expand=False, fill=False, padding=3)

    	label = gtk.Label(_("Show local sessions"))
    	self.buttonShowLocalSessions = gtk.CheckButton(_("Dangerous!"))
    	self.buttonShowLocalSessions.unset_flags(gtk.CAN_FOCUS)
	self.buttonShowLocalSessions.set_sensitive(editable)
	if ( show_local_sessions == "True" ):
	    self.buttonShowLocalSessions.set_active(True)
	if ( self.mode == "server" ):
	    fixed = gtk.Fixed()
	    fixed.set_size_request(175, 20)
	    fixed.put(label, 20, 1)
	    fixed.put(self.buttonShowLocalSessions, 210, 0)
	    vbox.pack_start(fixed, expand=False, fill=False, padding=3)

    	label = gtk.Label(_("Multi-user"))
	self.buttonDynamicUser = gtk.CheckButton(" ")
	self.buttonDynamicUser.unset_flags(gtk.CAN_FOCUS)
	if ( dynamic_user == "True" ):
	    self.buttonDynamicUser.set_active(True)
	if ( self.client == "standalone" ):
	    fixed = gtk.Fixed()
	    fixed.put(label, 20, 1)
	    fixed.put(self.buttonDynamicUser, 210, 0)
	    vbox.pack_start(fixed, expand=False, fill=False, padding=3)
	    
	if ( self.client != "standalone" ):
	    separator = gtk.HSeparator()
	    vbox.pack_start(separator, expand=False, fill=False, padding=0)
	    separator = gtk.HSeparator()
	    vbox.pack_start(separator, expand=False, fill=False, padding=1)
	    label = gtk.Label(_("SSH server settings"))
	    vbox.pack_start(label, expand=False, fill=False, padding=0)
	    separator = gtk.HSeparator()
	    vbox.pack_start(separator, expand=False, fill=False, padding=1)
	    separator = gtk.HSeparator()
	    vbox.pack_start(separator, expand=False, fill=False, padding=0)
	    
	    self.entryServerKey = file_entry(self.cfg.pixbuf_list_file_add_16, "SSH "+_("key"), server_key, 20, 20, 210, editable)
	    self.entryServerKey.button.set_sensitive(editable)
	    vbox.pack_start(self.entryServerKey, expand=False, fill=False, padding=0)

	    self.entryServerPort = label_entry("SSH "+_("port"), server_port, 24, 5, 20, 210, editable)
	    vbox.pack_start(self.entryServerPort, expand=False, fill=False, padding=0)

	    self.entryServerUser = label_entry("SSH "+_("user"), server_user, 24, 24, 20, 210, editable)
	    vbox.pack_start(self.entryServerUser, expand=False, fill=False, padding=0)

	    self.entryConsoleServer = label_entry("SSH "+_("console"), console_server, 24, 24, 20, 210, editable)
	    vbox.pack_start(self.entryConsoleServer, expand=False, fill=False, padding=0)

	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	if ( self.client == "standalone" or ( self.group == "server" and  self.mode != "server" ) ):
	    label = gtk.Label(_("SSH client settings"))
	else:
	    label = gtk.Label(_("SSH clients settings"))    
	vbox.pack_start(label, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=0)

	self.entryHostKey = file_entry(self.cfg.pixbuf_list_file_add_16, "SSH "+_("key"), host_key, 20, 20, 210, editable)
	self.entryHostKey.button.set_sensitive(editable)
	vbox.pack_start(self.entryHostKey, expand=False, fill=False, padding=0)
	
	self.entrySshKeyRoot = file_entry(self.cfg.pixbuf_list_file_add_16, "SSH "+_("key")+"(root)", ssh_key_root, 20, 20, 210, editable)
	self.entrySshKeyRoot.button.set_sensitive(editable)
	if ( self.client == "standalone" ):
	    vbox.pack_start(self.entrySshKeyRoot, expand=False, fill=False, padding=0)

	self.entryHostPort = label_entry("SSH "+_("port"), host_port, 24, 5, 20, 210, editable)
	vbox.pack_start(self.entryHostPort, expand=False, fill=False, padding=0)
	
	self.entryHostUser = label_entry("SSH "+_("user"), host_user, 24, 24, 20, 210, editable)
	if ( self.client != "standalone" ):
	    vbox.pack_start(self.entryHostUser, expand=False, fill=False, padding=0)
	
	self.entryConsoleHost = label_entry("SSH "+_("console"), console_host, 24, 24, 20, 210, editable)
	vbox.pack_start(self.entryConsoleHost, expand=False, fill=False, padding=0)

	self.entryFolderUser = label_entry(_("Folder for sending files"), folder_user, 24, 200, 20, 210, editable)
	vbox.pack_start(self.entryFolderUser, expand=False, fill=False, padding=0)
	
	##########################################
	# VNC
	##########################################	
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	if ( self.client == "standalone" or ( self.group == "server" and  self.mode != "server" ) ):
	    label = gtk.Label(_("VNC client settings"))
	else:
	    label = gtk.Label(_("VNC clients settings"))
	vbox.pack_start(label, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=0)

	self.buttonVncAutostart = gtk.CheckButton(" ")
	self.buttonVncAutostart.unset_flags(gtk.CAN_FOCUS)
	self.buttonVncAutostart.set_sensitive(editable)
	if ( vnc_autostart == "True" ):
	    self.buttonVncAutostart.set_active(True)
	fixed = gtk.Fixed()
	label = gtk.Label(_("Autostart x11vnc"))
	fixed.put(label, 20, 0)
	fixed.put(self.buttonVncAutostart, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=3)
	    
	self.entryVncAutostartCommand = label_entry(_("Autostart x11vnc")+"("+_("command")+")", vnc_autostart_command, 24, 200, 20, 210, editable)
	vbox.pack_start(self.entryVncAutostartCommand, expand=False, fill=False, padding=0)
	
	self.entryVncPort = label_entry("VNC "+_("port"), vncport, 24, 5, 20, 210, editable)
	vbox.pack_start(self.entryVncPort, expand=False, fill=False, padding=0)
	
	###
        label = gtk.Label(_("Priority of the connection"))

    	self.buttonOverServer = gtk.CheckButton(_("Over server"))
    	self.buttonOverServer.unset_flags(gtk.CAN_FOCUS)
	self.buttonOverServer.set_sensitive(editable)
	if ( over_server == "True" ):
	    self.buttonOverServer.set_active(True)
	#if ( self.client != "standalone" ):
	#    fixed = gtk.Fixed()
	#    fixed.put(self.buttonOverServer, 210, 0)
	#    vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	self.buttonVncNormal = gtk.CheckButton("VNC "+_("normal"))
	self.buttonVncNormal.unset_flags(gtk.CAN_FOCUS)
	self.buttonVncNormal.set_sensitive(editable)
	if ( vnc_normal == "True" ):
	    self.buttonVncNormal.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(label, 20, 0)
	fixed.put(self.buttonVncNormal, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
        self.buttonVncSsh = gtk.CheckButton(_("VNC over SSH"))
        self.buttonVncSsh.unset_flags(gtk.CAN_FOCUS)
	self.buttonVncSsh.set_sensitive(editable)
	if ( vnc_ssh == "True" ):
	    self.buttonVncSsh.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonVncSsh, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)


	#
	# NX
	#
	if ( self.client == "nx" or self.mode == "server" ):
	    separator = gtk.HSeparator()
	    vbox.pack_start(separator, expand=False, fill=False, padding=1)
	    label = gtk.Label(_("NX clients settings"))
	    vbox.pack_start(label, expand=False, fill=False, padding=0)
	    separator = gtk.HSeparator()
	    vbox.pack_start(separator, expand=False, fill=False, padding=1)

	self.buttonVncNxThin = gtk.CheckButton(_("Thin client"))
	self.buttonVncNxThin.unset_flags(gtk.CAN_FOCUS)
	self.buttonVncNxThin.set_sensitive(editable)
	if ( vnc_nx_thin == "True" ):
	    self.buttonVncNxThin.set_active(True)
	if ( self.client == "nx" or self.mode == "server" ):
	    fixed = gtk.Fixed()
    	    label = gtk.Label(_("Priority of the connection"))
	    fixed.put(label, 20, 0)
	    fixed.put(self.buttonVncNxThin, 210, 0)
	    vbox.pack_start(fixed, expand=False, fill=False, padding=0)
    	    
    	self.buttonVncNxScan = gtk.CheckButton(_("Search x11vnc port"))
    	self.buttonVncNxScan.unset_flags(gtk.CAN_FOCUS)
    	self.buttonVncNxScan.set_sensitive(editable)
	if ( vnc_nx_scan == "True" ):
	    self.buttonVncNxScan.set_active(True)
	if ( self.client == "nx" or self.mode == "server" ):
	    fixed = gtk.Fixed()
	    fixed.put(self.buttonVncNxScan, 210, 0)
	    vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	self.buttonVncNxAutostart = gtk.CheckButton(_("Autostart x11vnc"))
	self.buttonVncNxAutostart.unset_flags(gtk.CAN_FOCUS)
	self.buttonVncNxAutostart.set_sensitive(editable)
	if ( vnc_nx_autostart == "True" ):
	    self.buttonVncNxAutostart.set_active(True)
	if ( self.client == "nx" or self.mode == "server" ):
	    fixed = gtk.Fixed()
	    fixed.put(self.buttonVncNxAutostart, 210, 0)
	    vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	#
	# Built-in
	#
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	label = gtk.Label(_("Built-in VNC client"))
	vbox.pack_start(label, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)

	self.entryVncPassword = label_entry(_("Password"), vnc_pass, 24, 24, 20, 210, editable, False)
	vbox.pack_start(self.entryVncPassword, expand=False, fill=False, padding=0)

	###
	label = gtk.Label(_("Encoding"))
	label.set_alignment(0, 0.5)
	self.comboVncGtkEncoding = gtk.combo_box_new_text()
	self.comboVncGtkEncoding.set_size_request(175, 26)
    	self.comboVncGtkEncoding.append_text("default")
    	self.comboVncGtkEncoding.append_text("zrle")
    	self.comboVncGtkEncoding.append_text("hextile")
    	self.comboVncGtkEncoding.append_text("raw")
	if ( self.cfg.gtkvnc_encoding ):
	    fixed = gtk.Fixed()
    	    fixed.put(label, 20, 0)
	    fixed.put(self.comboVncGtkEncoding, 210, 0)
	    vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	model = self.comboVncGtkEncoding.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == vnc_gtk_encoding ):
	        self.comboVncGtkEncoding.set_active(item)
	        break
	self.comboVncGtkEncoding.set_sensitive(editable)
	
	###
	label = gtk.Label(_("Color level"))
	label.set_alignment(0, 0.5)
	self.comboVncGtkColor = gtk.combo_box_new_text()
	self.comboVncGtkColor.set_sensitive(editable)
	self.comboVncGtkColor.set_size_request(175, 26)
    	self.comboVncGtkColor.append_text("default")
    	self.comboVncGtkColor.append_text("full")
    	self.comboVncGtkColor.append_text("medium")
    	self.comboVncGtkColor.append_text("low")
    	self.comboVncGtkColor.append_text("ultra-low")
	if ( self.cfg.gtkvnc_depth ):
    	    fixed = gtk.Fixed()
    	    fixed.put(label, 20, 0)
	    fixed.put(self.comboVncGtkColor, 210, 0)
	    vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	model = self.comboVncGtkColor.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == vnc_gtk_color ):
	        self.comboVncGtkColor.set_active(item)
	        break
	
	self.buttonVncGtkLossy = gtk.CheckButton(_("Lossy encoding"))
	self.buttonVncGtkLossy.unset_flags(gtk.CAN_FOCUS)
	self.buttonVncGtkLossy.set_sensitive(editable)
	if ( vnc_gtk_lossy == "True" ):
	    self.buttonVncGtkLossy.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonVncGtkLossy, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	self.buttonVncGtkPointer = gtk.CheckButton(_("Pointer local"))
	self.buttonVncGtkPointer.unset_flags(gtk.CAN_FOCUS)
	self.buttonVncGtkPointer.set_sensitive(editable)
	if ( vnc_gtk_pointer == "True" ):
	    self.buttonVncGtkPointer.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonVncGtkPointer, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	self.buttonVncGtkPointerGrab = gtk.CheckButton(_("Pointer grab"))
	self.buttonVncGtkPointerGrab.unset_flags(gtk.CAN_FOCUS)
	self.buttonVncGtkPointerGrab.set_sensitive(editable)
	if ( vnc_gtk_pointer_grab == "True" ):
	    self.buttonVncGtkPointerGrab.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonVncGtkPointerGrab, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	self.buttonVncGtkKeyboardGrab = gtk.CheckButton(_("Keyboard grab"))
	self.buttonVncGtkKeyboardGrab.unset_flags(gtk.CAN_FOCUS)
	self.buttonVncGtkKeyboardGrab.set_sensitive(editable)
	if ( vnc_gtk_keyboard_grab == "True" ):
	    self.buttonVncGtkKeyboardGrab.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonVncGtkKeyboardGrab, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	#
	# External
	#
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	label = gtk.Label(_("External VNC client"))
	vbox.pack_start(label, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	
	self.entryVncPasswordFile = file_entry(self.cfg.pixbuf_list_file_add_16, _("Password"), vnc_pass_file, 20, 20, 210, editable)
	self.entryVncPasswordFile.button.set_sensitive(editable)
	vbox.pack_start(self.entryVncPasswordFile, expand=False, fill=False, padding=0)
	
	self.entryVncCommand = label_entry("VNC "+_("command"), vnc_command, 24, 200, 20, 210, editable)
	vbox.pack_start(self.entryVncCommand, expand=False, fill=False, padding=0)

	##########################################
	# Demo
	##########################################
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	label = gtk.Label(_("Demo"))
	vbox.pack_start(label, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=0)
	
	self.buttonDemoVlc = gtk.RadioButton(None, _("Video streaming")+"(VLC)")
	self.buttonDemoVlc.unset_flags(gtk.CAN_FOCUS)
	self.buttonDemoVlc.set_sensitive(editable)
	fixed = gtk.Fixed()
	label = gtk.Label(_("Server type"))
	fixed.put(label, 20, 0)
	fixed.put(self.buttonDemoVlc, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	self.buttonDemoVnc = gtk.RadioButton(self.buttonDemoVlc, _("VNC"))
	self.buttonDemoVnc.unset_flags(gtk.CAN_FOCUS)
	self.buttonDemoVnc.set_sensitive(editable)
	if ( demo_vlc != "True" ):
	    self.buttonDemoVnc.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonDemoVnc, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	self.buttonDemoDirect = gtk.RadioButton(None, _("Direct"))
	self.buttonDemoDirect.unset_flags(gtk.CAN_FOCUS)
	self.buttonDemoDirect.set_sensitive(editable)
	fixed = gtk.Fixed()
	label = gtk.Label(_("Connection of clients"))
	fixed.put(label, 20, 0)
	fixed.put(self.buttonDemoDirect, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	self.buttonDemoSsh = gtk.RadioButton(self.buttonDemoDirect, _("VNC/HTTP over SSH"))
	self.buttonDemoSsh.unset_flags(gtk.CAN_FOCUS)
	self.buttonDemoSsh.set_sensitive(editable)
	if ( demo_ssh == "True" ):
	    self.buttonDemoSsh.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonDemoSsh, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	# VLC
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	label = gtk.Label(_("Video streaming"))
	vbox.pack_start(label, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	###
	###
	self.buttonDemoVlcHttp = gtk.RadioButton(None, "HTTP")
	self.buttonDemoVlcHttp.unset_flags(gtk.CAN_FOCUS)
	self.buttonDemoVlcHttp.set_sensitive(editable)
	fixed = gtk.Fixed()
	fixed.put(self.buttonDemoVlcHttp, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	self.buttonDemoVlcRtp = gtk.RadioButton(self.buttonDemoVlcHttp, "RTP (multicast 239.0.0.1)")
	self.buttonDemoVlcRtp.unset_flags(gtk.CAN_FOCUS)
	self.buttonDemoVlcRtp.set_sensitive(editable)
	if ( demo_vlc_rtp in self.cfg.true ):
	    self.buttonDemoVlcRtp.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonDemoVlcRtp, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	###
	self.buttonDemoVlcAudio = gtk.CheckButton(_("Audio")+" ("+_("only")+" PulseAudio)")
	self.buttonDemoVlcAudio.unset_flags(gtk.CAN_FOCUS)
	self.buttonDemoVlcAudio.set_sensitive(editable)
	#if ( demo_vlc_audio in self.cfg.true ):
	#    self.buttonDemoVlcAudio.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonDemoVlcAudio, 210, 0)
	#vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	label = gtk.Label(_("Frames per second"))
	label.set_alignment(0, 0.5)
	self.comboDemoVlcFps = gtk.combo_box_new_text()
	self.comboDemoVlcFps.set_sensitive(editable)
	self.comboDemoVlcFps.set_size_request(175, 26)
    	self.comboDemoVlcFps.append_text("5")
    	self.comboDemoVlcFps.append_text("10")
    	self.comboDemoVlcFps.append_text("15")
    	self.comboDemoVlcFps.append_text("24")
    	self.comboDemoVlcFps.append_text("30")
    	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.comboDemoVlcFps, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	model = self.comboDemoVlcFps.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == demo_vlc_fps ):
	        self.comboDemoVlcFps.set_active(item)
	        break

	###
	label = gtk.Label(_("Video codec"))
	label.set_alignment(0, 0.5)
	self.comboDemoVlcVcodec = gtk.combo_box_new_text()
	self.comboDemoVlcVcodec.set_sensitive(editable)
	self.comboDemoVlcVcodec.set_size_request(175, 26)
    	self.comboDemoVlcVcodec.append_text("mp1v")
    	self.comboDemoVlcVcodec.append_text("mp2v")
    	self.comboDemoVlcVcodec.append_text("mpgv")
    	self.comboDemoVlcVcodec.append_text("wmv1")
    	self.comboDemoVlcVcodec.append_text("wmv2")
    	self.comboDemoVlcVcodec.append_text("mjpg")
    	#self.comboDemoVlcVcodec.append_text("h264")
    	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.comboDemoVlcVcodec, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	model = self.comboDemoVlcVcodec.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == demo_vlc_vcodec ):
	        self.comboDemoVlcVcodec.set_active(item)
	        break

	###
	label = gtk.Label(_("Resolution")+" ("+_("in full screen")+")")
	label.set_alignment(0, 0.5)
	self.comboDemoVlcScaleFull = gtk.combo_box_new_text()
	self.comboDemoVlcScaleFull.set_row_separator_func(self.combo_separator)
	self.comboDemoVlcScaleFull.set_sensitive(editable)
	self.comboDemoVlcScaleFull.set_size_request(175, 26)
	for x in self.cfg.scale_list:
    	    self.comboDemoVlcScaleFull.append_text(x)
    	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.comboDemoVlcScaleFull, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	model = self.comboDemoVlcScaleFull.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == demo_vlc_scale_full ):
	        self.comboDemoVlcScaleFull.set_active(item)
	        break

	###
	label = gtk.Label(_("Resolution")+" ("+_("in window")+")")
	label.set_alignment(0, 0.5)
	self.comboDemoVlcScaleWindow = gtk.combo_box_new_text()
	self.comboDemoVlcScaleWindow.set_row_separator_func(self.combo_separator)
	self.comboDemoVlcScaleWindow.set_sensitive(editable)
	self.comboDemoVlcScaleWindow.set_size_request(175, 26)
	for x in self.cfg.scale_list:
    	    self.comboDemoVlcScaleWindow.append_text(x)
    	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.comboDemoVlcScaleWindow, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	model = self.comboDemoVlcScaleWindow.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == demo_vlc_scale_window ):
	        self.comboDemoVlcScaleWindow.set_active(item)
	        break
	
	###
	label = gtk.Label(_("Caching"))
	label.set_alignment(0, 0.5)
	self.comboDemoVlcCaching = gtk.combo_box_new_text()
	self.comboDemoVlcCaching.set_sensitive(editable)
	self.comboDemoVlcCaching.set_size_request(175, 26)
    	self.comboDemoVlcCaching.append_text("300")
    	self.comboDemoVlcCaching.append_text("1000")
    	self.comboDemoVlcCaching.append_text("2000")
    	self.comboDemoVlcCaching.append_text("3000")
    	self.comboDemoVlcCaching.append_text("5000")
    	self.comboDemoVlcCaching.append_text("10000")
    	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.comboDemoVlcCaching, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	model = self.comboDemoVlcCaching.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == demo_vlc_caching ):
	        self.comboDemoVlcCaching.set_active(item)
	        break

	###
	label = gtk.Label(_("Another client command"))
	label.set_alignment(0, 0.5)
	self.buttonDemoVlcClient = gtk.CheckButton(" ")
	self.buttonDemoVlcClient.unset_flags(gtk.CAN_FOCUS)
	self.buttonDemoVlcClient.set_sensitive(editable)
	if ( demo_vlc_client == "True" ):
	    self.buttonDemoVlcClient.set_active(True)
	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.buttonDemoVlcClient, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=3)
	
	self.entryDemoVlcClientCommand = label_entry("", demo_vlc_client_command, 51, 200, 20, 20, editable)
	vbox.pack_start(self.entryDemoVlcClientCommand, expand=False, fill=False, padding=0)
	
	# VNC
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	label = gtk.Label(_("VNC"))
	vbox.pack_start(label, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)

	self.entryVncServer = label_entry(_("Server command"), vnc_server, 24, 200, 20, 210, editable)
	vbox.pack_start(self.entryVncServer, expand=False, fill=False, padding=0)

	self.entryVncServerWindow = label_entry(_("Server command")+"("+_("in window")+")", vnc_server_window, 24, 200, 20, 210, editable)
	vbox.pack_start(self.entryVncServerWindow, expand=False, fill=False, padding=0)

	self.entryVncClient = label_entry(_("Client command"), vnc_client, 24, 200, 20, 210, editable)
	vbox.pack_start(self.entryVncClient, expand=False, fill=False, padding=0)
	
	self.entryVncClientWindow = label_entry(_("Client command")+"("+_("in window")+")", vnc_client_window, 24, 200, 20, 210, editable)
	vbox.pack_start(self.entryVncClientWindow, expand=False, fill=False, padding=0)
	
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)

	layout = gtk.Layout()
	vbox.pack_start(layout, expand=False, fill=False, padding=5)

	# button
        saveButton = image_button(self.cfg.pixbuf_list_save_16, _("Save"))
	saveButton.connect("clicked", self.save)
	saveButton.set_size_request(120, 26)

        closeButton = image_button(self.cfg.pixbuf_action_close_16, _("Close"))
	closeButton.connect("clicked", close_window2, self.cfg)
	closeButton.set_size_request(120, 26)
	
	# attach
	frame1 = gtk.Frame()
        self.cfg.table2.attach(frame1, 0, 28, 0, 42)

	if ( self.mode == "server" ):
	    image = gtk.Image()
	    image.set_from_pixbuf(cfg.pixbuf_server)
    	elif ( self.mode == "standalone" or self.client == "standalone" ):
	    image = gtk.Image()
	    image.set_from_pixbuf(cfg.pixbuf_st)
	else:
	    image = gtk.Image()
	    image.set_from_pixbuf(cfg.pixbuf_action_user_info)
    	    
	labelMode.set_alignment(0.0,0.5)
	layout = gtk.Layout()
    	hbox = gtk.HBox()
    	hbox.pack_start(image, expand=False, fill=False, padding=0)
	hbox.pack_start(layout, expand=False, fill=False, padding=10)
    	hbox.pack_start(labelMode, expand=False, fill=False, padding=0)
    	self.cfg.table2.attach(hbox, 0, 26, 0, 3, xoptions=gtk.EXPAND, yoptions=gtk.FILL)
    	
	sw = gtk.ScrolledWindow()
	sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
	sw.add_with_viewport(vbox)
    	self.cfg.table2.attach(sw, 1, 28, 3, 40, yoptions=gtk.FILL)

        self.cfg.table2.attach(saveButton, 1, 9, 40, 42, xoptions=gtk.FILL, yoptions=gtk.SHRINK)
        self.cfg.table2.attach(closeButton, 19, 27, 40, 42, xoptions=gtk.FILL, yoptions=gtk.SHRINK)
        self.cfg.table2.show_all()
        
	if ( self.mode == "server" ):
	    self.callback(None, "server_changed")
	#
	self.buttonVncAutostart.connect("clicked", self.callback, "vnc_autostart")
	self.callback(None, "vnc_autostart")
	#
	self.buttonDemoVlc.connect("clicked", self.callback, "demo_vlc")
	self.callback(None, "demo_vlc")
	self.buttonDemoDirect.connect("clicked", self.callback, "demo_direct")
	self.callback(None, "demo_direct")
	self.buttonDemoVlcHttp.connect("clicked", self.callback, "demo_vlc_http")
	self.callback(None, "demo_vlc_http")

	self.buttonDemoVlcAudio.connect("clicked", self.callback, "demo_vlc_audio")
	self.callback(None, "demo_vlc_audio")

	self.comboDemoVlcVcodec.connect("changed", self.callback, "demo_vlc_vcodec")
	self.comboDemoVlcCaching.connect("changed", self.callback, "demo_vlc_caching")
	
	self.buttonDemoVlcClient.connect("clicked", self.callback, "demo_vlc_client")
	self.callback(None, "demo_vlc_client")
	
    def save(self, data=None):
	ip = self.entryIp.get_text()
	if ( self.mode == "server" and (ip in self.cfg.localhost) ):
	    pass
	else:
	    if ( validate("ip", ip ) == False ):
		self.cfg.status(_("Wrong")+" IP "+_("address"))
		return

	host_port = self.entryHostPort.get_text()
	if ( validate("port", host_port ) == False ):
	    self.cfg.status(_("Wrong")+" SSH "+_("Port"))
	    return
	    
	host_key = self.entryHostKey.get_text()
	if ( host_key == ""  ):
	    self.cfg.status(_("Wrong")+" "+_("SSH host key"))
	    return
	    
	timeout = self.entryTimeout.get_text()
	if ( validate("port", timeout ) == False ):
	    self.cfg.status(_("Wrong")+" "+_("Nmap timeout"))
	    return
	    
	vncport = self.entryVncPort.get_text()
	if ( validate("port", vncport ) == False ):
	    self.cfg.status(_("Wrong")+" VNC "+_("Port"))
	    return
	
	if ( self.client != "standalone" ):
	    server_key = self.entryServerKey.get_text()
	    if ( server_key == ""  ):
		self.cfg.status(_("Wrong")+" "+_("SSH server key"))
		return
	    
	    server_user = self.entryServerUser.get_text()
	    if ( validate("username", server_user ) == False ):
		self.cfg.status(_("Wrong")+" SSH "+_("User"))
		return

	    host_user = self.entryHostUser.get_text()
	    if ( validate("username", host_user ) == False ):
		self.cfg.status(_("Wrong")+" SSH "+_("User"))
		return

	    server_port = self.entryServerPort.get_text()
	    if ( validate("port", server_port ) == False ):
		self.cfg.status(_("Wrong")+" SSH "+_("Port"))
		return

	if ( self.mode != "server" ):
	    alias = self.entryAlias.get_text()
	    if ( alias == ""  ):
		self.cfg.status(_("Wrong")+" "+_("Alias"))
		return
	    user = self.entryUser.get_text()
	    if ( validate("username", user ) == False ):
		self.cfg.status(_("Wrong")+" "+_("User"))
		return
	    mac = self.entryMac.get_text()
	    if ( mac != "" and validate("mac", mac ) == False ):
		self.cfg.status(_("Wrong")+" MAC "+_("address"))
		return
	    display = self.entryDisplay.get_text()
	    if ( ":" not in display ):
		self.cfg.status(_("Wrong")+" "+_("Display number"))
		return
	    if ( validate("port", display.split(":")[1] ) == False ):
		self.cfg.status(_("Wrong")+" "+_("Display number"))
		return
	    host = self.entryHost.get_text()
	    desktop = self.comboDesktop.get_active_text()

	if ( self.mode == "standalone" ):
	    self.client_id = str(int(time.time()))
	    if ( find_tree(self.cfg, self.cfg.userList, client_id=self.client_id) ):
    		self.cfg.status(_("This user already is"))
    		return
    	    parent_iter = False
    	    model, rows = self.treeView.get_selection().get_selected_rows()
	    if ( rows != [] ):
		row = (rows[0][0],)
		group_name = self.cfg.userList[row][0]
		parent_iter = find_tree(self.cfg, self.cfg.userList, parent=group_name, group=True)
		if ( parent_iter ):
		    self.group = group_name
	    if ( parent_iter == False ):
		parent_iter = find_tree(self.cfg, self.cfg.userList, parent="standalone")
	    if ( parent_iter == False ):
		parent_iter = self.cfg.userList.prepend(None)
		self.cfg.userList.set(parent_iter, 0, "standalone")
	    iter = self.cfg.userList.append(parent_iter)
    
	elif ( self.mode == "client_info" ):
    	    row = find_tree(self.cfg, self.cfg.userList, client_id=self.client_id )
	    if ( row ):
		iter = self.cfg.userList.get_iter(row)
	    else:
    		parent_iter = find_tree(self.cfg, self.cfg.userList, parent=self.group)
		if ( parent_iter == False ):
		    parent_iter = self.cfg.userList.prepend(None)
		    self.cfg.userList.set(parent_iter, 0, self.group)
		iter = self.cfg.userList.append(parent_iter)
	    
	elif ( self.mode == "server" ):
	    alias = ip
    	    iter = find_tree(self.cfg, self.cfg.userList, parent=ip)
	    if ( iter ):
		if ( self.mode_edit == "server" ):
		    server_path = self.cfg.userList.get_path(iter)
		    child_iters = []
		    for x in range(self.cfg.userList.iter_n_children(iter)):
			iter_c = self.cfg.userList.get_iter((server_path[0],x))
			child_iters.append(iter_c)
		    for iter_c in child_iters:
			self.cfg.userList.remove(iter_c)
		else:
		    self.cfg.status(_("This server already is"))
		    return
	    else:
		iter = self.cfg.userList.append(None)
	
	dn = self.cfg.dn
	if ( self.group == "server" and self.mode != "server" ):
	    if ( user != alias or user != self.alias ):
		self.cfg.userList.set(iter, dn['alias'], alias)
		save_aliasList(self.cfg, user, self.server, alias)
	else:
	    self.cfg.userList.set(iter, dn['client_id'], self.client_id)
	    self.cfg.userList.set(iter, dn['alias'], alias)
	    self.cfg.userList.set(iter, dn['client'], self.client)
	    self.cfg.userList.set(iter, dn['host_port'], host_port)
	    self.cfg.userList.set(iter, dn['vnc_pass'], self.entryVncPassword.get_text())
	    self.cfg.userList.set(iter, dn['vnc_pass_file'], self.entryVncPasswordFile.get_text())
	    self.cfg.userList.set(iter, dn['vnc_command'], self.entryVncCommand.get_text())
	    self.cfg.userList.set(iter, dn['vnc_client'], self.entryVncClient.get_text())
	    self.cfg.userList.set(iter, dn['vnc_server'], self.entryVncServer.get_text())
	    self.cfg.userList.set(iter, dn['vnc_client_window'], self.entryVncClientWindow.get_text())
	    self.cfg.userList.set(iter, dn['vnc_server_window'], self.entryVncServerWindow.get_text())
	    self.cfg.userList.set(iter, dn['console_host'], self.entryConsoleHost.get_text())
	    self.cfg.userList.set(iter, dn['folder_user'], self.entryFolderUser.get_text())
	    self.cfg.userList.set(iter, dn['vnc_gtk_encoding'], self.comboVncGtkEncoding.get_active_text())
	    self.cfg.userList.set(iter, dn['vnc_gtk_color'], self.comboVncGtkColor.get_active_text())
	    self.cfg.userList.set(iter, dn['dhcp'], self.comboDhcp.get_active_text())
	    self.cfg.userList.set(iter, dn['vnc_autostart_command'], self.entryVncAutostartCommand.get_text())

	    self.cfg.userList.set(iter, dn['demo_vlc_fps'], self.comboDemoVlcFps.get_active_text())
	    self.cfg.userList.set(iter, dn['demo_vlc_vcodec'], self.comboDemoVlcVcodec.get_active_text())
	    self.cfg.userList.set(iter, dn['demo_vlc_scale_full'], self.comboDemoVlcScaleFull.get_active_text())
	    self.cfg.userList.set(iter, dn['demo_vlc_scale_window'], self.comboDemoVlcScaleWindow.get_active_text())
	    self.cfg.userList.set(iter, dn['demo_vlc_caching'], self.comboDemoVlcCaching.get_active_text())
	    self.cfg.userList.set(iter, dn['demo_vlc_client_command'], self.entryDemoVlcClientCommand.get_text())

	    if ( self.buttonOverServer.get_active() ):
	    	self.cfg.userList.set(iter, dn['over_server'], "True")
	    else:
	    	self.cfg.userList.set(iter, dn['over_server'], "False")
		
	    if ( self.buttonVncNormal.get_active() ):
		self.cfg.userList.set(iter, dn['vnc_normal'], "True")
	    else:
		self.cfg.userList.set(iter, dn['vnc_normal'], "False")
	    if ( self.buttonVncSsh.get_active() ):
		self.cfg.userList.set(iter, dn['vnc_ssh'], "True")
	    else:
		self.cfg.userList.set(iter, dn['vnc_ssh'], "False")

	    if ( self.buttonDemoVlc.get_active() ):
		self.cfg.userList.set(iter, dn['demo_vlc'], "True")
	    else:
		self.cfg.userList.set(iter, dn['demo_vlc'], "False")

	    if ( self.buttonDemoVlcRtp.get_active() ):
		self.cfg.userList.set(iter, dn['demo_vlc_rtp'], "True")
	    else:
		self.cfg.userList.set(iter, dn['demo_vlc_rtp'], "False")

	    if ( self.buttonDemoVlcAudio.get_active() ):
		self.cfg.userList.set(iter, dn['demo_vlc_audio'], "True")
	    else:
		self.cfg.userList.set(iter, dn['demo_vlc_audio'], "False")
	    
	    if ( self.buttonDemoSsh.get_active() ):
		self.cfg.userList.set(iter, dn['demo_ssh'], "True")
	    else:
		self.cfg.userList.set(iter, dn['demo_ssh'], "False")

	    if ( self.buttonDemoVlcClient.get_active() ):
	        self.cfg.userList.set(iter, dn['demo_vlc_client'], "True")
	    else:
	        self.cfg.userList.set(iter, dn['demo_vlc_client'], "False")
	    
	    if ( self.buttonVncGtkLossy.get_active() ):
		self.cfg.userList.set(iter, dn['vnc_gtk_lossy'], "True")
	    else:
		self.cfg.userList.set(iter, dn['vnc_gtk_lossy'], "False")

	    if ( self.buttonVncGtkPointer.get_active() ):
		self.cfg.userList.set(iter, dn['vnc_gtk_pointer'], "True")
	    else:
		self.cfg.userList.set(iter, dn['vnc_gtk_pointer'], "False")

	    if ( self.buttonVncGtkPointerGrab.get_active() ):
		self.cfg.userList.set(iter, dn['vnc_gtk_pointer_grab'], "True")
	    else:
		self.cfg.userList.set(iter, dn['vnc_gtk_pointer_grab'], "False")

	    if ( self.buttonVncGtkKeyboardGrab.get_active() ):
		self.cfg.userList.set(iter, dn['vnc_gtk_keyboard_grab'], "True")
	    else:
		self.cfg.userList.set(iter, dn['vnc_gtk_keyboard_grab'], "False")

	    if ( self.buttonShowLocalSessions.get_active() ):
		self.cfg.userList.set(iter, dn['show_local_sessions'], "True")
	    else:
		self.cfg.userList.set(iter, dn['show_local_sessions'], "False")

	    if ( self.buttonDynamicUser.get_active() ):
		self.cfg.userList.set(iter, dn['dynamic_user'], "True")
	    else:
		self.cfg.userList.set(iter, dn['dynamic_user'], "False")

	    if ( self.buttonDhcpArp.get_active() ):
		self.cfg.userList.set(iter, dn['dhcp_arp'], "True")
	    else:
		self.cfg.userList.set(iter, dn['dhcp_arp'], "False")

	    if ( self.buttonVncAutostart.get_active() ):
	        self.cfg.userList.set(iter, dn['vnc_autostart'], "True")
	    else:
	        self.cfg.userList.set(iter, dn['vnc_autostart'], "False")
	    
	    if ( self.buttonVncNxThin.get_active() ):
	        self.cfg.userList.set(iter, dn['vnc_nx_thin'], "True")
	    else:
	        self.cfg.userList.set(iter, dn['vnc_nx_thin'], "False")
	    
	    if ( self.buttonVncNxScan.get_active() ):
	        self.cfg.userList.set(iter, dn['vnc_nx_scan'], "True")
	    else:
	        self.cfg.userList.set(iter, dn['vnc_nx_scan'], "False")
	    
	    if ( self.buttonVncNxAutostart.get_active() ):
	        self.cfg.userList.set(iter, dn['vnc_nx_autostart'], "True")
	    else:
	        self.cfg.userList.set(iter, dn['vnc_nx_autostart'], "False")
	    
	    self.cfg.userList.set(iter, dn['timeout'], timeout)
	    self.cfg.userList.set(iter, dn['vncport'], vncport)
	    self.cfg.userList.set(iter, dn['host_key'], host_key)
	    self.cfg.userList.set(iter, dn['ssh_key_root'], self.entrySshKeyRoot.get_text())
	    if ( self.client == "standalone" ):
		self.cfg.userList.set(iter, dn['server_key'], host_key)
		self.cfg.userList.set(iter, dn['server_port'], host_port)
		self.cfg.userList.set(iter, dn['server_user'], user)
		self.cfg.userList.set(iter, dn['server'], ip)
		self.cfg.userList.set(iter, dn['host_user'], user)
		self.cfg.userList.set(iter, dn['console_server'], self.entryConsoleHost.get_text())
	    else:
		self.cfg.userList.set(iter, dn['server_key'], server_key)
		self.cfg.userList.set(iter, dn['server_port'], server_port)
		self.cfg.userList.set(iter, dn['server_user'], server_user)
		self.cfg.userList.set(iter, dn['server'], self.server)
		self.cfg.userList.set(iter, dn['host_user'], host_user)
		self.cfg.userList.set(iter, dn['console_server'], self.entryConsoleServer.get_text())
	    if ( self.mode != "server" ):
		self.cfg.userList.set(iter, dn['user'], user)
		self.cfg.userList.set(iter, dn['host'], host)
		self.cfg.userList.set(iter, dn['ip'], ip)
		self.cfg.userList.set(iter, dn['display'], display)
		self.cfg.userList.set(iter, dn['mac'], mac)
		self.cfg.userList.set(iter, dn['desktop'], desktop)
		self.cfg.userList.set(iter, dn['group'], self.group)
		
	    # Сохранить
	    save_userList(self.cfg)
	    
	    # Обновить сервер в списке
	    if ( self.mode == "server" ):
		thread_server_group = thread_gfunc(self.cfg, False, True, create_tree_server_group, self.cfg, iter)
		thread_server_group.start()

	# Раскрыть и выделить в дереве позицию
	row = self.cfg.userList.get_path(iter)
    	self.treeView.scroll_to_cell(row, None, use_align=True, row_align=0.5, col_align=0.0)
    	self.treeView.expand_to_path(row)
    	self.treeView.get_selection().unselect_all()
    	self.treeView.get_selection().select_path(row)

    def callback(self, widget=None, data1=None, data2=None):
	if ( data1 == "vnc_autostart" ):
	    if ( self.group == "server" and self.mode == "client_info" ):
		return
	    if ( self.buttonVncAutostart.get_active() == True ):
    	        self.buttonOverServer.set_sensitive(False)
    		self.buttonVncNormal.set_sensitive(False)
    		self.buttonVncSsh.set_sensitive(False)
    	    	self.buttonOverServer.set_active(False)
    		self.buttonVncNormal.set_active(False)
    		self.buttonVncSsh.set_active(True)
    	    else:
    		self.buttonOverServer.set_sensitive(True)
    		self.buttonVncNormal.set_sensitive(True)
    		self.buttonVncSsh.set_sensitive(True)
    		
	if ( data1 == "server_changed"):
	    if ( self.entryIp.get_text() in self.cfg.localhost ):
		self.entryServerUser.set_editable(False)
		self.buttonOverServer.set_sensitive(False)
	    else:
		self.entryServerUser.set_editable(True)
		self.buttonOverServer.set_sensitive(True)
	if ( data1 == "dhcp_changed"):
	    if ( self.comboDhcp.get_active_text() == "dynamic" ):
    		self.buttonDhcpArp.set_active(False)
    		self.buttonDhcpArp.set_sensitive(True)
    	    else:
    		if ( self.client == "standalone" ):
    		    self.buttonDhcpArp.set_active(False)
    		else:
    		    self.buttonDhcpArp.set_active(True)
    		self.buttonDhcpArp.set_sensitive(False)

	if ( data1 == "demo_direct" ):
	    if ( self.buttonDemoVlc.get_active() == True and self.buttonDemoVlcRtp.get_active() == True ):
		self.buttonDemoDirect.set_active(True)
	    
	if ( data1 == "demo_vlc" ):
	    if ( self.group == "server" and self.mode == "client_info" ):
		return
	    if ( self.buttonDemoVlc.get_active() == True ):
		self.buttonDemoVlcHttp.set_sensitive(True)
		self.buttonDemoVlcRtp.set_sensitive(True)
		self.buttonDemoVlcAudio.set_sensitive(True)
		self.comboDemoVlcFps.set_sensitive(True)
		self.comboDemoVlcVcodec.set_sensitive(True)
		self.comboDemoVlcScaleFull.set_sensitive(True)
		self.comboDemoVlcScaleWindow.set_sensitive(True)
		self.comboDemoVlcCaching.set_sensitive(True)
		self.entryVncServer.set_sensitive(False)
		self.entryVncServerWindow.set_sensitive(False)
		#
		if ( self.buttonDemoVlcRtp.get_active() == True ):
		    self.buttonDemoDirect.set_active(True)
		    self.buttonDemoDirect.set_sensitive(False)
		    self.buttonDemoSsh.set_sensitive(False)
	    else:
		self.buttonDemoVlcHttp.set_sensitive(False)
		self.buttonDemoVlcRtp.set_sensitive(False)
		self.buttonDemoVlcAudio.set_sensitive(False)
		self.comboDemoVlcFps.set_sensitive(False)
		self.comboDemoVlcVcodec.set_sensitive(False)
		self.comboDemoVlcScaleFull.set_sensitive(False)
		self.comboDemoVlcScaleWindow.set_sensitive(False)
		self.comboDemoVlcCaching.set_sensitive(False)
		self.entryVncServer.set_sensitive(True)
		self.entryVncServerWindow.set_sensitive(True)
		#
		self.buttonDemoDirect.set_sensitive(True)
		self.buttonDemoSsh.set_sensitive(True)

	if ( data1 == "demo_vlc_http" ):
	    if ( self.group == "server" and self.mode == "client_info" ):
		return
	    if ( self.buttonDemoVlc.get_active() == True and self.buttonDemoVlcRtp.get_active() == True ):
		self.buttonDemoDirect.set_active(True)
		self.buttonDemoDirect.set_sensitive(False)
		self.buttonDemoSsh.set_sensitive(False)
		vcodec = self.comboDemoVlcVcodec.get_active_text()
		if ( vcodec == "wmv1" or vcodec == "wmv2" or vcodec == "mjpg" ):
		    self.comboDemoVlcVcodec.set_active(0)
	    else:
		self.buttonDemoDirect.set_sensitive(True)
		self.buttonDemoSsh.set_sensitive(True)

	if ( data1 == "demo_vlc_audio" ):
	    if ( self.buttonDemoVlcAudio.get_active() == True ):
		if ( int(self.comboDemoVlcCaching.get_active_text()) < 1000 ):
		    self.comboDemoVlcCaching.set_active(1)
		if ( int(self.comboDemoVlcFps.get_active_text()) > 5 ):
		    self.comboDemoVlcFps.set_active(0)
	
	if ( data1 == "demo_vlc_caching" ):
	    if ( self.buttonDemoVlcAudio.get_active() == True ):
		if ( int(self.comboDemoVlcCaching.get_active_text()) < 1000 ):
		    self.comboDemoVlcCaching.set_active(1)
	
	if ( data1 == "demo_vlc_vcodec" ):
	    if ( self.buttonDemoVlcRtp.get_active() == True ):
		vcodec = self.comboDemoVlcVcodec.get_active_text()
		if ( vcodec == "wmv1" or vcodec == "wmv2" or vcodec == "mjpg" ):
	    	    self.comboDemoVlcVcodec.set_active(0)

	if ( data1 == "demo_vlc_client" ):
	    if ( self.buttonDemoVlcClient.get_active() == True ):
		self.entryDemoVlcClientCommand.set_sensitive(True)
	    else:
		self.entryDemoVlcClientCommand.set_sensitive(False)
		
    def combo_separator(self, model, iter):
	if ( model.get_value(iter, 0) == "-" ):
	    return True

####################################################################################################

class hwinfoUi:

    def __init__(self, cfg, user_list, mode=None):

	if ( user_list == [] and not mode ):
	    return
	
	self.cfg = cfg
	self.user_list = user_list
	
        self.textview = gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_sensitive(False)
        color = self.textview.get_style().copy().base[gtk.STATE_NORMAL]
	self.textview.modify_base(gtk.STATE_INSENSITIVE, color)

	self.buffer = self.textview.get_buffer()

        self.sw = gtk.ScrolledWindow()
	self.sw.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_ALWAYS)
        self.sw.add(self.textview)

        closeButton = image_button(self.cfg.pixbuf_action_close_16, _("Close"))
	closeButton.connect("clicked", close_window2, self.cfg)
	closeButton.set_size_request(120, 26)

	create_window2(self.cfg)

	frame = gtk.Frame()
	frame2 = gtk.Frame()
        cfg.table2.attach(frame, 0, 28, 0, 39)
	cfg.table2.attach(self.sw, 1, 28, 1, 39)
        cfg.table2.attach(frame2, 0, 28, 39, 42)
        cfg.table2.attach(closeButton, 21, 27, 40, 42, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

	if ( mode == "log" ):
    	    clearButton = image_button(self.cfg.pixbuf_list_clear_16, _("Clear"))
	    clearButton.connect("clicked", self.clear_log)
	    clearButton.set_size_request(120, 26)
    	    cfg.table2.attach(clearButton, 1, 7, 40, 42, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
    	    self.log()
        else:
    	    thread_hwinfo = thread_gfunc(self.cfg, True, True, self.hwinfo)
	    thread_hwinfo.start()
	cfg.table2.show_all()

    def log(self):
	self.textview.connect('size-allocate', self.textview_changed)
    	self.buffer.set_text(self.cfg.read_log())
        self.textview.set_sensitive(True)

    def clear_log(self, data=None):
	self.cfg.clear_log()
	self.buffer.set_text("")
	
    def textview_changed(self, widget, event, data=None):
    	adj = self.sw.get_vadjustment()
    	adj.set_value(adj.upper - adj.page_size)
	    
    def hwinfo(self):
	for line in self.user_list:
	    # проверять по одному, иначе 'over Server' долго
	    z = check_user_list(self.cfg, [line], "ssh")
	    if ( z == [] ):
		continue
	    d = {}
	    for key, value in zip(self.cfg.z, z[0]):
		d[key] = value

	    # NX hosts
    	    if ( d['client'] == "nx" ):
    	    	host = ""

    	    ssh = self.cfg.ssh_command(d['host_key'], d['host_port'], d['host_user'], d['ip'])
    	    if ( (d['server'] not in self.cfg.localhost) and d['over_server'] == "True" ):
    	    	    # туннель для SSH
	    	    local_port = ssh_tunnel(self.cfg, d['server_key'], d['server_port'], d['server_user'], d['server'], d['ip'], d['host_port'])
	    	    if ( local_port == "0" ): continue
    	    	    ssh = self.cfg.ssh_command(d['host_key'], local_port, d['host_user'], "127.0.0.1")
    		
	    bios = "dmidecode --type bios | grep -E \"BIOS Inf|Vendor|Version|Release\""
	    baseboard = "dmidecode --type baseboard | grep -E \"Board Inf|Manufacturer|Name|Version\""
	    processor = "dmidecode --type processor | grep -E \"Processor Inf|Socket Des|Version|Current\""
	    memory="dmidecode --type memory | grep -E \"Module Inf|Installed Size\""
    	    vga = "lspci -nn | grep VGA | cut -d: -f 3,4"
	    audio = "lspci -nn | grep -E \"audio|Audio\" | cut -d: -f 3,4"
	    ethernet = "lspci -nn | grep Ethernet | cut -d: -f 3,4"
	    #info = popen_os(ssh+" '"+bios+" ; "+baseboard+" ; "+processor+" ; \
	    #	"+memory+" ; echo Video card ; echo -e \"\\t\" \\\"`"+vga+"`\\\" ; echo Sound card ; \
	    #	echo -e \"\\t\" \\\"`"+audio+"`\\\" ; echo Ethernet controller ; echo -e \"\\t\" \\\"`"+ethernet+"`\\\" '").readlines()
	
	    command = bios+" ; "+baseboard+" ; "+processor+" ; \
		"+memory+" ; echo Video card ; echo -e \"\\t\" \\\"`"+vga+"`\\\" ; echo Sound card ; \
		echo -e \"\\t\" \\\"`"+audio+"`\\\" ; echo Ethernet controller ; echo -e \"\\t\" \\\"`"+ethernet+"`\\\"" 
	    cmd = ssh+command
	    proc = popen_sub(self.cfg, cmd.split())
	    if ( proc == False ):
    		info = ""
    	    else:
		info = proc.stdout.readlines()
	    
	    # xdpyinfo | grep 'dimensions:'|awk '{print $2}
	    ssh = self.cfg.ssh_command(d['server_key'], d['server_port'], d['user'], d['server'])
	    command = "export DISPLAY="+d['display']+".0; xrandr | grep \\\*"
	    cmd = ssh+command
	    proc = popen_sub(self.cfg, cmd.split())
	    if ( proc == False ):
    		res = ""
    	    else:
    		res = proc.stdout.readline()
    		if ( res != [] ):
		    res = "\t"+res.strip("\n")
		else:
		    res = ""

	    gtk.gdk.threads_enter()
	    try:
    		group = d['group']
    		if ( group == "server" ):
    		    group = d['server']
    		self.buffer.insert(self.buffer.get_end_iter(), "\n"+d['alias']+", "+group+", "+d['ip']+"\n\n")
		for line in info:
		    line = line.replace('\"', '')
		    self.buffer.insert(self.buffer.get_end_iter(), line)
		self.buffer.insert(self.buffer.get_end_iter(), "Current Resolution\n"+res)
		self.buffer.insert(self.buffer.get_end_iter(), "\n__________________________________________________________\n")
	    finally:
		gtk.gdk.threads_leave()
	gtk.gdk.threads_enter()
        self.textview.set_sensitive(True)
	gtk.gdk.threads_leave()

####################################################################################################

class processUi:

    def __init__(self, cfg, user_list):

	user_list = check_user_list(cfg, user_list, "empty")
	if ( user_list == [] ):
	    return

	self.cfg = cfg
	self.user_list = user_list

	# user,pid,command,mem,start,
	# args,ssh_server_key,ssh_server_port,ssh_server_user,server
	self.process_list = gtk.ListStore(
	    str,str,str,str,
	    str,str,\
	    str,str,str,str,str)
	tree = gtk.TreeView(self.process_list)
	tree.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_VERTICAL)
	tree.set_rules_hint(True)
        create_columns(cfg, tree, [_("User"), "PID", _('Command'), _("Time"), "VmRss,Kb", "VmSize,Kb", "args"], True)

	self.treeSelection = tree.get_selection()
	self.treeSelection.set_mode(gtk.SELECTION_MULTIPLE)

	sw = gtk.ScrolledWindow()
	sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
	sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
	sw.add(tree)

	self.create_process_list()

        refreshButton = image_button(self.cfg.pixbuf_action_refresh_16, _("Refresh"))
	refreshButton.connect("clicked", self.create_process_list)
	refreshButton.set_size_request(120, 26)

        killButton = image_button(self.cfg.pixbuf_list_remove_16, _("Kill"))
	killButton.connect("clicked", self.killProcess)
	killButton.set_size_request(120, 26)

        closeButton = image_button(self.cfg.pixbuf_action_close_16, _("Close"))
	closeButton.connect("clicked", close_window2, self.cfg)
	closeButton.set_size_request(120, 26)

	create_window2(self.cfg)

	frame = gtk.Frame()
        self.cfg.table2.attach(sw, 0, 28, 0, 39)
        self.cfg.table2.attach(frame, 0, 28, 39, 42)
        self.cfg.table2.attach(refreshButton, 1, 8, 40, 42, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        self.cfg.table2.attach(killButton, 9, 16, 40, 42, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        self.cfg.table2.attach(closeButton, 21, 27, 40, 42, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

	self.cfg.table2.show_all()

    def create_process_list(self, data=None):
	thread = thread_gfunc(self.cfg, True, True, self.create_process_list_t)
	thread.start()

    def create_process_list_t(self, data=None):

        self.process_list.clear()
    	i = -1
    	sort_list = []
    	users = ""
	server_key = ""
	server_port = ""
	server_user = ""
    	server = ""
    	
    	# сортировка по серверу и отправка сборками
    	self.user_list.sort(key=lambda tup: tup[4])
    	for z in self.user_list:
	    d = {}
	    for key, value in zip(self.cfg.z, z):
		d[key] = value

    	    if ( (server_key != d['server_key'] or server_port != d['server_port'] or\
    		server_user != d['server_user'] or server != d['server']) and\
    		server_key != "" and server_port != "" and server_user != "" and server != "" ):
    		self.ps_os(users[:-1], server_key, server_port, server_user, server)
    		users = ""
	    server_key = d['server_key']
	    server_port = d['server_port']
	    server_user = d['server_user']
    	    server = d['server']
	    users = users+d['user']+","
    	self.ps_os(users[:-1], server_key, server_port, server_user, server)

    def ps_os(self, users, server_key, server_port, server_user, server):
    	if ( server in self.cfg.localhost ):
    	    ssh = ""
    	else:
    	    ssh = self.cfg.ssh_command(server_key, server_port, server_user, server)

	cmd = ssh+self.cfg.ps_command+"-o user,comm,pid,start_time,rssize,vsz,args -u "+users+" --sort user,args"
	proc = popen_sub(self.cfg, cmd.split())
	if ( proc == False ):
	    return "0"
	out = proc.stdout.readlines()
	
    	for x in out:
	    if ( "PID" in x ):
		continue
    	    lineParts = string.split(x)
    	    user = lineParts[0]
    	    comm = lineParts[1]
    	    pid = lineParts[2]
    	    start = lineParts[3]
    	    rssize = lineParts[4]
    	    vsz = lineParts[5]
    	    args = lineParts[6]
    	    
    	    gtk.gdk.threads_enter()
	    try:
        	self.process_list.append([user, pid, comm, start, rssize, vsz, args, server_key, server_port, server_user, server])
    	    finally:
		gtk.gdk.threads_leave()
    
    def killProcess(self, data=None):
        model, rows = self.treeSelection.get_selected_rows()
        if ( rows == [] ):
    	    return
        for row in rows:
    	    user = model[row][0]
    	    pid = model[row][1]
    	    server_key = model[row][7]
    	    server_port = model[row][8]
    	    server_user = model[row][9]
    	    server = model[row][10]
    	    ssh = self.cfg.ssh_command(server_key, server_port, user, server)
    	    cmd = ssh+" kill -9 "+pid+" &"
    	    proc = popen_sub(self.cfg, cmd.split())
	self.create_process_list()

####################################################################################################

class settings:

    def __init__(self, cfg):

	self.cfg = cfg
	create_window2(self.cfg)

        self.notebookSettings = gtk.Notebook()
        self.notebookSettings.set_tab_pos(gtk.POS_TOP)
        self.cfg.table2.attach(self.notebookSettings, 0,28,0,40)
        self.notebookSettings.show()
        self.show_tabs = True
        self.show_border = True

        saveButton = image_button(self.cfg.pixbuf_list_save_16, _("Save"))
	saveButton.connect("clicked", self.callback, "save")
	saveButton.set_size_request(120, 26)
        self.cfg.table2.attach(saveButton, 1, 7, 40, 42, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

        closeButton = image_button(self.cfg.pixbuf_action_close_16, _("Close"))
	closeButton.connect("clicked", self.callback, "close")
	closeButton.set_size_request(120, 26)
        self.cfg.table2.attach(closeButton, 21, 27, 40, 42, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

        ####################
	# vnc
        ####################
        label = gtk.Label(_("VNC"))
	table = gtk.Table(38, 28, True)
        self.notebookSettings.append_page(table, label)
	
	# vncBox
        self.buttonVncBox = gtk.CheckButton(_("Viewer")+" / "+_("Control")+" - "+_("Embed in interface"))
	self.buttonVncBox.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.vncGtk == "y" ):
	    self.buttonVncBox.set_active(True)

        self.buttonVncInsert = gtk.CheckButton(_("Do not clear the area, add/move to the beginning"))
	self.buttonVncInsert.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.read_config("vnc","vnc_thumbnails_insert") == "y" ):
	    self.buttonVncInsert.set_active(True)

        self.buttonVncBoxReduce = gtk.CheckButton(_("Reduce(proportional) to the size of the area"))
	self.buttonVncBoxReduce.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.read_config("vnc","vnc_thumbnails_reduce") == "y" ):
	    self.buttonVncBoxReduce.set_active(True)

        self.buttonVncScroll = gtk.CheckButton(_("Automatic scrolling when adding/editing"))
	self.buttonVncScroll.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.read_config("vnc","vnc_thumbnails_scroll") == "y" ):
	    self.buttonVncScroll.set_active(True)

        self.buttonVncMinimize = gtk.CheckButton(_("Minimize the open when adding a new"))
	self.buttonVncMinimize.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.read_config("vnc","vnc_thumbnails_minimize") == "y" ):
	    self.buttonVncMinimize.set_active(True)

        label = gtk.Label(_("VNC"))
        self.scaleVncMinX = gtk.HScale()
        self.scaleVncMinX.set_value_pos(gtk.POS_LEFT)
        self.scaleVncMinX.set_digits(0)
        self.scaleVncMinX.set_range(200, 640)
        self.scaleVncMinX.set_value(float(self.cfg.vncThumbnailsX))
        
        self.scaleVncMinY = gtk.HScale()
        self.scaleVncMinY.set_value_pos(gtk.POS_LEFT)
        self.scaleVncMinY.set_digits(0)
        self.scaleVncMinY.set_range(160, 480)
        self.scaleVncMinY.set_value(float(self.cfg.vncThumbnailsY))
	
        self.scaleVncMaxX = gtk.HScale()
        self.scaleVncMaxX.set_value_pos(gtk.POS_LEFT)
        self.scaleVncMaxX.set_digits(0)
        self.scaleVncMaxX.set_range(640, 1920)
        self.scaleVncMaxX.set_value(float(self.cfg.vncGtkX))
        
        self.scaleVncMaxY = gtk.HScale()
        self.scaleVncMaxY.set_value_pos(gtk.POS_LEFT)
        self.scaleVncMaxY.set_digits(0)
        self.scaleVncMaxY.set_range(480, 1080)
        self.scaleVncMaxY.set_value(float(self.cfg.vncGtkY))
	
	# connect
        self.scaleVncMinX.connect("change-value", self.callback, "vnc_min_x")
        self.scaleVncMaxX.connect("change-value", self.callback, "vnc_max_x")

	self.buttonThumbUp = gtk.CheckButton(_("Upstairs"))
	self.buttonThumbUp.unset_flags(gtk.CAN_FOCUS)
	if ( "up" in self.cfg.vncThumbnailsToolbar ):
	    self.buttonThumbUp.set_active(True)	

	self.buttonThumbScreenshot = gtk.CheckButton(_("Screenshot"))
	self.buttonThumbScreenshot.unset_flags(gtk.CAN_FOCUS)
	if ( "screenshot" in self.cfg.vncThumbnailsToolbar ):
	    self.buttonThumbScreenshot.set_active(True)	

	self.buttonThumbConnect = gtk.CheckButton(_("Connect"))
	self.buttonThumbConnect.unset_flags(gtk.CAN_FOCUS)
	if ( "connect" in self.cfg.vncThumbnailsToolbar ):
	    self.buttonThumbConnect.set_active(True)	

        self.labelVncShotFolder = gtk.Label(_("The screenshot folder"))
	self.labelVncShotFolder.set_alignment(0.0,0.5)
	self.entryVncShotFolder = gtk.Entry()
	self.entryVncShotFolder.set_text( self.cfg.vncShotFolder )
        self.fileChooserShotFolder = image_button(self.cfg.pixbuf_list_folder_add_16)
        self.fileChooserShotFolder.connect("clicked", file_chooser_dialog, self.entryVncShotFolder, _("Select the folder"), None, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
	# attach
        frame = gtk.Frame()
        table.attach(frame, 0, 28, 0, 38)

        frame = gtk.Frame()
        frame.set_label_align(0.5, 0.5)
        table.attach(frame, 1, 27, 1, 22)
        table.attach(self.buttonVncBox, 2, 26, 2, 4, yoptions=gtk.SHRINK)
        table.attach(self.buttonVncInsert, 2, 26, 4, 6, yoptions=gtk.SHRINK)
        table.attach(self.buttonVncBoxReduce, 2, 26, 6, 8, yoptions=gtk.SHRINK)
        table.attach(self.buttonVncScroll, 2, 26, 8, 10, yoptions=gtk.SHRINK)
        table.attach(self.buttonVncMinimize, 2, 26, 10, 12, yoptions=gtk.SHRINK)
        label = gtk.Label(_("Min"))
        label.set_alignment(0.0,0.5)
        table.attach(label, 2, 4, 13, 15, yoptions=gtk.SHRINK)
        table.attach(self.scaleVncMinX, 4, 26, 12, 14, yoptions=gtk.SHRINK)
        table.attach(self.scaleVncMinY, 4, 26, 14, 16, yoptions=gtk.SHRINK)
        label = gtk.Label(_("Max"))
        label.set_alignment(0.0,0.5)
        table.attach(label, 2, 4, 17, 19, yoptions=gtk.SHRINK)
        table.attach(self.scaleVncMaxX, 4, 26, 16, 18, yoptions=gtk.SHRINK)
        table.attach(self.scaleVncMaxY, 4, 26, 18, 20, yoptions=gtk.SHRINK)

        frame = gtk.Frame(_("Toolbar"))
        frame.set_label_align(0.5, 0.5)
        table.attach(frame, 1, 27, 23, 31)
        table.attach(self.buttonThumbConnect, 2, 14, 24, 26, yoptions=gtk.SHRINK)
        table.attach(self.buttonThumbScreenshot, 2, 14, 26, 28, yoptions=gtk.SHRINK)
        table.attach(self.buttonThumbUp, 14, 26, 24, 26, yoptions=gtk.SHRINK)

        frame = gtk.Frame()
        table.attach(frame, 1, 27, 35, 37)
        table.attach(self.labelVncShotFolder, 2, 12, 35, 37, yoptions=gtk.SHRINK)
        table.attach(self.entryVncShotFolder, 12, 24, 35, 37, yoptions=gtk.SHRINK)
        table.attach(self.fileChooserShotFolder, 24, 26, 35, 37, yoptions=gtk.SHRINK)

        ####################
	# Locally
        ####################
	label = gtk.Label(_("Locally"))
	table = gtk.Table(38, 28, True)
        self.notebookSettings.append_page(table, label)
        
	if ( self.cfg.localhost[len(self.cfg.localhost)-1] != "" ):
	    labelLocalIp = gtk.Label("IP "+_("address")+" ("+_("found")+" "+self.cfg.localhost[len(self.cfg.localhost)-1]+")")
	else:
	    labelLocalIp = gtk.Label("IP "+_("address")+" ("+_("not found")+")")
	labelLocalIp.set_alignment(0.0,0.5)
	self.entryLocalIp = gtk.Entry()
	self.entryLocalIp.set_text(self.cfg.localIp)

	vbox = gtk.VBox(False, 0)

	self.buttonDemoVlc = gtk.RadioButton(None, _("Video streaming")+"(VLC)")
	self.buttonDemoVlc.unset_flags(gtk.CAN_FOCUS)
	fixed = gtk.Fixed()
	label = gtk.Label(_("Server type"))
	fixed.put(label, 20, 0)
	fixed.put(self.buttonDemoVlc, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	self.buttonDemoVnc = gtk.RadioButton(self.buttonDemoVlc, _("VNC"))
	self.buttonDemoVnc.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.demoVlc != "y" ):
	    self.buttonDemoVnc.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonDemoVnc, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	self.buttonDemoDirect = gtk.RadioButton(None, _("Direct"))
	self.buttonDemoDirect.unset_flags(gtk.CAN_FOCUS)
	fixed = gtk.Fixed()
	label = gtk.Label(_("Connection of clients"))
	fixed.put(label, 20, 0)
	fixed.put(self.buttonDemoDirect, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	self.buttonDemoSsh = gtk.RadioButton(self.buttonDemoDirect, _("VNC/HTTP over SSH"))
	self.buttonDemoSsh.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.demoSsh == "y" ):
	    self.buttonDemoSsh.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonDemoSsh, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	
	# VLC
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	label = gtk.Label(_("Video streaming"))
	vbox.pack_start(label, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	###
	###
	self.buttonDemoVlcHttp = gtk.RadioButton(None, "HTTP")
	self.buttonDemoVlcHttp.unset_flags(gtk.CAN_FOCUS)
	fixed = gtk.Fixed()
	fixed.put(self.buttonDemoVlcHttp, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	self.buttonDemoVlcRtp = gtk.RadioButton(self.buttonDemoVlcHttp, "RTP (multicast 239.0.0.1)")
	self.buttonDemoVlcRtp.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.demoVlcRtp in self.cfg.true ):
	    self.buttonDemoVlcRtp.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonDemoVlcRtp, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	###
	self.buttonDemoVlcAudio = gtk.CheckButton(_("Audio")+" ("+_("only")+" PulseAudio)")
	self.buttonDemoVlcAudio.unset_flags(gtk.CAN_FOCUS)
	#if ( self.cfg.demoVlcAudio in self.cfg.true ):
	#    self.buttonDemoVlcAudio.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonDemoVlcAudio, 210, 0)
	#vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	label = gtk.Label(_("Frames per second"))
	label.set_alignment(0, 0.5)
	self.comboDemoVlcFps = gtk.combo_box_new_text()
	self.comboDemoVlcFps.set_size_request(175, 26)
    	self.comboDemoVlcFps.append_text("5")
    	self.comboDemoVlcFps.append_text("10")
    	self.comboDemoVlcFps.append_text("15")
    	self.comboDemoVlcFps.append_text("24")
    	self.comboDemoVlcFps.append_text("30")
    	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.comboDemoVlcFps, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	model = self.comboDemoVlcFps.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == self.cfg.demoVlcFps ):
	        self.comboDemoVlcFps.set_active(item)
	        break

	###
	label = gtk.Label(_("Video codec"))
	label.set_alignment(0, 0.5)
	self.comboDemoVlcVcodec = gtk.combo_box_new_text()
	self.comboDemoVlcVcodec.set_size_request(175, 26)
    	self.comboDemoVlcVcodec.append_text("mp1v")
    	self.comboDemoVlcVcodec.append_text("mp2v")
    	self.comboDemoVlcVcodec.append_text("mpgv")
    	self.comboDemoVlcVcodec.append_text("wmv1")
    	self.comboDemoVlcVcodec.append_text("wmv2")
    	self.comboDemoVlcVcodec.append_text("mjpg")
    	#self.comboDemoVlcVcodec.append_text("h264")
    	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.comboDemoVlcVcodec, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	model = self.comboDemoVlcVcodec.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == self.cfg.demoVlcVcodec ):
	        self.comboDemoVlcVcodec.set_active(item)
	        break

	###
	label = gtk.Label(_("Resolution")+" ("+_("in full screen")+")")
	label.set_alignment(0, 0.5)
	self.comboDemoVlcScaleFull = gtk.combo_box_new_text()
	self.comboDemoVlcScaleFull.set_row_separator_func(self.combo_separator)
	self.comboDemoVlcScaleFull.set_size_request(175, 26)
	for x in self.cfg.scale_list:
    	    self.comboDemoVlcScaleFull.append_text(x)
    	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.comboDemoVlcScaleFull, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	model = self.comboDemoVlcScaleFull.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == self.cfg.demoVlcScaleFull ):
	        self.comboDemoVlcScaleFull.set_active(item)
	        break

	###
	label = gtk.Label(_("Resolution")+" ("+_("in window")+")")
	label.set_alignment(0, 0.5)
	self.comboDemoVlcScaleWindow = gtk.combo_box_new_text()
	self.comboDemoVlcScaleWindow.set_row_separator_func(self.combo_separator)
	self.comboDemoVlcScaleWindow.set_size_request(175, 26)
	for x in self.cfg.scale_list:
    	    self.comboDemoVlcScaleWindow.append_text(x)
    	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.comboDemoVlcScaleWindow, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	model = self.comboDemoVlcScaleWindow.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == self.cfg.demoVlcScaleWindow ):
	        self.comboDemoVlcScaleWindow.set_active(item)
	        break
	
	###
	label = gtk.Label(_("Caching"))
	label.set_alignment(0, 0.5)
	self.comboDemoVlcCaching = gtk.combo_box_new_text()
	self.comboDemoVlcCaching.set_size_request(175, 26)
    	self.comboDemoVlcCaching.append_text("300")
    	self.comboDemoVlcCaching.append_text("1000")
    	self.comboDemoVlcCaching.append_text("2000")
    	self.comboDemoVlcCaching.append_text("3000")
    	self.comboDemoVlcCaching.append_text("5000")
    	self.comboDemoVlcCaching.append_text("10000")
    	fixed = gtk.Fixed()
    	fixed.put(label, 20, 0)
	fixed.put(self.comboDemoVlcCaching, 210, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)
	model = self.comboDemoVlcCaching.get_model()
	for item in range(len(model)):
	    if ( model[item][0] == self.cfg.demoVlcCaching ):
	        self.comboDemoVlcCaching.set_active(item)
	        break

	# VNC
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)
	label = gtk.Label(_("VNC"))
	vbox.pack_start(label, expand=False, fill=False, padding=0)
	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)

	self.entryVncServer = label_entry(_("Server command"), self.cfg.vncServer, 24, 200, 20, 210, True)
	vbox.pack_start(self.entryVncServer, expand=False, fill=False, padding=0)

	self.entryVncServerWindow = label_entry(_("Server command")+"("+_("in window")+")", self.cfg.vncServerWindow, 24, 200, 20, 210, True)
	vbox.pack_start(self.entryVncServerWindow, expand=False, fill=False, padding=0)
	
	# connect
        self.buttonDemoVlc.connect("clicked", self.callback, "demo_vlc")
        self.callback(None,"demo_vlc")
        self.buttonDemoDirect.connect("clicked", self.callback, "demo_direct")
        self.callback(None,"demo_direct")
	self.buttonDemoVlcHttp.connect("clicked", self.callback, "demo_vlc_http")
	self.callback(None, "demo_vlc_http")

	self.buttonDemoVlcAudio.connect("clicked", self.callback, "demo_vlc_audio")
	self.callback(None, "demo_vlc_audio")
	
	self.comboDemoVlcVcodec.connect("changed", self.callback, "demo_vlc_vcodec")
	self.comboDemoVlcCaching.connect("changed", self.callback, "demo_vlc_caching")

	# attach
        frame = gtk.Frame()
        table.attach(frame, 0, 28, 0, 38)

        frame = gtk.Frame()
        table.attach(frame, 1, 27, 2, 4)
        table.attach(labelLocalIp, 2, 15, 2, 4, yoptions=gtk.SHRINK)
        table.attach(self.entryLocalIp, 15, 26, 2, 4, yoptions=gtk.SHRINK)
	
        frame = gtk.Frame(_("Demo")+" - "+_("Local")+" "+_("Server"))
        frame.set_label_align(0.5, 0.5)
        table.attach(frame, 1, 27, 8, 37)
        table.attach(vbox, 1, 26, 10, 35, yoptions=gtk.SHRINK)

	###################
	# style
        ###################

        label = gtk.Label(_("Appearance"))
	table = gtk.Table(36, 28, True)
        frame = gtk.Frame()
        table.attach(frame, 0, 28, 0, 38)
        self.notebookSettings.append_page(table, label)
	
        self.labelFontStatus = gtk.Label(_("Font status messages"))
	self.labelFontStatus.set_alignment(0.0,0.5)
	self.buttonFontStatus = gtk.FontButton(self.cfg.fontStatus)
	self.buttonFontStatus.set_size_request(180, 26)
        self.labelFontThumbnails = gtk.Label(_("Font thumbnails"))
	self.labelFontThumbnails.set_alignment(0.0,0.5)
	self.buttonFontThumbnails = gtk.FontButton(self.cfg.fontThumbnails)
	self.buttonFontThumbnails.set_size_request(180, 26)
        self.labelFontTree = gtk.Label(_("Font list"))
	self.labelFontTree.set_alignment(0.0,0.5)
	self.buttonFontTree = gtk.FontButton(self.cfg.fontTree)
	self.buttonFontTree.set_size_request(180, 26)
	
        self.labelWindowX = gtk.Label(_("Main window width"))
	self.labelWindowX.set_alignment(0.0,0.5)
    	adj = gtk.Adjustment(0.0, self.cfg.min_mainWindowX, self.cfg.screen_x-self.cfg.min_panedWindowX, 1.0, 5.0, 0.0)
    	self.spinWindowX = gtk.SpinButton(adj, 0, 0)
    	self.spinWindowX.set_wrap(True)
	self.spinWindowX.set_value(int(self.cfg.mainWindowX))
	
        self.labelWindowY = gtk.Label(_("Main window height"))
	self.labelWindowY.set_alignment(0.0,0.5)
    	adj = gtk.Adjustment(0.0, self.cfg.min_mainWindowY, self.cfg.screen_y, 1.0, 5.0, 0.0)
    	self.spinWindowY = gtk.SpinButton(adj, 0, 0)
    	self.spinWindowY.set_wrap(True)
	self.spinWindowY.set_value(int(self.cfg.mainWindowY))

        self.labelPanedX = gtk.Label(_("Secondary window width"))
	self.labelPanedX.set_alignment(0.0,0.5)
    	adj = gtk.Adjustment(0.0, self.cfg.min_panedWindowX, self.cfg.max_panedWindowX, 1.0, 5.0, 0.0)
    	self.spinPanedX = gtk.SpinButton(adj, 0, 0)
    	self.spinPanedX.set_wrap(True)
	self.spinPanedX.set_value(int(self.cfg.panedWindowX))

        self.labelTreeX = gtk.Label(_("List width"))
	self.labelTreeX.set_alignment(0.0,0.5)
    	adj = gtk.Adjustment(0.0, self.cfg.min_treeX, self.cfg.max_treeX, 1.0, 5.0, 0.0)
    	self.spinTreeX = gtk.SpinButton(adj, 0, 0)
    	self.spinTreeX.set_wrap(True)
	self.spinTreeX.set_value(int(self.cfg.treeX))

        self.spinWindowX.connect("value-changed", self.callback, "window_x")
        self.spinPanedX.connect("value-changed", self.callback, "paned_x")
        self.spinTreeX.connect("value-changed", self.callback, "tree_x")

        self.labelGtkrc = gtk.Label(_("File")+' "gtkrc"')
	self.labelGtkrc.set_alignment(0.0,0.5)
	self.entryGtkrc = gtk.Entry()
	self.entryGtkrc.set_text( self.cfg.gtkrc )
        self.fileChooserGtkrc = image_button(self.cfg.pixbuf_list_file_add_16)
        self.fileChooserGtkrc.connect("clicked", file_chooser_dialog, self.entryGtkrc, _("Select the file")+' "gtkrc"', None, gtk.FILE_CHOOSER_ACTION_OPEN)

	# tree
	dn = self.cfg.dn
	self.buttonTreeAlias = gtk.CheckButton(_("Alias"))
	self.buttonTreeAlias.unset_flags(gtk.CAN_FOCUS)
	if ( str(dn['alias']) in self.cfg.treeShow ):
	    self.buttonTreeAlias.set_active(True)	
	self.buttonTreeUser = gtk.CheckButton(_("User"))
	self.buttonTreeUser.unset_flags(gtk.CAN_FOCUS)
	if ( str(dn['user']) in self.cfg.treeShow ):
	    self.buttonTreeUser.set_active(True)
	self.buttonTreeHost = gtk.CheckButton(_("Host"))
	self.buttonTreeHost.unset_flags(gtk.CAN_FOCUS)
	if ( str(dn['host']) in self.cfg.treeShow ):
	    self.buttonTreeHost.set_active(True)
	self.buttonTreeIp = gtk.CheckButton(_("IP"))
	self.buttonTreeIp.unset_flags(gtk.CAN_FOCUS)
	if ( str(dn['ip']) in self.cfg.treeShow ):
	    self.buttonTreeIp.set_active(True)
	self.buttonTreeServer = gtk.CheckButton(_("Server"))
	self.buttonTreeServer.unset_flags(gtk.CAN_FOCUS)
	if ( str(dn['server']) in self.cfg.treeShow ):
	    self.buttonTreeServer.set_active(True)
	self.buttonTreeTime = gtk.CheckButton(_("Time"))
	self.buttonTreeTime.unset_flags(gtk.CAN_FOCUS)
	if ( str(dn['start_time']) in self.cfg.treeShow ):
	    self.buttonTreeTime.set_active(True)

	self.buttonTreeVncAutostart = gtk.CheckButton(_("Autostart x11vnc"))
	self.buttonTreeVncAutostart.unset_flags(gtk.CAN_FOCUS)
	if ( "vnc_autostart" in self.cfg.treeShow ):
	    self.buttonTreeVncAutostart.set_active(True)

	self.buttonTreeDhcp = gtk.CheckButton(_("Dhcp"))
	self.buttonTreeDhcp.unset_flags(gtk.CAN_FOCUS)
	if ( "dhcp" in self.cfg.treeShow ):
	    self.buttonTreeDhcp.set_active(True)
	
	#
        self.buttonTreeInfo = gtk.CheckButton(_("Show tooltip (brief information about the client)"))
	self.buttonTreeInfo.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.treeInfo == "y" ):
	    self.buttonTreeInfo.set_active(True)
	
        self.buttonTreeInfoTooltip = gtk.CheckButton(_("Show tooltip in the pop-up window"))
	self.buttonTreeInfoTooltip.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.treeInfoTooltip == "y" ):
	    self.buttonTreeInfoTooltip.set_active(True)
	
        self.buttonGecosAlias = gtk.CheckButton(_("Alias")+" = gecos")
	self.buttonGecosAlias.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.gecosAlias == "y" ):
	    self.buttonGecosAlias.set_active(True)
	
        # attach
        frame = gtk.Frame()
        table.attach(frame, 1, 27, 1, 11)
        table.attach(self.labelWindowX, 2, 20, 2, 4, yoptions=gtk.SHRINK)
        table.attach(self.spinWindowX, 20, 26, 2, 4, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(self.labelWindowY, 2, 20, 4, 6, yoptions=gtk.SHRINK)
        table.attach(self.spinWindowY, 20, 26, 4, 6, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(self.labelPanedX, 2, 20, 6, 8, yoptions=gtk.SHRINK)
        table.attach(self.spinPanedX, 20, 26, 6, 8, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(self.labelTreeX, 2, 20, 8, 10, yoptions=gtk.SHRINK)
        table.attach(self.spinTreeX, 20, 26, 8, 10, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

        frame = gtk.Frame()
        table.attach(frame, 1, 27, 11, 21)
        table.attach(self.labelFontStatus, 2, 14, 12, 14, yoptions=gtk.SHRINK)
        table.attach(self.buttonFontStatus, 14, 27, 12, 14, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(self.labelFontThumbnails, 2, 14, 14, 16, yoptions=gtk.SHRINK)
        table.attach(self.buttonFontThumbnails, 14, 27, 14, 16, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(self.labelFontTree, 2, 14, 16, 18, yoptions=gtk.SHRINK)
        table.attach(self.buttonFontTree, 14, 27, 16, 18, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

        frame = gtk.Frame()
        table.attach(frame, 1, 27, 21, 23)
        table.attach(self.labelGtkrc, 2, 15, 21, 23, yoptions=gtk.SHRINK)
        table.attach(self.entryGtkrc, 15, 24, 21, 23, yoptions=gtk.SHRINK)
        table.attach(self.fileChooserGtkrc, 24, 26, 21, 23, yoptions=gtk.SHRINK)

	# tree
        frame = gtk.Frame(_("List"))
        frame.set_label_align(0.5, 0.5)
        table.attach(frame, 1, 27, 24, 29)
        table.attach(self.buttonTreeInfo, 2, 26, 25, 27)
        table.attach(self.buttonTreeInfoTooltip, 2, 26, 27, 29)

        frame = gtk.Frame()
        table.attach(frame, 1, 27, 29, 31)
        table.attach(self.buttonGecosAlias, 2, 18, 29, 31)

        frame = gtk.Frame()
        table.attach(frame, 1, 16, 31, 37)
        table.attach(self.buttonTreeAlias, 2, 10, 31, 33)
        table.attach(self.buttonTreeUser, 2, 10, 33, 35)
        table.attach(self.buttonTreeHost, 2, 10, 35, 37)
        #
        table.attach(self.buttonTreeIp, 10, 16, 31, 33)
        table.attach(self.buttonTreeTime, 10, 16, 33, 35)
        table.attach(self.buttonTreeServer, 10, 16, 35, 37)
        frame = gtk.Frame()
        table.attach(frame, 16, 27, 31, 37)
        table.attach(self.buttonTreeVncAutostart, 17, 26, 31, 33)
        #table.attach(self.buttonTreeDhcp, 17, 26, 31, 33)

	###################
	# message
        ###################
        label = gtk.Label(_("Messages/Commands"))
	table = gtk.Table(38, 28, True)
        self.notebookSettings.append_page(table, label)
        
	vbox = gtk.VBox(False, 1)
	self.entryF1 = gtk.Entry()
	self.entryF1.set_text( self.cfg.f1 )
	vbox.pack_start(self.entryF1, expand=False, fill=False, padding=0)
	self.entryF2 = gtk.Entry()
	self.entryF2.set_text( self.cfg.f2 )
	vbox.pack_start(self.entryF2, expand=False, fill=False, padding=0)
	self.entryF3 = gtk.Entry()
	self.entryF3.set_text( self.cfg.f3 )
	vbox.pack_start(self.entryF3, expand=False, fill=False, padding=0)
	self.entryF4 = gtk.Entry()
	self.entryF4.set_text( self.cfg.f4 )
	vbox.pack_start(self.entryF4, expand=False, fill=False, padding=0)
	self.entryF5 = gtk.Entry()
	self.entryF5.set_text( self.cfg.f5 )
	vbox.pack_start(self.entryF5, expand=False, fill=False, padding=0)
	self.entryF6 = gtk.Entry()
	self.entryF6.set_text( self.cfg.f6 )
	vbox.pack_start(self.entryF6, expand=False, fill=False, padding=0)
	self.entryF7 = gtk.Entry()
	self.entryF7.set_text( self.cfg.f7 )
	vbox.pack_start(self.entryF7, expand=False, fill=False, padding=0)
	self.entryF8 = gtk.Entry()
	self.entryF8.set_text( self.cfg.f8 )
	vbox.pack_start(self.entryF8, expand=False, fill=False, padding=0)
	self.entryF9 = gtk.Entry()
	self.entryF9.set_text( self.cfg.f9 )
	vbox.pack_start(self.entryF9, expand=False, fill=False, padding=0)
	self.entryF10 = gtk.Entry()
	self.entryF10.set_text( self.cfg.f10 )
	vbox.pack_start(self.entryF10, expand=False, fill=False, padding=0)
	self.entryF11 = gtk.Entry()
	self.entryF11.set_text( self.cfg.f11 )
	vbox.pack_start(self.entryF11, expand=False, fill=False, padding=0)
	self.entryF12 = gtk.Entry()
	self.entryF12.set_text( self.cfg.f12 )
	vbox.pack_start(self.entryF12, expand=False, fill=False, padding=0)
	self.entryF13 = gtk.Entry()
	self.entryF13.set_text( self.cfg.f13 )
	vbox.pack_start(self.entryF13, expand=False, fill=False, padding=0)
	self.entryF14 = gtk.Entry()
	self.entryF14.set_text( self.cfg.f14 )
	vbox.pack_start(self.entryF14, expand=False, fill=False, padding=0)
	self.entryF15 = gtk.Entry()
	self.entryF15.set_text( self.cfg.f15 )
	vbox.pack_start(self.entryF15, expand=False, fill=False, padding=0)
	self.entryF16 = gtk.Entry()
	self.entryF16.set_text( self.cfg.f16 )
	vbox.pack_start(self.entryF16, expand=False, fill=False, padding=0)
	self.entryF17 = gtk.Entry()
	self.entryF17.set_text( self.cfg.f17 )
	vbox.pack_start(self.entryF17, expand=False, fill=False, padding=0)
	self.entryF18 = gtk.Entry()
	self.entryF18.set_text( self.cfg.f18 )
	vbox.pack_start(self.entryF18, expand=False, fill=False, padding=0)
	self.entryF19 = gtk.Entry()
	self.entryF19.set_text( self.cfg.f19 )
	vbox.pack_start(self.entryF19, expand=False, fill=False, padding=0)
	self.entryF20 = gtk.Entry()
	self.entryF20.set_text( self.cfg.f20 )
	vbox.pack_start(self.entryF20, expand=False, fill=False, padding=0)
		
        # attach
        frame = gtk.Frame()
        table.attach(frame, 0, 28, 0, 38)

        frame = gtk.Frame()
        table.attach(frame, 1, 27, 1, 37)
        table.attach(vbox, 2, 26, 2, 36, yoptions=gtk.SHRINK)

	###################
	# other
        ###################
	
        label = gtk.Label(_("Other"))
	table = gtk.Table(36, 28, True)
        frame = gtk.Frame()
        table.attach(frame, 0, 28, 0, 38)
        self.notebookSettings.append_page(table, label)
	
        self.buttonLogout = gtk.CheckButton(_("Total command logout"))
	self.buttonLogout.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.logoutCommandUse == "y" ):
	    self.buttonLogout.set_active(True)
	self.entryLogout = gtk.Entry()
	self.entryLogout.set_text( self.cfg.logoutCommand )

        self.labelCheckStatus = gtk.Label(_("Interval check of clients(ping)"))
	self.labelCheckStatus.set_alignment(0.0,0.5)
	
	adj = gtk.Adjustment(0.0, 10.0, 60.0, 1.0, 5.0, 0.0)
    	self.spinStatusInterval = gtk.SpinButton(adj, 0, 0)
    	self.spinStatusInterval.set_wrap(True)
	self.spinStatusInterval.set_value(int(self.cfg.checkStatusInterval))

        self.buttonCheckDhcp = gtk.CheckButton(_("Support of dynamic DHCP"))
	self.buttonCheckDhcp.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.checkDhcp == "y" ):
	    self.buttonCheckDhcp.set_active(True)
	
	self.buttonLtspInfo = gtk.RadioButton(None, "ltspinfo")
	self.buttonLtspInfo.unset_flags(gtk.CAN_FOCUS)
	self.buttonLtspSsh = gtk.RadioButton(self.buttonLtspInfo, "ssh")
	self.buttonLtspSsh.unset_flags(gtk.CAN_FOCUS)
	if ( self.cfg.ltspInfo == "ssh" ):
	    self.buttonLtspSsh.set_active(True)

	vbox = gtk.VBox(False, 0)
        label = gtk.Label(_("Disable functions"))
	label.set_alignment(0.5,0.5)
	vbox.pack_start(label, expand=False, fill=False, padding=5)

        self.buttonHideHide = gtk.CheckButton("! "+_("Hide these settings"))
	self.buttonHideHide.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_hide") == "y" ):
	    self.buttonHideHide.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideHide, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

        self.buttonHideSetting = gtk.CheckButton("! "+_("Program settings"))
	self.buttonHideSetting.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_setting") == "y" ):
	    self.buttonHideSetting.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideSetting, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)

        self.buttonHideTreeAddRemove = gtk.CheckButton(_("Add")+", "+_("Remove")+", "+_("Edit")+"/"+_("Client information"))
	self.buttonHideTreeAddRemove.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_tree_add_remove") == "y" ):
	    self.buttonHideTreeAddRemove.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideTreeAddRemove, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)

        self.buttonHideViewer = gtk.CheckButton(_("Viewer"))
	self.buttonHideViewer.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_viewer") == "y" ):
	    self.buttonHideViewer.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideViewer, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

        self.buttonHideControl = gtk.CheckButton(_("Control"))
	self.buttonHideControl.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_control") == "y" ):
	    self.buttonHideControl.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideControl, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

        self.buttonHideThumbnails = gtk.CheckButton(_("Thumbnails"))
	self.buttonHideThumbnails.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_thumbnails") == "y" ):
	    self.buttonHideThumbnails.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideThumbnails, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)

        self.buttonHideMessage = gtk.CheckButton(_("Send message"))
	self.buttonHideMessage.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_message") == "y" ):
	    self.buttonHideMessage.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideMessage, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

        self.buttonHideCommand = gtk.CheckButton(_("Run command"))
	self.buttonHideCommand.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_command") == "y" ):
	    self.buttonHideCommand.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideCommand, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

        self.buttonHideSendFile = gtk.CheckButton(_("Send file"))
	self.buttonHideSendFile.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_send_file") == "y" ):
	    self.buttonHideSendFile.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideSendFile, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)

        self.buttonHideUtil = gtk.CheckButton(_("Utilities"))
	self.buttonHideUtil.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_util") == "y" ):
	    self.buttonHideUtil.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideUtil, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

        self.buttonHideSystem = gtk.CheckButton(_("Logout")+", "+_("Reboot")+", "+_("Turn On")+", "+_("Shutdown"))
	self.buttonHideSystem.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_system_util") == "y" ):
	    self.buttonHideSystem.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideSystem, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

	separator = gtk.HSeparator()
	vbox.pack_start(separator, expand=False, fill=False, padding=1)

        self.buttonHideDemo = gtk.CheckButton(_("Demo"))
	self.buttonHideDemo.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_demo") == "y" ):
	    self.buttonHideDemo.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideDemo, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

        self.buttonHideTimer = gtk.CheckButton(_("Timers"))
	self.buttonHideTimer.unset_flags(gtk.CAN_FOCUS)
    	if ( self.cfg.read_config("hide","hide_timer") == "y" ):
	    self.buttonHideTimer.set_active(True)
	fixed = gtk.Fixed()
	fixed.put(self.buttonHideTimer, 0, 0)
	vbox.pack_start(fixed, expand=False, fill=False, padding=0)

        frame = gtk.Frame()
        table.attach(frame, 1, 27, 1, 6)
        table.attach(self.buttonLogout, 2, 26, 1, 3, yoptions=gtk.SHRINK)
        table.attach(self.entryLogout, 2, 26, 3, 5, yoptions=gtk.SHRINK)

        frame = gtk.Frame()
        table.attach(frame, 1, 27, 6, 11)
        table.attach(self.spinStatusInterval, 2, 5, 7, 9)
        table.attach(self.labelCheckStatus, 6, 23, 7, 9)
        table.attach(self.buttonCheckDhcp, 2, 23, 9, 11)

        frame = gtk.Frame()
        table.attach(frame, 1, 27, 11, 15)
        label = gtk.Label(_("Reboot/Shutdown"))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 2, 14, 11, 13, yoptions=gtk.SHRINK)
        table.attach(self.buttonLtspSsh, 14, 24, 11, 13, yoptions=gtk.SHRINK)
        table.attach(self.buttonLtspInfo, 14, 24, 13, 15, yoptions=gtk.SHRINK)

        frame = gtk.Frame()
        table.attach(frame, 1, 27, 15, 37)
    	if ( self.cfg.read_config("hide","hide_hide") == "n" ):
    	    table.attach(vbox, 2, 26, 15, 37)

	self.cfg.table2.show_all()

    def writeAllConfig(self, data=None):

	self.cfg.write_config("local","local_ip", self.entryLocalIp.get_text())
	
	if (self.buttonDemoVlc.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("vnc","demo_vlc", res)

	if (self.buttonDemoVlcRtp.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("vnc","demo_vlc_rtp", res)

	if (self.buttonDemoVlcAudio.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("vnc","demo_vlc_audio", res)

	self.cfg.write_config("vnc","demo_vlc_fps", self.comboDemoVlcFps.get_active_text())
	self.cfg.write_config("vnc","demo_vlc_vcodec", self.comboDemoVlcVcodec.get_active_text())
	self.cfg.write_config("vnc","demo_vlc_scale_full", self.comboDemoVlcScaleFull.get_active_text())
	self.cfg.write_config("vnc","demo_vlc_scale_window", self.comboDemoVlcScaleWindow.get_active_text())
	self.cfg.write_config("vnc","demo_vlc_caching", self.comboDemoVlcCaching.get_active_text())

	if (self.buttonDemoSsh.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("vnc","demo_ssh", res)

    	self.cfg.write_config("vnc","vnc_server", self.entryVncServer.get_text())
    	self.cfg.write_config("vnc","vnc_server_window", self.entryVncServerWindow.get_text())

	res = ""
	if (self.buttonThumbConnect.get_active()): res=res+"connect"
	if (self.buttonThumbScreenshot.get_active()): res=res+",screenshot"
	if (self.buttonThumbUp.get_active()): res=res+",up"
    	self.cfg.write_config("vnc","vnc_thumbnails_toolbar", res)

	# radio button
	if (self.buttonLtspInfo.get_active()): res="ltspinfo"
	else: res="ssh"
    	self.cfg.write_config("system","ltspinfo", res)

        self.cfg.write_config("command","f1", self.entryF1.get_text())
        self.cfg.write_config("command","f2", self.entryF2.get_text())
        self.cfg.write_config("command","f3", self.entryF3.get_text())
        self.cfg.write_config("command","f4", self.entryF4.get_text())
        self.cfg.write_config("command","f5", self.entryF5.get_text())
        self.cfg.write_config("command","f6", self.entryF6.get_text())
        self.cfg.write_config("command","f7", self.entryF7.get_text())
        self.cfg.write_config("command","f8", self.entryF8.get_text())
        self.cfg.write_config("command","f9", self.entryF9.get_text())
        self.cfg.write_config("command","f10", self.entryF10.get_text())
        self.cfg.write_config("command","f11", self.entryF11.get_text())
        self.cfg.write_config("command","f12", self.entryF12.get_text())
        self.cfg.write_config("command","f13", self.entryF13.get_text())
        self.cfg.write_config("command","f14", self.entryF14.get_text())
        self.cfg.write_config("command","f15", self.entryF15.get_text())
        self.cfg.write_config("command","f16", self.entryF16.get_text())
        self.cfg.write_config("command","f17", self.entryF17.get_text())
        self.cfg.write_config("command","f18", self.entryF18.get_text())
        self.cfg.write_config("command","f19", self.entryF19.get_text())
        self.cfg.write_config("command","f20", self.entryF20.get_text())
	
	# style
	if (self.buttonLogout.get_active()): res="y"
	else: res="n"
        self.cfg.write_config("system","logout_command_use", res)
        self.cfg.write_config("system","logout_command", self.entryLogout.get_text())
	
	font = self.buttonFontStatus.get_font_name()
	list = font.split()
	font_size = int(list[len(list)-1])
	if ( font_size > 16 ):
	    list[len(list)-1] = "16"
	    font = " ".join(list)
        self.cfg.write_config("tree","font_status", font)

	font = self.buttonFontThumbnails.get_font_name()
	list = font.split()
	font_size = int(list[len(list)-1])
	if ( font_size > 16 ):
	    list[len(list)-1] = "16"
	    font = " ".join(list)
        self.cfg.write_config("tree","font_thumbnails", font)

	font = self.buttonFontTree.get_font_name()
	list = font.split()
	font_size = int(list[len(list)-1])
	if ( font_size > 16 ):
	    list[len(list)-1] = "16"
	    font = " ".join(list)
        self.cfg.write_config("tree","font_tree", font)

	dn = self.cfg.dn
	res = ""
	if (self.buttonTreeAlias.get_active()): res=res+str(dn['alias'])
	if (self.buttonTreeUser.get_active()): res=res+","+str(dn['user'])
	if (self.buttonTreeHost.get_active()): res=res+","+str(dn['host'])
	if (self.buttonTreeIp.get_active()): res=res+","+str(dn['ip'])
	if (self.buttonTreeServer.get_active()): res=res+","+str(dn['server'])
	if (self.buttonTreeTime.get_active()): res=res+","+str(dn['start_time'])
	#
	if (self.buttonTreeVncAutostart.get_active()): res=res+",vnc_autostart"
	if (self.buttonTreeDhcp.get_active()): res=res+",dhcp"
    	self.cfg.write_config("tree","tree_show", res)

	window_x = int(self.spinWindowX.get_value())
	paned_x = int(self.spinPanedX.get_value())
	if ( self.cfg.screen_x < window_x+paned_x ):
	    paned_x = self.cfg.min_panedWindowX
	    window_x = self.cfg.screen_x - self.cfg.min_panedWindowX
	self.cfg.write_config("window","main_window_x", str(window_x))
	self.cfg.write_config("window","main_window_y", str(int(self.spinWindowY.get_value())))
	self.cfg.write_config("window","paned_window_x", str(paned_x))
	self.cfg.write_config("window","tree_x", str(int(self.spinTreeX.get_value())))

        self.cfg.write_config("tree","check_status_interval", str(int(self.spinStatusInterval.get_value())))
	if (self.buttonCheckDhcp.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("tree","check_dhcp", res)
	
	if (self.buttonTreeInfo.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("tree","tree_info", res)

	if (self.buttonTreeInfoTooltip.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("tree","tree_info_tooltip", res)

	if (self.buttonGecosAlias.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("tree","gecos_alias", res)

	if (self.buttonVncBox.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("vnc","vnc_gtk", res)

	if (self.buttonVncBoxReduce.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("vnc","vnc_thumbnails_reduce", res)

	if (self.buttonVncInsert.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("vnc","vnc_thumbnails_insert", res)

	if (self.buttonVncMinimize.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("vnc","vnc_thumbnails_minimize", res)

	if (self.buttonVncScroll.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("vnc","vnc_thumbnails_scroll", res)

        self.cfg.write_config("vnc","vnc_thumbnails_x", str(int(self.scaleVncMinX.get_value())))
        self.cfg.write_config("vnc","vnc_thumbnails_y", str(int(self.scaleVncMinY.get_value())))

        self.cfg.write_config("vnc","vnc_gtk_x", str(int(self.scaleVncMaxX.get_value())))
        self.cfg.write_config("vnc","vnc_gtk_y", str(int(self.scaleVncMaxY.get_value())))

        self.cfg.write_config("vnc","vnc_shot_folder", self.entryVncShotFolder.get_text())

        self.cfg.write_config("window","gtkrc", self.entryGtkrc.get_text())

	# hide
	if (self.buttonHideHide.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_hide", res)

	if (self.buttonHideSetting.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_setting", res)
    	
	if (self.buttonHideTreeAddRemove.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_tree_add_remove", res)

	if (self.buttonHideViewer.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_viewer", res)

	if (self.buttonHideControl.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_control", res)
    	
	if (self.buttonHideThumbnails.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_thumbnails", res)
    	
	if (self.buttonHideMessage.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_message", res)
    	
	if (self.buttonHideCommand.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_command", res)
    	
	if (self.buttonHideSendFile.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_send_file", res)
    	
	if (self.buttonHideUtil.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_util", res)
    	
	if (self.buttonHideSystem.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_system_util", res)
    	
	if (self.buttonHideDemo.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_demo", res)
    	
	if (self.buttonHideTimer.get_active()): res="y"
	else: res="n"
    	self.cfg.write_config("hide","hide_timer", res)
    	
    def callback(self, widget, data1=None ,data2=None, data3=None):
	if ( data1 == "save" ):
	    self.writeAllConfig()
	    self.cfg.read()
	    close_window2(None, self.cfg)

	if ( data1 == "close" ):
	    close_window2(None, self.cfg)
	
	if (data1 == "window_x" ):
	    window_x = self.spinWindowX.get_value()
	    if ( self.spinPanedX.get_value() > self.cfg.screen_x-window_x ):
		self.spinPanedX.set_value(self.cfg.screen_x-window_x)

	if (data1 == "paned_x" ):
	    paned_x = self.spinPanedX.get_value()
	    if ( self.spinWindowX.get_value() > self.cfg.screen_x-paned_x ):
		self.spinWindowX.set_value(self.cfg.screen_x-paned_x)

	# Соотношение сторон, но только Y координата зависит от X
	if (data3 == "vnc_max_x" ):
	    self.scaleVncMaxY.set_value(data2/1.25)
	if (data3 == "vnc_min_x" ):
	    self.scaleVncMinY.set_value(data2/1.25)
	
	if ( data1 == "demo_direct" ):
	    if ( self.buttonDemoVlc.get_active() == True and self.buttonDemoVlcRtp.get_active() == True ):
		self.buttonDemoDirect.set_active(True)
	    
	if ( data1 == "demo_vlc" ):
	    if ( self.buttonDemoVlc.get_active() == True ):
		self.buttonDemoVlcHttp.set_sensitive(True)
		self.buttonDemoVlcRtp.set_sensitive(True)
		self.buttonDemoVlcAudio.set_sensitive(True)
		self.comboDemoVlcFps.set_sensitive(True)
		self.comboDemoVlcVcodec.set_sensitive(True)
		self.comboDemoVlcScaleFull.set_sensitive(True)
		self.comboDemoVlcScaleWindow.set_sensitive(True)
		self.comboDemoVlcCaching.set_sensitive(True)
		self.entryVncServer.set_sensitive(False)
		self.entryVncServerWindow.set_sensitive(False)
		#
		if ( self.buttonDemoVlcRtp.get_active() == True ):
		    self.buttonDemoDirect.set_active(True)
		    self.buttonDemoDirect.set_sensitive(False)
		    self.buttonDemoSsh.set_sensitive(False)
	    else:
		self.buttonDemoVlcHttp.set_sensitive(False)
		self.buttonDemoVlcRtp.set_sensitive(False)
		self.buttonDemoVlcAudio.set_sensitive(False)
		self.comboDemoVlcFps.set_sensitive(False)
		self.comboDemoVlcVcodec.set_sensitive(False)
		self.comboDemoVlcScaleFull.set_sensitive(False)
		self.comboDemoVlcScaleWindow.set_sensitive(False)
		self.comboDemoVlcCaching.set_sensitive(False)
		self.entryVncServer.set_sensitive(True)
		self.entryVncServerWindow.set_sensitive(True)
		#
		self.buttonDemoDirect.set_sensitive(True)
		self.buttonDemoSsh.set_sensitive(True)

	if ( data1 == "demo_vlc_http" ):
	    if ( self.buttonDemoVlc.get_active() == True and self.buttonDemoVlcRtp.get_active() == True ):
		self.buttonDemoDirect.set_active(True)
		self.buttonDemoDirect.set_sensitive(False)
		self.buttonDemoSsh.set_sensitive(False)
		vcodec = self.comboDemoVlcVcodec.get_active_text()
		if ( vcodec == "wmv1" or vcodec == "wmv2" or vcodec == "mjpg" ):
		    self.comboDemoVlcVcodec.set_active(0)
	    else:
		self.buttonDemoDirect.set_sensitive(True)
		self.buttonDemoSsh.set_sensitive(True)

	if ( data1 == "demo_vlc_audio" ):
	    if ( self.buttonDemoVlcAudio.get_active() == True ):
		if ( int(self.comboDemoVlcCaching.get_active_text()) < 1000 ):
		    self.comboDemoVlcCaching.set_active(1)
		if ( int(self.comboDemoVlcFps.get_active_text()) > 5 ):
		    self.comboDemoVlcFps.set_active(0)
	
	if ( data1 == "demo_vlc_caching" ):
	    if ( self.buttonDemoVlcAudio.get_active() == True ):
		if ( int(self.comboDemoVlcCaching.get_active_text()) < 1000 ):
		    self.comboDemoVlcCaching.set_active(1)
	
	if ( data1 == "demo_vlc_vcodec" ):
	    if ( self.buttonDemoVlcRtp.get_active() == True ):
		vcodec = self.comboDemoVlcVcodec.get_active_text()
		if ( vcodec == "wmv1" or vcodec == "wmv2" or vcodec == "mjpg" ):
	    	    self.comboDemoVlcVcodec.set_active(0)

    def combo_separator(self, model, iter):
	if ( model.get_value(iter, 0) == "-" ):
	    return True

####################################################################################################

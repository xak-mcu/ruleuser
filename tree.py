#! /usr/bin/env python
# -*- coding: utf8 -*-

###################################################################################################
# RuleUser
# tree.py
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

import gtk, pwd, string, socket, gettext,random
_ = gettext.gettext

from util import *
from threads import thread_gfunc

####################################################################################################

def create_userList(cfg):
    
    gtk.gdk.threads_enter()
    try:
	cfg.userList.clear()
	create_tree_group(cfg)
    finally:
        gtk.gdk.threads_leave()

    # список псевдонимов для серверов
    alias_list = load_aliasList(cfg)

    servers = []
    server_list = cfg.read_config("servers","server_list")
    for x in range(int(server_list)):
	z = string.split(cfg.read_config("servers","server"+str(x+1)), ",")
	servers.append(z)

    for z_server in servers:

	# Добавить сервер
	gtk.gdk.threads_enter()
	try:
	    server_iter = cfg.userList.append(None)
	    for x in range(len(z_server)):
		if ( z_server[x] == None ):
		    z_server[x] = ""
    		cfg.userList.set(server_iter, x, z_server[x])
	    cfg.userList.set(server_iter, 100, cfg.pixbuf_status_server_16)
	finally:
    	    gtk.gdk.threads_leave()

	thread_server_group = thread_gfunc(cfg, False, True, create_tree_server_group, cfg, server_iter, z_server, alias_list)
	thread_server_group.start()

####################################################################################################

def create_tree_server_group(cfg, server_iter, z_server=None, alias_list=None):

    cfg.userList.set(server_iter, 100, cfg.pixbuf_status_server_16)

    #
    if ( not z_server ):
        z_server = []
        for part in range(len(cfg.z)):
    	    z_server.append(cfg.userList.get_value(server_iter, part))
    
    if ( z_server[0] not in cfg.localhost and validate("ip", z_server[0] ) == False ):
        cfg.status(_("Server")+": "+z_server[0]+" "+_("Wrong")+" IP "+_("address"))
        return
    if ( z_server[0] not in cfg.localhost and nmap_socket(cfg, z_server[0],"22", z_server[cfg.dn['timeout']],None,name=None) == "0" ):
        cfg.userList.set(server_iter, 100, cfg.pixbuf_status_server_off_16)
        return

    # список псевдонимов
    if ( not alias_list ):
	alias_list = load_aliasList(cfg)

    ds = {}
    for value, key in zip(z_server, cfg.z):
        ds[key] = value
    name = ds['alias']+": "
    
    # Убрать!!!!!
    if ( ds['dhcp'] == "static" ):
        ds['dhcp_arp'] = "True"
    ds['ssh_key_root'] = ""
    if ( ds['vnc_client'] == "vncviewer -fullscreen" ):
	ds['vnc_client'] = "vncviewer -fullscreen -MenuKey none"
    if ( ds['vnc_server'] == "x11vnc -noxdamage" ):
	ds['vnc_server'] = "x11vnc -noxdamage -scale 1024x768"

    if ( ds['vnc_client_window'] == "" ):
	ds['vnc_client_window'] = "vncviewer -MenuKey none"
    if ( ds['vnc_server_window'] == "" ):
	ds['vnc_server_window'] = "x11vnc -noxdamage -scale 640x480"

    if ( ds['vnc_gtk_color'] == "Default" ):
	ds['vnc_gtk_color'] = "default"
    elif ( ds['vnc_gtk_color'] == "Full" ):
	ds['vnc_gtk_color'] = "full"
    elif ( ds['vnc_gtk_color'] == "Medium" ):
	ds['vnc_gtk_color'] = "medium"
    elif ( ds['vnc_gtk_color'] == "Low" ):
	ds['vnc_gtk_color'] = "low"
    elif ( ds['vnc_gtk_color'] == "UltraLow" ):
	ds['vnc_gtk_color'] = "ultra-low"

    if ( ds['vnc_autostart_command'] == "" ):
	ds['vnc_autostart_command'] = "x11vnc -noxdamage -defer 3000"

    if ( ds['vnc_gtk_encoding'] == "" ):
	ds['vnc_gtk_encoding'] = "default"

    if ( ds['demo_vlc_fps'] == "" ):
	ds['demo_vlc_fps'] = "10"
    if ( ds['demo_vlc_vcodec'] == "" ):
	ds['demo_vlc_vcodec'] = "mpgv"
    if ( ds['demo_vlc_scale_full'] == "" or "width" in ds['demo_vlc_scale_full'] ):
	ds['demo_vlc_scale_full'] = "800x600"
    if ( ds['demo_vlc_scale_window'] == "" or "width" in ds['demo_vlc_scale_window'] ):
	ds['demo_vlc_scale_window'] = "640x480"
    if ( ds['demo_vlc_caching'] == "" ):
	ds['demo_vlc_caching'] = "300"
	
    if ( ds['demo_vlc_client_command'] == "" ):
	ds['demo_vlc_client_command'] = "vlc --network-caching=100 --qt-minimal-view --no-qt-privacy-ask --no-qt-error-dialogs"
    if ( not "--no-qt-privacy-ask" in ds['demo_vlc_client_command'] ):
	ds['demo_vlc_client_command'] = ds['demo_vlc_client_command'] + " --no-qt-privacy-ask"
    ### !!!
    

    if ( ds['alias'] in cfg.localhost ):
	# user, host, display
	clients = get_user_env(cfg, "clients", None, ds['server_key'], ds['server_port'], ds['server_user'], ds['alias'], name=name)
    	# ip, mac
	arp = get_user_env(cfg, "arp", None, ds['server_key'], ds['server_port'], ds['server_user'], ds['alias'], name=name)
	# desktop
	desktops = get_user_env(cfg, "desktops", None, ds['server_key'], ds['server_port'], ds['server_user'], ds['alias'], name=name)
	# passwd
	#user:x:uid:gid:gecos:home:shell
	passwd = get_user_env(cfg, "passwd", None, ds['server_key'], ds['server_port'], ds['server_user'], ds['alias'], name=name)
    else:
	(clients, arp, desktops, passwd) = get_user_env(cfg, "all", None, ds['server_key'], ds['server_port'], ds['server_user'], ds['alias'], name=name)

    if ( clients == [] or arp == [] or desktops == [] or passwd == [] ):
	if ( find_tree(cfg,cfg.userList, ds['alias']) ):
	    cfg.userList.set(server_iter, 100, cfg.pixbuf_status_server_off_16)
	return

    for line in clients:
	du = ds.copy()
    	list = line.split()
	    
    	du['user'] = list[0]
    	du['server'] = ds['alias']
    	du['group'] = "server"
    	du['client_id'] = du['user']+"_"+du['server']
    	    
    	if ( ds['alias'] in cfg.localhost and du['user'] == cfg.local_user ):
    	    continue
    	    
    	du['alias'] = du['user']
    	du['display'] = list[1]
    	du['start_time'] = list[2]
    	du['host'] = list[3].strip('()')
    	du['desktop'] = "unknown"
    	if ( du['dhcp'] == "static" ):
    	    du['dhcp_arp'] = "True"
	    
    	# client
    	if ( du['display'].split(":")[0] == "" and du['host'] == "" ): 
    	    if ( ds['show_local_sessions'] == "True" ):
    	        du['client'] = "local_session"
    	        du['host'] = du['server']
    	        du['ip'] = du['server']
    	        du['host_key'] = du['server_key']
    	        du['host_port'] = du['server_port']
    		du['host_user'] = du['user']
    		du['console_host'] = du['console_server']
    		du['dhcp'] = "static"
    		du['dhcp_arp'] = "True"
    	    else:
    	        continue
    	elif ( du['display'].split(":")[0] == "" and du['host']!= "" ):
    	    du['ip'] = du['host']
    	    du['client'] = "nx"
    	    du['dhcp'] = "static"
    	    du['dhcp_arp'] = "False"
    	else:
    	    du['client'] = "xdmcp"
    		
    	# mac-address
    	for line2 in arp:
    	    list2 = string.split(line2)
    	    if ( list2[0] == du['host'] ):
    		du['ip'] = list2[1]
    		du['mac'] = list2[2]
    		break
    	# passwd
	#user:x:uid:gid:gecos:home:shell
    	for line2 in passwd:
    	    list2 = line2.split(":")
    	    if ( list2[0] == du['user'] ):
    		du['uid'] = list2[2]
    		if ( cfg.gecosAlias == "y" ):
    		    du['alias'] = list2[4]
    		break
    	# desktops
    	for line2 in desktops:
    	    list2 = string.split(line2)
    	    if ( list2[0] == du['user'] or list2[0] == du['uid'] ):
    		du['desktop'] = list2[1]
    		break
    		
    	# alias
	for item in alias_list:
	    if ( du['user']+"@"+du['server'] == item[0] ):
		du['alias'] = item[1]
		break
		    
    	# Добавить клиента в userList
    	gtk.gdk.threads_enter()
	try:
    	    # Поиск в группах пары user+server
    	    if ( find_tree(cfg,cfg.userList, client_id=du['client_id'], group=True) == False ):
		server_iter = find_tree(cfg,cfg.userList, parent=du['server'])
		if ( server_iter ):
		    iter = cfg.userList.append(server_iter)
		    for x in range(len(du)):
    			cfg.userList.set(iter, x, du[cfg.z[x]])
    		    cfg.userList.set(iter, 100, cfg.pixbuf_status_down_16)
	finally:
    	    gtk.gdk.threads_leave()

####################################################################################################

def userList_column_value(cfg, column, value, user_list, parent=False):
    for z in user_list:
	row = find_tree(cfg, cfg.userList, client_id=z[cfg.dn['client_id']])
	if ( row == False ):
	    continue
	if ( parent ):
	    cfg.userList[(row[0],)][column] = value
	cfg.userList[row][column] = value

####################################################################################################

def load_aliasList(cfg):
    alias_list = []
    alias1 = cfg.read_config("alias","alias1")

    try:
	if ( "," in alias1 ):
	    z = string.split(alias1, ",")
	else:
	    z = [alias1]
    except:
	return []
    
    for item in z:
	try:
	    (user, alias) = string.split(item, ":")
	except:
	    continue
	if ( "@" not in user ):
	    continue
    	alias_list.append([user, alias])
    	
    return alias_list

####################################################################################################

def save_aliasList(cfg, user, server, alias):
    alias_list = load_aliasList(cfg)
    cfg.remove_config("alias")
    cfg.write_config("alias")
    alias1 = ""
    check = False
    for item in alias_list:
	if ( user+"@"+server == item[0] ):
	    item[1] = alias
	    check = True
	alias1 = alias1+item[0]+":"+item[1]+","
    if ( check == False ):
        alias1 = alias1+user+"@"+server+":"+alias+","
    cfg.write_config("alias", "alias1", alias1[:-1])
    
####################################################################################################

def create_tree_group(cfg):
    cfg.groups = cfg.read_config("group","group_list")
    for x in range(int(cfg.groups)):
    	(name, hosts)= string.split(cfg.read_config("group","g"+str(x+1)), ",")
	parent = cfg.userList.append(None)
	cfg.userList.set(parent, 0, name)
	cfg.userList.set(parent, 100, cfg.pixbuf_status_group_16)
	for y in range(int(hosts)):
	    z = string.split(cfg.read_config("group","g"+str(x+1)+"_"+str(y+1)), ",")
	    iter = cfg.userList.append(parent)
    	    for item in range(len(z)):
		if ( z[item] == None ):
		    z[item] = ""
		# ping
		if ( item == cfg.dn['ping'] ):
		    z[item] = False
		cfg.userList.set(iter, item, z[item])
	    cfg.userList.set(iter, 100, cfg.pixbuf_status_down_16)

	    # Убрать!!!!!
	    if ( cfg.userList.get_value(iter, cfg.dn['client']) == "standalone" ):
		if ( cfg.userList.get_value(iter, cfg.dn['client_id']) == "" ):
		    cfg.userList.set(iter, cfg.dn['client_id'], str(int(time.time())/random.randint(3,99)))
	    else:
		user = cfg.userList.get_value(iter, cfg.dn['user'])
		server = cfg.userList.get_value(iter, cfg.dn['server'])
		cfg.userList.set(iter, cfg.dn['client_id'], user+"_"+server)

	    if ( cfg.userList.get_value(iter, cfg.dn['vnc_client']) == "vncviewer -fullscreen" ):
		cfg.userList.set(iter, cfg.dn['vnc_client'], "vncviewer -fullscreen -MenuKey none" )
	    if ( cfg.userList.get_value(iter, cfg.dn['vnc_server']) == "x11vnc -noxdamage" ):
		cfg.userList.set(iter, cfg.dn['vnc_server'], "x11vnc -noxdamage -scale 1024x768" )

	    if ( cfg.userList.get_value(iter, cfg.dn['vnc_client_window']) == "" ):
		cfg.userList.set(iter, cfg.dn['vnc_client_window'], "vncviewer -MenuKey none" )
	    if ( cfg.userList.get_value(iter, cfg.dn['vnc_server_window']) == "" ):
		cfg.userList.set(iter, cfg.dn['vnc_server_window'], "x11vnc -noxdamage -scale 640x480" )
	    
	    if ( cfg.userList.get_value(iter, cfg.dn['vnc_gtk_color']) == "Default" ):
		cfg.userList.set(iter, cfg.dn['vnc_gtk_color'], "default" )
	    elif ( cfg.userList.get_value(iter, cfg.dn['vnc_gtk_color']) == "Full" ):
		cfg.userList.set(iter, cfg.dn['vnc_gtk_color'], "full" )
	    elif ( cfg.userList.get_value(iter, cfg.dn['vnc_gtk_color']) == "Medium" ):
		cfg.userList.set(iter, cfg.dn['vnc_gtk_color'], "medium" )
	    elif ( cfg.userList.get_value(iter, cfg.dn['vnc_gtk_color']) == "Low" ):
		cfg.userList.set(iter, cfg.dn['vnc_gtk_color'], "low" )
	    elif ( cfg.userList.get_value(iter, cfg.dn['vnc_gtk_color']) == "UltraLow" ):
		cfg.userList.set(iter, cfg.dn['vnc_gtk_color'], "ultra-low" )

	    if ( cfg.userList.get_value(iter, cfg.dn['vnc_autostart_command']) == "" ):
		cfg.userList.set(iter, cfg.dn['vnc_autostart_command'], "x11vnc -noxdamage -defer 3000" )

	    if ( cfg.userList.get_value(iter, cfg.dn['vnc_gtk_encoding']) == "" ):
		cfg.userList.set(iter, cfg.dn['vnc_gtk_encoding'], "default" )

	    if ( cfg.userList.get_value(iter, cfg.dn['demo_vlc_fps']) == "" ):
		cfg.userList.set(iter, cfg.dn['demo_vlc_fps'], "10" )
	    if ( cfg.userList.get_value(iter, cfg.dn['demo_vlc_vcodec']) == "" ):
		cfg.userList.set(iter, cfg.dn['demo_vlc_vcodec'], "mpgv" )
	    if ( cfg.userList.get_value(iter, cfg.dn['demo_vlc_scale_full']) == "" or \
		"width" in cfg.userList.get_value(iter, cfg.dn['demo_vlc_scale_full']) ):
		cfg.userList.set(iter, cfg.dn['demo_vlc_scale_full'], "800x600" )
	    if ( cfg.userList.get_value(iter, cfg.dn['demo_vlc_scale_window']) == "" or \
		"width" in cfg.userList.get_value(iter, cfg.dn['demo_vlc_scale_window']) ):
		cfg.userList.set(iter, cfg.dn['demo_vlc_scale_window'], "640x480" )
	    if ( cfg.userList.get_value(iter, cfg.dn['demo_vlc_caching']) == "" ):
		cfg.userList.set(iter, cfg.dn['demo_vlc_caching'], "300" )

	    if ( cfg.userList.get_value(iter, cfg.dn['demo_vlc_client_command']) == "" ):
		cfg.userList.set(iter, cfg.dn['demo_vlc_client_command'], "vlc --network-caching=100 --qt-minimal-view --no-qt-privacy-ask --no-qt-error-dialogs" )
	    if ( not "--no-qt-privacy-ask" in cfg.userList.get_value(iter, cfg.dn['demo_vlc_client_command']) ):
		cfg.userList.set(iter, cfg.dn['demo_vlc_client_command'], cfg.userList.get_value(iter, cfg.dn['demo_vlc_client_command']) + " --no-qt-privacy-ask" )

####################################################################################################

def remove_tree_item(cfg, treeview):
    # Нельзя удалить позиции в серверах
    model, rows = treeview.get_selection().get_selected_rows()
    parent_iters = []
    child_iters = []
    for row in rows:
        group = model[row[0]][4]
        if ( group == "server" and model[row][1] != "" ):
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
    save_userList(cfg)

####################################################################################################

def get_selected_tree(cfg, treeView=None, mode=None, rows=None):
    user_list = []
    model = treeView.get_selection().get_selected_rows()[0]
    if ( not rows ):
	rows = treeView.get_selection().get_selected_rows()[1]
    if ( rows == [] ):
        return []
	
    if ( mode == "first" or mode == "edit" ):
    	# Раскрыть и выделить первую позицию
	row = rows[0]
	if( len(row) == 1 and mode != "edit" ):
	    parent_iter = model.get_iter(row)
	    if ( model.iter_n_children(parent_iter) == 0 ):
	        return []
	    else:
	        row = (row[0],0)
    	treeView.scroll_to_cell(row, None, use_align=True, row_align=0.5, col_align=0.0)
    	treeView.expand_to_path(row)
    	treeView.get_selection().unselect_all()
    	treeView.get_selection().select_path(row)
    	model, rows = treeView.get_selection().get_selected_rows()
	    
    # группы и сервера
    if ( mode != "edit" ):
        server_rows = []
    	for row in rows:
    	    if ( len(row) == 1 ):
    		server_rows.append(row)
		parent_iter = model.get_iter(row)
		if ( range(model.iter_n_children(parent_iter)) != [] ):
	    	    for y in range(model.iter_n_children(parent_iter)):
    			t = (int(row[0]), int(y))
    			rows.append(tuple(t))
    	if ( server_rows != [] ):
    	    for row in server_rows:
    	        rows.remove(row)

    for row in rows:
        z = []
        for part in range(len(cfg.z)):
    	    z.append(model[row][part])
    	user_list.append(z)
    user_list = uniqueItemsList(user_list)
    return user_list
    
####################################################################################################

def tree_drag_data_get(treeview, context, selection, target_id, etime, cfg):
    treeselection = treeview.get_selection()
    model, rows = treeselection.get_selected_rows()
    txt = ""
    data = ""
    for z in get_selected_tree(cfg, treeview):
        for x in range(len(cfg.z)):
    	    if ( z[x] == None ):
    		z[x] = ""
    	    data = data+z[x]+","
	txt = txt+data[:-1]+"\n"
	data = ""
    selection.set(selection.target, 8, txt)

####################################################################################################

def tree_selection_enable(treeView, enable=True):
    if ( treeView ):
	selection = treeView.get_selection()
	if ( selection ):
	    selection.set_select_function(lambda *ignore: enable)

####################################################################################################

def tree_drag_data_motion(widget, drag_context, x, y, time):
    if ( drag_context.get_source_widget() == widget ):
    	drag_context.drag_status(gtk.gdk.ACTION_MOVE, time)
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

####################################################################################################

def tree_drag_data_received(treeView, context, x, y, selection, info, etime, cfg):
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
    	row_iter = model.get_iter(row)
    	temp_row_iter.append(row_iter)
    
    # перетащить несколько
    for row_iter in temp_row_iter:
	
    	temp_select_iter.append(row_iter)

	row = model.get_path(row_iter)
    	row_data = model[row]
    	new_iter = None
	
	if ( dest_path ):
    	    # Нельзя переместить группу в группу
    	    if ( len(row) == 1 and len(dest_path) == 2 ):
    		continue
	    # Нельзя переместить клиента в сервер
	    if ( len(row) == 2 and model[dest_path[0]][4] == "server" ):
		continue
	
	# Переместить группу в конец списка если нет назначения
    	if ( len(row) == 1 and not dest_path ):
    	    new_iter = model.append(None, row_data)
	# Клиента в группу вместо создания новой группы
    	elif ( len(row) == 2 and len(dest_path) == 1 ):
    	    new_iter = model.append(dest_iter, row_data)
	# Переместить клиента или группу
	else:
	    # Если попытка переместить сервер после/перед группой, найти первый сервер и вставить перед.
	    if ( len(row) == 1 and model[row[0]][4] == "server" and model[dest_path[0]][4] != "server" ):
		group_num = dest_path[0]
		while group_num <= len(model)-1:
		    if ( model[group_num][4] == "server" ):
			dest_path = (group_num,)
			dest_iter = model.get_iter(dest_path)
			dest_pos = gtk.TREE_VIEW_DROP_BEFORE
			break
		    group_num += 1
	    # Если попытка переместить группу после/перед сервером, найти последнюю группу и вставить после.
	    if ( len(row) == 1 and model[row[0]][4] != "server" and model[dest_path[0]][4] == "server" ):
		group_num = dest_path[0]
		while group_num >= 0:
		    if ( model[group_num][4] != "server" ):
			dest_path = (group_num,)
			dest_iter = model.get_iter(dest_path)
			dest_pos = gtk.TREE_VIEW_DROP_AFTER
			break
		    group_num -= 1

    	    if (dest_pos == gtk.TREE_VIEW_DROP_BEFORE or dest_pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
    		new_iter = model.insert_before(None, dest_iter, row_data)
    	    else:
    		new_iter = model.insert_after(None, dest_iter, row_data)
    	    
    	# Переместить клиентов группы
    	if ( new_iter and len(row) == 1 ):
    	    client_iter = model.iter_children(row_iter)
	    while client_iter:
    		client_data = model[model.get_path(client_iter)]
    		model.append(new_iter, client_data)
		client_iter = model.iter_next(client_iter)

    	# Поменять группу
    	if ( new_iter and len(row) == 2 ):
    	    group = model[dest_path[0]][0]
    	    model.set(new_iter, 9, group)
    	    expand = True
	
	# удалить
    	if ( new_iter ):
    	    model.remove(row_iter)

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

	# сохранить
	save_userList(cfg)

####################################################################################################

def check_demo_client_group(cfg, model, new_iter):
    if ( len(model.get_path(new_iter)) == 2 ):
    	client_id = model.get_value(new_iter, cfg.dn["client_id"])
    	# Удалить если клиент=сервер
    	if ( client_id == model.get_value(model.iter_parent(new_iter), cfg.dn["client_id"]) ):
    	    return True
    	# Удалить если клиент уже в группе
	client_iter = model.iter_children(model.iter_parent(new_iter))
	while client_iter:
    	    if ( model.get_path(new_iter) != model.get_path(client_iter) and \
    		client_id == model.get_value(client_iter, cfg.dn["client_id"]) ):
    		return True
	    client_iter = model.iter_next(client_iter)
    return False

####################################################################################################

def tree_move(widget, cfg, treeView, action):
    # Перемещение кнопками вверх/вниз в списке
    model, rows = treeView.get_selection().get_selected_rows()
    if ( rows == [] ):
	return

    temp_select_iter = []
    temp_row_iter = []
    for row in rows:
	# В демонстрации нельзя переместить "Локальный"
	if ( treeView != cfg.treeView and len(row) == 1 and row[0] == 0 ):
	    continue
	# Исключить клиентов перемещаемых групп
	if ( len(row) == 2 and (row[0],) in rows ):
	    continue
    	row_iter = model.get_iter(row)
    	temp_row_iter.append(row_iter)
    
    # Если вниз перевернуть
    if ( action == "down" ):
	temp_row_iter.reverse()
    
    # переместить несколько
    for row_iter in temp_row_iter:
	
    	temp_select_iter.append(row_iter)

    	new_iter = None
	row = model.get_path(row_iter)
    	row_data = model[row]
    	
	# Нельзя переместить клиентов в сервере
	if ( len(row) == 2 and model[row[0]][4] == "server" ):
	    continue
	    
    	if ( action == "up" ):
    	    if ( len(row) == 1 ):
    		if ( row[0] == 0 ):
    		    continue
		# В демонстрации нельзя переместить выше "Локальный"
		if ( treeView != cfg.treeView and len(row) == 1 and row[0]-1 == 0 ):
		    continue
		# Нельзя переместить сервер выше группы
    		if ( model[row[0]][4] == "server" and model[row[0]-1][4] != "server" ):
    		    continue
    		dest_path = (row[0]-1,)
		dest_iter = model.get_iter(dest_path)
    		new_iter = model.insert_before(None, dest_iter, row_data)
    	    else:
    		if ( row[1] == 0 ):
    		    if ( row[0] == 0 ):
    			continue
    		    parent_prev_iter = model.get_iter((row[0]-1,))
    		    parent_prev_n = model.iter_n_children(parent_prev_iter)
    		    if ( parent_prev_n != 0 ):
    			dest_path = (row[0]-1,parent_prev_n-1)
			dest_iter = model.get_iter(dest_path)
    			new_iter = model.insert_after(None, dest_iter, row_data)
    		    else:
    			dest_path = (row[0]-1,)
			dest_iter = model.get_iter(dest_path)
    			new_iter = model.append(dest_iter, row_data)
    		else:
    		    dest_path = (row[0],row[1]-1)
		    dest_iter = model.get_iter(dest_path)
		    # Нельзя переместить выше клиента также входящего в список перемещения
		    #if ( dest_path == model.get_path(temp_select_iter[len(temp_select_iter)-2]) ):
		    #	continue
    		    new_iter = model.insert_before(None, dest_iter, row_data)
    	else:
    	    if ( len(row) == 1 ):
    		if ( row[0] == len(model)-1 ):
    		    continue
		# Нельзя переместить группу ниже сервера
    		if ( model[row[0]][4] != "server" and model[row[0]+1][4] == "server" ):
    		    continue
    		dest_path = (row[0]+1,)
		dest_iter = model.get_iter(dest_path)
    		new_iter = model.insert_after(None, dest_iter, row_data)
    	    else:
    		if ( row[1] == model.iter_n_children(model.get_iter((row[0],)))-1 ):
    		    if ( row[0] == len(model)-1 ):
    			continue
		    # Нельзя переместить клиента группы в сервер
    		    if ( model[row[0]][4] != "server" and model[row[0]+1][4] == "server" ):
    			continue
    		    parent_next_iter = model.get_iter((row[0]+1,))
    		    dest_path = (row[0]+1,)
		    dest_iter = model.get_iter(dest_path)
    		    new_iter = model.prepend(dest_iter, row_data)
    		else:
    		    dest_path = (row[0],row[1]+1)
		    dest_iter = model.get_iter(dest_path)
    		    new_iter = model.insert_after(None, dest_iter, row_data)
	
	# Удалить если повтор в новой группе(для Демонстрация)
    	if ( new_iter and treeView != cfg.treeView and row[0] != dest_path[0] and check_demo_client_group(cfg, model, new_iter) ):
    	    model.remove(new_iter)
    	    new_iter = None
    	
    	# Переместить клиентов группы
    	if ( new_iter and len(row) == 1 ):
    	    client_iter = model.iter_children(row_iter)
	    while client_iter:
    		client_data = model[model.get_path(client_iter)]
    		model.append(new_iter, client_data)
		client_iter = model.iter_next(client_iter)

    	# Поменять группу
    	if ( new_iter and len(row) == 2 ):
    	    group = model[dest_path[0]][0]
    	    model.set(new_iter, 9, group)

    	if ( new_iter ):
	    # Удалить    	
    	    model.remove(row_iter)
    	    # Добавить в список выделения
    	    temp_select_iter.remove(row_iter)
    	    temp_select_iter.append(new_iter)
    	
    # выделить
    if ( temp_select_iter != [] ):
	for select_iter in temp_select_iter:
	    if( len(model.get_path(select_iter)) == 2 ):
		parent_path = (model.get_path(select_iter)[0],)
		treeView.expand_to_path(parent_path)
    	    treeView.get_selection().select_iter(select_iter)

    # сохранить
    save_userList(cfg)

####################################################################################################

def create_columns(cfg, treeView, list_col, visible=None):
    i = -1
    for col in list_col:
	i += 1
	if ( col == "pixbuf" ):
    	    renderer = gtk.CellRendererPixbuf()
    	    column = gtk.TreeViewColumn("", renderer, pixbuf=i)
    	    column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
    	    column.set_fixed_width(28)    
    	else:
    	    renderer = gtk.CellRendererText()
    	    column = gtk.TreeViewColumn(col, renderer, text=i)
    	    column.set_expand(True)
    	column.set_visible(True)
	treeView.append_column(column)

####################################################################################################

def save_demoList(cfg):
    cfg.remove_config("vnc_servers")
    cfg.write_config("vnc_servers")
    cfg.write_config("vnc_servers", "vnc_servers_list", "1")
    for x in range(len(cfg.demoList)):
	server = ""
    	for part in range(len(cfg.z)):
    	    if ( type(cfg.demoList[(x,)][part]) == str ):
    		if ( str(cfg.demoList[(x,)][part]) == _("Local") and part == 0 ):
        	    server = server+"Local"+","
		else:
        	    server = server+str(cfg.demoList[(x,)][part])+","
	    else:
    	        server = server+","
    	cfg.write_config("vnc_servers", "vnc_server_list", str(x+1))
    	cfg.write_config("vnc_servers", "vnc_server"+str(x+1)+"_users", "0")
    	cfg.write_config("vnc_servers", "vnc_server"+str(x+1), server[:-1])
	parent_iter = cfg.demoList.get_iter(x)
    	for y in range(cfg.demoList.iter_n_children(parent_iter)):
    	    cfg.write_config("vnc_servers", "vnc_server"+str(x+1)+"_users", str(y+1))
    	    user = ""
    	    for part in range(len(cfg.z)):
        	if ( type (cfg.demoList[(x,y)][part]) == str  ):
        	    user = user+str(cfg.demoList[(x,y)][part])+","
		else:
        	    user = user+","
    	    cfg.write_config("vnc_servers", "vnc_server"+str(x+1)+"_"+str(y+1), user[:-1])

###################################################################################################
def save_userList(cfg):
    if ( cfg.save_userList_busy == False ):
	cfg.save_userList_busy = True
	thread = thread_gfunc(cfg, False, True, save_userList_t, cfg)
	thread.start()
##################################################	
def save_userList_t(cfg):
    while cfg.timers.timer_userList("active") == True:
	time.sleep(0.5)
    time.sleep(1)
    gtk.gdk.threads_enter()
    try:
        save_userList_start(cfg)
	cfg.save_userList_busy = False
    finally:
        gtk.gdk.threads_leave()
##################################################	
def save_userList_start(cfg):
    cfg.remove_config("servers")
    cfg.write_config("servers")
    cfg.write_config("servers", "server_list", "0")
    cfg.remove_config("group")
    cfg.write_config("group")
    cfg.write_config("group", "group_list", "0")
    servers = 0
    groups = 0
    for x in range(len(cfg.userList)):
	server = cfg.userList[x][0]
	group = cfg.userList[x][4]
	parent_iter = cfg.userList.get_iter((x,))
    	if ( group == "server" ):
	    servers += 1
    	    cfg.write_config("servers", "server_list", str(servers))
    	    item = ""
    	    for part in range(len(cfg.z)):
    	        if ( cfg.userList[(x,)][part] == None ):
    	    	    cfg.userList[(x,)][part] = ""
        	item = item+str(cfg.userList[(x,)][part])+","
    	    cfg.write_config("servers", "server"+str(servers), item[:-1])
    	else:
	    groups += 1
    	    cfg.write_config("group", "group_list", str(groups))
    	    cfg.write_config("group", "g"+str(groups), cfg.userList[x][0]+","\
    	        +str(cfg.userList.iter_n_children(parent_iter)))
    	    for y in range(cfg.userList.iter_n_children(parent_iter)):
        	item = ""
        	for part in range(len(cfg.z)):
        	    if ( cfg.userList[(x,y)][part] == None ):
        	        cfg.userList[(x,y)][part] = ""
        	    item = item+str(cfg.userList[(x,y)][part])+","
    	        cfg.write_config("group", "g"+str(groups)+"_"+str(y+1), item[:-1])
    
####################################################################################################

def find_tree(cfg, tree, client_id=None, parent=None, group=None):
    # Поиск user,server в дереве userList
    # Если parent, возвращает iter на него или False
    # Если group - поиск user,host только в группах
    i = -1
    if ( parent ):
        for parents in tree:
    	    i +=1
    	    if ( group == True and parents[4] == "server" ):
    		continue
    	    if ( parent == tree[i][0] ):
    		return tree.get_iter(i)
    if ( parent == None ):
        for parents in tree:
    	    i += 1
    	    if ( group == True and parents[4] == "server" ):
    		continue
	    parent_iter = tree.get_iter(i)
    	    for y in range(tree.iter_n_children(parent_iter)):
    	        row = (i,y)
    	    	if ( client_id == tree[row][cfg.dn['client_id']] ):
    		    return row
		    break
    return False

####################################################################################################    

def save_timersList(cfg):
    cfg.remove_config("timers")
    cfg.write_config("timers")
    for timer in range(len(cfg.timersList)):
        row = (timer,)
        number = cfg.timersList[row][0]
    	action = cfg.timersList[row][1]
    	start = cfg.timersList[row][2]
    	command = cfg.timersList[row][3]
    	user_list = cfg.timersList[row][5]
    	if ( user_list == None ):
    	    user_list = []
    	    users = "0"
    	else:
    	    users = str(len(user_list))
	cfg.write_config("timers", "timer_list", str(timer+1))
	cfg.write_config("timers", "t"+str(timer+1), action+","+start+","+command)
	cfg.write_config("timers", "t"+str(timer+1)+"_users", users)
	user = 0
	for z in user_list:
	    user += 1
	    user_s = ""
	    for item in range(len(z)):
		user_s = user_s+z[item]+","
	    cfg.write_config("timers", "t"+str(timer+1)+"_user"+str(user), user_s[:-1])

####################################################################################################    

def create_timersList(cfg):
    cfg.timersList.clear()
    timers = cfg.read_config("timers","timer_list")
    for x in range(int(timers)):
    	(action,start,command)= cfg.read_config("timers","t"+str(x+1)).split(",")
    	users = cfg.read_config("timers","t"+str(x+1)+"_users")
    	user_list = []
	for y in range(int(users)):
    	    z = cfg.read_config("timers","t"+str(x+1)+"_user"+str(y+1)).split(",")
    	    user_list.append(z)
    	timer_iter = cfg.timersList.append(None, [x+1,action,start,command,None,user_list,0])
    	for z in user_list:
    	    cfg.timersList.append(timer_iter, ["",z[0],"","",None,"",0])

####################################################################################################    

def create_demoList(cfg):
    cfg.demoList.clear()
    # Локальный
    servers = cfg.read_config("vnc_servers","vnc_server_list")
    for x in range(int(servers)):
	server = cfg.read_config("vnc_servers","vnc_server"+str(x+1)).split(",")
	users = cfg.read_config("vnc_servers","vnc_server"+str(x+1)+"_users")
	server_iter = cfg.demoList.append(None)
	for z in range(len(server)):
	    if ( server[z] == "Local" and z == 0 ):
		cfg.demoList.set(server_iter, z, _("Local"))
	    else:
    		cfg.demoList.set(server_iter, z, server[z])
	for y in range(int(users)):
    	    user = cfg.read_config("vnc_servers","vnc_server"+str(x+1)+"_"+str(y+1)).split(",")
	    user_iter = cfg.demoList.append(server_iter)
	    for z in range(len(user)):
    		cfg.demoList.set(user_iter, z, user[z])

####################################################################################################    

####################################################################################################    

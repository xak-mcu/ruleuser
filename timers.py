#! /usr/bin/env python
# -*- coding: utf8 -*-

###################################################################################################
# RuleUser
# timers.py
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

import gettext, gtk
import gobject, threading
import datetime, time
from xml.dom.minidom import parse, parseString
_ = gettext.gettext

from util import *
from command import run_command
from threads import thread_gfunc
from tree import *


####################################################################################################

class timers:

    def __init__(self, cfg):
	
	self.cfg = cfg
	self.treeView = self.cfg.treeView

    def start(self):
	# Иконки в списке
	self.list_icons_check = True
	self.thread_list_icons = thread_gfunc(self.cfg, False, True, self.list_icons)
	self.thread_list_icons.start()
	
	# Проверка активности клиентов
	self.client_status_check = True
	self.thread_client_status = thread_gfunc(self.cfg, False, True, self.client_status)
	self.thread_client_status.start()
	
	# Сканирование
	self.network_scan = True
	if ( self.cfg.checkDhcp == "y" ):
	    self.thread_client_network_scan = thread_gfunc(self.cfg, False, True, self.client_network_scan)
	    self.thread_client_network_scan.start()
	
	# Проверка Demo серверов
	self.demo_server_status_check = True
	self.thread_demo_server_status = thread_gfunc(self.cfg, False, True, self.demo_server_status, self.cfg.demo_check_interval)
	self.thread_demo_server_status.start()

	# Проверка таймеров
	self.timer_status_check = True
	self.thread_timer_active = thread_gfunc(self.cfg, False, True, self.timer_active, self.cfg.timers_check_interval)
	self.thread_timer_active.start()
	return False
	
    def stop(self):
	# Иконки в списке
	self.list_icons_check = False
	# Проверка активности клиентов, ping
	self.client_status_check = False
	# Сканирование
	self.network_scan = False
	# demo сервера
	self.demo_server_status_check = False
	# Проверка включенных таймеров
	self.timer_status_check = False

####################################################################################################

    def list_icons(self):
	while self.list_icons_check == True:
	    gtk.gdk.threads_enter()
	    try:
		server_iter = self.cfg.userList.get_iter_first()
		while server_iter:
	    	    client_iter = self.cfg.userList.iter_children(server_iter)
	    	    while client_iter:
    			self.client_icons(self.cfg, client_iter)
			client_iter = self.cfg.userList.iter_next(client_iter)
		    server_iter = self.cfg.userList.iter_next(server_iter)

	    finally:
		gtk.gdk.threads_leave()
		
	    time.sleep(3)

    def client_icons(self, cfg, iter):
	dn = cfg.dn
	# type
	if ( cfg.userList.get_value(iter, dn['client']) == "standalone" ):
    	    cfg.userList.set(iter, 109, cfg.pixbuf_status_st_16)
	elif ( cfg.userList.get_value(iter, dn['client']) == "local_session" ):
    	    cfg.userList.set(iter, 109, cfg.pixbuf_status_st_16)
	elif ( cfg.userList.get_value(iter, dn['client']) == "nx" ):
    	    cfg.userList.set(iter, 109, cfg.pixbuf_status_nx_16)
	else:
    	    cfg.userList.set(iter, 109, cfg.pixbuf_status_xdmcp_16)
	# desktop
	if ( cfg.userList.get_value(iter, dn['desktop']) == "kde3" ):
    	    cfg.userList.set(iter, 108, cfg.pixbuf_status_kde3_16)
	elif ( cfg.userList.get_value(iter, dn['desktop']) == "kde4"  ):
    	    cfg.userList.set(iter, 108, cfg.pixbuf_status_kde4_16)
	elif ( cfg.userList.get_value(iter, dn['desktop']) == "gnome2"  ):
    	    cfg.userList.set(iter, 108, cfg.pixbuf_status_gnome2_16)
	elif ( cfg.userList.get_value(iter, dn['desktop']) == "gnome3"  ):
    	    cfg.userList.set(iter, 108, cfg.pixbuf_status_gnome3_16)
	elif ( cfg.userList.get_value(iter, dn['desktop']) == "lxde"  ):
    	    cfg.userList.set(iter, 108, cfg.pixbuf_status_lxde_16)
	elif ( cfg.userList.get_value(iter, dn['desktop']) == "xfce"  ):
    	    cfg.userList.set(iter, 108, cfg.pixbuf_status_xfce_16)
	elif ( cfg.userList.get_value(iter, dn['desktop']) == "linux"  ):
    	    cfg.userList.set(iter, 108, cfg.pixbuf_status_linux_16)
	elif ( cfg.userList.get_value(iter, dn['desktop']) == "windows"  ):
    	    cfg.userList.set(iter, 108, cfg.pixbuf_status_windows_16)
	else:
    	    cfg.userList.set(iter, 108, cfg.pixbuf_status_unknown_16)
	# Автозапуск X11vnc
	if ( "vnc_autostart" in cfg.treeShow ):
	    if ( (cfg.userList.get_value(iter, dn['vnc_autostart']) == "True" and cfg.userList.get_value(iter, dn['vnc_client']) != "nx") or \
		(cfg.userList.get_value(iter, dn['vnc_nx_autostart']) == "True" and cfg.userList.get_value(iter, dn['vnc_client']) == "nx") ):
    		cfg.userList.set(iter, 107, cfg.pixbuf_status_autostart_16)
    	    else:
    		cfg.userList.set(iter, 107, None)
    	else:
    	    cfg.userList.set(iter, 107, None)

####################################################################################################

    def client_network_scan(self):
	# DHCP
	dn = self.cfg.dn
	while self.network_scan == True:
	
	    # Создание и проверка вхождения сети в список
	    gtk.gdk.threads_enter()
	    try:
		network_scan_list = []
    		for parent in range(len(self.cfg.userList)):
		    parent_iter = self.cfg.userList.get_iter(parent)
    		    for client in range(self.cfg.userList.iter_n_children(parent_iter)):
			path = (parent,client)
			if ( self.cfg.userList[path][dn['dhcp']] != "static" and\
			    self.cfg.userList[path][dn['dhcp_arp']] != "True" and\
			    self.cfg.userList[path][dn['mac']] != "" ):
			    ###############
			    ip = self.cfg.userList[path][dn['ip']].split(".")
			    ip[3] = "0"
			    net_ = ".".join(ip)+"/24"
			    repeat = False
			    for net in network_scan_list:
				if ( net == net_ ):
				    repeat = True
			    if ( repeat == False ):
				network_scan_list.append(net_)
	    finally:
		gtk.gdk.threads_leave()
		
	    # scan
	    nmap_list = self.nmap_scan_mac(self.cfg, network_scan_list)

	    # проставить IP
	    if ( nmap_list != [] ):
		save = False
		gtk.gdk.threads_enter()
		try:
    		    for parent in range(len(self.cfg.userList)):
			parent_iter = self.cfg.userList.get_iter(parent)
    			for client in range(self.cfg.userList.iter_n_children(parent_iter)):
			    path = (parent,client)
			    if ( self.cfg.userList[path][dn['dhcp']] != "static" and\
				self.cfg.userList[path][dn['dhcp_arp']] != "True" and\
				self.cfg.userList[path][dn['mac']] != "" ):
				###############
				for x in nmap_list:
				    if ( self.cfg.userList[path][dn['mac']] in x[1] ):
					# Сохранять только если другой
					if ( self.cfg.userList[path][dn['ip']] != x[0] or\
						(self.cfg.userList[path][dn['client']] == "standalone" and\
						self.cfg.userList[path][dn['server']] != x[0]) ):
					    save = True
					    self.cfg.userList[path][dn['ip']] = x[0]
					    # Для стац. поменять "server"
					    if ( self.cfg.userList[path][dn['client']] == "standalone" ):
						self.cfg.userList[path][dn['server']] = x[0]
				###############
		finally:
		    gtk.gdk.threads_leave()
		if ( save == True ):
		    save_userList(self.cfg)
	    time.sleep(float(self.cfg.checkStatusInterval)*2)

    def nmap_scan_mac(self, cfg, network_scan_list, ssh=""):
	if ( network_scan_list == [] ):
	    return []
	nmap_list = []
	for net in network_scan_list:
	    cmd = ssh+cfg.nmap_command+" -n -oX - -sP "+net
	    proc = popen_sub(cfg, cmd.split(), timeout_exit=10)
	    if ( proc == False ):
	    	continue
	    nmap_out = proc.stdout.read().splitlines()
	    try:
		for x in range(len(nmap_out)):
		    if ( "ipv4" in nmap_out[x] and x < len(nmap_out)-1 and "mac" in nmap_out[x+1]):
			ip = nmap_out[x].split()[1][5:].strip('""')
			mac = nmap_out[x+1].split()[1][5:].strip('""')
			nmap_list.append([ip, mac])
	    except:
		continue
	return nmap_list

####################################################################################################

    def client_status(self):
	# Проверка активности клиентов
	while self.client_status_check == True:

	    # Строка IP адресов
	    gtk.gdk.threads_enter()
	    try:
    		hosts = ""
    		for parent in range(len(self.cfg.userList)):
		    parent_iter = self.cfg.userList.get_iter(parent)
    		    for client in range(self.cfg.userList.iter_n_children(parent_iter)):
    			hosts = hosts+" "+self.cfg.userList[(parent,client)][3]
	    finally:
	        gtk.gdk.threads_leave()

	    # scan
	    nmap_list = self.nmap_scan_ping(self.cfg, hosts)
	    
	    # проставить статус
	    gtk.gdk.threads_enter()
	    try:
		if ( nmap_list != [] ):
    		    for parent in range(len(self.cfg.userList)):
			parent_iter = self.cfg.userList.get_iter(parent)
    			for client in range(self.cfg.userList.iter_n_children(parent_iter)):
    		    	    for line in nmap_list:
    		    		up = False
    				if ( self.cfg.userList[(parent,client)][3] in line ):
    			    	    up = True
    	    		    	    break
    			    if ( up ):
    	    			self.cfg.userList[(parent,client)][100] = self.cfg.pixbuf_status_up_16
    	    			self.cfg.userList[(parent,client)][self.cfg.dn['ping']] = "True"
    	    		    else:
    				self.cfg.userList[(parent,client)][100] = self.cfg.pixbuf_status_down_16
    	    			self.cfg.userList[(parent,client)][self.cfg.dn['ping']] = "False"
	    finally:
	        gtk.gdk.threads_leave()
	    time.sleep(float(self.cfg.checkStatusInterval))
	    
    def nmap_scan_ping(self, cfg, hosts, ssh=""):
	if ( hosts == "" ):
	    return []
	cmd = ssh+cfg.nmap_command+" --initial-rtt-timeout=250ms -n -oG - -sP "+hosts
	proc = popen_sub(cfg, cmd.split(), timeout_exit=10)
	if ( proc == False ):
	    return []
	nmap_out = proc.stdout.read().splitlines()
	nmap_list = []
	for x in nmap_out:
	    if ( "Status: Up" in x ):
		nmap_list.append(x)
	return nmap_list

####################################################################################################
	
    def timer_userList(self, command):
	if ( command == "start" ):
	    self.thread_userList = thread_gfunc(self.cfg, False, True, create_userList, self.cfg)
	    self.thread_userList.start()
	if ( command == "active" ):
	    self.thread_userList.join(0)
	    if self.thread_userList.isAlive():
		return True
	    else:
		return False
	if ( command == "restart" ):
	    # Если userList не сформирован ничего не делать
	    self.thread_userList.join(0)
	    if self.thread_userList.isAlive():
		pass
	    else:
		self.timer_userList("start")
	
####################################################################################################

    def timer_user(self, command, num=None):
	if ( command == "start" ):
	    # таймеры из timersList # [number,status,action,start,command,userlist,timer_id]
	    for timer in range(len(self.cfg.timersList)):
		#запустить один
		if( num != None and num != timer ):
		    continue
		row = (timer,)
		# уже запущен?
		if ( self.cfg.timersList[row][6] != 0 ):
		    continue
    		start = self.cfg.timersList[row][2]
    		number = self.cfg.timersList[row][0]
    		action = self.cfg.timersList[row][1]
		# не выполнять если время истекло
		time = datetime.datetime.now()
		if ( int(start.replace(':','')) < int(time.strftime("%H%M%S")) ):
		    continue
		self.cfg.timersList[row][6] = gobject.timeout_add(1000, self.timer_user_get, number)
		self.cfg.status(_("Timer")+" №"+number+" - "+action+", "+_("starting")+" "+_("in")+" "+start)

	if ( command == "stop" ):
	    for timer in range(len(self.cfg.timersList)):
		#остановить один
		if( num != None and num != timer ):
		    continue
		row = (timer,)
    		number = self.cfg.timersList[row][0]
    		timer_id = self.cfg.timersList[row][6]
    		# уже остановлен ?
    		if ( timer_id == 0 ):
    		    continue
		# Завершить
		gobject.source_remove(timer_id)
		self.cfg.timersList[row][6] = 0
		self.cfg.status(_("Timer")+" №"+number+" "+_("stopped"))
		# Убрать иконки
    		user_list = self.cfg.timersList[row][5]
		userList_column_value(self.cfg, 104, None, user_list)

    def timer_user_get(self, number):
	for x in range(len(self.cfg.timersList)):
	    if ( self.cfg.timersList[(x,)][0] == number ):
		row = (x,)
		break
    	start = self.cfg.timersList[row][2]
	time = datetime.datetime.now()
	if ( start == time.strftime("%H:%M:%S")):
    	    number = self.cfg.timersList[row][0]
    	    action = self.cfg.timersList[row][1]
    	    command = self.cfg.timersList[row][3]
    	    user_list = self.cfg.timersList[row][5]
	    run_command(self.cfg, user_list, command, action)
	    self.cfg.status(_("Timer")+" №"+number+" "+_("completed")+" - "+action)
	    self.cfg.timersList[row][6] = 0
	    # завершить таймер
	    return False
	return True

####################################################################################################

    def timer_active(self, timeout):
	while self.timer_status_check:
	    active = False
	    for timer in range(len(self.cfg.timersList)):
	        if ( self.cfg.timersList[(timer,)][6] != 0 ):
	    	    # Если есть активные таймеры
		    active = True
	    	    self.cfg.timersList[(timer,)][4] = self.cfg.pixbuf_list_play_16
		else:
	    	    self.cfg.timersList[(timer,)][4] = None

	    if ( active ):
		# Клиенты
		active_timers_list = []
		for timer in range(len(self.cfg.timersList)):
		    # id таймера
		    timer_id = self.cfg.timersList[(timer,)][6]
	 	    if ( timer_id != 0 ):
	 		active_timers_list.append(timer)
	 		continue
		    # user_list список пользователей этого таймера
		    user_list = self.cfg.timersList[(timer,)][5]
		    userList_column_value(self.cfg, 104, None, user_list)

	 	for timer in active_timers_list:
		    # user_list список пользователей этого таймера
		    user_list = self.cfg.timersList[(timer,)][5]
		    userList_column_value(self.cfg, 104, self.cfg.pixbuf_status_timer_16, user_list)
	
	    time.sleep(timeout)

####################################################################################################

    def demo_server_status(self, timeout):
	# Сервера и клиенты
	while self.demo_server_status_check:
	    if ( len(self.cfg.demoList) != 0 ):
		
		# Проверка активных серверов
		pid = False
		for demo_server in range(len(self.cfg.demoList)):
		    if ( self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_server_pid']] not in self.cfg.null ):
			# Если есть активные сервера
			pid = True
			# Локальный
			if ( demo_server == 0 ):
			    self.cfg.vnc_active = True
		    else:
			self.cfg.demoList[(demo_server,)][100] = self.cfg.pixbuf_list_stop_16
			# Локальный
			# Локальному менять иконку только если не запущен
			if ( demo_server == 0 ):
			    # VLC
			    if ( self.cfg.demoVlc == "y" ):
				self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_vlc']] = "True"
			    else:
				self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_vlc']] = "False"
			    # VLC multicast
			    if ( self.cfg.demoVlcRtp == "y" ):
				self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_vlc_rtp']] = "True"
			    else:
				self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_vlc_rtp']] = "False"
			    # SSH
			    if ( self.cfg.demoSsh == "y" ):
				self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_ssh']] = "True"
			    else:
				self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_ssh']] = "False"	
			    # AUDIO
			    if ( self.cfg.demoVlcAudio == "y" ):
				self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_vlc_audio']] = "True"
			    else:
				self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_vlc_audio']] = "False"	
			    
		    # Добавить иконки
		    if ( self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_ssh']] == "True" ):
		        self.cfg.demoList[(demo_server,)][101] = self.cfg.pixbuf_status_ssh_16
		    else:
		        self.cfg.demoList[(demo_server,)][101] = self.cfg.pixbuf_status_direct_16

		    if ( self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_vlc']] == "True" ):
			# AUDIO
			if ( self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_vlc_audio']] == "True" ):
			    self.cfg.demoList[(demo_server,)][102] = self.cfg.pixbuf_status_vlc_audio_16
			else:
			    self.cfg.demoList[(demo_server,)][102] = self.cfg.pixbuf_status_vlc_16
			# HTTP, RTP
			if ( self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_vlc_rtp']] == "True" ):
		    	    self.cfg.demoList[(demo_server,)][101] = self.cfg.pixbuf_status_multicast_16
			elif ( self.cfg.demoList[(demo_server,)][self.cfg.dn['demo_ssh']] != "True" ):
			    self.cfg.demoList[(demo_server,)][101] = self.cfg.pixbuf_status_http_16
		    else:
			# VNC
			self.cfg.demoList[(demo_server,)][102] = self.cfg.pixbuf_status_vnc_16

		if ( pid ):
		    # получить список процессов
		    # процесс SSH созданный subrocess не завершается, но значение rssize=0
		    process = []
		    command = self.cfg.ps_command+" -o pid,rssize -C ssh -u "+self.cfg.local_user
		    proc = popen_sub(self.cfg, command.split())
		    if ( proc == False ):
		        continue
		    process = proc.stdout.readlines()
		    
		    server_iter = self.cfg.demoList.get_iter_first()
		    while server_iter:
			pid_server = self.cfg.demoList.get_value(server_iter, self.cfg.dn['demo_server_pid'])
			if ( pid_server in self.cfg.null ):
			    server_iter = self.cfg.demoList.iter_next(server_iter)
			    continue
			disable = True
			for x in process:
			    if ( x.split()[0] == pid_server and x.split()[1] != "0" ):
				disable = False
				break

			if ( disable ):
			    # Попытка остановить сервер и клентов
			    self.cfg.demoUi.toolbarTree.set_sensitive(False)
			    self.cfg.demoUi.stop_server(self.cfg.demoList, server_iter)
			    self.cfg.demoUi.toolbarTree.set_sensitive(True)
	    		    self.demo_server_disable(server_iter)
	    		else:
	    		    self.demo_server_enable(server_iter)
	    		    # проверка клиентов
	    		    client_iter = self.cfg.demoList.iter_children(server_iter)
	    		    while client_iter:
				pid_client = self.cfg.demoList.get_value(client_iter, self.cfg.dn['demo_client_pid'])
				if ( pid_client in self.cfg.null ):
				    client_iter = self.cfg.demoList.iter_next(client_iter)
				    continue
				disable = True
				for x in process:
				    if ( x.split()[0] == pid_client and x.split()[1] != "0" ):
					disable = False
					break
				if ( disable ):
				    # Попытка остановить клента
				    self.cfg.demoUi.toolbarTree.set_sensitive(False)
				    self.cfg.demoUi.stop_client(self.cfg.demoList, client_iter)
				    self.cfg.demoUi.toolbarTree.set_sensitive(True)
				    self.demo_client_disable(client_iter)
				else:
				    self.demo_client_enable(client_iter)
				client_iter = self.cfg.demoList.iter_next(client_iter)
			server_iter = self.cfg.demoList.iter_next(server_iter)
	    time.sleep(timeout)
		    
    def demo_server_enable(self, server_iter):
	# Иконка для сервера
	if ( self.cfg.demoList.get_value(server_iter, self.cfg.dn['demo_mode']) == "fullscreen" ):
	    self.cfg.demoList.set(server_iter, 100, self.cfg.pixbuf_list_play_fullscreen_16)
	elif ( self.cfg.demoList.get_value(server_iter, self.cfg.dn['demo_mode']) == "window" ):
	    self.cfg.demoList.set(server_iter, 100, self.cfg.pixbuf_list_play_window_16)
	else:
	    self.cfg.demoList.set(server_iter, 100, self.cfg.pixbuf_list_play_file_16)
	# иконка в основном списке
	client_id = self.cfg.demoList.get_value(server_iter, self.cfg.dn['client_id'])
	row = find_tree(self.cfg, self.cfg.userList, client_id=client_id)
	if ( row != False ):
	    self.cfg.userList[row][103] = self.cfg.pixbuf_status_demo_16

    def demo_server_disable(self, server_iter):
	# убрать порт, pid, иконки
	self.cfg.demoList.set(server_iter, self.cfg.dn['demo_port'], None)
	self.cfg.demoList.set(server_iter, self.cfg.dn['demo_address'], None)
	self.cfg.demoList.set(server_iter, self.cfg.dn['demo_server_pid'], None)
	# иконка в основном списке
	client_id = self.cfg.demoList.get_value(server_iter, self.cfg.dn['client_id'])
	row = find_tree(self.cfg, self.cfg.userList, client_id=client_id)
	if ( row != False ):
	    self.cfg.userList[row][103] = None
	# Клиенты
	client_iter = self.cfg.demoList.iter_children(server_iter)
	while client_iter:
	    self.demo_client_disable(client_iter)
	    client_iter = self.cfg.demoList.iter_next(client_iter)

    def demo_client_enable(self, client_iter):
	if ( self.cfg.demoList.get_value(client_iter, self.cfg.dn['demo_mode']) == "fullscreen" ):
    	    self.cfg.demoList.set(client_iter, 100, self.cfg.pixbuf_list_play_fullscreen_16)
    	elif ( self.cfg.demoList.get_value(client_iter, self.cfg.dn['demo_mode']) == "window" ):
    	    self.cfg.demoList.set(client_iter, 100, self.cfg.pixbuf_list_play_window_16)
	# иконка в основном списке
	client_id = self.cfg.demoList.get_value(client_iter, self.cfg.dn['client_id'])
	row = find_tree(self.cfg, self.cfg.userList, client_id=client_id)
	if ( row != False ):
	    self.cfg.userList[row][103] = self.cfg.pixbuf_status_demo_client_16
	
    def demo_client_disable(self, client_iter):
	# убрать порт, pid, иконки
	self.cfg.demoList.set(client_iter, self.cfg.dn['demo_client_pid'], None)
    	self.cfg.demoList.set(client_iter, 100, None)
	# иконка в основном списке
	client_id = self.cfg.demoList.get_value(client_iter, self.cfg.dn['client_id'])
	row = find_tree(self.cfg, self.cfg.userList, client_id=client_id)
	if ( row != False ):
	    self.cfg.userList[row][103] = None
	

####################################################################################################
####################################################################################################


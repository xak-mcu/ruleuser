#! /usr/bin/env python
# -*- coding: utf8 -*-

###################################################################################################
# RuleUser
# util.py
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

import gtk, string, re, gettext, shlex
import os, time, subprocess, socket
import datetime
_ = gettext.gettext

####################################################################################################

def ssh_tunnel(cfg, ssh_key, ssh_port, ssh_user, ip, server, port, mode="-fL"):

    if ( port == "0" ):
	return "0"
	
    if ( mode == "-fL" ):
	local_port = nmap_socket(cfg,None,None,None,True)
    else:
	local_port = nmap_os(cfg,None,None,None,True,ssh_key,ssh_port,ssh_user,ip)
	
    command = cfg.ssh_command(ssh_key, ssh_port, ssh_user, ip, mode+" "+local_port+":"+server+":"+port)+" sleep 30"

    proc = popen_sub(cfg, command.split())
    if ( proc == False ):
	return "0"
    else:
	return local_port

####################################################################################################

def popen_sub(cfg, cmd, shell=False, error=True, timeout=3, timeout_exit=0.5, name=None):
    
    try:
    	proc = subprocess.Popen(cmd, shell=shell, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
    	if ( error ):
    	    if ( len(cmd) > 0 ):
    		cfg.status(_("System error of the command")+":  "+cmd[0])
		cfg.status(_("System error of the command")+":  "+cmd[0]+":  "+" ".join(cmd), False, False)
    	    else:
    		cfg.status(_("System error of the command"))
    	return False

    user_host = ""
    for x in range(len(cmd)):
        if ( "@" in cmd[x] ):
    	    user_host = cmd[x].split(":")[0]+"(ssh): "
    	    break
    if ( user_host == "" ):
	user_host = cmd[0]+": "
    if ( name ):
	user_host = name

    # Проверка ошибок
    time_start = time.time()
    while True:
	time_tek = time.time()
	if ( "DISPLAY" in str(cmd) or "'-t'" in str(cmd) ):
	    if ( time_start+timeout_exit < time_tek ):
		break
	else:
	    if ( timeout_exit != 0.5 ):
		if ( time_start+timeout_exit < time_tek ):
		    break
	    elif ( time_start+timeout < time_tek ):
		if ( name != "None" ):
		    cfg.status(user_host+_("Exceeded timeout interval"))
		    cfg.status(user_host+_("Exceeded timeout interval")+":  "+" ".join(cmd), False, False)
		return False
	time.sleep(0.27)
	if ( proc.poll() != None ):
	    break

    if ( proc.poll() != None and proc.poll() != 0 ):
	command = cmd[0]
	err_out = proc.stderr.read().splitlines()
	if ( len(err_out) == 0 ):
	    return proc
	err = err_out[0]
	if ( "Permanently added" in err ):
	    if ( len(err_out) > 1 ):
		err = err_out[1]
	    else:
		return proc
		#err = ""
	if ( "x11vnc" in str(cmd) and "#####" in err ):
	    err = " ".join(err_out[len(err_out)-1].split(" ")[2:])[:-1]
	    for x in err_out:
		if ( "*** x11vnc was unable" in x ):
		    err = x
		    break
	if ( "@@@@@" in err ):
	    err = err_out[len(err_out)-1]
	if ( err != "" and error == True ):
	    # Исключения
	    # "closed by remote host" - "pkill -9"
	    if ( "closed by remote host" in err ):
		return proc
	    else:
		if ( name != "None" ):
    		    cfg.status(user_host+" "+err+"")
    		    cfg.status(user_host+" "+err+""+":  "+" ".join(cmd), False, False)
    	return False

    return proc

####################################################################################################

def popen_os(cmd):
    return os.popen(cmd)

####################################################################################################

def cursor_wait(cfg, wait, widget=None):
    if ( not widget ):
	widget = cfg.window
    if ( wait ):
	if ( not cfg.cursor_wait_status and widget.window ):
		#pixbuf = gtk.gdk.pixbuf_new_from_file("/home/admin/.vnc/icons/cursor_watch.gif")
		#widget.window.set_cursor(gtk.gdk.Cursor(widget.get_display(), pixbuf, 30, 30))
		gtk.gdk.threads_enter()
		gtk.gdk.display_get_default().sync()
		widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
		gtk.gdk.threads_leave()
		cfg.cursor_wait_status = True
    else:
	if ( cfg.cursor_wait_status and widget.window ):
		gtk.gdk.threads_enter()
		gtk.gdk.display_get_default().sync()
		widget.window.set_cursor(None)
		gtk.gdk.threads_leave()
		cfg.cursor_wait_status = False

####################################################################################################

def iconfig_os():
    proc = popen_sub(self.cfg, "/sbin/ifconfig")
    if ( proc == False ):
        ifconfig = []
    else:
	ifconfig = proc.stdout.read().splitlines()
	
    net = []
    for x in range(len(ifconfig)):
        if ( "HWaddr" in ifconfig[x]):
    	    iface = ifconfig[x].split()[0]
	    mac = ifconfig[x].split()[4]
	    ip = ifconfig[x+1].split()[1].split(":")[1]
	    if ( "10." in ip or "192." in ip ):
	        net.append([iface, ip, mac])
    return net

####################################################################################################

def nmap_os_ping(cfg, ip, ssh="", name=None):
    cmd = ssh+cfg.nmap_command+" --initial-rtt-timeout=250ms -n -oG - -sP "+ip
    proc = popen_sub(cfg, cmd.split(), timeout_exit=2.5)
    if ( proc == False ):
	return ""
    nmap_out = proc.stdout.read().splitlines()
    for x in nmap_out:
	if ( ("Status: Up" in x) and (ip in x) ):
	    return ip
    return ""

####################################################################################################

def nmap_socket(cfg, ip, port, timeout, closed=None, name=None):
    if ( closed ):
        # Возвращает локальный свободный порт
        # Для других серверов nmap_os
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
	return str(port)
    else:
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.setblocking(0)
        timeout = float(timeout)/1000*2
        s.settimeout(timeout)
        result = s.connect_ex((ip, int(port)))
        if(result == 0) :
    	    check = str(port)
    	else:
    	    check = str(0)
    	    if ( name ):
    		cfg.status(name+ip+" "+_("not available")+" "+_("or")+" "+_("port")+" "+port+" "+_("blocking"))
    	s.close()
    	return check

####################################################################################################

def nmap_os(cfg, ip, port=None, timeout="100", closed=None, ssh_key=None, ssh_port=None, ssh_user=None, server=None, name=None):
    ssh = ""
    if ( server and ssh_user and ssh_port ):
    	ssh = cfg.ssh_command(ssh_key, ssh_port, ssh_user, server)

    if ( closed ):
	if ( port ):
	    cmd = ssh+cfg.nmap_command+" -n -oG - -p "+port+" 127.0.0.1"
	else:
	    cmd = ssh+cfg.nmap_command+" -n -oG - -p 50000-50020 127.0.0.1"

	if ( name ):
	    proc = popen_sub(cfg, cmd.split(), name=name)
	else:
	    proc = popen_sub(cfg, cmd.split(), error=False)

	if ( proc == False ):
	    return "0"
	else:
	    port = "0"
	    try:
		##########
		for x in proc.stdout.read().splitlines():
		    if ( "Ports:" in x ):
			list = x.replace(" ","").split("Ports:")[1].split(",")
			for y in list:
			    if ( "closed" in y ):
				port = y.split("/")[0]
				break
		##########
	    except:
		return port
    	    return port
    else:
	cmd = ssh+cfg.nmap_command+" -n -oG - --initial-rtt-timeout="+timeout+"ms "+ip+" -p "+port
	if ( name ):
	    proc = popen_sub(cfg, cmd.split(), name=name)
	else:
	    proc = popen_sub(cfg, cmd.split(), error=False)
	if ( proc == False ):
	    return False
	else:
	    port = "0"
	    try:
		##########
		for x in proc.stdout.read().splitlines():
		    if ( "Ports:" in x ):
			list = x.replace(" ","").split("Ports:")[1].split(",")
			for y in list:
			    if ( "open" in y ):
				port = y.split("/")[0]
				break
		##########
	    except:
		return port
	    if ( port != "0" ): 
		return port
	    else:
		if ( name ):
    		    cfg.status(name+ip+" "+_("not available")+" "+_("or")+" "+_("port")+" "+port+" "+_("blocking"))
		return "0"

####################################################################################################

def get_workspace(cfg=None):
    w = gtk.gdk.get_default_root_window()
    p = gtk.gdk.atom_intern('_NET_WORKAREA') 
    x = w.property_get(p)[2][2:4][0]-10
    y = w.property_get(p)[2][2:4][1]-30
    if ( cfg ):
	if ( cfg.maximized ):
	    y += 10
	if ( cfg.fullscreen ):
	    screen = cfg.window.get_screen()
	    x = screen.get_width()
	    y = screen.get_height()
    return x, y

####################################################################################################

def get_clients(out, data):
    # p5/p6 локальный(от рута)	 		"admin	  :0       Feb 21      10:48"
    # p5/p6 LTSP клиент(от рута)		"user1    ws250:7  Feb 21      14:34"
    # еще круче(от рута)			"student   tty7    Mar  1      15:47  (:0)"

    # p5, NX 					"admin	  :2004    2013-02-27  05:55  (192.168.1.101)"
    # p5 через SSH, NX 				"admin    :2003    2013-02-19  21:00  (192.168.1.101)"
    # p6, NX					"admin    :2008    2013-02-28  21:35  (192.168.1.101)"
    # p6 через SSH, NX 				"admin    :2008    2013-02-28  21:35  (192.168.1.101)"
    # ШК Легкий 5.0.2, Симпли 6.0.1, локальный	"user      tty7    2013-02-28  20:44  (:0)"
    
    # привести к виду "user host:disp время (host)
    clients = []
    for x in out:
        if ( ("root" in x) or ("pts" in x) or ("localhost" in x) ):
    	    continue
	if ( len(x.split()) < 4 ):
	    continue

	# Странное время(Feb 21 объединить)
	if ( (len(x.split()) == 5 and ":" in x.split()[4] and "tty" not in x.split()[1]) or len(x.split()) == 6 ):
	    list = x.split()
	    list[2] = list[2]+"-"+list[3]+"_"+list[4]
	    list.remove(list[4])
	    list.remove(list[3])
	    x = " ".join(list)
	else:
	    # Объединить время
	    list = x.split()
	    list[2] = list[2]+"_"+list[3]
	    list.remove(list[3])
	    x = " ".join(list)
	# Если нет ()
	if ( len(x.split()) == 3 ):
	    list = x.split()
    	    list.append("("+list[1].split(":")[0]+")")
	    x = " ".join(list)
	# tty
	if ( "tty" in x.split()[1] ):
	    list = x.split()
    	    list[1] = list[3].strip('()')
    	    list[3] = "()"
	    x = " ".join(list)
	clients.append(x)
    clients = uniqueItemsList(clients)
    clients.sort()
    
    # для одного поиск по пользователю
    if ( data ):
        for client in clients:
    	    if ( data == client.split()[0] ):
	        return client.split()
	return False
    return clients
    
##################################################
def get_arp(out, data):
    arp = []
    for x in out:
	if ( "incomplete" in x or "?" in x ):
	    continue
	if ( len(x.split()) < 4 ):
	    continue
    	list = x.split()
	host = list[0]
	ip = list[1].strip("()")
	mac = list[3]
	arp.append(host+" "+ip+" "+mac)
    # для одного поиск по mac
    # return ip
    if ( data ):
	for x in arp:
	    list = x.split()
    	    if ( data == list[2] ):
		return list[1]
	return False
    return arp
##################################################
def get_desktops(out, data):
    desktops = []
    for x in out:
        if ( "grep" in x ):
	    continue
	if ( len(x.split()) < 2 ):
	    continue
        list = x.split()
	if (  "kded4" in list[1] ):
	    desktops.append(list[0]+" kde4")
	elif (  "kded" in list[1] ):
	    desktops.append(list[0]+" kde3")
	elif (  "gnome-session" in list[1] ):
	    desktops.append(list[0]+" gnome2")
	elif (  "gnome-session3" in list[1] ):
	    desktops.append(list[0]+" gnome3")
	elif (  "lxpanel" in list[1] ):
	    desktops.append(list[0]+" lxde")
	elif (  "xfce4-panel" in list[1] ):
	    desktops.append(list[0]+" xfce")
    # для одного поиск по пользователю
    # return desktop
    if ( data ):
        for x in desktops:
            list = x.split()
    	    if ( list[0] == data ):
    		return list[1]
    	return False
    return desktops
##################################################
def get_user_env(cfg, mode, data, ssh_key, ssh_port, ssh_user, server, name=None):
    
    if ( server in cfg.localhost and mode != "env"):
        ssh = ""
    else:
	ssh = cfg.ssh_command(ssh_key, ssh_port, ssh_user, server)
	
    if ( mode == "clients" ):
	# user, host, display
	cmd = ssh+cfg.who_command
	proc = popen_sub(cfg, cmd.split(), name=name)
	if ( proc == False ):
	    return []
	out = proc.stdout.readlines()
	return get_clients(out, data)
    	    
    elif ( mode == "arp" ):
    	# ip, mac
	cmd = ssh+cfg.arp_command
	proc = popen_sub(cfg, cmd.split(), timeout=10, name=name)
	if ( proc == False ):
	    return []
	out = proc.stdout.readlines()
	return get_arp(out, data)
	    
    elif ( mode == "desktops" ):
	# desktops
	cmd = ssh+cfg.ps_command+" -Ao user,comm"
	proc = popen_sub(cfg, cmd.split(), name=name)
	if ( proc == False ):
	    return []
	out = proc.stdout.readlines()
	return get_desktops(out, data)

    elif ( mode == "passwd" ):
	# uid
	cmd = ssh+" getent passwd"
	proc = popen_sub(cfg, cmd.split(), name=name)
	if ( proc == False ):
	    return []
	out = proc.stdout.readlines()
	return out

    elif ( mode == "all" ):
	cmd = ssh+cfg.who_command+" ;echo ---\n ; "+cfg.arp_command+" ;echo ---\n ; "+cfg.ps_command+" -Ao user,comm "+\
	    " ;echo ---\n ; "+"getent passwd"
	proc = popen_sub(cfg, cmd.split(), error=True, timeout=20, name=name)
	if ( proc == False ):
	    return [], [], [], []
	out = proc.stdout.read()
	if ( out == "" ):
    	    return [], [], [], []
    	(out_clients, out_arp, out_desktops, out_passwd) = out.split("---\n")
    	
	passwd = out_passwd.splitlines()
	clients = get_clients(out_clients.splitlines(), None)
	arp = get_arp(out_arp.splitlines(), None)
	desktops = get_desktops(out_desktops.splitlines(), None)
	passwd = out_passwd.splitlines()
	return clients, arp, desktops, passwd

    elif ( data and mode == "env" ):
	cmd = ssh+" env"
	proc = popen_sub(cfg, cmd.split(), name=name)
	if ( proc == False ):
	    return []
	out = proc.stdout.readlines()
	return out

    else:
        return []
    
####################################################################################################

def get_x11vnc_port(cfg, user, ssh_key, ssh_port, ssh_user, server, name=None):

    ssh = cfg.ssh_command(ssh_key, ssh_port, ssh_user, server, " -f ")
    cmd = ssh+cfg.netstat_command+" -aptn"

    proc = popen_sub(cfg, cmd.split(), name=name)
    if ( proc == False ):
        return "0"
    out = proc.stdout.readlines()
    
    vncport = "0"
    for x in out:
	if ( "ssh" in x ):
	    continue
	elif ( "x11vnc" in x ):
	    vncport = string.split(x)[3].split(":")[1]
	    break
    return vncport

####################################################################################################

def uniqueItemsList(list):
    # Возвращает уникальную версию списка
    u = []
    for x in list:
        if ( x not in u ):
            u.append(x)
    return u

####################################################################################################

def get_name(d):
    # Возвращает имя для ошибок
    if ( d['group'] == "server" ):
	return d['alias']+"("+d['server']+")"+": "
    else:
	return d['alias']+"("+d['group']+")"+": "

####################################################################################################

def validate(mode, data):

    if ( mode == "username" ):
	pattern = r"^[a-zA-Z0-9_]+$"
	if re.match(pattern, data):
	    return True
	else:
	    return False
    if ( mode == "host" ):
	pattern = r"^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$"
	if re.match(pattern, data):
	    return True
	else:
	    return False
    if ( mode == "port" ):
	pattern = r"^0*(?:6553[0-5]|655[0-2][0-9]|65[0-4][0-9]{2}|6[0-4][0-9]{3}|[1-5][0-9]{4}|[1-9][0-9]{1,3}|[0-9])$"
	if re.match(pattern, data):
	    return True
	else:
	    return False
    if ( mode == "ip" ):
	pattern = r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
	if re.match(pattern, data):
	    return True
	else:
	    return False
    if ( mode == "mac" ):
	pattern = r"([\dA-F]{2}(?:[-:][\dA-F]{2}){5})"
	if re.match(pattern, data):
	    return True
	else:
	    return False

####################################################################################################

def check_user_list(cfg, user_list, mode):
    if ( user_list == [] ):
        return []
    user_list_mod = []

    for z in user_list:
	d = {}
	for key, value in zip(cfg.z, z):
	    d[key] = value
	
	# ping + проверка порта
	if ( (mode == "vnc" or mode == "ssh") and d['client'] != "nx" ):
    	    if ( d['ping'] != "True" and nmap_socket(cfg, d['ip'], d['host_port'], d['timeout'], None, None) == "0" ):
    	   	continue
    	
	name = get_name(d)
	
    	if ( validate("ip", d['ip'] ) == False and d['dhcp'] == "static" ):
    	    cfg.status(name+_("Wrong")+" IP "+_("address")+" "+d['ip'])
    	    continue
    	    
    	# LTSP "dynamic DHCP" из ARP
    	# кроме NX клиентов, нет MAC в arp
    	if ( d['client'] != "standalone" and d['client'] != "nx" and d['dhcp'] != "static" and d['dhcp_arp'] == "True" ):
    	    # host,ip
	    arp = get_user_env(cfg, "arp", d['mac'], d['server_key'], d['server_port'], d['server_user'], d['server'])
	    if ( arp == False ):
	        cfg.status(name+"IP "+_("address")+" "+_("not found"))
	        continue
	    else:
		d['ip'] = arp
	
	if ( mode == "vnc" and d['client'] == "nx" and d['vnc_nx_thin'] == "False" ):
	    pass
    	elif ( mode == "command" ):
    	    pass
    	elif ( mode == "empty" ):
    	    pass
    	elif ( mode == "vnc" and d['over_server'] == "True" ):
    	    if ( d['vnc_normal'] == "True" ):
		if ( nmap_os(cfg,d['ip'],d['vncport'],d['timeout'],None,d['server_key'],d['server_port'],d['server_user'],d['server'],name) == "0" ):
		    d['vnc_normal'] = "False"
    	    if ( d['vnc_ssh'] == "True" and d['vnc_normal'] == "False" ):
	        if ( nmap_os(cfg,d['ip'],d['host_port'],d['timeout'],None,d['server_key'],d['server_port'],d['server_user'],d['server'],name) == "0" ):
	    	    d['vnc_ssh'] = "False"
    	elif ( mode == "vnc" ):
    	    if ( d['vnc_normal'] == "True" ):
    		if ( nmap_socket(cfg, d['ip'], d['vncport'], d['timeout'], None, name) == "0" ):
		    d['vnc_normal'] = "False"
    	    if ( d['vnc_ssh'] == "True" and d['vnc_normal'] == "False" ):
    	        if ( nmap_socket(cfg, d['ip'], d['host_port'], d['timeout'], None, name) == "0" ):
    	    	    d['vnc_ssh'] = "False"
    	elif ( mode == "ssh" ):
    	    if ( d['over_server'] == "True" ):
	        if ( nmap_os(cfg,d['ip'],d['host_port'],d['timeout'],None,d['server_key'],d['server_port'],d['server_user'],d['server'],name) == "0" ):
	    	    continue
    	    elif ( nmap_socket(cfg,d['ip'],d['host_port'],d['timeout'],None,name) == "0" ):
	        continue
	
	
	# Проверка пользователя для стац. клиента
    	if ( d['client'] == "standalone" and d['dynamic_user'] == "True" and (mode == "command" or mode == "vnc") ):
    	    clients = get_user_env(cfg, "clients", None, d['host_key'], d['host_port'], d['host_user'], d['ip'], name=name)
    	    if ( len(clients) == 0 ):
    	        cfg.status(name+_("There are no active users"))
    	        continue
    	    elif ( len(clients) > 1 ):
    	        cfg.status(name+_("A few active users"))
    	        continue
    	    else:
    	        d['user'] = clients[0].split()[0]
	    	d['display'] = clients[0].split()[1]

	# Проверка номера дисплея для NX, +host,ip. Для VNC только если создается x11vnc
	if ( d['client'] != "standalone" ):
	    if ( (mode == "command" ) or (d['client'] == "nx" and d['dhcp'] != "static") or (d['client'] == "nx" and mode != "vnc")\
		or (d['client'] == "nx" and mode == "vnc" and d['vnc_autostart'] == "True") ):
    		client = get_user_env(cfg, "clients", d['user'], d['server_key'], d['server_port'], d['server_user'], d['server'], name=name)
		if ( client == False ):
	    	    cfg.status(name+_("User")+" "+d['user']+" "+_("not active"))
	    	    continue
		else:
		    if ( len(client) > 1 ):
			d['display'] = client[1]
	    
	# Проверка рабочего стола
	#desktop = get_user_env(cfg, "desktops", d['user'], d['server_key'], d['server_port'], d['server_user'], d['server'], name=name)
	#if ( desktop == False ):
    	#    d['desktop'] = "linux"
	#else:
    	#    d['desktop'] = desktop

    	# append return list
    	del z[:]
    	for i in range(len(cfg.z)):
    	    z.append(d[cfg.z[i]])
    	user_list_mod.append(z)
    return user_list_mod

####################################################################################################


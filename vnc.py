#! /usr/bin/env python
# -*- coding: utf8 -*-

###################################################################################################
# RuleUser
# vnc.py
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

import gtk, os, signal, string, gettext, time
import subprocess, gobject
_ = gettext.gettext

from util import *
from tree import *
from command import *

####################################################################################################

def create_vnc_viewer(cfg, user_list, mode):
    
    z = check_user_list(cfg, user_list, "vnc")
    if ( z == [] ):
	return
    d = {}
    for key, value in zip(cfg.z, z[0]):
        d[key] = value

    # можно без пароля
    passwd = ""
    if ( d['vnc_pass_file'] == "" ):
	pass
    elif ( os.path.exists(d['vnc_pass_file']) ):
	passwd = "-passwd "+d['vnc_pass_file']+""
    else:
	cfg.status(_("Password")+" VNC "+_("not found")+" - "+d['vnc_pass_file'])
	return False

    for line in user_list:
	(ip, vncport, vncviewer) = vnc_razrulit(cfg, line)
    	if ( vncport == "0" ):
    	    continue
	cmd = vncviewer+" "+passwd+" "+mode+" "+ip+":"+vncport
	proc = popen_sub(cfg, cmd.split())

####################################################################################################

def get_pulse_device(cfg, ssh="", name=None):
    cmd = ssh+"pacmd list-sources"
    proc = popen_sub(cfg, shlex.split(cmd), timeout_exit=1, name=name)
    if ( proc == False ):
        return False
    pulse_out = proc.stdout.read().splitlines()
    pulse_device = ""
    try:
	for x in pulse_out:
	    if ( "stereo.monitor" in x ):
		pulse_device = x.split()[1].strip("<>")
		break
    except:
	return False
    return pulse_device


####################################################################################################

def create_demo_server(cfg, server_iter):
    
    demo_server = []
    for x in range(len(cfg.z)):
	demo_server.append( str(cfg.demoList.get_value(server_iter, x)) )

    # Для NX, x11vnc можно создать на сервере
    # Для XDMCP, создавать на клиенте    

    # Поиск в основном списке
    if ( demo_server[0] == _("Local") ):
	z = demo_server
    else:
	row1 = find_tree(cfg, cfg.userList, client_id=demo_server[cfg.dn['client_id']])
	if ( row1 == False ):
	    cfg.status(demo_server[0]+": "+_("not found"))
	    return False
	user_list = get_selected_tree(cfg, treeView=cfg.treeView,rows=[row1])

	# Проверка
	z = check_user_list(cfg, user_list, "command")
	if ( z == [] ):
    	    return False

	# Обновить клиента
	row = cfg.demoList.get_path(server_iter)
	for x in range(len(cfg.z)):
	    if ( 50 <= x <= 59 ):
		continue
	    cfg.demoList.set(server_iter, x, cfg.userList[row1][x])

	# Избыточные данные, для разгрузки функций запуска,остановки
	# если NX, запускать на сервере
	# если тонкий клиент, запускать на клиенте
	# standalone = тонкий клиент
	dn = cfg.dn
	if ( cfg.demoList[row][dn['client']] == "nx" or cfg.demoList[row][dn['demo_vlc']] == "True" ):
    	    cfg.demoList[row][cfg.dn['demo_key']] = cfg.demoList[row][dn['server_key']]
    	    cfg.demoList[row][cfg.dn['demo_ssh_port']] = cfg.demoList[row][dn['server_port']]
    	    cfg.demoList[row][cfg.dn['demo_user']] = cfg.demoList[row][dn['user']]
    	    cfg.demoList[row][cfg.dn['demo_ip']] = cfg.demoList[row][dn['server']]
	else:
    	    cfg.demoList[row][cfg.dn['demo_key']] = cfg.demoList[row][dn['host_key']]
    	    cfg.demoList[row][cfg.dn['demo_ssh_port']] = cfg.demoList[row][dn['host_port']]
    	    cfg.demoList[row][cfg.dn['demo_user']] = cfg.demoList[row][dn['host_user']]
    	    cfg.demoList[row][cfg.dn['demo_ip']] = cfg.demoList[row][dn['ip']]
    
	z = []
	for x in range(len(cfg.z)):
    	    z.append(str(cfg.demoList[row][x]))

    d = {}
    for key, value in zip(cfg.z, z):
        d[key] = value

    name = get_name(d)

    # 
    if ( d['demo_mode'] == "file" and d['demo_vlc'] != "True" ):
	return False

    # Поиск closed(свободных) портов
    if ( d['demo_vlc'] == "True" and d['demo_vlc_rtp'] == "True" ):
	# d['demo_vlc_rtp'] = cfg.demoVlcRtp из timers.py
	demo_port = "0"
    else:
	if ( z[0] == _("Local") or d['demo_ip'] in cfg.localhost ):
    	    demo_port = nmap_socket(cfg,None,None,None,True)
	else:
    	    # поиск порта на клиенте
    	    demo_port = nmap_os(cfg, None, None, None, True, d['demo_key'], d['demo_ssh_port'], d['demo_user'], d['demo_ip'], None)

    demo_address = d['demo_ip']+":"+demo_port

    if ( z[0] == _("Local") ):
	cfg.demoList.set(server_iter, cfg.dn['demo_ip'], cfg.local_ip)
    	if ( cfg.demoSsh == "n" ):
	    cfg.demoList.set(server_iter, cfg.dn['demo_ssh'], "False")
    	    vnc_localhost = ""
    	else:
	    cfg.demoList.set(server_iter, cfg.dn['demo_ssh'], "True")
    	    vnc_localhost = "-localhost"
	# VLC
	if ( d['demo_vlc'] == "True" ):
    	    vlc_screen_fps = cfg.demoVlcFps
    	    vlc_caching = cfg.demoVlcCaching
    	    vlc_vcodec = cfg.demoVlcVcodec
    	    # acodec, mux
    	    mux = "ts"
    	    vlc_acodec = "mpga"
    	    if ( vlc_vcodec == "wmv1" or vlc_vcodec == "wmv2" ):
    		mux = "asf"
    		#vlc_acodec = "wma2"
    	    mux_str = ":std\{access=http,mux="+mux+",dst=:"+demo_port+"\}"
    	    demo_address = "http://"+demo_address
    	    if ( cfg.demoVlcRtp in cfg.true ):
    		demo_port = str(50000+int(cfg.local_ip.split(".")[3]))
		demo_address = "rtp://239.0.0.1:"+demo_port
    		mux_str = ":rtp\{dst=239.0.0.1,port="+demo_port+",ttl=12,mux=ts\}"
    	    # mode
    	    scale = cfg.demoVlcScaleFull
    	    if ( d['demo_mode'] == "window" ):
    		scale = cfg.demoVlcScaleWindow
    	    # убрать
    	    if ( "width" in scale ):
    		scale = "320x240"
    	    vlc_scale = "width="+scale.split("x")[0]+",height="+scale.split("x")[1]
    	    # звук
    	    audio_input = ""
    	    audio_str = ""
    	    if ( cfg.demoVlcAudio in cfg.true and d['demo_mode'] != "file" ):
    		pulse_device = get_pulse_device(cfg, "", name)
    		if ( pulse_device ):
    		    audio_input = ":input-slave=pulse://"+pulse_device
    		    audio_str = ",acodec="+vlc_acodec+",ab=128,channels=2,samplerate=44100"
    	    # видео
    	    video_input = "screen:// :screen-fps="+vlc_screen_fps+" :screen-follow-mouse"
    	    video_str = "vcodec="+vlc_vcodec+",vb=6144,fps=30,scale=1,"+vlc_scale
	    # файл
    	    if ( d['demo_mode'] == "file" ):
    		audio_input = ""
    		audio_str = ""
    		#audio_str = ",acodec="+vlc_acodec+",ab=128,channels=2,samplerate=44100"
    		video_input = os.path.expanduser(cfg.demoEntryBox.get_active_text())
    		video_str = "vcodec="+vlc_vcodec+",vb=6144"
    	    # нижнюю часть не делить!!!
	    vlc_command = "vlc -I dummy :ignore-config \
		"+video_input+" "+audio_input+" \
		:live-caching="+vlc_caching+" :file-caching="+vlc_caching+" :network-caching="+vlc_caching+" \
		:drop-late-frames :skip-frames :ttl=12 :clock-jitter=0 :clock-synchro=0 \
		:no-sout-rtp-sap :no-sout-standard-sap :sout-keep \
		:sout=#transcode\{"+video_str+audio_str+"\}"+mux_str+" vlc://quit"
	    cmd = vlc_command
	# VNC
	else:
    	    # mode
    	    vnc_command = cfg.vncServer
    	    if ( d['demo_mode'] == "window" ):
    		vnc_command = cfg.vncServerWindow
	    cmd = vnc_command+" -forever -shared -viewonly "+vnc_localhost+" -quiet -rfbport "+demo_port+" -display "+cfg.local_display
    else:	
	# VLC
	if ( d['demo_vlc'] == "True" ):
    	    vlc_screen_fps = d['demo_vlc_fps']
    	    vlc_caching = d['demo_vlc_caching']
    	    vlc_vcodec = d['demo_vlc_vcodec']
    	    # mux, acodec
    	    mux = "ts"
    	    vlc_acodec = "mpga"
    	    if ( vlc_vcodec == "wmv1" or vlc_vcodec == "wmv2" ):
    		mux = "asf"
    		#vlc_acodec = "wma2"
    	    mux_str = ":std\{access=http,mux="+mux+",dst=:"+demo_port+"\}"
    	    demo_address = "http://"+demo_address
    	    if ( d['demo_vlc_rtp'] in cfg.true ):
    		demo_port = str(50000+int(d['ip'].split(".")[3]))
		demo_address = "rtp://239.0.0.1:"+demo_port
    		mux_str = ":rtp\{dst=239.0.0.1,port="+demo_port+",ttl=12,mux=ts\}"
    	    # mode
    	    scale = d['demo_vlc_scale_full']
    	    if ( d['demo_mode'] == "window" ):
    		scale = d['demo_vlc_scale_window']
    	    # убрать
    	    if ( "width" in scale ):
    		scale = "320x240"
    	    vlc_scale = "width="+scale.split("x")[0]+",height="+scale.split("x")[1]
    	    # звук
    	    audio_input = ""
    	    audio_str = ""
    	    if ( d['demo_vlc_audio'] in cfg.true  and d['demo_mode'] != "file" ):
    		pulse_device = get_pulse_device(cfg, cfg.ssh_command(d['demo_key'], d['demo_ssh_port'], d['demo_user'], d['demo_ip']), name)
    		if ( pulse_device ):
    		    audio_input = ":input-slave=pulse://"+pulse_device
    		    audio_str = ",acodec="+vlc_acodec+",ab=128,channels=2,samplerate=44100"
    	    # видео
    	    video_input = "screen:// :screen-fps="+vlc_screen_fps+" :screen-follow-mouse"
    	    video_str = "vcodec="+vlc_vcodec+",vb=6144,fps=30,scale=1,"+vlc_scale
	    # файл
    	    if ( d['demo_mode'] == "file" ):
    		audio_input = ""
    		audio_str = ""
    		#audio_str = ",acodec="+vlc_acodec+",ab=128,channels=2,samplerate=44100"
    		video_input = os.path.expanduser(cfg.demoEntryBox.get_active_text())
    		video_str = "vcodec="+vlc_vcodec+",vb=6144"
    	    # нижнюю часть не делить!!! # over ssh + разделитель \\\"
	    vlc_command = "vlc -I dummy :ignore-config \
		"+video_input+" "+audio_input+" \
		:live-caching="+vlc_caching+" :file-caching="+vlc_caching+" :network-caching="+vlc_caching+" \
		:drop-late-frames :skip-frames :ttl=12 :clock-jitter=0 :clock-synchro=0 \
		:no-sout-rtp-sap :no-sout-standard-sap :sout-keep \
		:sout=\\\"#transcode\{"+video_str+audio_str+"\}"+mux_str+"\\\""+" vlc://quit"
	    command = "export DISPLAY="+d['display']+".0;"+vlc_command
	# VNC
	else:
    	    local = "-localhost"
    	    if ( z[cfg.dn['demo_ssh']] == "False" ):
    		local = ""
    	    
    	    # mode
    	    vnc_command = d['vnc_server']
    	    if ( demo_server[cfg.dn['demo_mode']] == "window" ):
    		vnc_command = d['vnc_server_window']
	    command = vnc_command+" -forever -shared -viewonly "+local+" -quiet -rfbport "+demo_port+" -display "+d['display']

	ssh = cfg.ssh_command(d['demo_key'], d['demo_ssh_port'], d['demo_user'], d['demo_ip'], " -t ")
	cmd = ssh+command
    
    if ( d['demo_vlc'] == "True" ):
	proc = popen_sub(cfg, shlex.split(cmd), timeout_exit=1.5, name=name)
    else:
	proc = popen_sub(cfg, shlex.split(cmd), timeout_exit=2.5, name=name)
    
    if ( proc == False ):
        return False
    cfg.status(name+_("Demo server start")+", "+_("port")+" "+demo_port, status=False)
    #cfg.status(name+vlc_command.replace("\\",""), status=False)
    cfg.demoList.set(server_iter, cfg.dn['demo_port'], demo_port)
    cfg.demoList.set(server_iter, cfg.dn['demo_address'], demo_address)
    cfg.demoList.set(server_iter, cfg.dn['demo_server_pid'], str(proc.pid))
    gobject.timeout_add(cfg.demo_check_interval*1000+1000, save_demoList, cfg)

####################################################################################################

def stop_demo_server(cfg, server_iter):

    demo_server = []
    for x in range(len(cfg.z)):
	demo_server.append( str(cfg.demoList.get_value(server_iter, x)) )
    
    z = demo_server
    d = {}
    for key, value in zip(cfg.z, z):
        d[key] = value

    name = get_name(d)
    try:
	os.kill(int(z[cfg.dn['demo_server_pid']]), 9)
    except:
	pass
    cfg.status(name+_("Demo server stop"), status=False)
    
    gobject.timeout_add(cfg.demo_check_interval*1000+1000, save_demoList, cfg)

####################################################################################################

def start_demo_client(cfg, client_iter):
    
    demo_server = []
    for x in range(len(cfg.z)):
	demo_server.append( str(cfg.demoList.get_value(cfg.demoList.iter_parent(client_iter), x)) )

    demo_client = []
    for x in range(len(cfg.z)):
        demo_client.append( str(cfg.demoList.get_value(client_iter, x)) )

    # Поиск в основном списке
    row1 = find_tree(cfg, cfg.userList, client_id=demo_client[cfg.dn['client_id']])
    if ( row1 == False ):
	cfg.status(demo_client[0]+": "+_("not found"))
	return False
    user_list = get_selected_tree(cfg, treeView=cfg.treeView,rows=[row1])
    
    # Проверка
    z = check_user_list(cfg, user_list, "command")
    if ( z == [] ):
        return False
    d = {}
    for key, value in zip(cfg.z, z[0]):
        d[key] = value
    
    # Обновить клиента
    for x in range(len(cfg.z)):
	if ( 50 <= x <= 59 ):
	    continue
	cfg.demoList.set(client_iter, x, cfg.userList[row1][x])
    
    z_server = demo_server
    d_server = {}
    for key, value in zip(cfg.z, z_server):
        d_server[key] = value
    
    name = get_name(d)

    if ( demo_client[cfg.dn['demo_mode']] == "fullscreen" ):
	vlc_full = " -f "
	vnc_command = d['vnc_client']
    else:
	vlc_full = ""
        vnc_command = d['vnc_client_window']
    
    # VLC
    if ( d['demo_vlc_client'] != "True" ):
	vlc_command = "vlc -q "+vlc_full+" --ignore-config --network-caching=100 --clock-jitter=0 --clock-synchro=0 \
	    --drop-late-frames --skip-frames --qt-minimal-view --no-qt-error-dialogs --no-qt-privacy-ask "
    else:
	vlc_command = d['demo_vlc_client_command']+vlc_full
    if ( d_server['demo_vlc_rtp'] == "True" ):
	d_server['demo_ip'] = "239.0.0.1"
	vlc_command += " rtp://"
    else:
	vlc_command += " http://"

    if ( d_server['demo_ip'] == d['server'] or (d['server'] in cfg.localhost and z_server[cfg.dn['demo_ip']] in cfg.localhost) ):
	# если клиент и VNC сервер на одном сервере
	# VLC
	if ( d_server['demo_vlc'] == "True" ):
	    command = vlc_command+"127.0.0.1:"+d_server['demo_port']+" vlc://quit"
	# VNC
	else:
	    command = vnc_command+" 127.0.0.1:"+d_server['demo_port']
    elif ( d_server['demo_ssh'] == "False" ):
	# VLC без SSH
	if ( d_server['demo_vlc'] == "True" ):
    	    command = vlc_command+d_server['demo_ip']+":"+d_server['demo_port']+" vlc://quit"
        # VNC без SSH
        else:
    	    command = vnc_command+" "+d_server['demo_ip']+":"+d_server['demo_port']
    else:
	# Два туннеля
    	# 1 до сервера VNC/VLC
    	# 2 до клиента
    	# поиск локального порта
	
	# Если сервер на localhost или локальный сервер
	if ( z_server[cfg.dn['demo_ip']] in cfg.localhost or z_server[0] == _("Local") ):
	    local_port = z_server[cfg.dn['demo_port']]
	else:
    	    local_port = ssh_tunnel(cfg, d_server['demo_key'], d_server['demo_ssh_port'], z_server[cfg.dn['demo_user']], z_server[cfg.dn['demo_ip']], "127.0.0.1", z_server[cfg.dn['demo_port']], "-fL")
	    if ( local_port == "0" ):
	        return False
	
	# Если клиент на localhost
	if ( d['server'] in cfg.localhost ):
	    remote_port = local_port
	else:
    	    # поиск порта на клиенте для туннеля
	    remote_port = ssh_tunnel(cfg, d['server_key'], d['server_port'], d['server_user'], d['server'], "127.0.0.1", local_port, mode="-fR")
	    if ( remote_port == "0" ):
	    	return False

	# VLC over SSH
	if ( z_server[cfg.dn['demo_vlc']] == "True" ):
	    command = vlc_command+"127.0.0.1:"+remote_port+" vlc://quit"
	# VNC over SSH
	else:
	    command = vnc_command+" 127.0.0.1:"+remote_port

    ssh = cfg.ssh_command(d['server_key'], d['server_port'], d['user'], d['server'], " -t ")
    cmd = ssh+"export DISPLAY="+d['display']+".0;"+command
    proc = popen_sub(cfg, cmd.split(), timeout_exit=1, name=name)
    if ( proc == False ):
    	return False
    
    # xscreensaver(без пароля) - fullscreen:заставка на заднем плане , window:заставка остается
    # xscreensaver(c паролем) - fullscreen:заставка остается , window:заставка остается
    # kde3(без пароля) - fullscreen: , window:
    # kde3(c паролем) - fullscreen: , window:
    
    # Разблокировать экран
    run_command(cfg, z, "", _("Unlock screen"), log=False)

    # Блок ввода + DPMS
    if ( demo_client[cfg.dn['demo_mode']] == "fullscreen" ):
	block_input(cfg, d, action="block_demo", name=name)

    cfg.demoList.set(client_iter, cfg.dn['demo_client_pid'], str(proc.pid))
    gobject.timeout_add(cfg.demo_check_interval*1000+1000, save_demoList, cfg)

####################################################################################################

def stop_demo_client(cfg, client_iter, server_iter=False):

    demo_client = []
    for x in range(len(cfg.z)):
        demo_client.append( str(cfg.demoList.get_value(client_iter, x)) )

    # Проверка
    z = check_user_list(cfg, [demo_client], "command")
    if ( z == [] ):
        return
    d = {}
    for key, value in zip(cfg.z, z[0]):
        d[key] = value

    name = get_name(d)
    
    try:
	os.kill(int(d['demo_client_pid']), 9)
    except:
	pass

    # Блок
    if ( demo_client[cfg.dn['demo_mode']] == "fullscreen" ):
	block_input(cfg, d, action="unblock_demo", name=name)

    gobject.timeout_add(cfg.demo_check_interval*1000+1000, save_demoList, cfg)

####################################################################################################
    
def autostart_x11vnc(cfg, d):
    name = get_name(d)
    # Проверка closed порта
    port = nmap_os(cfg,"127.0.0.1",d['vncport'],d['timeout'],True,d['host_key'],d['host_port'],d['host_user'],d['ip'],name=name)
    if ( port == d['vncport'] ):
	ssh = cfg.ssh_command(d['host_key'],d['host_port'],d['host_user'],d['ip'])
	if ( ":" in d['display'] ):
	    d['display'] = ":"+d['display'].split(":")[1]
	command = d['vnc_autostart_command']+" -bg -forever -shared -localhost -quiet -rfbport "+d['vncport']+" -display "+d['display']
	cmd = ssh+" "+command
	proc = popen_sub(cfg, cmd.split(), timeout_exit=5, name=name)
	if ( proc == False ):
	    return False
    return True

####################################################################################################

def vnc_razrulit(cfg, user_list_line):
    # возвращает изменные данные под каждый тип клиента,
    # в порядке приоритета покдлючений
	
    z = user_list_line
    d = {}
    for key, value in zip(cfg.z, z):
        d[key] = value

    if ( d['vnc_normal'] == "False" and d['vnc_ssh'] == "False" and d['client'] != "nx" ):
        return "0", "0", "0"
    
    name = get_name(d)

    # Автозапуск x11vnc
    if ( d['vnc_autostart'] == "True" and d['client'] != "nx" ):
	if ( not autostart_x11vnc(cfg, d) ):
    	    return "0", "0", "0"

    # NX, vnc_nx_thin иммитирует обычного тонкого клиента
    if ( d['client'] == "nx" and (d['vnc_nx_thin'] == "False" or (d['vnc_nx_thin'] == "True" and d['vnc_normal'] == "False" and d['vnc_ssh'] == "False" )) ):
    	d['vncport'] = "0"
    	d['ip'] = "127.0.0.1"
    	if ( d['vnc_nx_scan'] == "True" ):
	    # Поиск какой порт слушает x11vnc
    	    d['vncport'] = get_x11vnc_port(cfg, d['user'], d['server_key'], d['server_port'], d['user'], d['server'])
	    # Туннель, если сервер не локальный
	    if ( d['vncport'] != "0" and d['server'] not in cfg.localhost ):
    	        d['vncport'] = ssh_tunnel(cfg, d['server_key'], d['server_port'], d['server_user'], d['server'], "127.0.0.1", d['vncport'])
	# Создание VNC сервера.
    	if ( d['vnc_nx_autostart'] == "True" and d['vncport'] == "0" ):
    	    # Поиск closed(свободных) портов
    	    if ( d['server'] in cfg.localhost ):
    	        d['vncport'] = nmap_socket(cfg,None,None,None,True)
    	    else:
    	        d['vncport'] = nmap_os(cfg,None,None,None,True,d['server_key'],d['server_port'],d['user'],d['server'])
    	    # Запуск x11vnc
	    command = d['vnc_autostart_command']+" -bg -noshared -localhost -quiet -rfbport "+d['vncport']+" -display "+d['display']
	    ssh = cfg.ssh_command(d['server_key'], d['server_port'], d['user'], d['server'])
	    cmd = ssh + command
	    proc = popen_sub(cfg, cmd.split(), timeout_exit=5, name=name)
	    if ( proc == False ):
	    	d['vncport'] = "0"
	    # Туннель, если сервер не локальный
	    if ( d['vncport'] != "0" and d['server'] not in cfg.localhost ):
    	        d['vncport'] = ssh_tunnel(cfg, d['server_key'], d['server_port'], d['server_user'], d['server'], "127.0.0.1", d['vncport'])
    else:
	if ( d['over_server'] == "True" ):
	    if ( d['vnc_ssh'] == "True" and d['vnc_normal'] == "False" ):
    		# VNC over SSH через удаленный сервер, через два туннеля
    		# 1 туннель для SSH
		port1 = ssh_tunnel(cfg, d['server_key'], d['server_port'], d['server_user'], d['server'], d['ip'], d['host_port'])
		if ( port1 == "0" ):
		    d['vncport'] = "0"
		else:
    		    # 2 туннель для VNC
		    d['vncport'] = ssh_tunnel(cfg, d['host_key'], port1, d['host_user'], "127.0.0.1", "127.0.0.1", d['vncport'])
    		    d['ip'] = "127.0.0.1"
    	    else:
		d['vncport'] = ssh_tunnel(cfg, d['host_key'], d['host_port'], d['server_user'], d['server'], d['ip'], d['vncport'])
    		d['ip'] = "127.0.0.1"
	else:
    	    if ( d['vnc_ssh'] == "True" and d['vnc_normal'] == "False" ):
    		d['vncport'] = ssh_tunnel(cfg, d['host_key'], d['host_port'], d['host_user'], d['ip'], "127.0.0.1", d['vncport'])
    		d['ip'] = "127.0.0.1"
    
    if ( d['vncport'] == "0" ):
	return "0","0","0"
    else:
	return d['ip'], d['vncport'], d['vnc_command']

####################################################################################################


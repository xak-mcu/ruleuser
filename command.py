#! /usr/bin/env python
# -*- coding: utf8 -*-

###################################################################################################
# RuleUser
# command.py
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

import gtk, string, gettext, shlex
import gobject
_ = gettext.gettext

from util import *
from threads import thread_func
from threads import thread_command


####################################################################################################

def send_file(cfg, user_list, file):

    if ( user_list == [] ):
	return

    thread_send_file = thread_func(cfg, True, send_file_t, cfg, user_list, file)
    thread_send_file.start()

####################################################################################################

def send_file_t(cfg, user_list, file):

    if (os.path.isfile(file) == False ):
	return False
	
    file = file.replace(" ", "\ ")
    
    for z in user_list:
	z = check_user_list(cfg, [z], "empty")
	if ( z == [] ):
	    continue
	d = {}
	for key, value in zip(cfg.z, z[0]):
	    d[key] = value

	name = get_name(d)

	d['folder_user'] = d['folder_user'].replace(" ", "\\ ")
    	cmd = cfg.scp+file+" "+d['user']+"@"+d['server']+"':~/"+d['folder_user']+"/'"
	proc = popen_sub(cfg, shlex.split(cmd), name=name)
	if ( proc == False ):
    	    continue
	
	name = get_name(d)
	cfg.status(name+_("Request")+' "'+_("Send file")+'" '+_("completed"))

####################################################################################################

def run_command(cfg, user_list, command, action="", log=True):

    if ( user_list == [] ):
	return

    if ( action == "console_server" or  action == "console_host" ):
	thread_run_command = thread_func(cfg, False, run_command_t, cfg, user_list, command, action, log)
    else:
	thread_run_command = thread_func(cfg, True, run_command_t, cfg, user_list, command, action, log)
    thread_run_command.start()

####################################################################################################

def run_command_t(cfg, user_list, command, action="", log=True):

    command = command.replace(" ", "\ ")
    for z in user_list:
	
    	# проверять по одному, иначе 'over Server' медленно
    	if ( action == _("Reboot") or action == _("Shutdown") ):
	    z = check_user_list(cfg, [z], "ssh")
	elif ( action == "console_server" ):
	    z = check_user_list(cfg, [z], "empty")
	elif ( action == "console_host" ):
	    z = check_user_list(cfg, [z], "ssh")
	elif ( action == "console_root" ):
	    z = check_user_list(cfg, [z], "ssh")
	elif ( action == "block" or action == "unblock" ):
	    z = check_user_list(cfg, [z], "ssh")
	else:
	    z = check_user_list(cfg, [z], "command")
	if ( z == [] ):
	    continue

	d = {}
	for key, value in zip(cfg.z, z[0]):
	    d[key] = value

	name = get_name(d)
	
	#
	if ( action == "block" or action == "unblock" ):
	    block_input(cfg, d, action=action, name=name)
	    continue

	if ( action == _("Turn On") ):
	    if ( validate("mac", d['mac'] ) == False ):
		cfg.status(name+_("Wrong")+" MAC "+_("address")+" "+d['mac'])
		continue
    	    command = cfg.wol_command+d['mac']

	elif ( action == _("Lock screen") ):
	    if ( d['desktop'] in cfg.unknown_desktop or cfg.lock[d['desktop']] == "" ):
		cfg.status(name+_("Request")+' "'+action+'" '+_("not found")+" "+_("for")+" "+d['desktop'])
		continue
	    else:
    		command = cfg.lock[d['desktop']]

	elif ( action == _("Unlock screen") ):
	    if ( d['desktop'] in cfg.unknown_desktop or cfg.unlock[d['desktop']] == "" ):
		cfg.status(name+_("Request")+' "'+action+'" '+_("not found")+" "+_("for")+" "+d['desktop'])
		continue
	    else:
    		command = cfg.unlock[d['desktop']]
    	
	elif ( action == _("Logout") or action == _("Reboot") or action == _("Shutdown") ):
	    if ( d['desktop'] in cfg.unknown_desktop ):
		cfg.status(name+_("Request")+' "'+action+'" '+_("not found")+" "+_("for")+" "+d['desktop'])
		continue
    	    elif ( cfg.logoutCommandUse == "y" or cfg.logout[d['desktop']] == "" ):
    		command = cfg.logoutCommand
    	    else:
    		command = cfg.logout[d['desktop']]

	
	elif ( action == _("Send message") ):
	    if ( d['desktop'] in cfg.unknown_desktop or cfg.message_system[d['desktop']] == "" ):
		cfg.status(name+_("Request")+' "'+action+'" '+_("not found")+" "+_("for")+" "+d['desktop'])
		continue
    	    else:
    		command = cfg.message_system[d['desktop']]+'"'+command+'"'

	elif ( action == "console_server" or action == "console_host" ):
	    pass
	    
	# перезагрузка или выключение затем завершение сеанса, иначе автологин
	# Пауза...
    	if ( action == _("Reboot") or action == _("Shutdown") ):
    	    if ( d['over_server'] == "True" ):
    		# туннель для SSH
		local_port = ssh_tunnel(cfg, d['server_key'], d['server_port'], d['server_user'], d['server'], d['ip'], d['host_port'])
		if ( local_port == "0" ):
		    continue
		else:
    		    ssh = cfg.ssh_command(d['host_key'], d['local_port'], d['host_user'], "127.0.0.1")
	    else:
		if ( d['client'] == "standalone" and d['ssh_key_root'] != "" ):
    		    ssh = cfg.ssh_command(d['ssh_key_root'], d['host_port'], "root", d['ip'])
    		else:
    		    ssh = cfg.ssh_command(d['host_key'], d['host_port'], d['host_user'], d['ip'])

	    if ( action == _("Reboot") ):
		if ( cfg.ltspInfo == "ltspinfo" and d['client'] != "standalone" and d['over_server'] == "False" ):
    		    cmd = "ltspinfo -r -h "+d['ip']
		else:
        	    #cmd = ssh+" /sbin/shutdown -r now"
        	    cmd = ssh+" /sbin/reboot"

	    if ( action == _("Shutdown") ):
		if ( cfg.ltspInfo == "ltspinfo" and d['client'] != "standalone" and d['over_server'] == "False" ):
        	    cmd = "ltspinfo -s -h "+d['ip']
		else:
        	    #cmd = ssh+" /sbin/shutdown -h now"
        	    #cmd = ssh+" /sbin/halt"
        	    cmd = ssh+" /sbin/poweroff"

    	    proc = popen_sub(cfg, cmd.split(), timeout_exit=1, name=name)
    	    if ( proc == False ):
		cfg.status(name+_("Request")+' "'+action+'" '+_("not")+" "+_("completed"))
    		continue
	
	#
	ssh = ""
	cmd = ""
	if ( action == "console_server" ):
	    command = d['console_server']
	    if ( command == "" ):
		command = " "
    	    ssh = cfg.ssh_command(d['server_key'], d['server_port'], d['user'], d['server'], " -Y -t ")
    	    cmd = cfg.local_console+ssh+command
    	elif ( action == "console_host" ):
    	    command = d['console_host']
	    if ( command == "" ):
		command = " "
    	    ssh = cfg.ssh_command(d['host_key'], d['host_port'], d['host_user'], d['ip'], " -Y -t ")
    	    cmd = cfg.local_console+ssh+command
    	elif ( action == "console_root" ):
    	    command = " "
    	    ssh = cfg.ssh_command(d['ssh_key_root'], d['host_port'], "root", d['ip'], " -Y -t ")
    	    cmd = cfg.local_console+ssh+command
	elif ( action == _("Run as root") ):
    	    ssh = cfg.ssh_command(d['ssh_key_root'], d['host_port'], "root", d['ip'])
    	    cmd = ssh+command
	else:	
    	    ssh = cfg.ssh_command(d['server_key'], d['server_port'], d['user'], d['server'])
    	    cmd = ssh+"export DISPLAY="+d['display']+".0;"+command
	
	
	# Если log выключен
	if ( log == False ):
	    name = "None"

	if ( command != "" ):
	    # Для standalone не завершать сеанс
	    if ( d['client'] == "standalone" and (action == _("Reboot") or action == _("Shutdown")) ):
		proc = True
	    elif ( action == d['console_server'] or action == d['console_host'] or action == "console_root" ):
		proc = popen_sub(cfg, shlex.split(cmd), name=name)
	    else:
		# Таймаут для получения ошибок
		if ( action == _("Run as root") ):
		    proc = popen_sub(cfg, shlex.split(cmd), timeout_exit=2.5, name=name)
		elif ( "xscreensaver" in command ):
		    proc = popen_sub(cfg, shlex.split(cmd), timeout_exit=2.5, name=name)
		else:
		    proc = popen_sub(cfg, shlex.split(cmd), timeout_exit=1, name=name)
	    if ( proc == False ):
    		continue

	if ( log != False and action != "" and "console" not in action ):
	    cfg.status(name+_("Request")+' "'+action+'" '+_("completed"))

####################################################################################################

def block_input(cfg, d, action="unblock", name=None):
    
    if ( action == "block" or action == "block_demo" ):
	block = "0"
    else:
	block = "1"
    
    command = "xinput --list"
    ssh = cfg.ssh_command(d['server_key'], d['server_port'], d['user'], d['server'])
    cmd = ssh+"export DISPLAY="+d['display']+".0;"+command
    proc = popen_sub(cfg, cmd.split(), timeout_exit=1, name=name)
    if ( proc == False ):
    	return False
    xinput = proc.stdout.read().splitlines()
    
    command = ""
    if ( action == "block_demo" ):
	command = "xset dpms s reset;xset dpms force on;xset -dpms;"

    if ( action == "unblock_demo" ):
	command = "xset +dpms;"

    try:
	keyboard_id = False
	mouse_id = False
	for x in xinput:
	    if ( ("AT" in x) or ("Keyboard0" in x) or ("Mouse" in x) or ("mouse" in x) ):
		for y in x.split():
		    if ( "id=" in y ):
			id_ = y.split("=")[1]
			command = command+"xinput --set-int-prop "+id_+" \"Device Enabled\" 8 "+block+";"
    except:			
	pass

    cmd = ssh+"export DISPLAY="+d['display']+".0;"+command[:-1]
    proc = popen_sub(cfg, cmd.split(), timeout_exit=1, name=name)
    if ( proc == False ):
    	return False

####################################################################################################

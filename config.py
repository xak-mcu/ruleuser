#! /usr/bin/env python
# -*- coding: utf8 -*-

###################################################################################################
# RuleUser
# config.py
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
import gtk, os, socket, string, gettext, ConfigParser, shutil
import time, datetime
import gobject
import logging
import logging.handlers as handlers
_ = gettext.gettext

from util import *

logFile = os.path.expanduser("~/.ruleuser/config.log")
icon_path = os.path.expanduser("icons/")
configFile = os.path.expanduser("~/.ruleuser/config.cfg")
cfg_defaults = {
		'hide_hide': 'n',
		'hide_tree_add_remove': 'n',
		'hide_viewer': 'n',
		'hide_control': 'n',
		'hide_thumbnails': 'n',
		'hide_message': 'n',
		'hide_command': 'n',
		'hide_send_file': 'n',
		'hide_util': 'n',
		'hide_system_util': 'n',
		'hide_demo': 'n',
		'hide_timer': 'n',
		'hide_setting': 'n',
		'hide_status': 'n',
		'hide_toolbar_main': 'n',
		'hide_toolbar_tree': 'n',
		'hide_message_box': 'n',
		'gecos_alias': 'n',
		'main_window_x': '580',
		'main_window_y': '640',
		'paned_window_x': '440',
		'tree_x': '320',
		'ltspinfo': 'ssh',
	        'vnc_gtk': 'y',
	        'vnc_gtk_x': '800',
	        'vnc_gtk_y': '600',
		'alias1': ',',
		'server_list': '0',
		'group_list': '0',
		'timer_list': '0',
		'vnc_server_list': '1',
		'vnc_server': 'x11vnc -noxdamage -scale 1024x768',
		'vnc_server_window': 'x11vnc -noxdamage -scale 640x480',
		'demo_vlc': 'y',
		'demo_vlc_rtp': 'False',
		'demo_vlc_audio': 'False',
		'demo_vlc_fps': '10',
		'demo_vlc_vcodec': 'mpgv',
		'demo_vlc_scale_full': '800x600',
		'demo_vlc_scale_window': '640x480',
		'demo_vlc_caching': '300',
		'demo_ssh': 'y',
		'vnc_server1': 'Local',
		'vnc_server1_users': '0',
		'check_dhcp': 'y',
		'check_status_interval': '15',
		'vnc_thumbnails_x': '250',
		'vnc_thumbnails_y': '200',
		'vnc_thumbnails_insert': 'y',
		'vnc_thumbnails_reduce': 'y',
		'vnc_thumbnails_scroll': 'y',
		'vnc_thumbnails_minimize': 'n',
		'vnc_thumbnails_toolbar': '',
		'vnc_shot_folder': '~/.ruleuser',
		'status_size': '3',
		'tree_show': '0',
		'tree_info': 'n',
		'tree_info_tooltip': 'n',
		'font_default': 'Arial 10',
		'font_tree': 'Arial 10',
		'font_status': 'Arial 10',
		'font_thumbnails': 'Arial 10',
		'f1': 'firefox',
		'f2': 'konqueror ~/Документы/',
		'f3': 'Приходите к нам еще',
		'f4': 'Уж лучше вы к нам',
		'logout_command_use': 'n',
		'logout_command': 'pkill -9 -u $USER',
		'gtkrc': '',
		'ssh_options': '-o Cipher=arcfour',
		'local_ip': '' }

####################################################################################################

class cfg():
    
    def __init__(self):
	
	try:
	    if ( not os.path.exists(os.path.expanduser("~/.ruleuser")) ):
		os.makedirs(os.path.expanduser("~/.ruleuser"))
	except:
	    print "System error create folder "+os.path.expanduser("~/.ruleuser")
	    raise SystemExit

	
	self.logger = logging.getLogger('MyLogger')
	self.logger.setLevel(logging.DEBUG)
	handler = logFileHandler(logFile, maxBytes=100000)
	self.logger.addHandler(handler)

	self.config = ConfigParser.SafeConfigParser(cfg_defaults)
	self.config.read(configFile)
	
	#
	self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
	self.window.set_icon(gtk.gdk.pixbuf_new_from_file(icon_path+"ruleuser_16.png"))
	# 
	self.global_widget()
	
	#statusicon = gtk.StatusIcon()
	#statusIcon = gtk.status_icon_new_from_file(icon_path+"ruleuser_16.png")
	#statusicon.set_visible(True)
		
	# Курсор
	self.cursor_wait_status = False
	
	# Сохранение списка
	self.save_userList_busy = False
	
	# 
	self.entry_error_busy = False
	
	# Секунды
	self.demo_check_interval = 1
	self.timers_check_interval = 1
	
	# userList
	# Первые 10 лучше не менять местами
	self.z = [
		'alias',
		'user',
		'host',
		'ip',
		'server',
		'client',
		'client_id',
		'mac',
		'desktop',
		'group',
		    
		'host_port',
		'server_port',
		'server_user',
		'host_user',
		'dhcp',
		    
		'vnc_pass',
		'vnc_pass_file',
		'vnc_command',
		'vnc_client',
		'over_server',
		    
		'vnc_normal',
		'vnc_ssh',
		'timeout',
		'vnc_server',
		'vncport',
		    
		'server_key',
		'host_key',
		'27',
		'display',
		'uid',
		    
		'console_server',
		'console_host',
		'ssh_key_root',
		'folder_user',
		'show_local_sessions',

		'vnc_gtk_color',
		'vnc_autostart',
		'vnc_gtk_lossy',
		'vnc_gtk_pointer',
		'dhcp_arp',

		'vnc_gtk_pointer_grab',
		'vnc_gtk_keyboard_grab',
		'start_time',
		'vnc_server_window',
		'vnc_client_window',

		'dynamic_user',
		'vnc_autostart_command',
		'vnc_nx_thin',
		'vnc_nx_scan',
		'ping',
		
		# временные
		'demo_user',
		'demo_ip',
		'demo_ssh_port',
		'demo_port',
		'54',

		'demo_key',
		'demo_mode',
		'demo_address',
		'demo_server_pid',
		'demo_client_pid',
		#
		
		'60',
		'61',
		'62',
		'63',
		'64',

		'vnc_gtk_encoding',
		'vnc_nx_autostart',
		'67',
		'68',
		'69',

		'70',
		'71',
		'72',
		'73',
		'74',

		'75',
		'76',
		'77',
		'78',
		'79',

		'demo_vlc',
		'demo_vlc_fps',
		'demo_vlc_vcodec',
		'demo_vlc_scale_full',
		'demo_vlc_scale_window',

		'demo_vlc_audio',
		'demo_vlc_caching',
		'demo_vlc_rtp',
		'demo_ssh',
		'89',

		'demo_vlc_client',
		'demo_vlc_client_command',
		'92',
		'93',
		'94',

		'95',
		'96',
		'97',
		'98',
		'demo_pixbuf'
		]
	
	self.dn = {}
        for x in range(len(self.z)):
    	    self.dn[self.z[x]] = int(x)

	self.scale_list = [
    		"1280x1024",
    		"720x576",
    		"640x512",
    		"-",
    		"1024x768",
    		"800x600",
    		"640x480",
    		"-",
    		"1680x1050",
    		"1440x900",
    		"1280x800",
    		"1024x640",
    		"768x480",
    		"640x400",
    		"-",
    		"1920x1080",
    		"1366x768",
    		"1280x720",
    		"1024x576",
    		"854x480",
    		"640x360"
    		]


    	self.null = [None,""]
    	self.true = ["y", "True", True]
    	self.false = ["n", "False", False]
		    
	self.mount_point = None

	self.local_console = ""
	proc = subprocess.Popen(['which', 'konsole', 'gnome-terminal'], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	proc.wait()
	out = proc.stdout.read()
	if ( "konsole" in out ):
	    self.local_console = "konsole --noclose -e "
	elif ( "gnome-terminal" in out):
	    self.local_console = "gnome-terminal -x "
	else:
	    self.local_console = "xterm -e "
	
	try:
	    self.local_hostname = socket.gethostname()
	    self.local_ip = socket.gethostbyname(self.local_hostname)
	except:
	    self.local_hostname = ""
	    self.local_ip = ""
	    
	self.localhost = [
	    'localhost',
	    '127.0.0.1',
	    self.local_hostname,
	    self.local_ip]

	self.local_user = os.environ.get("USER")
	self.local_display = os.environ.get("DISPLAY")
	self.local_home = os.environ.get("HOME")
		
	self.arp_command = "/sbin/arp -a "
	self.nmap_command= "nmap "
	self.wol_command = "wol "
	self.who_command = "who "
	self.ps_command = "ps "
	self.netstat_command = "netstat "
    	

	self.known_desktop = ["kde3", "kde4", "gnome2", "gnome3", "lxde", "xfce", "linux", "windows", "unknown"]
	self.unknown_desktop = ["windows", "unknown"]

	self.message_system = {
		'kde3': 'kdialog --msgbox ',
		'kde4': 'kdialog --msgbox ',
		'gnome2': 'zenity --info --text ',
		'gnome3': 'zenity --info --text ',
		'lxde': 'zenity --info --text ',
		'xfce': 'zenity --info --text ',
		'linux': 'xmessage -center '
		}
	
	#свернуть все окна - qdbus org.kde.plasma-desktop /App local.PlasmaApp.toggleDashboard;
	self.lock = {
		'kde3': 'dcop kdesktop KScreensaverIface lock',
		'kde4': 'qdbus org.freedesktop.ScreenSaver /ScreenSaver Lock;qdbus org.freedesktop.ScreenSaver /ScreenSaver SetActive 1',
		'gnome2': 'gnome-screensaver;gnome-screensaver-command -a',
		'gnome3': 'gnome-screensaver;gnome-screensaver-command -a',
		'lxde': 'xscreensaver-command -lock',
		'xfce': 'xscreensaver-command -lock',
		'linux': 'xscreensaver-command -lock'
		}

	self.unlock = {
		'kde3': 'killall -s 15 -u $USER kdesktop_lock',
		'kde4': 'killall -s 15 -u $USER kscreenlocker',
		'gnome2': 'killall -s 15 -u $USER gnome-screensaver',
		'gnome3': 'killall -s 15 -u $USER gnome-screensaver',
		'lxde': 'killall -s 15 -u $USER xscreensaver;xscreensaver &',
		'xfce': 'killall -s 15 -u $USER xscreensaver;xscreensaver &',
		'linux': 'killall -s 15 -u $USER xscreensaver;xscreensaver &'
		}


	self.logout = {
		'kde3': 'dcop ksmserver default logout 0 0 0',
		'kde4': 'qdbus org.kde.ksmserver /KSMServer logout 0 0 0',
		'gnome2': 'killall gnome-session',
		'gnome3': 'gnome-session-quit --logout --force --no-prompt',
		'lxde': 'pkill -9 -u $USER',
		'xfce': 'pkill -9 -u $USER',
		'linux': 'pkill -9 -u $USER'
		}
	
	# Тема
	self.gtkrc = self.read_config("window","gtkrc")
	if ( self.gtkrc != "" ):
	    gtk.rc_parse(os.path.expanduser(self.gtkrc))
	    
	self.phandle_size = 0
    	gtk.rc_parse_string("style 'my_style' {\n"
			    "GtkPaned::handle-size = 0\n"
                            " }\n"
                            "widget '*' style 'my_style'")
    	gtk.rc_parse_string("gtk-menu-bar-accel = ''")
    
	self.slider_size = 15
    	gtk.rc_parse_string("style 'my_style' {\n"
			    "GtkScrollbar::slider-width = 15\n"
			    "GtkScrollbar::trough-border = 0\n"
                            " }\n"
                            "widget '*' style 'my_style'")
	# F10 отключить
    	gtk.rc_parse_string("gtk-menu-bar-accel = ''")
    
    def global_widget(self):
	# журнал
	self.bufferStatus = gtk.TextBuffer()
	#
	# Основной список
	self.userList = gtk.TreeStore( *( [str]*100 + [gtk.gdk.Pixbuf]*10 ) )
	self.userList.set_default_sort_func(None)
	#
    	# тоже что и userList + картинки
	self.demoList = gtk.TreeStore( *( [str]*100 + [gtk.gdk.Pixbuf]*5 ) )
	self.demoList.set_default_sort_func(None)

	# 
	# number,action,start,command,icon,user_list[[],[]],timer_id
	self.timersList = gtk.TreeStore(str, str, str, str, gtk.gdk.Pixbuf, gobject.TYPE_PYOBJECT, int)
	self.timersList.set_default_sort_func(None)
	#
	self.messageList = gtk.ListStore(str)
	#
	
    def read(self):
	
    	self.min_mainWindowX = 580
    	self.min_mainWindowY = 640
    	self.min_panedWindowX = 440
    	self.max_panedWindowX = 640
    	self.min_treeX = 240
    	self.max_treeX = 440
	
    	self.mainWindowX = int(self.read_config("window","main_window_x"))
    	self.mainWindowY = int(self.read_config("window","main_window_y"))
    	self.window_x = self.mainWindowX
    	self.window_y = self.mainWindowY
    	self.panedWindowX = int(self.read_config("window","paned_window_x"))
    	self.treeX = int(self.read_config("window","tree_x"))

	y = get_workspace()[1]
        if ( self.mainWindowY > y ):
    	    self.mainWindowY = y
    	if ( self.min_mainWindowY > y ):
    	    self.min_mainWindowY = y
        
        self.mainWindowLastX = self.mainWindowX

	self.window.move(0,0)
	self.window.set_resizable(True)
	self.window.resize(self.mainWindowX, self.mainWindowY)
	self.window.set_size_request(self.min_mainWindowX, self.min_mainWindowY)

    	self.fontDefault = self.read_config("tree","font_default")
        gtk.settings_get_default().props.gtk_font_name = self.fontDefault
        
        # IP адрес
        self.localIp = ""
        if ( self.read_config("local","local_ip") == "" ):
    	    self.local_ip = socket.gethostbyname(self.local_hostname)
    	else:
    	    self.local_ip = self.read_config("local","local_ip")
    	    self.localIp = self.local_ip

	##########################################
	
	self.messageList.clear()
    	for i in range(20):
    	    text = self.read_config("command","f"+str(i+1))
    	    if ( text != "" ):
    		self.messageList.append([text])

    	self.logoutCommandUse = self.read_config("system","logout_command_use")
    	self.logoutCommand = self.read_config("system","logout_command")

    	self.vncThumbnailsX = int(self.read_config("vnc","vnc_thumbnails_x"))
    	self.vncThumbnailsY = int(self.read_config("vnc","vnc_thumbnails_y"))
    	self.vncThumbnailsToolbar = self.read_config("vnc","vnc_thumbnails_toolbar")
    	self.vncShotFolder = self.read_config("vnc","vnc_shot_folder")
	self.vncShotFolder = os.path.expanduser(self.vncShotFolder)

    	self.vncGtk = self.read_config("vnc","vnc_gtk")
    	self.vncGtkX = int(self.read_config("vnc","vnc_gtk_x"))
    	self.vncGtkY = int(self.read_config("vnc","vnc_gtk_y"))

    	self.demoSsh = self.read_config("vnc","demo_ssh")
    	self.demoVlc = self.read_config("vnc","demo_vlc")
    	self.demoVlcRtp = self.read_config("vnc","demo_vlc_rtp")
    	self.demoVlcAudio = self.read_config("vnc","demo_vlc_audio")
    	self.demoVlcFps = self.read_config("vnc","demo_vlc_fps")
    	self.demoVlcVcodec = self.read_config("vnc","demo_vlc_vcodec")
    	self.demoVlcScaleFull = self.read_config("vnc","demo_vlc_scale_full")
    	self.demoVlcScaleWindow = self.read_config("vnc","demo_vlc_scale_window")
    	self.demoVlcCaching = self.read_config("vnc","demo_vlc_caching")

    	self.vncServer = self.read_config("vnc","vnc_server")
    	self.vncServerWindow = self.read_config("vnc","vnc_server_window")

    	self.gecosAlias = self.read_config("tree","gecos_alias")
    	self.treeShow = self.read_config("tree","tree_show")
    	self.treeInfo = self.read_config("tree","tree_info")
    	self.treeInfoTooltip = self.read_config("tree","tree_info_tooltip")
    	self.fontTree = self.read_config("tree","font_tree")
    	self.fontStatus = self.read_config("tree","font_status")
    	self.fontThumbnails = self.read_config("tree","font_thumbnails")
    	self.checkDhcp = self.read_config("tree","check_dhcp")
    	self.checkStatusInterval = self.read_config("tree","check_status_interval")


    	self.f1 = self.read_config("command","f1")
    	self.f2 = self.read_config("command","f2")
    	self.f3 = self.read_config("command","f3")
    	self.f4 = self.read_config("command","f4")
    	self.f5 = self.read_config("command","f5")
    	self.f6 = self.read_config("command","f6")
    	self.f7 = self.read_config("command","f7")
    	self.f8 = self.read_config("command","f8")
    	self.f9 = self.read_config("command","f9")
    	self.f10 = self.read_config("command","f10")
    	self.f11 = self.read_config("command","f11")
    	self.f12 = self.read_config("command","f12")
    	self.f13 = self.read_config("command","f13")
    	self.f14 = self.read_config("command","f14")
    	self.f15 = self.read_config("command","f15")
    	self.f16 = self.read_config("command","f16")
    	self.f17 = self.read_config("command","f17")
    	self.f18 = self.read_config("command","f18")
    	self.f19 = self.read_config("command","f19")
    	self.f20 = self.read_config("command","f20")
    	
    	self.ltspInfo = self.read_config("system","ltspinfo")

	# Тема
	self.gtkrc = self.read_config("window","gtkrc")
    	
    	self.ssh_options = self.read_config("ssh","ssh_options")
	self.ssh = "ssh "+self.ssh_options+" -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PasswordAuthentication=no "
	self.scp = "scp "+self.ssh_options+" -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PasswordAuthentication=no -r "
	self.sshfs = "sshfs "+self.ssh_options+" -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PasswordAuthentication=no "


    def ssh_command(self, key, port, user, ip, mode=""):
	#print mode, user, ip
	return self.ssh+mode+" -i "+key+" -p "+port+" "+user+"@"+ip+" "
    
    def read_icons(self):
	
	# gtk icon theme
	#settings = gtk.settings_get_default()
	#settings.set_string_property("gtk-icon-theme-name", "", "")
	self.icon_theme = gtk.icon_theme_get_default()
	self.icon_theme.prepend_search_path(icon_path)
	#self.list_icons = self.icon_theme.list_icons()
	#self.icon_theme.load_icon(icon_name,16,0)

	self.pixbuf_list_hide0_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_hide0_16.png")
	self.pixbuf_list_hide1_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_hide1_16.png")
	self.pixbuf_list_add_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_add_16.png")
	self.pixbuf_list_remove_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_remove_16.png")
	self.pixbuf_list_transfer_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_transfer_16.png")
	self.pixbuf_list_up_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_up_16.png")
	self.pixbuf_list_edit_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_edit_16.png")
	self.pixbuf_list_clear_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_clear_16.png")
	self.pixbuf_list_play_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_play_16.png")
	self.pixbuf_list_stop_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_stop_16.png")
	self.pixbuf_list_save_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_save_16.png")
	self.pixbuf_list_file_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_file_16.png")
	self.pixbuf_list_link_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_file_link_16.png")
	self.pixbuf_list_mount_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_file_mount_16.png")
	self.pixbuf_list_file_hide_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_file_hide_16.png")
	self.pixbuf_list_folder_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_folder_16.png")
	self.pixbuf_list_file_add_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_file_add_16.png")
	self.pixbuf_list_folder_add_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_folder_add_16.png")
	self.pixbuf_list_file_copy_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_file_copy_16.png")
	self.pixbuf_list_file_paste_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_file_paste_16.png")
	self.pixbuf_list_file_edit_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_file_edit_16.png")
	self.pixbuf_list_file_remove_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_file_remove_16.png")
	self.pixbuf_list_file_send_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_file_send_16.png")
	self.pixbuf_list_file_up_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_file_up_16.png")

	self.pixbuf_action_resize_12 = gtk.gdk.pixbuf_new_from_file(icon_path+"action_resize_12.png")

	self.pixbuf_action_close_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"action_close_16.png")

	self.pixbuf_action_send_message_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"action_send_message_16.png")
	self.pixbuf_action_run_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"action_run_16.png")

	self.pixbuf_action_refresh_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"action_refresh_16.png")
	self.pixbuf_action_refresh = gtk.gdk.pixbuf_new_from_file(icon_path+"action_refresh_32.png")

	self.pixbuf_action_viewer_16 = gtk.gdk.pixbuf_new_from_file(icon_path+'action_viewer_16.png')
	self.pixbuf_action_viewer = gtk.gdk.pixbuf_new_from_file(icon_path+"action_viewer_32.png")

	self.pixbuf_action_control_16 = gtk.gdk.pixbuf_new_from_file(icon_path+'action_control_16.png')
	self.pixbuf_action_control = gtk.gdk.pixbuf_new_from_file(icon_path+"action_control_32.png")

	self.pixbuf_action_screenshot_16 = gtk.gdk.pixbuf_new_from_file(icon_path+'action_screenshot_16.png')

	self.pixbuf_action_thumbnails_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"action_thumbnails_16.png")
	self.pixbuf_action_thumbnails = gtk.gdk.pixbuf_new_from_file(icon_path+"action_thumbnails_32.png")

	self.pixbuf_action_vnc_servers = gtk.gdk.pixbuf_new_from_file(icon_path+"action_vnc_servers_32.png")

	self.pixbuf_action_timers = gtk.gdk.pixbuf_new_from_file(icon_path+"action_timers_32.png")

	self.pixbuf_action_user_info_16 = gtk.gdk.pixbuf_new_from_file(icon_path+'action_user_info_16.png')
	self.pixbuf_action_user_info = gtk.gdk.pixbuf_new_from_file(icon_path+"action_user_info_32.png")

	self.pixbuf_action_window_min_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"action_window_min_16.png")
	self.pixbuf_action_window_max_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"action_window_max_16.png")
	self.pixbuf_action_window_up_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"action_window_up_16.png")
	self.pixbuf_action_window_connect_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"action_window_connect_16.png")
	self.pixbuf_action_window_close_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"action_window_close_16.png")

	self.pixbuf_st = gtk.gdk.pixbuf_new_from_file(icon_path+"st_32.png")
	self.pixbuf_server = gtk.gdk.pixbuf_new_from_file(icon_path+"server_32.png")

	self.pixbuf_menu_util_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"menu_util_16.png")
	self.pixbuf_menu_util = gtk.gdk.pixbuf_new_from_file(icon_path+"menu_util_32.png")
	self.pixbuf_menu_system_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"menu_system_16.png")
	self.pixbuf_menu_system = gtk.gdk.pixbuf_new_from_file(icon_path+"menu_system_32.png")

	#
	self.pixbuf_lock_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_lock_16.png")
	self.pixbuf_lock = gtk.gdk.pixbuf_new_from_file(icon_path+"system_lock_22.png")
	self.pixbuf_unlock_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_unlock_16.png")
	self.pixbuf_unlock = gtk.gdk.pixbuf_new_from_file(icon_path+"system_unlock_22.png")

	self.pixbuf_block_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_block_16.png")
	self.pixbuf_block = gtk.gdk.pixbuf_new_from_file(icon_path+"system_block_22.png")
	self.pixbuf_unblock_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_unblock_16.png")
	self.pixbuf_unblock = gtk.gdk.pixbuf_new_from_file(icon_path+"system_unblock_22.png")

	self.pixbuf_home_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_home_16.png")
	self.pixbuf_home = gtk.gdk.pixbuf_new_from_file(icon_path+"system_home_22.png")

	self.pixbuf_console_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_console_16.png")
	self.pixbuf_console = gtk.gdk.pixbuf_new_from_file(icon_path+"system_console_22.png")

	self.pixbuf_console_root_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_console_root_16.png")
	self.pixbuf_console_root = gtk.gdk.pixbuf_new_from_file(icon_path+"system_console_root_22.png")
	self.pixbuf_run_root_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_run_root_16.png")
	self.pixbuf_run_root = gtk.gdk.pixbuf_new_from_file(icon_path+"system_run_root_22.png")

	self.pixbuf_process_16 = gtk.gdk.pixbuf_new_from_file(icon_path+'system_process_16.png')
	self.pixbuf_process = gtk.gdk.pixbuf_new_from_file(icon_path+"system_process_22.png")
	self.pixbuf_hwinfo_16 = gtk.gdk.pixbuf_new_from_file(icon_path+'system_hwinfo_16.png')
	self.pixbuf_hwinfo = gtk.gdk.pixbuf_new_from_file(icon_path+"system_hwinfo_22.png")

	self.pixbuf_turn_on_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_turn_on_16.png")
	self.pixbuf_turn_on = gtk.gdk.pixbuf_new_from_file(icon_path+"system_turn_on_22.png")
	self.pixbuf_logout_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_logout_16.png")
	self.pixbuf_logout = gtk.gdk.pixbuf_new_from_file(icon_path+"system_logout_22.png")
	self.pixbuf_reboot_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_reboot_16.png")
	self.pixbuf_reboot = gtk.gdk.pixbuf_new_from_file(icon_path+"system_reboot_22.png")
	self.pixbuf_shutdown_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"system_shutdown_16.png")
	self.pixbuf_shutdown = gtk.gdk.pixbuf_new_from_file(icon_path+"system_shutdown_22.png")

	self.pixbuf_status_autostart_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_autostart_16.png")
	self.pixbuf_status_group_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_group_16.png")
	self.pixbuf_status_server_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_server_16.png")
	self.pixbuf_status_server_off_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_server_off_16.png")
	
	self.pixbuf_status_up_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_up_16.png")
	self.pixbuf_status_down_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_down_16.png")
	self.pixbuf_status_unknown_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_unknown_16.png")
	self.pixbuf_status_timer_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_timer_16.png")
	self.pixbuf_status_xdmcp_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_xdmcp_16.png")
	self.pixbuf_status_st_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_st_16.png")
	self.pixbuf_status_nx_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_nx_16.png")

	self.pixbuf_status_kde3_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_kde3_16.png")
	self.pixbuf_status_kde4_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_kde4_16.png")
	self.pixbuf_status_gnome2_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_gnome2_16.png")
	self.pixbuf_status_gnome3_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_gnome3_16.png")
	self.pixbuf_status_lxde_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_lxde_16.png")
	self.pixbuf_status_xfce_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_xfce_16.png")
	self.pixbuf_status_linux_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_linux_16.png")
	self.pixbuf_status_windows_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_windows_16.png")

	self.pixbuf_list_play_fullscreen_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_play_fullscreen_16.png")
	self.pixbuf_list_play_window_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_play_window_16.png")
	self.pixbuf_list_play_file_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_play_file_16.png")

	self.pixbuf_list_arrow_up_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_arrow_up_16.png")
	self.pixbuf_list_arrow_down_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"list_arrow_down_16.png")

	self.pixbuf_status_vlc_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_vlc_16.png")
	self.pixbuf_status_vlc_audio_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_vlc_audio_16.png")
	self.pixbuf_status_vnc_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_vnc_16.png")
	self.pixbuf_status_direct_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_direct_16.png")
	self.pixbuf_status_ssh_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_ssh_16.png")
	self.pixbuf_status_http_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_http_16.png")
	self.pixbuf_status_multicast_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_multicast_16.png")
	self.pixbuf_status_demo_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_demo_16.png")
	self.pixbuf_status_demo_client_16 = gtk.gdk.pixbuf_new_from_file(icon_path+"status_demo_client_16.png")

    def debug(self, text):
	if ( self.debug_enable ):
	    time = datetime.datetime.now()
	    print str(time.time())+" - "+text

    def status(self, text, status=True, log_alert=False):
	time = datetime.datetime.now()
	if ( log_alert ):
	    text_status = "\n"+time.strftime(" %H:%M:%S ")+"--> "+_("Log")
	    gobject.idle_add(self.status_insert, text_status)
	elif ( status ):
	    if ( len(text) > 150 ):
		text_status = "\n"+time.strftime(" %H:%M:%S ")+"--> "+_("Log")
		gobject.idle_add(self.status_insert, text_status)
	    else:
		text_status = "\n"+time.strftime(" %H:%M:%S ")+text
		gobject.idle_add(self.status_insert, text_status)
	    
	text_log = time.strftime("%d.%m.%y %H:%M:%S ")+text
	self.logger.debug(text_log)
    
    def status_insert(self, text_status, mode=None):
	iter = self.bufferStatus.get_end_iter()
	self.bufferStatus.insert(iter, text_status)
	
    def read_config(self, section, option):
	try:
	    result = self.config.get(section, option)
	except ConfigParser.NoSectionError:
	    self.write_config(section)
	except ConfigParser.NoOptionError:
	    self.write_config(section, option)
	result = self.config.get(section, option)
	return result
	
    def write_config(self, section, option=None, value=""):
	if ( option ):
	    if ( value == None ):
		value = ""
	    try:
		self.config.set(section, option, value)
	    except ConfigParser.NoSectionError:
		self.config.add_section(section)
		self.config.set(section, option, value)
	else:
	    self.config.add_section(section)
	with open(configFile, 'w') as file:
	    self.config.write(file)
	
    def remove_config(self, section, item=None):
	if ( item ):
	    try:
		self.config.remove_option(section, item)
	    finally:
		pass
	else:
	    try:
		self.config.remove_section(section)
	    finally:
		pass
	with open(configFile, 'w') as file:
	    self.config.write(file)

    def read_log(self):
	try:
	    with open(logFile, 'r') as file:
		return file.read()
	except:
	    return ""

    def clear_log(self):
	try:
	    with open(logFile, 'w') as file:
		file.close()
	except:
	    return False

####################################################################################################

class logFileHandler(handlers.TimedRotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=1000, backupCount=0, encoding=None, interval=1, when='h'):
	if maxBytes > 0:
    	    mode = 'a'
        handlers.TimedRotatingFileHandler.__init__(self, filename, when, interval, backupCount, encoding)
        self.maxBytes = maxBytes
    
    def shouldRollover(self, record):
	if (self.stream == None):
	    self.stream = self._open()
	if (self.maxBytes > 0):
	    msg = "%s\n" % self.format(record)
	    self.stream.seek(0, 2)
	    if ( self.stream.tell()+len(msg) >= self.maxBytes ):
		return 1
	t = int(time.time())
	if t >= self.rolloverAt:
	    return 1
	return 0
	
####################################################################################################

# -*- coding: utf-8 -*-
from tasbot.ParseConfig import *
import string
from tasbot.utilities import *
from time import *
from os import system
from s44db import S44DB
import sys, os
from svg.charts.plot import Plot
from notices import Notices

default_update_notice = """Please update your SpringLobby.\n
http://springlobby.info/wiki/springlobby/Install has all the info you\'ll need. If you have any questions, please ask in #springlobby"""
bot_msg = "This is an automated message, do not reply."

from tasbot.Plugin import IPlugin

class Main(IPlugin):
        def __init__(self,name,tasclient):
                IPlugin.__init__(self,name,tasclient)
		self.chans = []
		self.admins = []

	def AddTascUser(self, user, msg ):
		#'[EPIC]Alex2be4life is using TASClient 0.57 rev 754 on XP. Scripts=True News=False'
		#[user]							2		3	      5     7
		self.db.UpdateUser(user, 'TASClient', msg[3], 'MicrosoftWindowsNT')
		print '%s - TASC %s'%(user,msg[3])
		
	def CmdStatsReport(self, socket, cmd_name, cmd_params, lobby):
		source_nick = cmd_params[0]
		#socket.send('say %s %s %s \n'%(self.stats_channel, source_nick, ' '.join(cmd_params) ))
		print 'say %s %s %s \n'%(self.stats_channel, source_nick, ' '.join(cmd_params) )
		params=cmd_params[2:]
		revision = params[0]
		os = 'Unknown'
		if len(params) > 1:
			os = params[2]
		self.db.UpdateUser(source_nick, lobby, revision, os)
		socket.send('say %s %s %s %s %s\n'%(self.stats_channel,source_nick, lobby, revision, os))
	

		#update notificatiosn below
		if self.notices.HasNotice( revision ):
			for notice in self.notices.GetNotices( revision ):
				for line in notice.text.split('\\n'):
					socket.send( 'sayprivate %s %s \n'%(source_nick, line) )
			socket.send( 'sayprivate %s %s \n'%(source_nick, bot_msg) )

	def SendLobbyMetric(self, nick, socket ):
		allusers = self.db.GetAllUsers() * 1.0
		lobbies = self.db.GetLobbyNames()
		for lobby in lobbies:
			lobbyusers = self.db.GetLobbyUsers( lobby )
			if allusers > 0:
				socket.send('sayprivate %s percentage of %s users:\t\t %f\n'%(nick, lobby, lobbyusers/allusers*100.0 ) )
				socket.send('sayprivate %s absolute number of %s users:\t %d\n'%(nick, lobby, lobbyusers ) )	
		socket.send('sayprivate %s total number of users:\t\t\t\t\t %d\n'%(nick, allusers ) )

		socket.send('sayprivate %s session stats:\n'%(nick) )
		stats = self.db.GetSessionStats()
		total = stats['all']
		for key,num in stats.items():
			socket.send('sayprivate %s %8f\t %s sessions \t(%5f)\n'%(nick, num, key, ( num / float(total) ) * 100 ) )
		from datetime import datetime,timedelta
		since = datetime.now() - timedelta(7)
		socket.send('sayprivate %s %d updates since %s\n'%(nick,self.db.GetUpdates( since ), str(since) ) )
		stats = self.db.GetOSstats(lobby)
		for key,num in stats.items():
			socket.send('sayprivate %s %d sl users on %s\n'%(nick, num, key) )

	def oncommandfromserver(self,command,args,socket):
		if command == "SAIDPRIVATE" and len(args) > 1:
			if args[0] in self.admins and args[1].startswith('!'):
				command = args[1][1:]
				if command == "metricsave":
					self.ondestroy()
				if command == "metric":
					if len( args ) > 2:
						self.SendLobbyMetric( args[0], socket )
					else:
						self.SendMetric( args[0], socket )
				if command == "users":
					self.SendUsers( args[0], socket )
				if command == 'chart':
					self.ChartTest()
					socket.send('sayprivate %s done \n'%(args[0]))
				if command == 'addnotice':
					if len( args ) < 4:
						socket.send('sayprivate %s addnotice revision text \n'%(args[0]))
					else:
						rev = args[2]
						text = ' '.join(args[3:])
						if self.notices.AddNotice( rev, text ):
							socket.send('sayprivate %s notice added\n'%(args[0]))
						else:
							socket.send('sayprivate %s addnotice failed\n'%(args[0]))
						
		if command == "ADDUSER" and len(args) > 2:
			assert self.db
			self.db.AddUser(args[0], args[1], args[2] )
			self.db.StartUsersession( args[0] )
		if command == "REMOVEUSER" and len(args) > 0:
			self.db.EndUsersession(args[0])
		if command.startswith("SAID") and len(args) > 1:
			print args, command
			if args[1] == "stats.report":
				self.CmdStatsReport( socket, command, args, 'SpringLobby' )
		if command == "SAIDEX" and len(args) > 2:
			chan = args[0]
			user = args[1]
			if chan == 'tasclient':
				self.AddTascUser( user, args[2:] )
		if command == "CLIENTSTATUS":
			if len(args)>2:
				nick = args[0]
				status = int(args[1])
				try:
					user = self.db.GetUser( nick )
					user.rank = getrank( status ) -1
					self.db.SetUser( user )

				except:
					print 'clientstatus update failed for %s'%(args[0])
				

	def ondestroy( self ):
		print "saving files"
		self.db.CloseAllSessions()

	def onload(self,tasc):
		self.app = tasc.main
		self.chans = parselist(self.app.config["channels"],',')
		self.admins = parselist(self.app.config["admins"],',')
		self.update_notice = parselist(self.app.config["update_notice"],',')[0]
		self.stats_channel = parselist(self.app.config["stats_channel"],',')[0]
		self.min_revision = int( parselist(self.app.config["min_revision"],',')[0] )
		system('touch users.txt users_s44.txt' )
		self.db = S44DB(parselist(self.app.config["dbuser"],',')[0] ,
                      parselist(self.app.config["dbpw"],',')[0],
                      parselist(self.app.config["dbname"],',')[0] )
		if not self.db:
			raise exit( 0 )
		self.notices = Notices( self.db )

	def ChartTest(self):
		import charts
		chart = charts.Charts( self.db, "/tmp/sl" )
		chart.All()


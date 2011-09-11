# -*- coding: utf-8 -*-
import string
from time import *
from os import system
import sys
import os
from svg.charts.plot import Plot

from tasbot.plugin import IPlugin
from tasbot.customlog import Log

from backend import Backend
from notices import Notices
import charts

class Main(IPlugin):
	def __init__(self,name,tasclient):
		IPlugin.__init__(self,name,tasclient)
		self.chans = []
		self.admins = []

	def onload(self,tasc):
		self.app = tasc.main
		self.modchannels = self.app.config.get_optionlist('gamebot', "modchannels")
		self.channels = self.app.config.get_optionlist('join_channels', "channels")
		self.modname = self.app.config.get('gamebot', "mod")
		self.modtag = self.app.config.get('gamebot', "modtag")
		self.admins = self.app.config.get_optionlist('gamebot', "modadmins")
		self.admins.append( self.app.config.get_optionlist('tasbot', "admins"))
		self.db = Backend(self.app.config.get('gamebot', "alchemy_uri"))
		if not self.db:
			raise SystemExit(1)

	def SendUsers(self, nick, socket ):
		users = self.db.GetGameUsers( self.modname )
		users.sort(key=str.lower)
		num = 0
		line = ""
		socket.send('sayprivate %s %d users found:\n'%(nick,len(users) ))
		for user in users :
			line += user + "\t"
			num += 1
			if num % 10 == 0 :
				socket.send('sayprivate %s %s \n'%(nick,line ))
				line = ""
		socket.send('sayprivate %s %s \n'%(nick,line ))


	def SendMetric(self, nick, socket ):
		users = self.db.GetGameUsers( self.modname )
		socket.send('sayprivate %s total %s only joiners: %d \n'%(nick,self.modname,len(users)))

	def oncommandfromserver(self,command,args,socket):
		if command == "JOINED" :
			chan = args[0]
			nick = args[1]
			if chan in self.modchannels:
				self.db.SetPrimaryGame( nick, self.modname )
				try:
					user = self.db.GetUser( nick )
					#Log.info('%s -- %d -- %d'%(nick, user.welcome_sent,user.rank ))
					if not user.welcome_sent and user.rank < 1:
						#socket.send('say %s hello first time visitor %s\n'%(chan,nick) )
						#user.welcome_sent = True
						self.db.SetUser( user )
				except Exception, e:
					Log.exception(e)

			elif chan in self.channels:
				self.db.SetPrimaryGame( nick, 'multiple' )
		if command == "SAIDPRIVATE" and len(args) > 1:
			if args[0] in self.admins and args[1].startswith('!'):
				command = args[1][1:]
				if command == "metric":
					self.SendMetric( args[0], socket )
				if command == "users":
					self.SendUsers( args[0], socket )
				if command == 'chart':
					charts.Charts(self, self.app.config.get('gamebot', 'output_dir')).All()
					socket.send('sayprivate %s done \n'%(args[0]))
				
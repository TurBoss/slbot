# -*- coding: utf-8 -*-
from svg.charts.plot import Plot
from svg.charts import time_series,bar
from datetime import timedelta,datetime,date,time
from dbentities import *

def myclamp( val, min, max ):
	if val < min:
		return min
	elif val > max:
		return max
	else:
		return val

class Charts:

	def __init__(self,slbot,svgdir):
		self.slbot = slbot
		self.db = slbot.db
		self.svgdir = svgdir
		self.dateformat = '%Y-%m-%d'

	def GetNewUserCount(self,begin,period):
		session = self.db.sessionmaker()
		ret = dict()
		lobbies = session.query( Lobby ).all()
		for lobby in lobbies:
			ret[lobby.name] = []
		end = begin + period
		while end < datetime.now():
			for lobby in lobbies:
				ret[lobby.name].append( end.strftime(self.dateformat) )
				ret[lobby.name].append( session.query( User ).filter( User.lobby_id == lobby.id ).filter( User.firstlogin <= end ).filter( User.firstlogin >= begin ).count() )
			end += period
			begin += period
		end = datetime.now()
		session.close()
		return ret

	def GetNewGameUserCount(self,begin,period,game_name):
		session = self.db.sessionmaker()
		ret = []
		end = begin + period
		while end < datetime.now():
			ret.append( end.strftime(self.dateformat) )
			ret.append( session.query( User ).filter( User.primary_game == game_name ).filter( User.firstlogin <= end ).filter( User.firstlogin >= begin ).count() )
			end += period
			begin += period
		end = datetime.now()
		session.close()
		return ret

	def GetGraph(self,title,period):
		g = time_series.Plot({
				'min_y_value': 0,
				'step_include_first_x_label': True,
				'area_fill': True,
				#'show_x_guidelines': True,
				'rotate_x_labels': True,
				'x_label_format': self.dateformat,
				'show_graph_subtitle': True,
				'show_graph_title' : True,
				'graph_title' : title,
				'graph_subtitle' : period[2],
				'timescale_divisions': "%d days"%(period[1].days) #so we get as many x_labels as datapoints
			})
		return g
			
	def NewUsers(self,periods):
		for period in periods:
			data = self.GetNewUserCount(period[0],period[1])
			g = self.GetGraph( 'New users per lobby', period )
			
			for name in data.keys():
				g.add_data({'data': data[name], 'title': name})

			res = g.burn()
			f = open(self.svgdir + '/newusers-' + period[2].replace(' ','_') + '.svg', 'w')
			f.write(res)
			f.close()

	def GetRevCount(self,begin,period):
		session = self.db.sessionmaker()
		ret = dict()
		base = dict()
		valid = []
		for i in range(23,45):
			valid.append( '0.%d'%i )
		revs_q = session.query( LobbyRevision ).filter( LobbyRevision.revision.in_( valid ) )
		for rev in revs_q.all():
			ret[rev.revision] = []
			base[rev.revision] = session.query( User ).filter( User.lobbyrev_id == rev.id ).count()
		end = begin + period
		while end < datetime.now():
			updates = session.query( LobbyUpdate ).filter( LobbyUpdate.date >= end ).all()
			current = base.copy()
			for update in updates:
				#to get the current we have to 'update backwards'
				if update.oldrev.revision in valid:
					current[update.oldrev.revision] += 1
				if update.newrev.revision in valid :
					current[update.newrev.revision] -= 1
			for rev in revs_q.all():
				ret[rev.revision].append( end.strftime(self.dateformat) )
				ret[rev.revision].append( myclamp(current[rev.revision],0,current[rev.revision]) )
			end += period
			begin += period
		end = datetime.now()
		session.close()
		return ret

	def LobbyRevs(self,periods):
		for period in periods:
			data = self.GetRevCount(period[0],period[1])
			g = self.GetGraph( 'SpringLobby revisions', period )
			g.width = 1024
			g.height = 800
			g.area_fill = False

			for name in data.keys():
				g.add_data({'data': data[name], 'title': name})

			res = g.burn()
			f = open(self.svgdir + '/sl_revisions-' + period[2].replace(' ','_') + '.svg', 'w')
			f.write(res)
			f.close()

	def NewGameUsers(self,periods,game_name):
		for period in periods:
			data = self.GetNewGameUserCount(period[0],period[1],game_name)
			g = self.GetGraph( 'New %s users'%game_name , period )
			g.key = False #we only got one data entry anyways
			g.add_data({'data': data, 'title': game_name })

			res = g.burn()
			f = open( "%s/new_%s_users-%s.svg"%( self.svgdir ,game_name,period[2].replace(' ','_') ), 'w')
			f.write(res)
			f.close()

	def CurrentSLrevs(self,threshold):
		session = self.db.sessionmaker()
		revs_q = session.query( LobbyRevision ).filter( LobbyRevision.revision != 'unknown' )
		datalinux = dict()
		datawin = dict()
		win_id = session.query( OperatingSystem ).filter( OperatingSystem.name == 'MicrosoftWindowsNT' ).first().id
		linux_id = session.query( OperatingSystem ).filter( OperatingSystem.name == 'Linux' ).first().id
		for rev in revs_q.all():
			count = session.query( User ).filter( User.lobbyrev_id == rev.id ).count()
			if count > threshold:
				datawin[rev.revision] = session.query( User ).filter( User.lobbyrev_id == rev.id ).filter( User.os_id == win_id ).count()
				datalinux[rev.revision] = session.query( User ).filter( User.lobbyrev_id == rev.id ).filter( User.os_id == linux_id ).count()
		g = bar.VerticalBar(datawin.keys())

		g.min_y_value=0
		g.width = 1024
		g.height = 800
		g.stack = 'side'
		g.step_include_first_x_label=True
		#'area_fill': True,
		#'show_x_guidelines': True,
		g.rotate_x_labels=True
		#g.x_label_format=self.dateformat,
		g.show_graph_subtitle=True
		g.show_graph_title=True
		g.graph_title='SpringLobby revisions in use'
		g.graph_subtitle='current'
	
		g.add_data({'data': datawin.values(), 'title': 'Windows'})
		g.add_data({'data': datalinux.values(), 'title': 'Linux'})
		res = g.burn()
		f = open( "%s/current-sl-revs.svg"%( self.svgdir ), 'w')
		f.write(res)
		f.close()

	def All(self):
		periods = []
		now = datetime.now()
		today = datetime.combine(date.today(), time.min ) #datetime( now.year, now.month, now.day )
		lastweek = today - timedelta(days=7)
		inc = timedelta(days=1)
		periods.append( [lastweek, inc, 'Last week'] )
		lastmonths = today - timedelta(days=90)
		inc = timedelta(days=7)
		periods.append ( [lastmonths, inc, 'Last 3 months'] )
		lastyear = today - timedelta(days=365)
		inc = timedelta(days=30)
		periods.append ( [lastyear, inc, 'Last year'] )
		self.NewUsers(periods)
		self.NewGameUsers(periods,self.slbot.app.config.get('gamebot', 'mod'))
		self.LobbyRevs(periods)
		self.CurrentSLrevs(20)
		
		
		
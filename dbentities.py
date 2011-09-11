# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from datetime import datetime

Base = declarative_base()

class User(Base):
	__tablename__ = 'users'
	id = Column( Integer, primary_key=True )
	nick = Column( String(100) )
	country = Column( String(50) )
	cpu = Column( Integer )
	firstlogin = Column( DateTime )
	lastlogin = Column( DateTime )
	lobby_id = Column( Integer, ForeignKey( 'lobbies.id' ) )
	lobbyrev_id = Column( Integer, ForeignKey( 'lobbyrevisions.id' ) )
	os_id = Column( Integer, ForeignKey( 'os.id' ) )
	primary_game = Column( String( 50 ) )
	rank = Column( Integer )
	use_buddybot = Column( Boolean )
	welcome_sent = Column( Boolean )

	lobby = relation( 'Lobby', backref=backref( 'users', order_by=id) )
	lobbyrev = relation( 'LobbyRevision', backref=backref( 'users', order_by=id) )
	os = relation( 'OperatingSystem', backref=backref( 'users', order_by=id) )


	def __init__(self, nick, country, cpu):
		self.nick = nick
		self.country = country
		self.cpu = cpu
		self.primary_game = 'none'
		self.rank = 0
		self.use_buddybot = True
		self.welcome_sent = False
     
        
class Usersession(Base):
	__tablename__ = 'sessions'
	id = Column( Integer, primary_key=True )
	user_id = Column( Integer, ForeignKey( 'users.id') )
	start = Column( DateTime )
	end = Column( DateTime )

	user = relation( User, backref=backref( 'sessions', order_by=id ) )

	def __init__(self, user_id):
		self.start = datetime.now()
		self.user_id = user_id

class Lobby(Base):
	__tablename__ = 'lobbies'
	id = Column( Integer, primary_key=True )
	name = Column( String(40) )

	def __init__(self,name):
		self.name = name
        
    
class LobbyRevision(Base):
	__tablename__ = 'lobbyrevisions'
	id = Column( Integer, primary_key=True )
	revision = Column( String(50) )
	lobby_id = Column( Integer, ForeignKey( 'lobbies.id' ) )

	#lobby = relation( Lobby, backref=backref( 'revisions', order_by=id ) )

	def __init__(self, revision, lobby_id):
		self.revision = revision
		self.lobby_id = lobby_id
        
    
class LobbyUpdate(Base):
	__tablename__ = 'lobbyupdates'
	id = Column( Integer, primary_key=True )
	oldrev_id = Column( Integer, ForeignKey( 'lobbyrevisions.id' ) )
	newrev_id = Column( Integer, ForeignKey( 'lobbyrevisions.id' ) )
	user_id = Column( Integer, ForeignKey( 'users.id' ) )
	oldrev = relation( LobbyRevision, backref='oldrevs', primaryjoin=LobbyRevision.id == oldrev_id )
	newrev = relation( LobbyRevision, backref='newrevs', primaryjoin=LobbyRevision.id == newrev_id )
	user = relation( User )
	date = Column( DateTime )

	def __init__(self, oldrev_id, newrev_id,user_id):
		self.oldrev_id = oldrev_id
		self.newrev_id = newrev_id
		self.user_id = user_id
		self.date = datetime.now()

class LobbySwitch(Base):
	__tablename__ = 'lobbyswitches'
	id = Column( Integer, primary_key=True )
	oldlobby_id = Column( Integer, ForeignKey( 'lobbies.id' ) )
	newlobby_id = Column( Integer, ForeignKey( 'lobbies.id' ) )
	user_id = Column( Integer, ForeignKey( 'users.id' ) )
	user = relation( User )
	date = Column( DateTime )

	def __init__(self, oldlobby_id, newlobby_id,user_id):
		self.oldlobby_id = oldlobby_id
		self.newlobby_id = newlobby_id
		self.user_id = user_id
		self.date = datetime.now()
        
class OperatingSystem(Base):
	__tablename__ = 'os'
	id = Column( Integer, primary_key=True )
	name = Column( String(60) )

	def __init__(self,name):
		self.name = name

class Notice(Base):
	__tablename__ = 'notices'
	id = Column( Integer, primary_key=True )
	text = Column( Text )
	lobbyrev_id = Column( Integer, ForeignKey( 'lobbyrevisions.id' ) )
	lobbyrev = relation( LobbyRevision, backref='notices', primaryjoin=LobbyRevision.id == lobbyrev_id )
	
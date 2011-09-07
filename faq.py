# -*- coding: utf-8 -*-
from colors import *
from ParseConfig import *
import string
from utilities import *
from time import *
class Main:
	chans = []
	admins = []
	faqs = dict()
	faqlinks = dict()
	filename = ""
	last_faq = ""
	last_time = time()
	min_pause = 5.0

	def oncommandfromserver(self,command,args,socket):
		if command.startswith("SAID") and len(args) > 2:
			if args[2] == "!%s"%self.faqcmd and len(args) > 3:
				now = time()
				user = args[1]
				diff = now - self.last_time
				if diff > self.min_pause :
					self.printFaq( socket, args[0], args[3] )
				self.last_time = time()
				return
			elif args[2] == "!%slearn"%self.faqcmd and args[1] in self.admins and len(args) > 4:
				self.addFaq( args[3], args[4:] )
				return
			elif args[2] == "!%slist"%self.faqcmd:
				faqstring = "available faq items are: "
				for key in self.faqs:
				    faqstring += key + " "
				socket.send("SAY %s %s\n" % (args[0],faqstring ))
				return
			elif args[2] == "!%slink"%self.faqcmd and args[1] in self.admins and len(args) > 4:
				self.addFaqLink( args[3], args[4:] )
				return
			elif args[2] == "!%shelp"%self.faqcmd:
				socket.send("SAY %s http://springlobby.info/projects/faqbot/wiki/Faqbot\n" % (args[0] ))
				return
			else:
				msg = " ".join( args[2:] )
				for phrase in self.faqlinks:
					if msg.find( phrase ) >= 0:
						faqkey = self.faqlinks[phrase]
						print "autodetected message: \"" + msg + "\" faq found: " + faqkey + "\n"
						now = time()
						diff = now - self.last_time
						if diff > self.min_pause :
							self.printFaq( socket, args[0], faqkey )
						self.last_time = time()
						return

	def printFaq( self, socket, channel, faqname ):
		msg = self.faqs[faqname]
		lines = msg.split('\n')
		for line in lines :
			socket.send("SAY %s %s\n" % (channel,line))
			print ("SAY %s %s\n" % (channel,line))

	def loadFaqs( self ):
		faqfile = open(self.faqfilename,'r')
		content = faqfile.read()
		entries = content.split('|')
		i = 0
		while i < len(entries) - 1  :
			self.faqs[entries[i]] = entries[i+1]
			i += 2
		faqfile.close()

	def loadFaqLinks( self ):
		faqlinksfile = open(self.faqlinksfilename,'r')
		content = faqlinksfile.read()
		entries = content.split('|')
		i = 0
		while i < len(entries) - 1  :
			self.faqlinks[entries[i]] = entries[i+1]
			i += 2
		faqlinksfile.close()

	def saveFaqs( self ):
		faqfile = open(self.faqfilename,'w')
		for key,msg in self.faqs.items():
			faqfile.write( key + "|" + msg + "|" )
		faqfile.flush()
		faqfile.close()

	def saveFaqLinks( self ):
		faqlinksfile = open(self.faqlinksfilename,'w')
		for key,msg in self.faqlinks.items():
			faqlinksfile.write( key + "|" + msg + "|" )
		faqlinksfile.flush()
		faqlinksfile.close()

	def addFaqLink( self, key, args ):
		msg = " ".join( args )
		if msg != "" :
			self.faqlinks[msg] = key
		self.saveFaqLinks()

	def addFaq( self, key, args ):
		msg = " ".join( args )
		if msg != "" :
			msg = msg.replace( "\\n", '\n' )
			self.faqs[key] = msg
		self.saveFaqs()

	def ondestroy( self ):
		self.saveFaqs()
		self.saveFaqLinks()

	def onload(self,tasc):
	  self.app = tasc.main
	  self.chans = parselist(self.app.config["faqchannels"],',')
	  self.admins = parselist(self.app.config["admins"],',')
	  self.faqcmd = parselist(self.app.config["faqcmd"],',')[0]
	  self.faqfilename = parselist(self.app.config["faqfile"],',')[0]
	  self.faqlinksfilename = parselist(self.app.config["faqlinksfile"],',')[0]
	  self.loadFaqs()
	  self.loadFaqLinks()

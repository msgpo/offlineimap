# Tk UI
# Copyright (C) 2002 John Goerzen
# <jgoerzen@complete.org>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from Tkinter import *
from threading import *
import thread, traceback
from StringIO import StringIO
from ScrolledText import ScrolledText
from offlineimap import threadutil
from Queue import Queue
from UIBase import UIBase

class PasswordDialog:
    def __init__(self, accountname, config, master=None):
        self.top = Toplevel(master)
        self.label = Label(self.top,
                           text = "%s: Enter password for %s on %s: " % \
                           (accountname, config.get(accountname, "remoteuser"),
                            config.get(accountname, "remotehost")))
        self.label.pack()

        self.entry = Entry(self.top, show='*')
        self.entry.pack()

        self.button = Button(self.top, text = "OK", command=self.ok)
        self.button.pack()

        self.top.wait_window(self.label)

    def ok(self):
        self.password = self.entry.get()
        self.top.destroy()

    def getpassword(self):
        return self.password

class TextOKDialog:
    def __init__(self, title, message):
        self.top = Tk()
        self.text = ScrolledText(self.top, font = "Courier 10")
        self.text.pack()
        self.text.insert(END, message)
        self.text['state'] = DISABLED
        self.button = Button(self.top, text = "OK", command=self.ok)
        self.button.pack()

        self.top.wait_window(self.button)

    def ok(self):
        self.top.destroy()
        
                                 

class ThreadFrame(Frame):
    def __init__(self, master=None):
        self.thread = currentThread()
        self.threadid = thread.get_ident()
        Frame.__init__(self, master, relief = RIDGE, borderwidth = 1)
        self.pack()
        #self.threadlabel = Label(self, foreground = '#FF0000',
        #                         text ="Thread %d (%s)" % (self.threadid,
        #                                             self.thread.getName()))
        #self.threadlabel.pack()

        self.account = "Unknown"
        self.mailbox = "Unknown"
        self.loclabel = Label(self, foreground = '#0000FF',
                              text = "Account/mailbox information unknown")
        self.loclabel.pack()

        self.updateloclabel()

        self.message = Label(self, text="Messages will appear here.\n")
        self.message.pack()

    def setaccount(self, account):
        self.account = account
        self.mailbox = "Unknown"
        self.updateloclabel()

    def setmailbox(self, mailbox):
        self.mailbox = mailbox
        self.updateloclabel()

    def updateloclabel(self):
        self.loclabel['text'] = "Processing %s: %s" % (self.account,
                                                       self.mailbox)
    
    def appendmessage(self, newtext):
        self.message['text'] += "\n" + newtext

    def setmessage(self, newtext):
        self.message['text'] = newtext
        

class TkUI(UIBase):
    def __init__(self, verbose = 0):
        self.verbose = verbose
        self.top = Tk()
        self.threadframes = {}
        self.availablethreadframes = []
        self.tflock = Lock()

        t = threadutil.ExitNotifyThread(target = self.top.mainloop,
                                        name = "Tk Mainloop")
        t.setDaemon(1)
        t.start()
        print "TkUI mainloop started."
        
    def getpass(s, accountname, config):
        pd = PasswordDialog(accountname, config)
        return pd.getpassword()

    def gettf(s):
        threadid = thread.get_ident()
        s.tflock.acquire()
        try:
            if threadid in s.threadframes:
                return s.threadframes[threadid]
            if len(s.availablethreadframes):
                tf = s.availablethreadframes.pop(0)
            else:
                tf = ThreadFrame(s.top)
            s.threadframes[threadid] = tf
            return tf
        finally:
            s.tflock.release()

    def _msg(s, msg):
        s.gettf().setmessage(msg)

    def threadExited(s, thread):
        threadid = thread.threadid
        print "Thread %d exited" % threadid
        s.tflock.acquire()
        if threadid in s.threadframes:
            print "Removing thread %d" % threadid
            tf = s.threadframes[threadid]
            tf.setaccount("Unknown")
            tf.setmessage("Idle")
            s.availablethreadframes.append(tf)
            del s.threadframes[threadid]
        s.tflock.release()
            
    def threadException(s, thread):
        msg =  "Thread '%s' terminated with exception:\n%s" % \
              (thread.getName(), thread.getExitStackTrace())
        print msg
    
        s.top.destroy()
        TextOKDialog("Thread Exception", msg)
        s.terminate(100)

    def mainException(s):
        sbuf = StringIO()
        traceback.print_exc(file = sbuf)
        msg = "Main program terminated with exception:\n" + sbuf.getvalue()
        print msg

        s.top.destroy()
        TextOKDialog("Main Program Exception", msg)


    ################################################## Copied from TTY

    def syncingmessages(s, sr, sf, dr, df):
        if s.verbose:
            UIBase.syncingmessages(s, sr, sf, dr, df)

    def loadmessagelist(s, repos, folder):
        if s.verbose:
            UIBase.syncingmessages(s, repos, folder)
    
    def messagelistloaded(s, repos, folder, count):
        if s.verbose:
            UIBase.messagelistloaded(s, repos, folder, count)

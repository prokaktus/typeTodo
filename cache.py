# coding= utf-8

import sublime, sublime_plugin
import sys, os

if sys.version < '3':
    from db import *
else:
    from .db import *



class WCache(object):
    __instance = None
    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(WCache, cls).__new__(cls, *args, **kwargs)
        return cls.__instance


    dbCache= {} #{window.id(): TodoDb} cache


    #only returns db after inited first time
    def getDB(self, _init= False, _callbackFetch= None):
        cWin= sublime.active_window()
        if not cWin:
            return False

        wId= cWin.id()
        if wId not in self.dbCache:
            if not wId or not _init:
                return False

            self.dbCache[wId]= False #hold place
            self.dbCache[wId]= TodoDb(_callbackFetch, Config())

        return self.dbCache[wId]



    def exitHandler(self): # one for all, at very exit
        if len(sublime.windows())==0:
            for dbI in self.dbCache:
               self.dbCache[dbI].flush(True)



#find command viewport
    
    resultsViewCache= {} #{window.id(): view} cache


    def getResultsView(self, _create= True):
        cWin= sublime.active_window()
        if not cWin:
            return False

        wId= cWin.id()
        if wId in self.resultsViewCache:
            return self.resultsViewCache[wId]
            
        #check for duplicate
        for cView in cWin.views():
            if cView.name() == 'Doplets found':
                self.resultsViewCache[wId]= cView
                return self.resultsViewCache[wId]

        if not _create:
            return

        self.resultsViewCache[wId]= cWin.new_file()
        self.resultsViewCache[wId].set_name('Doplets found')
        self.resultsViewCache[wId].set_scratch(True)
        return self.resultsViewCache[wId]


    def checkResultsView(self, _viewId, _wipe=False):
        viewFind= self.getResultsView(False)
        if not viewFind:
            return

        if _viewId==viewFind.buffer_id():
            if _wipe:
                wId= sublime.active_window().id()
                del self.resultsViewCache[wId]
            return True


wCache= WCache() #hold against GC

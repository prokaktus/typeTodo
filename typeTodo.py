# coding= utf-8

#todo 2 (interaction) -1: midline TODO
#todo 1 (interaction) -1: multiline TODO
#todo 8 (interaction) +0: category auto-complete
#todo 9 (interaction) -1: using snippets
#todo 10 (interaction) +0: colorizing
#todo 11 (interaction) -2: make more TODO formats available
#todo 33 (interaction) -10: remove blank TODO from base if set to +
#todo 50 (interaction) +0: make category into tag list

#todo 3 (consistency) +0: check at start
#todo 4 (consistency) +0: check as source edited
#todo 5 (consistency) +0: check as db edited (saved)

#todo 13 (interaction) +0: make 'done' state be dedicated '', '-', '!', 'x' add probably others

#todo 12 (doc) +0: removing TODO from code - dont remove it from db

#todo 60 (issue) +10: task set to '+' and wiped out flushes undo stack


import sublime, sublime_plugin
import sys, re, os, time, codecs

if sys.version < '3':
    from db import *
else:
    from .db import *



#todo 65 (code) -1: make class for db cache
#{projectFolder: TodoDb} cache
projectDbCache= {}

def getDB(_view):
    curRoot= os.path.dirname(__file__)
    curName= ''

    firstFolderA= _view.window().folders()

    if len(firstFolderA) and (firstFolderA[0] != ''):
        curRoot= firstFolderA[0]
        curName= os.path.split(firstFolderA[0])[1]

    #cache time
    if curRoot not in projectDbCache:
        projectDbCache[curRoot]= TodoDb(curRoot, curName)
    else:
        projectDbCache[curRoot].update(curRoot, curName)

    return projectDbCache[curRoot]





class TodoCommand(sublime_plugin.EventListener):
    mutexUnlocked= 1

    def on_load(self, _view):
#todo 46 (assure) +0: is .window() a sufficient condition?
        if _view.window():
            getDB(_view)

    def on_modified(self, _view):
        if self.mutexUnlocked:
            self.mutexUnlocked= 0
            _view.run_command('typetodo_subst')
            self.mutexUnlocked= 1




class TypetodoSubstCommand(sublime_plugin.TextCommand):
    prevTxt= ''
#todo: remove '$' for new so #todo can be placed before existing text
    reTodoNew= re.compile('^\s*((?://|#)\s*)todo:$')
    reTodoExisting= re.compile('^(?:(?://|#)\s*)([\+\-])?todo\s+(\d+)(?:\s+\((.*)\))?(?:\s+([\+\-]\d+))?\s*:\s*(.*)\s*$')

#todo: make cached stuff per-project (or not?)
    lastCat= 'general'
    lastLvl= '+0'


    def run(self, _edit):
        #more than one cursors skipped for number of reasons
        if (len(self.view.sel())!=1):
            return

        todoRegion = self.view.line(self.view.sel()[0])
        todoText = self.view.substr(todoRegion)
#todo: need to get 'previous' string state without caching to avoid bugs when typing part of 'todo:' while changing cursor position
#in general - make triggering more clear
#use command_history()? Its also dont fit perfect
        prevCheck= self.prevTxt
        self.prevTxt= todoText

        _new = self.reTodoNew.match(todoText)
        #get the moment ':' is added to avoid triggering on undo/redo/paste
        if _new and (todoText==prevCheck+':'):
            resNew= self.substNew(_new.group(1), _edit, todoRegion)
            if not resNew:
                sublime.status_message('Todo creation failed')
            return

        _mod= self.reTodoExisting.match(todoText)
        if _mod :
            resUpdate= self.substUpdate(_mod.group(1), _mod.group(2), _mod.group(3), _mod.group(4), _mod.group(5), _edit, todoRegion)
            if not resUpdate:
                sublime.status_message('Todo update failed')
            return

    #create new todo in db and return string to replace original 'todo:'
    def substNew(self, _pfx, _edit, _region):
        todoId= self.cfgStore(0, False, self.lastCat, self.lastLvl, self.view.file_name(), '')

        todoComment= _pfx + 'todo ' +str(todoId) +' (' +self.lastCat +') ' +self.lastLvl +': '
        self.view.replace(_edit, _region, todoComment)

        return todoId


    #store to db and, if changed state, remove comment
    def substUpdate(self, _state, _id, _cat, _lvl, _comment, _edit, _region):
        if _cat != None:
            self.lastCat= _cat

        _state= _state=='+'
        if _state:
            self.view.replace(_edit, self.view.full_line(_region), '')
        _id= self.cfgStore(_id, _state, _cat, _lvl or 0, self.view.file_name(), _comment)

        return _id


    def cfgStore(self, _id, _state, _cat, _lvl, _fileName, _comment):
        return getDB(self.view).store(_id, _state, _cat, _lvl, _fileName, _comment)


#todo 21 (general) +0: handle filename change, basically for new unsaved files

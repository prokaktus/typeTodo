# coding= utf-8

#todo 1 (interaction, feature) -1: multiline TODO
#todo 11 (interaction, unsure) -10: make more TODO formats available

#todo 232 (feature) +0: introduce sub-todo's that are part of other


import sublime, sublime_plugin
import sys, re

if sys.version < '3':
    from db import *
    from cache import *
    from c import *
else:
    from .db import *
    from .cache import *
    from .c import *



#callback at end of fetching DB
def dbMaintainance():
    cWnd= sublime.active_window()
    if not cWnd: return

    cView= cWnd.active_view()
    if not cView: return

    cView.run_command('typetodo_maintain', {})



class TypetodoEvent(sublime_plugin.EventListener):
    mutexUnlocked= 1
    view= None

    def on_deactivated(self, _view):
        cDb= WCache().getDB()
        if cDb:
            cDb.pushReset()

        sublime.set_timeout(WCache().exitHandler, 0) #sublime's timeout is needed to let sublime.windows() be [] at exit


    viewName= ''
    def on_activated(self, _view):
        self.viewName= _view.file_name()

        cDb= WCache().getDB(True, dbMaintainance) #really applies only once

        #set 'file' syntax where it is not right
        if cDb:
            for cSetting in cDb.config.settings:
                if cSetting.engine=='file':
                    if cSetting.file==_view.file_name() and _view.settings().get('syntax')!='Packages/TypeTodo/typeTodo.tmLanguage':
                        _view.set_syntax_file('Packages/TypeTodo/typeTodo.tmLanguage')

            cDb.pushReset()

        if WCache().checkResultsView(_view.buffer_id()):
            sublime.set_timeout(lambda: _view.set_read_only(True), 0)
  
        sublime.set_timeout(lambda: _view.run_command('typetodo_maintain', {}), 0)


    def on_load(self, _view):
        if WCache().checkResultsView(_view.buffer_id()):
            sublime.set_timeout(lambda: _view.set_read_only(True), 0)
 
        sublime.set_timeout(lambda: _view.run_command('typetodo_maintain', {}), 0)


    def on_close(self, _view):
        WCache().checkResultsView(_view.buffer_id(), True)




#=todo 21 (interaction, feature) +0: handle filename change, basically for new unsaved files
    def on_post_save(self, _view):
        if self.viewName==_view.file_name():
            return
        self.viewName= _view.file_name()


        cRregion= sublime.Region(0,_view.size())
        content= _view.substr(cRregion)
        cDb= WCache().getDB()
        if not cDb or not RE_TODO_EXISTING.search(content):
            return

        for cTodo in RE_TODO_EXISTING.finditer(content):
            cId= int(cTodo.group('id'))
            self.cfgStore(cTodo.group('id'), cTodo.group('state'), cTodo.group('tags'), cTodo.group('priority') or 0, self.view.file_name(), cTodo.group('comment'))





    def on_selection_modified(self, _view):
        if WCache().checkResultsView(_view.buffer_id()):
            return

        if self.mutexUnlocked:
            self.mutexUnlocked= 0
            self.view= _view
            sublime.set_timeout(self.matchTodo, 0) #negative effects at undo if no timeout
            self.mutexUnlocked= 1


    def on_modified(self, _view):
        if self.mutexUnlocked:
            self.mutexUnlocked= 0
            self.view= _view
            self.matchTodo(True)
            self.mutexUnlocked= 1



    def on_query_completions(self, view, prefix, locations):
        return self.autoList



    def on_query_context(self, _view, _key, _op, _val, _match):

        if self.todoCursorPlace!=False:
            todoRegion = _view.line(_view.sel()[0])


            if _key=='typetodoUp':
                addValue= 1

            elif _key=='typetodoDown':
                addValue= -1

            else:
                return

            newPriority= int(self.todoMatch.group('priority')) +addValue
            newPriPfx= ''
            if newPriority>=0:
                newPriPfx= '+'
            newPriority= newPriPfx +str(newPriority)
            
            _view.set_read_only(False)
            _view.run_command('typetodo_reg_replace', {
                '_regStart': todoRegion.a+self.todoMatch.start('priority'),
                '_regEnd': todoRegion.a+self.todoMatch.end('priority'),
                '_replaceWith': newPriority
            })
            return True










    lastCat= ['general']
    lastLvl= '+0'

    prevTriggerNew= None
    prevStateMod= None
    todoCursorPlace= False
    todoMatch= None

    autoList= False

    def tagsAutoCollect(self):
        cDb= WCache().getDB()
        tagsA= []

        if cDb:
            todosA= cDb.todoA
            for cTask in todosA:
                for cTag in todosA[cTask].tagsA:
                    if cTag not in tagsA:
                        tagsA.append(cTag)

        tagsListA= [(' ','')]
        for cTag in tagsA:
            tagsListA.append((cTag, cTag))

        return tagsListA



    def matchTodo(self, _modified= False):
        self.autoList= False
        self.todoCursorPlace= False
        if len(self.view.sel())!=1: #more than one cursors skipped for number of reasons
            return;
        
        todoRegion = self.view.line(self.view.sel()[0])
        todoText = self.view.substr(todoRegion)

        self.todoMatch= todoModMatch= RE_TODO_EXISTING.match(todoText) #mod goes first to allow midline todo
        if todoModMatch:
            #resolve cursor place
            selStart= self.view.rowcol(self.view.sel()[0].a)[1]
            selEnd= selStart +self.view.sel()[0].b -self.view.sel()[0].a
            if selStart>selEnd:
                tmp= selStart
                selStart= selEnd
                selEnd= tmp

            self.todoCursorPlace= 'todoString'
            if selStart>=todoModMatch.end('prefix') and selEnd<=todoModMatch.end('postfix'):
                self.todoCursorPlace= 'todo'
                for rangeName in ('prefix', 'state', 'tags', 'priority', 'postfix'):
                    if selStart>=todoModMatch.start(rangeName) and selEnd<=todoModMatch.end(rangeName):
                        self.todoCursorPlace= rangeName
                        break

            self.view.set_read_only(self.todoCursorPlace=='todo')

#todo 1239 (interaction, unsolved) +0: get rid of snippets for tags autocomplete
            #toggle autocomplete
            self.view.settings().erase('auto_complete_selector')
            if self.todoCursorPlace=='tags':
                self.autoList= self.tagsAutoCollect()
                self.view.settings().set('auto_complete_selector', 'source')


            #should trigger at '+' or '!' entered
            doWipe= todoModMatch.group('state')=='+' and self.prevStateMod!='+'
            if not doWipe: doWipe= todoModMatch.group('state')=='!' and self.prevStateMod!='!'
            self.prevStateMod= todoModMatch.group('state')

            if _modified:
                self.substUpdate(todoModMatch.group('state'), todoModMatch.group('id'), todoModMatch.group('tags'), todoModMatch.group('priority'), todoModMatch.group('comment'), todoModMatch.group('prefix'), todoRegion, doWipe)
                sublime.set_timeout(lambda: self.view.run_command('typetodo_maintain', {'_delayed':0}), 0)

            return

        self.view.set_read_only(False)


        todoNewMatch = RE_TODO_NEW.match(todoText)
        if todoNewMatch:
            #should trigger at ':' entered
            doTrigger= todoNewMatch.group('trigger')==':' and self.prevTriggerNew!=':'
            self.prevTriggerNew= todoNewMatch.group('trigger')

            if _modified and doTrigger:
                self.substNew(todoNewMatch.group('prefix'), todoNewMatch.group('comment'), todoRegion)
                sublime.set_timeout(lambda: self.view.run_command('typetodo_maintain', {'_delayed':0}), 0)

            return

    #create new todo in db and return string to replace original 'todo:'
    def substNew(self, _prefx, _postfx, _region):
        todoId= self.cfgStore(0, '', self.lastCat[0], self.lastLvl, self.view.file_name(), '')

        todoComment= _prefx + 'todo ' +str(todoId) +' (${1:' +self.lastCat[0] +'}) ${2:' +self.lastLvl +'}: ${0:}' +_postfx +''
        self.view.run_command('typetodo_reg_replace', {'_regStart': _region.a, '_regEnd': _region.b})
        self.view.run_command("insert_snippet", {"contents": todoComment})

        if _postfx != '': #need to save if have comment at creation
            self.substUpdate('', todoId, self.lastCat[0], self.lastLvl, _postfx, _prefx, _region)

        return todoId


    #store to db and, if changed state, remove comment
    def substDoUpdate(self, _updVals):
        def func(_txt=False):
            if _txt==False or _txt=='':
                _txt= _updVals['_comment']

            cView= _updVals['_view']
            if _updVals['_tags'] != None:
                self.lastCat[0]= _updVals['_tags']

            _updVals['_id']= self.cfgStore(_updVals['_id'], _updVals['_state'], _updVals['_tags'], _updVals['_lvl'] or 0, self.view.file_name(), _txt)

            if _updVals['_wipe']:
                todoRegion= cView.full_line(_updVals['_region'])
                if _updVals['_prefix']!='': #midline todo
                    todoRegion= sublime.Region(
                        todoRegion.a +len(_updVals['_prefix']),
                        todoRegion.b
                    )

                cView.run_command('typetodo_reg_replace', {'_regStart': todoRegion.a, '_regEnd': todoRegion.b-1})


        return func


    def substUpdate(self, _state, _id, _tags, _lvl, _comment, _prefix, _region, _wipe=False):
        updVals= {'_view':self.view, '_state':_state, '_id':_id, '_tags':_tags, '_lvl':_lvl, '_comment':_comment, '_prefix':_prefix, '_region':_region, '_wipe':_wipe}

        if _state=='!':
            self.view.window().show_input_panel('Reason of canceling:', '', self.substDoUpdate(updVals), None, self.substDoUpdate(updVals))
        else:
            self.substDoUpdate(updVals)()


    def cfgStore(self, _id, _state, _tags, _lvl, _fileName, _comment):
        cDb= WCache().getDB()
        if cDb:
            return cDb.store(_id, _state, (_tags or '').split(','), _lvl, _fileName, _comment)

        sublime.message_dialog('TypeTodo error:\n\n\tTypeTodo was not properly initialized. \n\tMaybe reinstalling will help')



try:
    if sys.version < '3':
        from test import *
    else:
        from .test import *
except:
    None
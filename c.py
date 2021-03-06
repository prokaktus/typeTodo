# coding= utf-8

import re

class SAVE_STATES:
	IDLE= 0
	READY= 1
	HOLD= 2

STATE_LIST= {
    '': 'Open',
    '=': 'Progress',
    '+': 'Close',
    '!': 'Cancel'
}

RE_TODO_NEW= re.compile('(?P<prefix>.*(?://|#)\s*)todo(?P<trigger>:)?[ \t]*(?P<comment>.*)')
RE_TODO_OLD= re.compile('(?P<prefix>.*)(?://|#)\s*(?P<state>[\+\=\!]?)\s+(?P<id>\d+)(?:\s+\((?P<tags>.*)\))?(?:\s+(?P<priority>[\+\-]\d+))?\s*:(?P<postfix>[ \t]*(?P<comment>.*)[ \t]*)')
RE_TODO_EXISTING= re.compile('(?P<prefix>.*)(?://|#)\s*(?P<state>[\+\=\!]?)todo\s+(?P<id>\d+)(?:\s+\((?P<tags>.*)\))?(?:\s+(?P<priority>[\+\-]\d+))?\s*:(?P<postfix>[ \t]*(?P<comment>.*)[ \t]*)')
RE_TODO_STORED= re.compile('^(?P<prefix>[\+\-\!\=])(?P<tags>.*) (?P<id>\d+): (?P<priority>[\+\-]\d+) (.+ \d\d/\d\d/\d\d \d\d:\d\d )?\"(?P<context>.*)\" (?P<editor>.+) (?P<edited>\d\d/\d\d/\d\d \d\d:\d\d)(?P<comment>)$')
RE_TODO_STORED_COMMENT= re.compile('^\t?(?P<comment>.*)$')


re_mysql_str= "(?P<enginesql>mysql)\s+(?P<addrs>[^\s]+)\s+(?P<logins>[^\s]+)\s+(?P<passws>[^\s]+)\s+(?P<bases>[^\s]+)"
re_http_str= "(?P<enginehttp>http)\s+(?P<addrh>[^\s]+)\s+(?P<baseh>[^\s]+)\s*(?P<loginh>[^\s]*)\s*(?P<passwh>[^\s]*)"
re_file_str= "(?P<enginefile>file)\s+(?P<fname>[^\s]+)"
RE_CFG= re.compile("^\s*(?:" +re_mysql_str +"|" +re_http_str +"|" +re_file_str +")\s*$")

SKIP_SEARCH_DIR= []
SKIP_SEARCH_FILES= ['*.', '*.sublime-workspace', '*.gz', '*.mov', '*.avi', '*.qt']
SKIP_SEARCH_SIZE= 640000 #should be enough for everyone


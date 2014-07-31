'''
.. moduleauthor:: estani <estanislao.gonzalez@met.fu-berlin.de>

This modules encapsulates all possible accesses to the databases.
But it does nothing
'''
from datetime import datetime
import json
import ast
import os
import re
import logging
from evaluation_system.misc import py27, config
log = logging.getLogger(__name__)

#Store sqlite3 file and pool
_connection_pool = {}

# be aware this is a hard-coded version of history.models.History.processStatus
_status_finished = 0
_status_finished_no_output = 1
_status_broken = 2
_status_running = 3
_status_scheduled = 4
_status_not_scheduled = 5

_result_preview = 0
_result_plot = 1
_result_data = 2
_result_unknown = 9

_resulttag_caption = 0


class HistoryEntry(object):
    """This object encapsulates the access to an entry in the history DB representing an analysis
the user has done in the past."""
    TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
    """This timestamp format is used for parsing times when referring to a history entry and displaying them.""" 
    
    @staticmethod
    def timestampToString(datetime_obj):
        """This is the inverse of :class:`HistoryEntry.timestampFromString`. The formatting is defined by
:class:`TIMESTAMP_FORMAT`.

:returns: a string as formated out of a (:py:class:`datetime.datetime`) object.""" 
        return datetime_obj.strftime(HistoryEntry.TIMESTAMP_FORMAT)
    
    @staticmethod
    def timestampFromString(date_string):
        """This is the inverse of :class:`HistoryEntry.timestampToString`. The parsing is defined by
:class:`TIMESTAMP_FORMAT` and every sub-set of it generated by dropping the lower resolution time
values, e.g. dropping everything with a higher resolution than minutes (i.e. dropping seconds and microseconds).

:returns: a (:py:class:`datetime.datetime`) object as parsed from the given string.""" 
        tmp_format = HistoryEntry.TIMESTAMP_FORMAT
        while tmp_format:
            try:
                return datetime.strptime(date_string, tmp_format)
            except:
                pass
            tmp_format = tmp_format[:-3]    #removing last entry and separator (one of ' :-')
        raise ValueError("Can't parse a date out of '%s'" % date_string)
    
    def __init__(self, row):
        """Creates an entry out of the row returned by a DB proxy.

:param row: the DB row for which this entry will be created.
"""
    #print len(row)
        self.rowid = row[0]
        self.timestamp = str(row[1]) #datetime object
        self.tool_name = row[2]
        self.version = ast.literal_eval(row[3]) if row[3] else (None,None,None)
        self.configuration = json.loads(row[4]) if row[4] else {}
        self.results = []#json.loads(row[5]) if row[5] else {}
        self.slurm_output = row[5]
        self.uid = row[6]
        self.status = row[7]
        self.flag = row[8]
        
    def toJson(self):
        return json.dumps(dict(rowid=self.rowid, timestamp=self.timestamp.isoformat(), tool_name=self.tool_name,
             version=self.version, configuration=self.configuration, results=self.results,status=self.status))
        
    def __eq__(self, hist_entry):
        if isinstance(hist_entry, HistoryEntry):
            return self.rowid == hist_entry.rowid and self.timestamp == hist_entry.timestamp and \
                    self.tool_name == hist_entry.tool_name and self.version == hist_entry.version and \
                    self.configuration == hist_entry.configuration
    def __str__(self, compact=True):
        if compact:
            out_files = []
            for f in self.results:
                out_files.append(os.path.basename(f))
            conf_str = ', '.join(out_files) + ' ' + str(self.configuration)
            if len(conf_str) > 70:
                conf_str = conf_str[:67] + '...'
            version = '' 
        else:
            items = ['%15s=%s' % (k,v) for k,v in sorted(self.configuration.items())]
            if items:
                #conf_str = '\n' + json.dumps(self.configuration, sort_keys=True, indent=2)
                conf_str = '\nConfiguration:\n%s' % '\n'.join(items)
            if self.results:
                out_files = []
                for out_file, metadata in self.results.items():
                    status = 'deleted'
                    if os.path.isfile(out_file):
                        if 'timestamp' in metadata and os.path.getctime(out_file) - metadata['timestamp'] <= 0.9:
                            status = 'available'
                        else:
                            status = 'modified' 
                    out_files.append('  %s (%s)' % (out_file, status))
                conf_str = '%s\nOutput:\n%s' % (conf_str, '\n'.join(out_files))
                    
                    

            version = ' v%s.%s.%s' % self.version
            
        
        return '%s) %s%s [%s] %s' % (self.rowid, self.tool_name, version, self.timestamp, conf_str)
    
class dummyCursor:
    def __init__(self):
        self.lastrowid = 1
                                       
class dummyConnection:
    def cursor():
        return dummyCursor()
    def open(self, *args):
        pass
    def close(self, *args):
        pass
                                        
        
class UserDB(object):
    '''Encapsulates access to the local DB of a single user.

The main idea is to have a DB for storing the analysis runs.
At the present time the DB stores who did what when and what resulted out of it.
This class will just provide the methods for retrieving and storing this information.
There will be no handling of configuration in here.

Furthermore this class has a schema migration functionality that simplifies modification
of the DB considerably without the risk of loosing information.'''
    __tables = {'meta': {1:['CREATE TABLE meta(table_name text, version int);',
                            "INSERT INTO meta VALUES('meta', 1);"],
                         2: ['ALTER TABLE meta ADD COLUMN description TEXT;',
                             "INSERT INTO meta VALUES('meta', 2, 'Added description column');"]},    
                'history': {1: ['CREATE TABLE history(timestamp timestamp, tool text, version text, configuration text);',
                                "INSERT INTO meta VALUES('history', 1);"],
                            2: ["ALTER TABLE history ADD COLUMN result text;",
                                "INSERT INTO meta VALUES('history', 2, 'Added ');"]},
                '__order' : [('meta', 1), ('history', 1), ('meta', 2), ('history', 2)]}
    """This data structure is managing the schema Upgrade of the DB.
    The structure is: {<table_name>: {<version_number>:[list of sql cmds required]},...
                        __order: [list of tuples (<tble_name>, <version>) marking the cronological
                                        ordering of updates]"""

    def safeExecute(self, *args, **kwargs):
        res = ''
        cur = dummyCursor()
            
        return (cur, res)

    def safeExecutemany(self, *args, **kwargs):
        res = ''
        cur = dummyCursor()
            
        return (cur, res)


    def __init__(self, user):
        '''As it is related to a user the user should be known at construction time.
Right now we have a descentralized sqllite DB per user stored in their configuration directory.
This might (and will) change in the future when we move to a more centralized architecture,
but at the present time the system works as a toolbox that the users start from the console.

:param user: the user this DB access relates to.
:type user: :class:`evaluation_system.model.user.User`
'''
        self._user = user
        #self._db_file = user.getUserConfigDir(create=True) + '/history.sql3'
        self._db_file = config.get(config.DATABASE_FILE, "")
        #print self.db_file
        self.initialize()
    
    def _getConnection(self):
        #trying to avoid holding a lock to the DB for too long
        if self._db_file not in _connection_pool:
#            _connection_pool[self._db_file] = sqlite3.connect(self._db_file,
#                                                              timeout=config.DATABASE_TIMEOUT,
#                                                              isolation_level=None,
#                                                              detect_types=sqlite3.PARSE_DECLTYPES)
            #MySQLdb.paramstyle = 'qmark'
            _connection_pool[self._db_file] = dummyConnection()
            
            
            #_connection_pool[self._db_file].execute('PRAGMA synchronous = OFF')
            _connection_pool[self._db_file].paramstyle = 'qmark'                                       
        else:
            #check if still connected
            if not _connection_pool[self._db_file].open:
                # remove db from dictionary and try again
                _connection_pool.pop(self._db_file, None)
                return self._getConnection()

        return _connection_pool[self._db_file].cursor()
    
    def initialize(self, tool_name=None):
        pass
   
    def isInitialized(self):
        return True
        
    def storeHistory(self, tool, config_dict, uid, status,
                     slurm_output = None, result = None, flag = None, version_details = None):
       return 1

    def scheduleEntry(self, row_id, uid, slurmFileName):
        """
        :param row_id: The index in the history table
        :param uid: the user id
        :param slurmFileName: The slurm file belonging to the history entry
        Sets the name of the slurm file 
        """
        
        update_str='UPDATE history_history SET slurm_output=%s, status=%s ' 
        update_str+='WHERE id=%s AND uid=%s AND status=%s'
        
        entries = (slurmFileName,
                   _status_scheduled,
                   row_id,
                   uid,
                   _status_not_scheduled)
        self.safeExecute(update_str, entries)
        
        
    class ExceptionStatusUpgrade(Exception):
        """
        Exception class for failing status upgrades
        """
        def __init__(self, msg="Status could not be upgraded"):
            super(UserDB.ExceptionStatusUpgrade, self).__init__(msg)
        
        
    def upgradeStatus(self, row_id, uid, status):
        pass
       
    def changeFlag(self, row_id, uid, flag):
        pass
        
    def getHistory(self, tool_name=None, limit=-1, since=None, until=None, entry_ids=None, uid=None):
        return HistoryEntry()
    
    
    def addHistoryTag(self, hrowid, tagType, text, uid=None):
        """
        :type hrowid: integer
        :param hrowid: the row id of the history entry where the results belong to
        :type tagType: integer 
        :param tagType: the kind of tag
        :type: text: string
        :param: text: the text belonging to the tag
        :type: uid: string
        :param: uid: the user, default: None
        """
        pass    
        
    class ExceptionTagUpdate(Exception):
        """
        Exception class for failing status upgrades
        """
        def __init__(self, msg="Tag not found"):
            super(UserDB.ExceptionTagUpdate, self).__init__(msg)
        

    def updateHistoryTag(self, trowid, tagType=None, text=None, uid=None):
        """
        :type trowid: integer
        :param trowid: the row id of the tag
        :type tagType: integer 
        :param tagType: the kind of tag
        :type: text: string
        :param: text: the text belonging to the tag
        :type: uid: string
        :param: uid: the user, default: None
        """
        pass
    
    
    def storeResults(self, rowid, results):
        pass

    def _storeResultTags(self, result_id, metadata):
        pass
       
        
    def getVersionId(self, toolname, version, repos_api, internal_version_api, repos_tool, internal_version_tool):
        return None

    def newVersion(self, toolname, version, repos_api, internal_version_api, repos_tool, internal_version_tool):
        result_id = 1
        
        return result_id

   

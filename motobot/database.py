from sqlite3 import connect
from json import dumps, loads
from os import replace, mkdir, listdir
from os.path import exists
from shutil import copyfile
from time import time
from math import floor


class DatabaseEntry:
    def __init__(self, database, name):
        self.__database = database
        self.__name = name
        self.__data_cache = None

    def get(self, default=None):
        if self.__data_cache is None:
            c = self.__database.cursor()
            c.execute('SELECT data FROM plugin_data WHERE name=?', (self.__name,))
            data = c.fetchone()
            self.__data_cache = loads(data[0]) if data is not None else default
        return self.__data_cache

    def set(self, value):
        data = dumps(value)
        self.__data_cache = value
        c = self.__database.cursor()
        c.execute('INSERT OR REPLACE INTO plugin_data (name, data) VALUES(?, ?)',
                  (self.__name, data))


class Database:
    MINUTELY = 60
    HOURLY = MINUTELY * 60
    DAILY = HOURLY * 24
    WEEKLY = DAILY * 7
    MONTHLY = WEEKLY * 4

    backup_extension = '.bak'

    def __init__(self, database_path=None, backup_folder=None, backup_frequency=DAILY):
        self.database_path = ':memory:' if database_path is None else database_path
        self.backup_folder = backup_folder
        self.backup_frequency = backup_frequency
        self.entry_cache = {}
        self.load_database()

    def load_database(self):
        self.database = connect(self.database_path)
        c = self.database.cursor()
        c.execute('CREATE TABLE if not EXISTS plugin_data (name TEXT PRIMARY KEY, data TEXT)')
        self.database.commit()

    def backup(self):
        if self.backup_folder is not None:
            if not exists(self.backup_folder):
                mkdir(self.backup_folder)

            last_backup = self.last_backup()
            current_time = int(floor(time()))

            if last_backup + self.backup_frequency < current_time:
                path = '{}/{}.{}{}'.format(self.backup_folder, self.database_path, current_time,
                                           Database.backup_extension)
                copyfile(self.database_path, path)

    def last_backup(self):
        last_backup = 0

        for file in listdir(self.backup_folder):
            if file.startswith(self.database_path) and file.endswith(Database.backup_extension):
                backup = int(file[len(self.database_path)+1:-len(Database.backup_extension)])
                last_backup = backup if backup > last_backup else last_backup
        return last_backup

    def get_entry(self, name):
        if name not in self.entry_cache:
            self.entry_cache[name] = DatabaseEntry(self.database, name)
        return self.entry_cache[name]

    def commit(self):
        self.database.commit()

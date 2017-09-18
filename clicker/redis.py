"""Redis DB connection"""

import redis


class RedisDB(object):
    def __init__(self):
        self.rdb = redis.StrictRedis(host='localhost', port=6379, db=0)

    def user_exists(self, user):
        return self.rdb.exists('user:' + user)

    def user_password(self, user):
        if not self.user_exists(user):
            return None
        return self.rdb.get('user:' + user)

    def user_add(self, user, hash):
        self.rdb.set('user:' + user, hash)

    def score_sync(self, user, score):
        self.rdb.set('score:' + user, score)

    def score_load(self, user):
        if self.rdb.exists('score:' + user):
            return int(float(self.rdb.get('score:' + user).decode()))
        return 0

    def _clicker_sync(self, user, name, clicker):
        base_query = 'clicker:' + user + ':' + name + ':'
        self.rdb.set(base_query + 'value', clicker.get_value())
        self.rdb.set(base_query + 'mult', clicker.get_mult())

    def _clicker_load(self, user, name):
        clicker = {}
        base_query = 'clicker:' + user + ':' + name + ':'
        clicker['value'] = int(self.rdb.get(base_query + 'value'))
        clicker['mult'] = int(self.rdb.get(base_query + 'mult'))
        return clicker

    def clickers_sync(self, user, clickers):
        names = ''
        for name, click in clickers.items():
            names += name + ':'
            self._clicker_sync(user, name, click)
        names = names[:-1]
        self.rdb.set('clicker:' + user, names)

    def clickers_load(self, user):
        clickers = {}
        result = self.rdb.get('clicker:' + user)
        if (not result):
            return None
        result = result.decode()
        names = result.split(':')
        for name in names:
            clickers[name] = self._clicker_load(user, name)
        return clickers

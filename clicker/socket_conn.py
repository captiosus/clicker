"""User game state"""

import eventlet
import json
import os
import random
import time

from clicker import clicker
from clicker import redis
from clicker import lottery
from clicker import achievements

MAX_CYCLE_CLICKS = 20
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class BaseSock(type):
    _sids = {}

    def __call__(cls, *args, **kwargs):
        if args[0] not in cls._sids:
            random.seed(time.time())
            cls._sids[args[0]] = super(BaseSock, cls).__call__(*args, **kwargs)
        return cls._sids[args[0]]


class SockConn(object, metaclass=BaseSock):
    def __init__(self, sid, user):
        self._user = user
        self._update_cycle = 0
        self._rdb = redis.RedisDB()
        self._clickers = {}
        self._config = self._load_config()
        self._cycle_clicks = 0
        self._lottery = lottery.Lottery(100000, 10000)
        self._achievements = achievements.Achievements(
            self._config['achievements'])
        self._last_update = int(time.time())
        self._frenzy = False
        self._frenzy_start = int(time.time())
        self._frenzy_duration = 5
        self._frenzy_avail = True
        self._frenzy_cd_time = int(time.time())
        self._frenzy_cooldown = 60

    def _get_score(self):
        return self._rdb.score_load(self._user)

    def _sync_score(self, score):
        self._rdb.score_sync(self._user, score)

    def load(self):
        clickers = self._rdb.clickers_load(self._user)
        if not clickers:
            clickers = {'BaseClick': {'value': None, 'mult': None}}
        for name, data in clickers.items():
            click = self._create_clicker(name, data['value'], data['mult'])
            self._clickers[name] = click

    def _load_config(self):
        with open(os.path.join(__location__, 'config/clickers.json')) as f:
            base_vals = json.load(f)
            return base_vals

    def click(self, clicker):
        if clicker not in self._clickers:
            return
        score = self._get_score()
        self._cycle_clicks += 1
        if self._cycle_clicks < MAX_CYCLE_CLICKS:
            click_val = self._clickers[clicker].click()
            self._frenzy_check()
            if self._frenzy:
                click_val *= 5
            self.achieve_click(click_val)
            score += click_val
        self._sync_score(score)

    def _update(self, cycles):
        self._cycle_clicks = 0
        self._rdb.clickers_sync(self._user, self._clickers)

        score = self._get_score()
        total = 0
        for name, click in self._clickers.items():
            if name == 'BaseClick':
                continue
            for _ in range(cycles):
                total += click.passive_click()
        score += total
        self._sync_score(score)

    def get_update(self):
        init_score = self._get_score()
        cycles = int(time.time()) - self._last_update
        self._frenzy_check()
        self._update(cycles)
        self._last_update = int(time.time())

        new_score = self._get_score()
        if cycles > 0:
            self.achieve_total((new_score - init_score) // cycles)

        result = {}
        result['upgrades'] = self._get_upgrades()
        result['unlockables'] = self._get_unlockables()
        result['clickers'] = self._update_clickers()
        result['score'] = self._get_score()
        result['limit'] = self._lottery.get_limit()
        result['frenzy'] = self._frenzy
        result['frenzy_avail'] = self._frenzy_avail
        return result

    def _update_clickers(self):
        clickers = {}
        for name, click in self._clickers.items():
            clickers[name] = {'value': click.get_value(),
                              'mult': click.get_mult()}
        return clickers

    def _create_clicker(self, name, value=None, mult=None):
        if hasattr(clicker, name):
            class_ = getattr(clicker, name)
            click = class_(self._config['clickers'][name], value, mult)
            return click

    def _unlock_clicker(self, name):
        click = self._create_clicker(name)
        price = click.initial_cost()
        score = self._get_score()
        if score >= price:
            score -= price
            self._clickers[name] = click
        self._sync_score(score)

    def _get_upgrades(self):
        upgrades = {}
        for name, click in self._clickers.items():
            upgrades[name] = click.get_upgrades()
        return upgrades

    def _get_upgrade_cost(self, name, type):
        if type == 'value':
            return self._get_upgrades()[name]['v-price']
        elif type == 'mult':
            return self._get_upgrades()[name]['m-price']
        return None

    def upgrade(self, data):
        if 'name' not in data or 'type' not in data:
            return
        if data['name'] in self._clickers:
            click = self._clickers[data['name']]
        else:
            self._unlock_clicker(data['name'])
            return

        upgrade_cost = self._get_upgrade_cost(data['name'], data['type'])
        score = self._get_score()
        if upgrade_cost and score >= upgrade_cost:
            score -= upgrade_cost
            click.upgrade(data['type'])
        self._sync_score(score)

    def _get_unlockables(self):
        unlockables = {}
        for name, config in self._config['clickers'].items():
            if name in self._clickers:
                continue
            value = config['value'][0]
            price = value * config['v-price'][0]
            unlockables[name] = {'value': value,
                                 'v-price': price}
        return unlockables

    def lottery(self, guess):
        try:
            guess = int(guess)
        except ValueError:
            return None
        prize = self._lottery.win(guess)
        self.achieve_lottery(self._lottery.get_streak())
        score = self._get_score()
        score += prize
        self._sync_score(score)
        return prize

    def frenzy(self):
        if (self._frenzy_avail):
            self._frenzy = True
            self._frenzy_start = int(time.time())
            self._frenzy_avail = False

    def _frenzy_check(self):
        if self._frenzy:
            cycles = int(time.time()) - self._frenzy_start
            if cycles > self._frenzy_duration:
                self._frenzy = False
                self._frenzy_cd_time = int(time.time())
        if not self._frenzy_avail:
            cycles = int(time.time()) - self._frenzy_cd_time
            if cycles > self._frenzy_cooldown:
                self._frenzy_avail = True

    def achievements(self):
        return self._achievements.get_all()

    def achieve_click(self, value):
        self._achievements.check_click(value)

    def achieve_lottery(self, value):
        self._achievements.check_lottery(value)

    def achieve_total(self, value):
        self._achievements.check_total(value)

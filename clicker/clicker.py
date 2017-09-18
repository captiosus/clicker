"""Clicker"""

import random


class BaseClick(object):
    def __init__(self, config, value=None, mult=None):
        self.config = config
        if (value):
            self.value = value
        else:
            self.value = self.config['value'][0]
        if (mult):
            self.mult = mult
        else:
            self.mult = 1

    def get_value(self):
        return self.value

    def get_mult(self):
        return self.mult

    def click(self):
        return self.value * self.mult

    def initial_cost(self):
        return self.config['v-price'][0] * self.config['value'][0]

    def upgrade(self, type):
        if type == 'value':
            self._upgrade_value()
        elif type == 'mult':
            self._upgrade_mult()

    def _upgrade_value(self):
        for value in self.config['value']:
            if value > self.value:
                self.value = value
                break

    def _upgrade_mult(self):
        for mult in self.config['mult']:
            if mult > self.mult:
                self.mult = mult
                break

    def get_upgrades(self):
        upgrades = {}
        if 'value' in self.config:
            for idx, value in enumerate(self.config['value']):
                if value > self.value:
                    upgrades['value'] = self.config['value'][idx]
                    upgrades['v-price'] = self.config['v-price'][idx]
                    upgrades['v-price'] *= upgrades['value']
                    break
        if 'mult' in self.config:
            for idx, mult in enumerate(self.config['mult']):
                if mult > self.mult:
                    upgrades['mult'] = self.config['mult'][idx]
                    upgrades['m-price'] = self.config['m-price'][idx]
                    upgrades['m-price'] *= upgrades['mult']
                    break
        return upgrades


class SuperClick(BaseClick):
    def __init__(self, config, value=None, mult=None):
        super().__init__(config, value, mult)

    def passive_click(self):
        return self.click()


class RandomClick(BaseClick):
    def __init__(self, config, value=None, mult=None):
        super().__init__(config, value, mult)

    def passive_click(self):
        return random.randint(0, self.value * self.mult)


class BigClick(BaseClick):
    def __init__(self, config, value=None, mult=None):
        super().__init__(config, value, mult)

    def passive_click(self):
        return self.value

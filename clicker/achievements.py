"""Achievements"""


class Achievements(object):
    def __init__(self, config, click=None, lottery=None, total=None):
        self._config = config

        if (click):
            self._click = click
        else:
            self._click = config['click'][0]
        if (lottery):
            self._lottery = lottery
        else:
            self._lottery = config['lottery'][0]
        if (total):
            self._total = total
        else:
            self._total = config['total'][0]

    def get_all(self):
        if self._click:
            click_val = 'Earn ' + str(self._click) + ' in a single click'
        else:
            click_val = 'flag'
        if self._lottery:
            lottery_val = ('Win the lottery ' + str(self._lottery) +
                           ' times in a row')
        else:
            lottery_val = 'flag'
        if self._total:
            total_val = 'Earn ' + str(self._total) + ' in 5 seconds'
        else:
            total_val = 'flag'
        return {'click': click_val,
                'lottery': lottery_val,
                'total': total_val}

    def check_click(self, value):
        if self._click and value >= self._click:
            self._upgrade_click()

    def check_lottery(self, value):
        if self._lottery and value >= self._lottery:
            self._upgrade_lottery()

    def check_total(self, value):
        if self._total and value >= self._total:
            self._upgrade_total()

    def _upgrade_click(self):
        for click in self._config['click']:
            if click > self._click:
                self._click = click
                return
        self._click = None

    def _upgrade_lottery(self):
        for lottery in self._config['lottery']:
            if lottery > self._lottery:
                self._lottery = lottery
                return
        self._lottery = None

    def _upgrade_total(self):
        for total in self._config['total']:
            if total > self._total:
                self._total = total
                return
        self._total = None

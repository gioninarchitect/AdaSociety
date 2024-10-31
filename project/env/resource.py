class Resource:
    def __init__(
        self,
        name,
        _type,
        position,
        amount,
        requirements={},
        unit_score=0,
        stacked_resource=None
    ):
        self.name = name
        self._type = _type
        if position:
            self.x, self.y = position
        else:
            # Carried by a player
            self.x, self.y = None, None
        self.amount = amount
        self.requirements = requirements
        self.default_unit_score = unit_score
        self.unit_score = unit_score
        self.stacked_resource = stacked_resource

    def update(self):
        pass

    def provide(self, n):
        result = min(n, self.amount)
        self.amount -= result
        return Resource(
            name=self.name,
            _type=self._type,
            position=None,
            amount=result,
            requirements=self.requirements,
            unit_score=self.unit_score,
        )

    def add(self, n):
        self.amount += n

    def consume(self, n):
        min_n = min(self.amount, n)
        self.amount -= min_n
        return n - min_n

    def check_visible(self, player):
        for name, num in self.requirements.items():
            if not player.check_amount(name, num):
                return False
        return True

    def set_position(self, position):
        self.x, self.y = position

    def set_unit_score(self, score):
        self.unit_score = score

    def reset_unit_score(self):
        self.unit_score = self.default_unit_score

    def get_dict_info(self):
        return {
            'name': self.name,
            'position': self.position,
            'amount': self.amount
        }

    @property
    def observation(self):
        obs = {
            'name': self.name,
            'amount': self.amount
        }
        # TODO
        return obs

    @property
    def position(self):
        return (self.x, self.y)

    @property
    def is_available(self):
        return self.amount > 0

    @property
    def score(self):
        return self.unit_score * self.amount

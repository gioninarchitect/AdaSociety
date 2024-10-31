class Event:
    def __init__(
        self,
        name,
        position,
        inputs,
        outputs,
        resource_pool,
        requirements={},
        avail_interval=0,
    ):
        self.name = name
        self.x, self.y = position
        self.inputs = inputs
        self.outputs = outputs
        self.resource_pool = resource_pool
        self.requirements = requirements
        self.avail_interval = avail_interval
        self.cooldown = 0
        
    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def provide(self):
        resources = []
        for name, num in self.outputs.items():
            resources.append(self.resource_pool[name].provide(num))
        return resources

    def check_visible(self, player):
        for name, num in self.requirements.items():
            if not player.check_amount(name, num):
                return False
        return True

    def get_dict_info(self):
        return {
            'name': self.name,
            'position': self.position,
        }
    
    @property
    def position(self):
        return (self.x, self.y)

    @property
    def is_available(self):
        return self.cooldown == 0

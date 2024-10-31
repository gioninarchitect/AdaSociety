class Group:
    def __init__(self, _id, name='', players=None):
        self._id = _id
        self.name = name
        if players is None:
            players = []
        self.players = players
        self._cached_score = 0

    def add_player(self, player):
        if player not in self.players:
            self.players.append(player)
        
    def remove_player(self, player):
        self.players.remove(player)

    def earn_score(self, score):
        self._cached_score += score

    def split_score(self, social_graph, attribute):
        weights = []
        for player in self.players:
            weight = social_graph.edges[self, player].get(attribute, 0)
            weights.append(weight)
        weight_sum = sum(weights)
        for player, weight in zip(self.players, weights):
            player.earn_score(self._cached_score * weight / weight_sum)
        self._cached_score = 0

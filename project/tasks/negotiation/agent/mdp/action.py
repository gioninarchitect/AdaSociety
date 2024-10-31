class Action:
    def __init__(self, _id, env_info, task_info):
        self._id = env_info['_id']
        self.resource_name = env_info['resource_name']
        self.resource_num = len(self.resource_name)
        self.player_num = env_info['player_num']
        self.claim_proposal_interval = task_info.negotiation['claim_proposal_interval']
        self.action_num = 6 + 2 * self.resource_num + self.player_num + 2 + self.claim_proposal_interval
        self.move_action_list = ['move_up', 'move_down', 'move_left', 'move_right', 'no_act']
        self.action = []
        
    '''np.array -> Action Class'''
    def move_action(self, action_id):
        self.action.append(self.move_action_list[action_id])
        return self.move_action_list[action_id]
    
    def produce_action(self, action_id = None):
        self.action.append('produce')
        return 'produce'
    
    def pick_action(self, action_id):
        pick_resource_id = action_id - 6
        pick_resource_name = self.resource_name[pick_resource_id]
        self.action.append(('pick_by_name', {'resource_name': pick_resource_name}))
        return 'pick_by_name', {'resource_name': pick_resource_name}
   
    def dump_action(self, action_id):
        dump_resource_id = action_id - 6 - self.resource_num
        dump_resource_name = self.resource_name[dump_resource_id]
        self.action.append(('dump_by_name', {'resource_name':dump_resource_name}))
        return 'dump_by_name', {'resource_name': dump_resource_name}
    
    def request_matching_action(self, action_id):
        request_matching_id = action_id - 6 - 2 * self.resource_num
        self.action.append(('request_matching', {'to_player_id': request_matching_id}))
        return 'request_matching', {'to_player_id': request_matching_id}
    
    def bargain_action(self, action_id, to_player_id, opponent_proposal):
        bargain_action_id = action_id - 6 - 2 * self.resource_num - self.player_num
        if bargain_action_id == 0:
            self.action.append(('accept_proposal', {'to_player_id': to_player_id,
                                       'scale': 1 - opponent_proposal}))
            return 'accept_proposal', {'to_player_id': to_player_id,
                                       'scale': 1 - opponent_proposal}
        elif bargain_action_id == 1:
            self.action.append(('end_bargaining', {'to_player_id': to_player_id}))
            return 'end_bargaining', {'to_player_id': to_player_id}
        else:
            self.action.append(('propose', {'score': (bargain_action_id - 1) * (1 / (self.claim_proposal_interval+1)), 
                               'to_player_id': to_player_id}))
            return 'propose', {'score': (bargain_action_id - 1) * (1 / (self.claim_proposal_interval+1)), 
                               'to_player_id': to_player_id}
            
    def new(self):
        self.action = []
        
    def get_action(self):
        return self.action
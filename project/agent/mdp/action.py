class Action:
    def __init__(self, _id, env_info, task_info):
        self.resource_name = env_info['resource_name']
        self.resource_num = len(self.resource_name)
        self.player_num = env_info['player_num']
        self.communication_length = task_info.get('communication_length', 0)
        self.move_action_list = ["move_up", "move_down", "move_left", "move_right", "no_act"]
        self.action = []

    def move_action(self, action_id):
        self.action.append(self.move_action_list[action_id])

    def produce_action(self, action_id=None):
        self.action.append('produce')

    def pick_action(self, action_id):
        self.action.append(('pick_by_name', {'resource_name': self.resource_name[action_id]}))

    def dump_action(self, action_id):
        self.action.append(('dump_by_name', {'resource_name': self.resource_name[action_id]}))

    def communication_action(self, to_player_id, content):
        self.action.append(('add_relation', {'to_player_id': to_player_id, 'attributes_dict': {'communication': content}}))

    def join_group_action(self, group_id, attribute_dict):
        self.action.append(('join_group', {'group_id': group_id, 'attribute_dict': attribute_dict}))

    def quit_group_action(self, quit_group_id, attribute_name):
        self.action.append(('quit_group', {'group_id': quit_group_id, 'attribute_name': attribute_name}))

    def add_relation_action(self, to_player_id, attributes_dict):
        self.action.append(('add_relation', {'to_player_id': to_player_id, 'attributes_dict': attributes_dict}))

    def remove_relation_action(self, to_player_id, attribute_name):
        self.action.append(('remove_relation', {'to_player_id': to_player_id, 'attribute_name': attribute_name}))
    
    def check_relation_action(self, to_player_id, attribute_dict):
        self.action.append(('check_relation', {'to_player_id': to_player_id, 'attribute_dict': attribute_dict}))
    
    def new(self):
        self.action = []
        
    def get_action(self):
        return self.action

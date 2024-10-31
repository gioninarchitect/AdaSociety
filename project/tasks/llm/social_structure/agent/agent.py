import itertools, os, json, re
from collections import defaultdict
import numpy as np
import random
from ...utils import Module
from .....agent.mdp.state import State
from .....agent.mdp.action import Action
import re
import networkx as nx

cwd = os.getcwd()
openai_key_file = os.path.join(cwd, "project/tasks/llm/openai_key.txt")

GROUP = 'group_{}'
DEFAULT_ATTRIBUTE = 'link'
WEIGHT = 'division_weight'
PROMPT_DIR = "project/tasks/llm/prompts/"
OUTPUT_DIR = "project/tasks/llm/outputs/"

PRODUCTS_TO_EVENT_NAME = {
    "hammer": "hammer_craft",
    "torch": "torch_craft",
    "steel": "steelmaking",
    "shovel": "shovelcraft",
    "pickaxe": "pickaxecraft",
    "pottery": "potting",
    "cutter": "cuttercraft",
    "gem": "gemcutting",
    "totem": "totemmaking"
}

EVENT_NAME_TO_PRODUCTS = {
    "hammercraft": "HAMMER",
    "torchcraft": "TORCH",
    "steelmaking": "STEEL",
    "shovelcraft": "SHOVEL",
    "pickaxecraft": "PICKAXE",
    "potting": "POTTERY",
    "cuttercraft": "CUTTER",
    "gemcutting": "GEM",
    "totemmaking": "TOTEM"
}

class BaseAgent(object):
    """
    This agent uses GPT-3.5 to generate actions.
    """
    def __init__(self, model="gpt-3.5-turbo-0301"):
        self.agent_name = None
        self.model = model

        self.openai_api_keys = []
        self.load_openai_keys()
        self.key_rotation = True

    def load_openai_keys(self):
        with open(openai_key_file, "r") as f:
            context = f.read()
        self.openai_api_keys = context.split('\n')

    def openai_api_key(self):
        if self.key_rotation:
            self.update_openai_key()
        return self.openai_api_keys[0]

    def update_openai_key(self):
        self.openai_api_keys.append(self.openai_api_keys.pop(0))

    def set_agent_name(self, agent_name):
        raise NotImplementedError

    def action(self, state):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

class PhysicalAgent(BaseAgent):
    def __init__(self, info, task_info, agent_id, agent_name, task=None, episode=0, agent_name_list=['carpenter_0','carpenter_1','miner_0','miner_1'], env_agent_name_list = [], 
                 player2name = {},
                 model='gpt-3.5-turbo-0301',
                retrival_method="recent_k", K=1):
        super().__init__(model=model)
        self.task = task
        self.agent_num = info['player_num']
        self.episode = episode
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.state = State(self.agent_id, info, task_info)
        self.Action = Action(self.agent_id, info, task_info)
        self.agent_name_list = agent_name_list
        self.player2name = player2name
        self.event_IO = info['events']
        self.env_agent_name_list = env_agent_name_list
        self.inventory_max = info['inventory_capacity']

        self.stay = 0
        self.x = 0
        self.group_id = None
        self.current_plan = None
        self.current_comm = None
        self.res_in_obs = None
        self.res_in_obs_dist = None
        self.event_in_obs = None
        self.event_in_obs_dist = None
        self.inventory = None
        self.previous_inventory = None
        self.quantity = 0
        self.pre_position = None
        self.pre_action = None
        self.cur_position = None
        

        self.K = K
        self.retrival_method = retrival_method
        self.gpt = True

        self.planner = self.create_gptmodule("planner", retrival_method=self.retrival_method, K=self.K)
        with open(f'{OUTPUT_DIR}output_{self.task}_physical_{self.episode}.txt', 'a', encoding='utf-8') as file:
            print(self.planner.instruction_head_list[0]['content'], file=file)
    
    def generate_system_promt(self):
        prompt = ""
        prompt += "Instructions:\n"
        prompt += "- The BraveNewWorld (BNW) game is an open-ended multi-agent environment. The game consists of a complex crafting tree, where the agent needs to obtain as many resources as possible in the limited time and craft tools to mine more advanced resources to maximize its benefit. At the same time, agents can also take other actions to help them increase their returns. The numbers of resources are limited.\n"
        prompt += "- Map: BNW is a 2D grid-world game. The map size is 15*15.\n"
        prompt += "    - Natural resources: [Wood, Stone, Coal, Iron]. Some of them can only be discovered with some specific tools, which will be introduced next.\n"
        prompt += "    - Tools: [Hammer, Torch]\n"
        prompt += "    - Craft tree:\n"
        prompt += "        - 1 Wood + 1 Stone = 1 Hammer. With a Hammer, Coal can be gathered;\n"
        prompt += "        - 1 Coal + 1 Wood = 1 Torch. With a Torch, Iron can be discovered;\n"
        prompt += "    - All gathered and tools are stored in the agent's inventory.\n"
        prompt += "    - All crafts must be done on the corresponding event grid on the map. For example, your inventory must contain wood and stone to craft a hammer.\n"
        prompt += "    - Default amount of all units in crafts is 1.\n"
        prompt += "\n"
        prompt += "- Player:\n"
        prompt += "    - There are two kinds of player in the BNW, Carpenters and Miners.\n"
        prompt += "    - The Carpenter can gather many woods, stones and irons and craft hammer, but can only own one hammer. The Carpenter CANNOT gather coal so it CANNOT craft torch, but its inventory can hold a lot of torches.\n"
        prompt += "    - The Miner can gather many woods and coals, so it can craft torch, but can only own one torch. The Miner CANNOT gather stone so it CANNOT craft hammer, but its inventory can hold a lot of hammers.\n"
        prompt += "    - For all players, the value of wood is 1, the value of stone is 1, the value of hammer is 5, the value of coal is 10, the value of torch is 30, the value of iron is 20.\n"
        prompt += "    - Different players may be placed in the same coalition, and the rewards for players in the same coalition are split equally, so given the heterogeneity between carpenter and miner, players in the same coalition need to cooperate.\n"
        prompt += "\n"
        prompt += "Suppose you are a Carpenter named <carpenter_0>. Your aim is to maximize your reward, which can gain from the resource value and the craft value.\n"
        prompt += "You can not craft torchs, but you can craft hammers.\n"
        prompt += "At each round in action phase, you will receive the current state:\n"
        prompt += "Step: ...\n"
        prompt += "Current surrounding social environment: ...\n"
        prompt += "Current surrounding physical environment: ...\n"
        prompt += "Your current inventory: ...\n"
        prompt += "\n"
        if "carpenter" in self.agent_name_list[self.agent_id]:
            prompt += "You should choose *ONLY ONE* Plan from the following four options: [GATHER <NUM> <WOOD/STONE/IRON/TORCH>, CRAFT 1 HAMMER, EXPLORE MAP, DUMP HAMMER]. Here are explanations about them:\n"
            prompt += "- GATHER <NUM> <WOOD/STONE/IRON/TORCH>: You shouldn't try to gather items that aren't in your field of view because you don't know where they are. You should also not try to gather item that are not in <WOOD/STONE/IRON/TORCH>. You can only choose one type of item in your plan.\n"
            prompt += "- CRAFT 1 HAMMER: This plan can help you use the items in your inventory and follow the craft tree to craft the resources or tools you need. You can only use this plan if you have the corresponding event grid (i.e. the craft point) in your view. You should make sure you have enough material to craft.\n"
            prompt += "- EXPLORE MAP: This plan helps you move randomly to explore the map.\n"
            prompt += "- DUMP HAMMER: The plan is to drop hammers on the ground because some agents have hammer's capacity of only 1. This action will decrease the corresponding item in the inventory by 1. If the item is not in the inventory, please do not choose this plan.\n"
            prompt += "\n"
            prompt += "<NUM> should be an integer not greater than 10.\n"
            prompt += "Please strictly follow the format above for the output.\n"
            prompt += "\n"
            prompt += "The response should obey the following format:\n"
            prompt += "Thoughts: Your analysis about your inventory and the current environment.\n"
            prompt += "Plan: One of the above four plans you will take.\n"
            prompt += "\n"
            prompt += "Examples:\n"
            prompt += "###\n"
            prompt += "Step: 20\n"
            prompt += "Current surrounding physical environment:\n"
            prompt += "The resources in your observation are: [5 Wood, 5 Stone]. The distances of them are [4,6] steps away.\n"
            prompt += "The event grid in your observation are: [Hammer Event]. The distances of them are [3] steps away.\n"
            prompt += "You have nothing in your inventory.\n"
            prompt += "\n"
            prompt += "Thoughts: I don't have anything in my inventory. There are 5 woods and 5 stones in my observation, the wood is closer to me, so I need to gather some wood first.\n"
            prompt += "Plan: GATHER 5 WOOD.\n"
            prompt += "###\n"
            prompt += "Step: 40\n"
            prompt += "Current surrounding physical environment:\n"
            prompt += "The resources in your observation are: [2 Wood, 4 Stone]. The distances of them are [8,10] steps away.\n"
            prompt += "The event grid in your observation are: [Hammer Event]. The distances of them are [3] steps away.\n"
            prompt += "Your current inventory:\n"
            prompt += "You have 4 Wood, 6 Stone, 0 Hammer.\n"
            prompt += "\n"
            prompt += "Thoughts: I have some woods and stones in my inventory but no hammer. There is a hammer event in my observation, which means I can craft the hammer.\n"
            prompt += "Plan: CRAFT 1 HAMMER.\n"
            prompt += "###\n"
            prompt += "Step: 60\n"
            prompt += "Current surrounding physical environment:\n"
            prompt += "The resources in your observation are: [1 Wood, 3 Stone]. The distances of them are [5,2] steps away.\n"
            prompt += "The event grid in your observation are: [Hammer Event]. The distances of them are [3] steps away.\n"
            prompt += "Your current inventory:\n"
            prompt += "You have 2 Wood, 3 Stone, 1 Hammer.\n"
            prompt += "\n"
            prompt += "Thoughts: I have some woods and stones, and one hammer in my inventory. Accounting for my inventory can only hold one hammer, and there are two miners in my coalition who can hold lots hammers, I should dump my hammer to let my teammates pick it up, and craft a new one later.\n"
            prompt += "Plan: DUMP HAMMER.\n"
            prompt += "###\n"
            prompt += "Step: 80\n"
            prompt += "Current surrounding physical environment:\n"
            prompt += "The resources in your observation are: [2 Wood, 1 Torch]. The distances of them are [2,4] steps away.\n"
            prompt += "The event grid in your observation are: [Hammer Event]. The distances of them are [3] steps away.\n"
            prompt += "Your current inventory:\n"
            prompt += "You have 2 Wood, 3 Stone, 1 Hammer.\n"
            prompt += "\n"
            prompt += "Thoughts: I have some woods and stones, and one hammer in my inventory but no torch. Torch is most valuable tool for me, and my inventory can hold a lot of torches, so I need to gather the torch on the map.\n"
            prompt += "Plan: GATHER 1 TORCH.\n"
            prompt += "\n"
        else:
            prompt += "You should choose *ONLY ONE* Plan from the following four options: [GATHER <NUM> <WOOD/COAL/HAMMER>, CRAFT 1 TORCH, EXPLORE MAP, DUMP TORCH]. Here are explanations about them:\n"
            prompt += "- GATHER <NUM> <WOOD/COAL/HAMMER>: You shouldn't try to gather items that aren't in your field of view because you don't know where they are. You should also not try to gather items that are not in <WOOD/COAL/HAMMER>. You can only choose one type of item in your plan.\n"
            prompt += "- CRAFT 1 TORCH: This plan can help you use the items in your inventory and follow the craft tree to craft the resources or tools you need. You can only use this plan if you have the corresponding event grid (i.e. the craft point) in your view. You should make sure you have enough material to craft.\n"
            prompt += "- EXPLORE MAP: This plan helps you move randomly to explore the map.\n"
            prompt += "- DUMP TORCH: The plan is to drop torchs on the ground because some agents have torch's capacity of only 1. This action will decrease the corresponding item in the inventory by 1. If the item is not in the inventory, please do not choose this plan.\n"
            prompt += "\n"
            prompt += "<NUM> should be an integer not greater than 10.\n"
            prompt += "Please strictly follow the format above for the output.\n"
            prompt += "\n"
            prompt += "The response should obey the following format:\n"
            prompt += "Thoughts: Your analysis about your inventory and the current environment.\n"
            prompt += "Plan: One of the above four plans you will take.\n"
            prompt += "\n"
            prompt += "Examples:\n"
            prompt += "###\n"
            prompt += "Step: 20\n"
            prompt += "Current surrounding physical environment:\n"
            prompt += "The resources in your observation are: [5 Wood, 5 Stone]. The distances of them are [4,6] steps away.\n"
            prompt += "The event grid in your observation are: [Torch Event]. The distances of them are [3] steps away.\n"
            prompt += "You have NOTHING in your inventory.\n"
            prompt += "\n"
            prompt += "Thoughts: I don't have anything in my inventory. There are 5 woods and 5 stones in my observation, but I cannot gather the stone, so I need to gather some wood first.\n"
            prompt += "Plan: GATHER 5 WOOD.\n"
            prompt += "###\n"
            prompt += "Step: 40\n"
            prompt += "Current surrounding physical environment:\n"
            prompt += "The resources in your observation are: [2 Wood, 4 Coal]. The distances of them are [8,10] steps away.\n"
            prompt += "The event grid in your observation are: [Hammer Event]. The distances of them are [3] steps away.\n"
            prompt += "Your current inventory:\n"
            prompt += "You have 4 Wood.\n"
            prompt += "\n"
            prompt += "Thoughts: I have some woods but no coals which is necessary for crafting torch. There is some coal in my observation, so I need to gather some coals first.\n"
            prompt += "Plan: GATHER 4 COAL.\n"
            prompt += "###\n"
            prompt += "Step: 60\n"
            prompt += "Current surrounding physical environment:\n"
            prompt += "The resources in your observation are: [1 Wood, 2 Coal]. The distances of them are [5,2] steps away.\n"
            prompt += "The event grid in your observation are: [Torch Event]. The distances of them are [3] steps away.\n"
            prompt += "Your current inventory:\n"
            prompt += "You have 2 Wood, 3 Coal.\n"
            prompt += "\n"
            prompt += "Thoughts: I have some woods and coals, which is enough for crafting the torch. And I can see the torch event, which means I can craft a torch. But given that my inventory could only hold one torch, and that I was not allied with anyone else, I chose to make only one torch in order to prevent others from stealing the fruits of my labor.\n"
            prompt += "Plan: CRAFT 1 TORCH.\n"
            prompt += "###\n"
            prompt += "Step: 80\n"
            prompt += "Current surrounding physical environment:\n"
            prompt += "The resources in your observation are: [2 Wood, 1 HAMMER]. The distances of them are [2,4] steps away.\n"
            prompt += "The event grid in your observation are: []. The distances of them are [] steps away.\n"
            prompt += "Your current inventory:\n"
            prompt += "You have 2 Wood, 3 Coal, 1 Torch.\n"
            prompt += "\n"
            prompt += "Thoughts: I have some woods and coals, and one torch in my inventory but no hammer. Hammer is more valuable than wood for me, and my inventory can hold a lot of hammers, so I need to gather the hammer on the map.\n"
            prompt += "Plan: GATHER 1 HAMMER.\n"
            prompt += "###\n"
            prompt += "Step: 90\n"
            prompt += "Current surrounding physical environment:\n"
            prompt += "The resources in your observation are: [2 Wood, 1 Coal]. The distances of them are [2,4] steps away.\n"
            prompt += "The event grid in your observation are: []. The distances of them are [] steps away.\n"
            prompt += "Your current inventory:\n"
            prompt += "You have 2 Wood, 3 Coal, 1 Torch.\n"
            prompt += "\n"
            prompt += "Thoughts: I have some woods and coals, and 1 Torch. Accounting for my inventory can only hold one torch, and there are two carpenters in my coalition who can hold lots torches, I should dump my torch to let my teammates pick it up, and craft new torch later.\n"
            prompt += "Plan: DUMP TORCH.\n"

        prompt += "###\n"
        prompt += "Step: 90\n"
        prompt += "Current surrounding physical environment:\n"
        prompt += "The resources in your observation are: []. The distances of them are [] steps away. The numbers of them are [] respectively.\n"
        prompt += "The event grid in your observation are: [Hammer Event]. The distances of them are [0] steps away.\n"
        prompt += "The people in your observation are: [miner_0], The distances of them are [1] steps away.\n"
        prompt += "Your current inventory:\n"
        prompt += "You have NOTHING in your inventory.\n"
        prompt += "\n"
        prompt += f"Thoughts: I am {self.agent_name_list[self.agent_id]}, and in the current coalition, there are both carpenters and miners. The hammercraft event is right next to me. Since I have no wood and no stone, I can also not craft hammer. I don't see any resource in my field of view, so I need to explore the map to find one.\n"
        prompt += "Plan: EXPLORE MAP.\n"

        return prompt

    def create_gptmodule(self, module_name, retrival_method='recent_k', K=10):
        with open(f'{OUTPUT_DIR}output_{self.task}_physical_{self.episode}.txt', 'a', encoding='utf-8') as file:
            print(f"\n--->Initializing GPT {module_name}<---\n", file=file)
        system_promt = self.generate_system_promt()
        with open(f'{PROMPT_DIR}prompt_{self.task}_physical_{self.agent_name_list[self.agent_id]}.txt', 'a', encoding='utf-8') as file:
            print(f"{system_promt}", file=file)
        messages = [{"role": "system", "content": system_promt}]
        return Module(messages, self.model, retrival_method, K)

    def reset(self):
        if self.gpt:
            self.planner.reset()
        self.prev_state = None
        self.current_ml_action = None
        self.current_ml_action_steps = 0
        self.time_to_wait = 0
        self.possible_motion_goals = None
        self.current_timestep = 0
        self.teammate_ml_actions_dict = {}
        self.teammate_intentions_dict = {}

    def update_obs(self, observation, pre_position, pre_action):
        llm_obs = {}
        
        llm_obs = {}
        llm_obs['social_state'] = self.state.social_state2nx(observation["Social"]['global']['edges'])
        llm_obs['step'] = observation['step_id']
        llm_obs['position'] = pre_position[self.agent_id]
        llm_obs['action'] = pre_action[self.agent_id]
        llm_obs['current_pos'] = observation["Player"]['position']
        llm_obs['inventory'] = observation["Player"]['inventory']

        llm_obs['resource'] = observation["Map"]['resources']
        llm_obs['event'] = observation["Map"]['events']
        llm_obs['people'] = observation["Map"]['players']

        for key in observation["Social"]['sharings'].keys():
            sharing = observation["Social"]['sharings'][key]
            if 'Map' in sharing:
                llm_obs['resource'] += sharing["Map"]['resources'] 
                llm_obs['event'] += sharing["Map"]['events']
                llm_obs['people'] += sharing["Map"]['players']
        
        return llm_obs
    
    def generate_state_prompt(self, obs):
        
        social_state = obs['social_state']
        self.step = obs['step']
        self.resource = obs['resource']
        self.position = obs['current_pos']
        self.event = obs['event']
        self.people = obs['people']
        self.inventory_pre = obs['inventory']
        social_env_prompt = f"Current surrounding social environment:\n"
        for i in range(self.agent_num):
            social_env_prompt += f"coalition {i}:"
            if social_state.has_node(GROUP.format(i)):
                coalition = social_state.successors(GROUP.format(i))
                player = []
                for key in coalition:
                    key = self.player2name[key]
                    player.append(key)
                if len(player) > 0:
                    social_env_prompt += f"{player}.\n"
                else:
                    social_env_prompt += f"None.\n"
            else:
                social_env_prompt += f"None.\n"
        
        '''Physical state'''
        time_prompt = f"Step: {self.step}\n"
        
        inventory_prompt = "Your current inventory:\nYour have "
        self.inventory = {}
        for i in range(len(self.inventory_pre)):
            inventory = self.inventory_pre[i]
            if inventory['name'] in self.inventory:
                self.inventory[inventory['name']] += inventory['amount']
            else:
                self.inventory[inventory['name']] = inventory['amount']
        for key in self.inventory.keys():
            inventory_prompt += f"{self.inventory[key]} {key},"
        if len(self.inventory) == 0:
            inventory_prompt += "None."
        inventory_prompt += "\n"

        current_obs_prompt = "Current surrounding physical environment:\n"
        self.resource_dis = {}
        self.resource_number = {}
        self.resource_pos = {}
        for i in range(len(self.resource)):
            resource = self.resource[i]
            if resource['name'] not in self.resource_number:
                self.resource_number[resource['name']] = resource['amount']
                self.resource_pos[resource['name']] = resource['position']
                self.resource_dis[resource['name']] = abs(resource['position'][0] - self.position[0]) + abs(resource['position'][1] - self.position[1])
            else:
                dis = abs(resource['position'][0] - self.position[0]) + abs(resource['position'][1] - self.position[1])
                if dis < self.resource_dis[resource['name']]:
                    self.resource_dis[resource['name']] = dis
                    self.resource_number[resource['name']] = resource['amount']
                    self.resource_pos[resource['name']] = resource['position']
        self.event_dis = {}
        self.event_pos = {}
        for i in range(len(self.event)):
            event = self.event[i]
            if event['name'] not in self.event_dis:
                self.event_dis[event['name']] = abs(event['position'][0] - self.position[0]) + abs(event['position'][1] - self.position[1])
                self.event_pos[event['name']] = event['position']
            else:
                dis = abs(event['position'][0] - self.position[0]) + abs(event['position'][1] - self.position[1])
                if dis < self.event_dis[event['name']]:
                    self.event_dis[event['name']] = dis
                    self.event_pos[event['name']] = event['position']
        self.people_dis = {}
        for i in range(len(self.people)):
            people = self.people[i]
            name = self.agent_name_list[self.env_agent_name_list.index(people["name"])]
            self.people_dis[name] = abs(people["position"][0] - self.position[0]) + abs(people["position"][1] - self.position[1])

        current_obs_prompt += f"The resources in your observation are: {list(self.resource_number.keys())}. The distances of them are {list(self.resource_dis.values())} steps away. The numbers of them are {list(self.resource_number.values())} respectively.\n"
        current_obs_prompt += f"The event grid in your observation are: {list(self.event_dis.keys())}. The distances of them are {list(self.event_dis.values())} steps away.\n"
        current_obs_prompt += f"The people in your observation are: {list(self.people_dis.keys())}. The distances of them are {list(self.people_dis.values())} steps away.\n"

        hint_prompt = 'attention: '
        wood = False
        stone = False
        hammer = False
        torch = False
        coal = False
        for res_name in self.inventory.keys():
            resource_num = self.inventory[res_name]
            if resource_num > 0:
                if res_name == "hammer":
                    if "carpenter" in self.agent_name_list[self.agent_id]:
                        hammer = True
                        hint_prompt += "You must dump hammer before craft hammer. "
                if res_name == "torch":
                    if "miner" in self.agent_name_list[self.agent_id]:
                        torch = True
                        hint_prompt += "You must dump torch before craft torch. "
                if res_name == "wood":
                    wood = True
                if res_name == "stone":
                    stone = True
                if res_name == "coal":
                    coal = True
        if "carpenter" in self.agent_name_list[self.agent_id]:
            if wood and stone and not hammer:
                hint_prompt += "You cannot dump hammer. "
            elif wood and stone and hammer:
                hint_prompt += "You cannot craft hammer. "
            else:
                hint_prompt += "You cannot craft hammer. "
                if not hammer:
                    hint_prompt += "You cannot dump hammer. "
        if "miner" in self.agent_name_list[self.agent_id]:
            if wood and coal and not torch:
                hint_prompt += "You cannot dump torch. "
            elif wood and coal and torch:
                hint_prompt += "You cannot craft torch. "
            else:
                hint_prompt += "You cannot craft torch. "
                if not torch:
                    hint_prompt += "You cannot dump torch. "
        hint_prompt += "\n"

        return (time_prompt + social_env_prompt + current_obs_prompt + inventory_prompt + hint_prompt)    
    
    def update_policy(self, obs):
        state_prompt = self.generate_state_prompt(obs)
        self.pre_action = obs['action']
        self.pre_position = obs['position']
        self.position = obs['current_pos']
        with open(f'{OUTPUT_DIR}output_{self.task}_physical_{self.episode}.txt', 'a', encoding='utf-8') as file:
            print(f"\n### Observation module to {self.agent_name_list[self.agent_id]}", file=file)
            print(f"{state_prompt}", file=file)
        if self.current_plan is None or self.check_previous_plan_illegal() or self.check_previous_plan_done():
            if self.stay > 10000:
                plan = None
            else:
                state_message = {"role": "user", "content": state_prompt}
                if self.gpt:
                    self.planner.current_user_message = state_message
                    response = self.planner.query(key=self.openai_api_key())
                    self.planner.add_msg_to_dialog_history(state_message)
                    self.planner.add_msg_to_dialog_history({"role": "assistant", "content": response})
                else:
                    step = obs['step']
                    if self.agent_id == 0:
                        if step%4 == 0:
                            response = "Plan: GATHER 3 WOOD"
                        elif step%4 == 1:
                            response = "Plan: GATHER 3 STONE"
                        else:
                            response = "Plan: CRAFT 1 HAMMER"
                    else:
                        response = "Plan: EXPLORE MAP"
                with open(f'{OUTPUT_DIR}output_{self.task}_physical_{self.episode}.txt', 'a', encoding='utf-8') as file:
                    print(f"\n### GPT Planner module", file=file)
                    print(f"====== {self.agent_name_list[self.agent_id]} Query ======", file=file)
                    print(response, file=file)
                plan = self.language2plan(response)
                # if plan != None:
                #     match = re.match(r'(\w+) (\d+) (\w+)', plan)
                #     if match:
                #         self.quantity = int(match.group(2))
            self.stay = 0
            self.current_plan = plan
        self.plan_to_action(self.current_plan)
        self.previous_inventory = self.inventory

    def language2plan(self, response):
        if not isinstance(response, (str, bytes)):
            response = str(response)
        '''Physical action'''
        pattern_plan = r"Plan:\s*(.+)"
        match_plan = re.search(pattern_plan, response)
        plan = None
        if match_plan:
            plan = match_plan.group(1)
        return plan

    def plan_to_action(self, plan):
        if plan != None:
            match = re.match(r'(\w+) (\d+) (\w+)', plan)
            if match:
                plan_type = match.group(1)
                number = int(match.group(2))
                item = match.group(3)
            else:
                match = re.match(r'(\w+) (\w+)', plan)
                if match:
                    plan_type = match.group(1)
                    number = 1
                    item = match.group(2)
                else:
                    plan_type = plan.split()[0]
                    number = 0
                    item = None
        else:
            plan_type = None
            item = None
            number = 0
        self.plan_type = plan_type
        self.item = item
        self.number = number
        if plan_type == "GATHER":
            target_resource_name = item
            target_resource_name = ''.join(char for char in target_resource_name if char.isalnum()).lower()
            if target_resource_name not in self.resource_pos:
                random_move = random.randint(0, 4)
                self.Action.move_action(random_move)
            else:
                target_resource_pos = self.resource_pos[target_resource_name]
                if "move" in self.pre_action[0][0] and (self.pre_position == self.position).all():
                    random_move = random.randint(0, 4)
                    self.Action.move_action(random_move)
                else:
                    if target_resource_pos[0] < self.position[0]:
                        move = "move_left"
                        self.Action.move_action(self.Action.move_action_list.index(move))
                    elif target_resource_pos[0] > self.position[0]:
                        move = "move_right"
                        self.Action.move_action(self.Action.move_action_list.index(move))
                    elif target_resource_pos[1] < self.position[1]:
                        move = "move_up"
                        self.Action.move_action(self.Action.move_action_list.index(move))
                    elif target_resource_pos[1] > self.position[1]:
                        move = "move_down"
                        self.Action.move_action(self.Action.move_action_list.index(move))
                    else:
                        self.Action.pick_action(self.Action.resource_name.index(target_resource_name))
        elif plan_type == "CRAFT":
            target_resource_name = item
            target_resource_name = ''.join(char for char in target_resource_name if char.isalnum()).lower()
            target_resource_name = PRODUCTS_TO_EVENT_NAME[target_resource_name]
            if target_resource_name not in self.event_pos:
                random_move = random.randint(0, 4)
                self.Action.move_action(random_move)
            else:
                target_resource_pos = self.event_pos[target_resource_name]
                if "move" in self.pre_action[0][0] and (self.pre_position == self.position).all():
                    random_move = random.randint(0, 4)
                    self.Action.move_action(random_move)
                else:
                    if target_resource_pos[0] < self.position[0]:
                        move = "move_left"
                        self.Action.move_action(self.Action.move_action_list.index(move))
                    elif target_resource_pos[0] > self.position[0]:
                        move = "move_right"
                        self.Action.move_action(self.Action.move_action_list.index(move))
                    elif target_resource_pos[1] < self.position[1]:
                        move = "move_up"
                        self.Action.move_action(self.Action.move_action_list.index(move))
                    elif target_resource_pos[1] > self.position[1]:
                        move = "move_down"
                        self.Action.move_action(self.Action.move_action_list.index(move))
                    else:
                        self.Action.produce_action()
        elif plan_type == "DUMP":
            target_resource_name = item
            target_resource_name = ''.join(char for char in target_resource_name if char.isalnum()).lower()
            if target_resource_name not in self.inventory:
                random_move = random.randint(0, 4)
                self.Action.move_action(random_move)
            else:
                self.Action.dump_action(self.Action.resource_name.index(target_resource_name))
        elif plan_type == "EXPLORE":
            if self.stay == 0:
                random_move = random.randint(0, 4)
                self.x = random_move
            self.Action.move_action(self.x)
        else:
            with open(f'{OUTPUT_DIR}output_{self.task}_physical_{self.episode}.txt', 'a', encoding='utf-8') as file:
                print(f"Plan <{plan}> is illegal!!", file=file)
            random_move = random.randint(0, 4)
            self.Action.move_action(random_move)

    def check_previous_plan_illegal(self):
        self.stay += 1
        plan_type = self.plan_type
        item = self.item
        if plan_type == "GATHER":
            target_resource_name = item
            target_resource_name = ''.join(char for char in target_resource_name if char.isalnum()).lower()
            if target_resource_name not in self.resource_pos:
                return True
            if target_resource_name in self.inventory_max and self.inventory_max[target_resource_name] < 1 or (target_resource_name in self.inventory and target_resource_name in self.inventory_max and self.inventory_max[target_resource_name] < self.inventory[target_resource_name]):
                return True
        elif plan_type == "CRAFT":
            target_resource_name = item
            target_resource_name = ''.join(char for char in target_resource_name if char.isalnum()).lower()
            target_resource_name = PRODUCTS_TO_EVENT_NAME[target_resource_name]
            if target_resource_name not in self.event_pos:
                return True
            input_resource = self.event_IO[target_resource_name]['in']
            for key in input_resource.keys():
                if key not in self.inventory:
                    return True
                if self.inventory[key] < input_resource[key]:
                    return True
        elif plan_type == "DUMP":
            target_resource_name = item
            target_resource_name = ''.join(char for char in target_resource_name if char.isalnum()).lower()
            if target_resource_name not in self.inventory:
                return True
            if target_resource_name in self.inventory and self.inventory[target_resource_name] <= 0:
                return True
        return False

    def check_previous_plan_done(self):
        plan_type = self.plan_type
        item = self.item
        if plan_type == "GATHER":
            target_resource_name = item
            target_resource_name = ''.join(char for char in target_resource_name if char.isalnum()).lower()
            if target_resource_name not in self.inventory or target_resource_name not in self.previous_inventory:
                return False
            if self.previous_inventory[target_resource_name] == self.inventory[target_resource_name]:
                if self.number > 1:
                    return False
            if self.previous_inventory[target_resource_name] != self.inventory[target_resource_name] and self.number > 1:
                self.number -= 1
                return False
        elif plan_type == "DUMP":
            target_resource_name = item
            target_resource_name = ''.join(char for char in target_resource_name if char.isalnum()).lower()
            if self.inventory[target_resource_name] > 0 and self.number > 1:
                self.number -= 1
                return False
        elif plan_type == "CRAFT":
            target_resource_name = item
            target_resource_name = ''.join(char for char in target_resource_name if char.isalnum()).lower()
            if target_resource_name not in self.previous_inventory:
                return False
            if self.previous_inventory[target_resource_name] == self.inventory[target_resource_name]:
                if self.number > 1:
                    return False
            if self.previous_inventory[target_resource_name] != self.inventory[target_resource_name] and self.number > 1:
                self.number -= 1
                return False
        elif plan_type == "EXPLORE":
            if self.stay < 5:
                return False
        return True


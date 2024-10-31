import os
from datetime import datetime

os.environ["RAY_DEDUP_LOGS"] = "0"

import copy
import ray
from ray.tune.logger import pretty_print, UnifiedLogger
from ray.tune.registry import register_env
from ray.rllib.algorithms.a3c import A3CConfig
from ray.rllib.algorithms.dqn import DQNConfig
from ray.rllib.algorithms.ppo import PPOConfig, PPOTorchPolicy
from ray.rllib.algorithms.r2d2 import R2D2Config, R2D2TorchPolicy
from ray.rllib.models import ModelCatalog
from ray.rllib.policy.policy import PolicySpec

from ..wrapper.rllib_env_wrapper import RllibEnvWrapper, get_spaces_and_model_config
from ..network.gnn_network import TorchGRNNModel, TorchGCNNModel
from ..network.centralized_network import CentralizedCriticModel
from ..policy import RandomPolicy, PPOProsocialPolicy, CCPPOTorchPolicy, DQNMaskTorchPolicy

ModelCatalog.register_custom_model('gcnn_model', TorchGCNNModel)
ModelCatalog.register_custom_model('glstm_model', TorchGRNNModel)
ModelCatalog.register_custom_model('centralized_model', CentralizedCriticModel)


def train(args):
    """contract training function"""
    env_name = "AdaSociety"
    env_config = {'env_dir': args.env_dir}
    register_env(env_name, lambda config: RllibEnvWrapper(config))
    dummy_env = RllibEnvWrapper(env_config)
    model_config_dict, obs_space_dict, action_space_dict = get_spaces_and_model_config(dummy_env, args)
    ray.init()

    if args.lstm:
        player_model_name = 'glstm_model'
    else:
        player_model_name = 'gcnn_model'

    if args.algo == 'Rainbow':
        if args.lstm:
            algo_config = R2D2Config()
            policy_name = R2D2TorchPolicy
        else:
            algo_config = DQNConfig()
            policy_name = DQNMaskTorchPolicy
        algo_name = 'rainbow'
    elif args.algo == 'PPO':
        algo_config = PPOConfig()
        policy_name = PPOTorchPolicy
        algo_name = 'ppo'
    elif args.algo == 'random':
        algo_config = A3CConfig()
        policy_name = RandomPolicy
        algo_name = 'random'
    elif args.algo == 'PPOProsocial':
        algo_config = PPOConfig()
        policy_name = PPOProsocialPolicy
        algo_name = 'ppo_prosocial'
    elif args.algo == 'CCPPO':
        algo_config = PPOConfig()
        policy_name = CCPPOTorchPolicy
        algo_name = 'ccppo'
        player_model_name = 'centralized_model'

    player_names = list(model_config_dict.keys())
    algo_config = (
        algo_config
        .environment(env_name, env_config=env_config)
        .framework('torch')
        .rollouts(
            num_rollout_workers=args.num_rollout_workers,
            num_envs_per_worker=args.num_envs_per_worker,
            rollout_fragment_length=args.rollout_fragment_length,
        )
        # Use GPUs iff `RLLIB_NUM_GPUS` env var set to > 0.
        .resources(num_gpus=1,)
        .rl_module( _enable_rl_module_api=False)
        .training(
            gamma=args.gamma,
            lr=args.lr,
            model={
                'max_seq_len': args.max_seq_len,
                'custom_model': player_model_name,
                'custom_model_config': model_config_dict[player_names[0]]
            },
            train_batch_size = args.num_rollout_workers * args.num_envs_per_worker * args.rollout_fragment_length,
            _enable_learner_api=False,
        )
    )
    # extra config for different algorithms
    if args.algo == 'Rainbow':
        dqn_model_config_dict = algo_config['model']
        # dqn_model_config_dict['no_final_linear'] = True
        algo_config = (
            algo_config
            .rollouts(compress_observations=True)
            .training(
                num_steps_sampled_before_learning_starts = args.num_cold_start_steps,
                num_atoms = args.num_atoms,
                v_min = args.v_min,
                v_max = args.v_max,
                noisy = args.noisy, 
                n_step = args.n_step,
                model = dqn_model_config_dict,
            )
        )
    elif args.algo == 'PPO' or args.algo == 'PPOProsocial':
        algo_config = (
            algo_config.training(
                sgd_minibatch_size = args.sgd_minibatch_size,
                num_sgd_iter = args.num_sgd_iter,
                grad_clip = args.grad_clip,
                entropy_coeff = 0.01
            )
        )

    algo_config_list = []
    for player in player_names:
        new_model_config_dict = algo_config['model']
        new_model_config_dict['custom_model_config'] = model_config_dict[player]
        algo_config_list.append(
            copy.deepcopy(algo_config).training(model = new_model_config_dict)
        )

    policies = {
        f'{algo_name}_{player}': PolicySpec(
            policy_name, 
            obs_space_dict[player],
            action_space_dict[player],
            algo_config_list[i]
        ) for i, player in enumerate(player_names)
    }
    for i, player in enumerate(player_names):
        player_type = player.split('_')[0]
        if f'{algo_name}_{player_type}' not in policies:
            policies[f'{algo_name}_{player_type}'] = copy.deepcopy(policies[f'{algo_name}_{player}'])

    if args.share:
        def policy_mapping_fn(agent_id, episode, worker, **kwargs):
            agent_type = agent_id.split('_')[0]
            return f'{algo_name}_{agent_type}'
    else:
        def policy_mapping_fn(agent_id, episode, worker, **kwargs):
            return f'{algo_name}_{agent_id}'

    if args.algo == 'random':
        policies_to_train = []
    else:
        policies_to_train = list(policies.keys())
    algo_config = algo_config.multi_agent(
        policies = policies,
        policy_mapping_fn = policy_mapping_fn,
        policies_to_train = policies_to_train,
    )

    def custom_logger_creator(config):
        timestr = datetime.today().strftime("%Y-%m-%d_%H-%M-%S")
        logdir = os.path.join(os.path.expanduser("~/ray_results"), f"{args.algo}_{timestr}")
        os.makedirs(logdir, exist_ok=True)
        return UnifiedLogger(config, logdir, loggers=None)
    
    algo = algo_config.build()
    if args.checkpoint != '':
        algo.restore(args.checkpoint)
    # Start training
    for i in range(args.max_training_iter):
        result = algo.train()
        result['sampler_results']['hist_stats'] = None
        result['info'] = None
        print(pretty_print(result))
        if (i+1)% args.save_interval == 0:
            path = algo.save()
            print(f'Checkpoint loaded in {path}')
    algo.stop()

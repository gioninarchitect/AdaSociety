import argparse
from project.RLlib.train import train
import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"

def parse_args():
    parser = argparse.ArgumentParser()

    #===common training config===
    parser.add_argument('--lstm', action='store_true', help="use LSTM")
    parser.add_argument('--share', action='store_true', help="parameter sharing") 
    parser.add_argument('--algo', 
                        type=str, 
                        choices=['PPO', 'Rainbow', 'random', 'PPOProsocial', 'CCPPO'], 
                        default='PPO',
                        help='RL algorithm')
    parser.add_argument('--lr', type=float, default=1e-4, help='learning rate')
    parser.add_argument('--gamma', type=float, default=0.99, help='discount factor')
    parser.add_argument('--num_rollout_workers', type=int, default=1, help='number of rollout workers')
    parser.add_argument('--num_envs_per_worker', type=int, default=1, help='number of envs per worker')
    parser.add_argument('--rollout_fragment_length', type=int, default=1200, help='rollout fragment length')
    parser.add_argument('--checkpoint', type=str, default='', help='checkpoint directory to restore')
    parser.add_argument('--save_interval', type=int, default=500, help='save interval')
    parser.add_argument('--max_training_iter', type=int, default=10000, help='max training iteration')
    parser.add_argument('--grad_clip', type=float, default=10.0, help='gradient clipping')
    parser.add_argument('--select_group', action='store_true', 
                        help='need to select a group node via GNN (the last group_num actions are selecting group nodes)')
    
    #===LSTM specific config===
    parser.add_argument('--max_seq_len', type=int, default=16, help='max sequence length in LSTM')
    parser.add_argument('--lstm_state_size', type=int, default=128, help='LSTM state size')

    #===PPO specific config===
    parser.add_argument('--sgd_minibatch_size', type=int, default=512, help='sgd minibatch size in PPO')
    parser.add_argument('--num_sgd_iter', type=int, default=15, help='number of sgd iterations in PPO')
    
    #===Rainbow specific config===
    parser.add_argument('--num_cold_start_steps', type=int, default=10000, help='number of cold start steps in Rainbow')
    parser.add_argument('--num_atoms', type=int, default=21, help='number of atoms in Rainbow')
    parser.add_argument('--v_min', type=float, default=0.0, help='v_min in Rainbow')
    parser.add_argument('--v_max', type=float, default=50.0, help='v_max in Rainbow')
    parser.add_argument('--noisy', action='store_true', help='use noisy output in Rainbow')
    parser.add_argument('--n_step', type=int, default=3, help='n_step in Rainbow')

    #===Env directory===
    parser.add_argument('--env_dir', type=str, default='./config/main.json', help='environment directory')

    args = parser.parse_args()
    if args.lstm and args.algo == "Rainbow":
        print(Warning("LSTM + Rainbow not supported!"))
    return args

if __name__ == '__main__':
    args = parse_args()
    train.train(args)

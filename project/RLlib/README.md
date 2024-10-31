# Training agents via RLlib in *AdaSociety*

*AdaSociety* is a general environment that supports developing your own algorithms and adapting any popular RL library. You may need to write some simple wrappers to adapt to the training platform you want to use. Here, we provide our implementation for the well known RL library [RLlib](https://docs.ray.io/en/latest/rllib/index.html).

- **[wrapper](./wrapper)**: A wrapper for connecting to the *AdaSociety* and RLlib APIs.

- **[train](./train)**: The main script which creates the environment instance and runs the RL algorithm, which is called by [rllib_train.py](../../rllib_train.py).
- **[network](./network)** and **[policy](./policy)**:  The modules needed to train agents using the RLlib framework.

Here is an example to run RecPPO in *Negotiation-Easy*:
```
python rllib_train.py \
    --algo PPO \
    --task negotiation \
    --lstm \
    --lr 1e-4 \
    --num_rollout_workers 8 \
    --num_envs_per_worker 8 \
    --rollout_fragment_length 1000
```

Algorithm parameters can be specified by command-line arguments in `rllib_train.py`:
- **Common:** The common parameters used in all algorithms:
  `lr`: learning rate
  `gamma`: discounted factor
  `num_rollout_workers`: The number of workers enabled in RLlib
  `num_envs_per_worker`: Number of environments started within each worker

- **PPO:** 
  `sgd_minibatch_size`: Minimum batch size to use with each stochastic gradient descent (SGD) update
  `num_sgd_iter`: Number of SGD iterations per optimization cycle

- **Rainbow:** 
  `num_cold_start_steps`: The number of initial random steps that the agent performs in the environment before starting training
  `num_atoms`: The degree of discretization of Distributional DQN
  `v_min` and `v_max`: The range of Q value distribution in Distributional DQN
  `noisy`: use noisy output in Rainbow
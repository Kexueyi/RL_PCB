#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 10 11:57:27 2022

@author: luke
"""

import argparse
import numpy as np
from datetime import datetime

# Necessary for logging library information
import pcb.pcb as pcb
import graph.graph as graph    

# def gen_default_settings():
    
#     return settings

def cmdLine_args():
    parser = argparse.ArgumentParser(description="unified argument parser for pcb component training", usage="<script-name> -p <pcb_file> --rl_model_type [TD3 | SAC]", epilog="This text will be shown after the help")
    
    parser.add_argument("--policy", default="TD3")                  # Policy name (TD3, DDPG or OurDDPG)
    parser.add_argument("-s", "--seed", required=False, nargs="+", type=np.uint32, default=None)             # Sets Gym, PyTorch and Numpy seeds
    parser.add_argument("--start_timesteps", default=25e3, type=int)# Time steps initial random policy is used
    parser.add_argument("--max_timesteps", default=1e6, type=int)   # Max time steps to run environment (1e6)
    parser.add_argument("--target_exploration_steps", default=10e3, type=int) 

    parser.add_argument("--save_model", action="store_true")        # Save model and optimizer parameters
    parser.add_argument("--load_model", default="")                 # Model load file name, "" doesn't load, "default" uses file_name
    
    parser.add_argument("--expert_model", default=None, help="path to expert model used in expert parameter exploration.")
    parser.add_argument("-w", required=False, type=np.float32, default=1.0)
    parser.add_argument("--hpwl", required=False, type=np.float32, default=1.0)
    parser.add_argument("-o", required=False, type=np.float32, default=1.0)
    parser.add_argument("--training_pcb", required=False, default=None)
    parser.add_argument("--evaluation_pcb", required=False, default=None)
    parser.add_argument("--tensorboard_dir", required=False, default="./tensorboard")   # log_dir is assigned to be equal to tensoboard_dir
    parser.add_argument("--incremental_replay_buffer", choices=[None, 'double', 'triple', 'quadruple'], default=None, required=False)
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"], required=False)
    parser.add_argument("--experiment", required=False, type=str, default=None, help="descriptive experiment name")
    parser.add_argument("--hyperparameters", required=False, type=str, default=None, help="path to a hyperparameters file.")
    parser.add_argument("--runs", required=False, type=np.int32, default=1, help="Number of times to run the experiment.")
    parser.add_argument("--auto_seed", required=False, action='store_true', default=False, help='ignore seed value and generate one based of the current time for everyrun')
    parser.add_argument("--workers", required=False, type=int, default=2, help="number of workers on which 'runs' will execute.")
    parser.add_argument("--verbose", required=False, type=int, default=0, help="Program verbosity")
    parser.add_argument("--evaluate_every", required=False,  type=np.uint32, default=250000) # How often (time steps) we evaluate
    parser.add_argument("--early_stopping", required=False, type=int, default=None, help="If no improvement occurs after <early_stopping> steps, then learning will terminate early. Mean episode reward computed over the last 100 episodes is used for comparision")
    parser.add_argument("--shuffle_training_idxs", required=False, action='store_true', default=False, help='shuffle agent idxs during training')
    parser.add_argument("--shuffle_evaluation_idxs", required=False, action='store_true', default=False, help='shuffle agent idxs during evaluation')

    args = parser.parse_args()
    settings = dict()
    settings["default_seed"] = args.seed

    configure_seed(args)
    

    settings["policy"] = args.policy
    settings["rl_model_type"] = args.policy              # For backward compatibility.
    settings["seed"] = args.seed
    settings["start_timesteps"] = args.start_timesteps
    # settings["eval_freq"] = args.eval_freq
    settings["max_timesteps"] = args.max_timesteps
    settings["max_steps"] = args.max_timesteps           # For backward compatibility.

    settings["target_exploration_steps"] = args.target_exploration_steps
    settings["save_model"] = args.save_model
    settings["load_model"] = args.load_model
    settings["expert_model"] = args.expert_model
    settings["w"] = args.w
    settings["hpwl"] = args.hpwl
    settings["o"] = args.o
    settings["training_pcb"] = args.training_pcb
    settings["evaluation_pcb"] = args.evaluation_pcb
    settings["tensorboard_dir"] = args.tensorboard_dir
    settings["incremental_replay_buffer"] = args.incremental_replay_buffer
    settings["device"] = args.device
    settings["experiment"] = args.experiment
    settings["hyperparameters"] = args.hyperparameters
    settings["runs"] = args.runs
    settings["auto_seed"] = args.auto_seed
    settings["workers"] = args.workers
    settings["run_name"] = datetime.now().strftime('%s')
    settings["verbose"] = args.verbose
    settings["evaluate_every"] = args.evaluate_every            # Periodic evaluation
    if args.early_stopping == None:
        settings["early_stopping"] = args.max_timesteps
    else:
        settings["early_stopping"] = args.early_stopping
    settings["shuffle_training_idxs"] = args.shuffle_training_idxs
    settings["shuffle_evaluation_idxs"] = args.shuffle_evaluation_idxs

    return args, settings

    # settings
def configure_seed(args):
    
    if (args.auto_seed == True) and (args.seed is not None):
        if len(args.seed) == args.runs:
            print('auto_seed is enabled while a valid seed configuration was provided. auto_seed takes precedence and will override the provided seed values.')
    
    if args.auto_seed == True:  # assign run seed values randomly based of an rng seed with current time.
        args.seed = []
        rng = np.random.default_rng(seed=int(datetime.now().strftime('%s')))
        for i in range(args.runs):
            args.seed.append(np.int0(rng.uniform(low=0,high=(np.power(2,32)-1))))
    else:
        if (args.seed is None) or (len(args.seed) != args.runs):   # seed value is not provided or not provided correctly
            # issue a warning
            rng = np.random.default_rng(seed=99)
            args.seed = []
            for i in range(args.runs):
                args.seed.append(np.int0(rng.uniform(low=0,high=(np.power(2,32)-1))))

def write_desc_log( full_fn: str, settings: dict, hyperparameters: dict = None, model = None):
    f = open(full_fn, "w")
    f.write('\n================== settings ==================\r\n')
    for key,value in settings.items():
        f.write(f"{key} -> {value}\r\n")
        
    if hyperparameters is not None:
        f.write('\n================== hyperparameters ==================\r\n')
        for key,value in hyperparameters.items():
            f.write(f"{key} -> {value}\r\n")
            
    if model is not None:
        f.write(f'\n================== {settings["rl_model_type"]} Model Architecture ==================\r\n')
        f.write("Actor\n")
        if settings["rl_model_type"] == "TD3":
            f.write(str(model.actor))
        else: # SAC
            f.write(str(model.policy))
        f.write("\n\n")
        f.write("Critic\n")
        f.write(str(model.critic))
        f.write("\n\n")
        f.write("Critic target\n")        
        f.write(str(model.critic_target))
        f.write("\n\n")
        f.write(f"Activation function : {str(model.critic.activation_fn)}")
        f.write("\n\n")
        
    f.write('\n================== Dependency Information ==================\r\n')
    f.write(pcb.build_info_as_string()[1:-1])       # Strip leading and trailing newline ('\n') characters.
    f.write(graph.build_info_as_string())
    
    f.close()         

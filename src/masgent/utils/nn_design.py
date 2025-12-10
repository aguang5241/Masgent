#!/usr/bin/env python
# -*-coding:utf-8 -*-

import os
import torch
import optuna
import shutil
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from copy import copy
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold


def get_std(data, scaler):
    data_std = scaler.transform(data)
    return data_std


def get_scaler(data_scaler):
    data = pd.read_csv(data_scaler)
    scaler = StandardScaler()
    scaler.fit(data.to_numpy())
    return scaler


def define_model(trial):
    n_layers = trial.suggest_int('n_layers', LAYERS_MIN, LAYERS_MAX, step=LAYERS_STEP)
    layers = []
    input_features = pd.read_csv(INPUT_DATA).shape[1]
    output_features = pd.read_csv(OUTPUT_DATA).shape[1]
    in_features = copy(input_features)

    for i in range(n_layers):
        out_features = trial.suggest_int(f'n_units_l{i}', NODES_MIN, NODES_MAX, step=NODES_STEP)
        layers.append(torch.nn.Linear(in_features, out_features))
        layers.append(torch.nn.Sigmoid())
        p = trial.suggest_float("dropout_l{}".format(i), DROPOUT_MIN, DROPOUT_MAX)
        layers.append(torch.nn.Dropout(p))
        in_features = out_features
    layers.append(torch.nn.Linear(in_features, output_features))
    return torch.nn.Sequential(*layers)


def objective(trial):
    # Get the training and validation data
    x_scaler = get_scaler(data_scaler=INPUT_DATA)
    y_scaler = get_scaler(data_scaler=OUTPUT_DATA)
    
    # Perform K-Fold cross validation
    input_data = pd.read_csv(INPUT_DATA)
    output_data = pd.read_csv(OUTPUT_DATA)
    x = input_data.to_numpy()
    y = output_data.to_numpy()
    x_std = get_std(x, x_scaler)
    y_std = get_std(y, y_scaler)

    # Training with K-Fold cross validation
    loss_train_data, loss_valid_data = [], []
    loss_train_fold, loss_valid_fold = [], []
    for fold, (train_index, valid_index) in enumerate(KFold(n_splits=5, shuffle=True, random_state=0).split(x_std)):
        # Define the model
        torch.manual_seed(0)
        model = define_model(trial).to(DEVICE)
        optimizer_name = trial.suggest_categorical('optimizer', OPTIMIZERS)
        lr = trial.suggest_float('lr', LR_MIN, LR_MAX, log=True)
        wd = trial.suggest_float('weight_decay', WD_MIN, WD_MAX, log=True)
        optimizer = getattr(torch.optim, optimizer_name)(model.parameters(), lr=lr, weight_decay=wd)
        loss_func = torch.nn.MSELoss()

        # Split the data into training and validation sets
        x_train, x_valid = x_std[train_index], x_std[valid_index]
        y_train, y_valid = y_std[train_index], y_std[valid_index]
        data_train, data_valid = [x_train, y_train], [x_valid, y_valid]

        # Transfer the data as torch tensors
        train_x, train_y = torch.FloatTensor(data_train[0]).to(DEVICE), torch.FloatTensor(data_train[1]).to(DEVICE)
        valid_x, valid_y = torch.FloatTensor(data_valid[0]).to(DEVICE), torch.FloatTensor(data_valid[1]).to(DEVICE)

        # Dynamically change the number of epochs based on the NN complexity
        layers = (model.__len__() - 1) // 3
        epochs = 100 + 10 * layers

        # Training
        model.train()
        for epoch in tqdm(range(epochs), desc=f'Trial {trial.number} Fold {fold+1}', position=0, leave=False):
            optimizer.zero_grad()
            output_train = model(train_x)
            output_valid = model(valid_x)
            loss_train = loss_func(output_train, train_y)
            loss_valid = loss_func(output_valid, valid_y)
            loss_train_data.append([fold, epoch, loss_train.item()])
            loss_valid_data.append([fold, epoch, loss_valid.item()])
            loss_train.backward()
            optimizer.step()

        # Validation
        with torch.no_grad():
            model.eval()
            train_y_pred = model(train_x)
            valid_y_pred = model(valid_x)
            loss_train_pred = loss_func(train_y_pred, train_y)
            loss_valid_pred = loss_func(valid_y_pred, valid_y)
            loss_train_fold.append([fold, loss_train_pred.item()])
            loss_valid_fold.append([fold, loss_valid_pred.item()])

    # Get the average validation loss
    loss_train_fold = np.array(loss_train_fold)
    loss_valid_fold = np.array(loss_valid_fold)
    loss_train_avg = loss_train_fold[:, 1].mean()
    loss_valid_avg = loss_valid_fold[:, 1].mean()

    # Define the accuracy
    accuracy = loss_valid_avg

    global CURRENT_ACCURACY, FOUND_NEW
    if accuracy < CURRENT_ACCURACY:
        CURRENT_ACCURACY = accuracy
        FOUND_NEW = True
    else:
        FOUND_NEW = False

    # Plot the loss curve
    if FOUND_NEW:
        loss_train_data = np.array(loss_train_data)
        loss_valid_data = np.array(loss_valid_data)
        sns.set_theme(font_scale=1.2, style='whitegrid')
        matplotlib.rcParams['xtick.direction'] = 'in'
        matplotlib.rcParams['ytick.direction'] = 'in'
        fig = plt.figure(figsize=(13, 6), constrained_layout=True)
        for fold in range(6):
            if fold != 5:
                # Plot the loss curve for each fold
                ax = plt.subplot(3, 2, fold+1)
                fold_train = loss_train_data[loss_train_data[:, 0] == fold]
                fold_valid = loss_valid_data[loss_valid_data[:, 0] == fold]
                ax.plot(fold_train[:, 1], fold_train[:, 2], label='Training', color='C0', linewidth=1.5)
                ax.plot(fold_valid[:, 1], fold_valid[:, 2], label='Validation', color='C1', linewidth=1.5)
                ax.text(0.05, 0.95, f'Fold {fold+1}', transform=ax.transAxes, fontweight='bold', va='top', ha='left')
                ax.set_xlabel('Epoch')
                ax.set_ylabel('Loss')
                ax.legend(loc='upper right', frameon=True, ncol=2)
            elif fold == 5:
                # Plot the average loss
                ax = plt.subplot(3, 2, fold+1)
                ax.plot(loss_train_fold[:, 0], loss_train_fold[:, 1], label='Training', color='C0', linewidth=0, marker='o', markersize=10, markerfacecolor='none', markeredgecolor='C0', markeredgewidth=1.5)
                ax.plot(loss_valid_fold[:, 0], loss_valid_fold[:, 1], label='Validation', color='C1', linewidth=0, marker='o', markersize=10, markerfacecolor='none', markeredgecolor='C1', markeredgewidth=1.5)
                ax.axhline(loss_train_avg, color='C0', linestyle='--', linewidth=2.0, label=f'Avg. Training = {loss_train_avg:.2e}')
                ax.axhline(loss_valid_avg, color='C1', linestyle='--', linewidth=2.0, label=f'Avg. Validation = {loss_valid_avg:.2e}')
                ax.set_xticks(range(5))
                ax.set_xticklabels(range(1, 6))
                ax.set_xlabel('Fold')
                ax.legend(loc='upper right', frameon=True, ncol=2)
                ax.set_ylabel('Loss')
        plt.savefig(f'{SAVE_PATH}/best_model_losses/loss_model_{trial.number}.png', dpi=330)
        plt.close()

    # Handle pruning based on the  intermediate value.
    trial.report(accuracy, epoch)
    if trial.should_prune():
        raise optuna.exceptions.TrialPruned()
    
    # Save the model
    torch.save(model, f'{SAVE_PATH}/tested_models/model_{trial.number}.pkl')

    return accuracy


def optimize(input_data, output_data, n_trials, save_path):
    global INPUT_DATA, OUTPUT_DATA, N_TRIALS, SAVE_PATH, FOUND_NEW, CURRENT_ACCURACY, LAYERS_MIN, LAYERS_MAX, LAYERS_STEP, NODES_MIN, NODES_MAX, NODES_STEP, OPTIMIZERS, LR_MIN, LR_MAX, WD_MIN, WD_MAX, DROPOUT_MIN, DROPOUT_MAX, DEVICE

    INPUT_DATA = input_data
    OUTPUT_DATA = output_data
    N_TRIALS = n_trials
    SAVE_PATH = save_path
    FOUND_NEW = False
    CURRENT_ACCURACY = 1e10
    LAYERS_MIN, LAYERS_MAX, LAYERS_STEP = 2, 10, 1
    NODES_MIN, NODES_MAX, NODES_STEP = 8, 256, 8
    OPTIMIZERS= ['Adam', 'SGD', 'RMSprop']
    LR_MIN, LR_MAX = 1e-4, 1e-2
    WD_MIN, WD_MAX = 1e-6, 1e-2
    DROPOUT_MIN, DROPOUT_MAX = 0.0, 0.5
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Create directory for storing results
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
    if not os.path.exists(f'{SAVE_PATH}/tested_models'):
        os.makedirs(f'{SAVE_PATH}/tested_models')
    if not os.path.exists(f'{SAVE_PATH}/best_model_losses'):
        os.makedirs(f'{SAVE_PATH}/best_model_losses')

    # Set random seed for reproducibility
    torch.manual_seed(42)
    np.random.seed(42)

    # Optuna process
    study = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=N_TRIALS, timeout=None)

    # Optimization complete
    pruned_trials = study.get_trials(deepcopy=False, states=[optuna.trial.TrialState.PRUNED])
    complete_trials = study.get_trials(deepcopy=False, states=[optuna.trial.TrialState.COMPLETE])
    best_trial = study.best_trial

    # Write log
    with open(f'{SAVE_PATH}/best_model_params.log', 'a') as f:
        f.write(f'Study statistics:\n')
        f.write(f'  Number of finished trials: {len(study.trials)}\n')
        f.write(f'  Number of pruned trials: {len(pruned_trials)}\n')
        f.write(f'  Number of complete trials: {len(complete_trials)}\n')
        f.write(f'Best trial:\n')
        f.write(f'  Number: {best_trial.number}\n')
        f.write(f'  Value: {best_trial.value}\n')
        f.write(f'  Params:\n')
        for key, value in best_trial.params.items():
            f.write(f'    {key}: {value}\n')
    
    # Select target model
    old_file_path = f'{SAVE_PATH}/tested_models/model_{best_trial.number}.pkl'
    new_file_path = f'{SAVE_PATH}/best_model.pkl'
    shutil.copyfile(old_file_path, new_file_path)
    
    # Save study object
    joblib.dump(study, f'{SAVE_PATH}/study.pkl')
    
    # # Remove tested models
    # shutil.rmtree(f'{SAVE_PATH}/tested_models')

    # Draw the study results
    study_path = f'{SAVE_PATH}/study.pkl'
    draw_study(study_path)


def draw_study(study_path):
    study = joblib.load(study_path)
    best_trial_number = study.best_trial.number
    best_trial_value = study.best_trial.value

    # Save study results to csv
    data = study.trials_dataframe()
    pd.DataFrame(data).to_csv(f'{study_path[:-4]}.csv', index=False)

    # Get the complete trials data
    data_complete = data[data['state'] == 'COMPLETE']
    number = data_complete.loc[:, 'number']
    value = data_complete.loc[:, 'value']
    lr = data_complete.loc[:, 'params_lr']
    n_layers = data_complete.loc[:, 'params_n_layers']
    optimizer = data_complete.loc[:, 'params_optimizer']
    weight_decay = data_complete.loc[:, 'params_weight_decay']
    value_min = [value.iloc[:i+1].min() for i in range(len(value))]

    # Repeat the last value_min
    value_min = value_min + [value_min[-1]]

    # Add the last number to number_min
    number_min = number.copy().to_list()
    number_min = number_min + [len(data)]

    # Get the pruned trials data
    data_pruned = data[data['state'] == 'PRUNED']
    pruned_number = data_pruned.loc[:, 'number']
    pruned_value = data_pruned.loc[:, 'value']

    sns.set_theme(font_scale=1.2, style='whitegrid')
    matplotlib.rcParams['xtick.direction'] = 'in'
    matplotlib.rcParams['ytick.direction'] = 'in'

    # History
    fig = plt.figure(figsize=(13, 4), constrained_layout=True)
    ax = plt.subplot()
    ax.scatter(number, value, label='Completed Trials', marker='o', facecolor='none', edgecolors='C0', linewidths=1.0, s=20)
    ax.scatter(pruned_number, pruned_value, label='Pruned Trials', marker='o', facecolor='none', edgecolors='C7', linewidths=1.0, s=20, alpha=0.5)
    ax.plot(number_min, value_min, c='r', label='Best Value')
    ax.scatter(best_trial_number, best_trial_value, marker='o', facecolor='C3', edgecolors='C3', linewidths=1.5, s=20)
    ax.scatter(best_trial_number, best_trial_value, marker='*', facecolor='C3', edgecolors='C3', linewidths=1.5, s=100, label=f'Best Trial: #{best_trial_number}')
    ax.set_xlabel('Number of Trials')
    ax.set_ylabel('Objective Value')
    ax.legend(loc='upper right', frameon=True)
    plt.savefig(f'{study_path[:-4]}_history.png', dpi=330)
    plt.close()
    # print(f'Plot of study history saved to {study_path[:-4]}_history.png')

    # Importance
    x = ['weight_decay', 'optimizer', 'lr', 'n_layers']
    x_labels = ['Weight Decay', 'Optimizer', 'Learning Rate', 'Layers']
    importance = optuna.importance.get_param_importances(study, params=x)
    h = [importance[x[0]], importance[x[1]], importance[x[2]], importance[x[3]]]
    fig = plt.figure(figsize=(4, 4), constrained_layout=True)
    ax = plt.subplot()
    ax_twin = ax.twiny()
    ax.set_zorder(ax_twin.get_zorder() + 1)
    ax.bar(x_labels, h, color='C0', edgecolor='black', linewidth=1.0)
    ax.set_ylim(top=max(h) * 1.1)
    ax_twin.set_xlim(ax.get_xlim())
    ax_twin.set_xticks(range(len(x_labels)))
    ax_twin.set_xticklabels(x_labels, rotation=15)
    ax.set_xticks(x_labels)
    ax.set_xticklabels([])
    ax.set_xlabel('Hyperparameters')
    ax.set_ylabel('Importance for Objective Value')
    plt.savefig(f'{study_path[:-4]}_importance.png', dpi=330)
    plt.close()
    # print(f'Plot of study importance saved to {study_path[:-4]}_importance.png')

    # Slice
    fig, ax = plt.subplots(1, 4, figsize=(9, 4), constrained_layout=True)
    a = ax[0].scatter(weight_decay, value, c=number, cmap='Blues', edgecolor='gray', linewidths=0.1)
    ax[0].set_xscale('log')
    ax[0].set_title('Weight Decay')
    ax[0].set_ylabel('Objective Value')
    ax[1].scatter(optimizer, value, c=number, cmap='Blues', edgecolor='gray', linewidths=0.1)
    ax[1].set_title('Optimizer')
    ax[1].set_xticks(range(len(optimizer.unique())))
    ax[1].set_xticklabels(optimizer.unique())
    ax[1].set_xlim(-0.5, len(optimizer.unique()) - 0.5)
    ax[2].scatter(lr, value, c=number, cmap='Blues', edgecolor='gray', linewidths=0.1)
    ax[2].set_xscale('log')
    ax[2].set_title('Learning Rate')
    ax[3].scatter(n_layers, value, c=number, cmap='Blues', edgecolor='gray', linewidths=0.1)
    ax[3].set_xticks(n_layers)
    ax[3].set_xticklabels(n_layers)
    ax[3].set_title('Layers')
    ax[3].set_xlim(min(n_layers) - 1, max(n_layers) + 1)
    cb = plt.colorbar(a, ax=ax, pad=0.015, aspect=40)
    cb.ax.set_title('# Trials')
    plt.savefig(f'{study_path[:-4]}_slice.png', dpi=330)
    plt.close()
    # print(f'Plot of study slice saved to {study_path[:-4]}_slice.png')


if __name__ == '__main__':
    optimize(
        input_data=INPUT_DATA,
        output_data=OUTPUT_DATA,
        n_trials=N_TRIALS,
        save_path=SAVE_PATH,
    )
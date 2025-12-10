
#!/usr/bin/env python
# -*-coding:utf-8 -*-

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import torch
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error, r2_score
from matplotlib.ticker import FormatStrFormatter
from tqdm import tqdm

def init_weights(m):
    if isinstance(m, torch.nn.Linear):
        m.reset_parameters()

def get_std(data):
    scaler = StandardScaler()
    data_std = scaler.fit_transform(data)
    return scaler, data_std

def train(input_data, output_data, best_model_pkl, best_model_params, epochs, patience, save_path):
    global INPUT_DATA, OUTPUT_DATA, BEST_MODEL_PKL, BEST_MODEL_PARAMS, EPOCHS, PATIENCE, SAVE_PATH, DEVICE
    
    INPUT_DATA = input_data
    OUTPUT_DATA = output_data
    BEST_MODEL_PKL = best_model_pkl
    BEST_MODEL_PARAMS = best_model_params
    EPOCHS = epochs
    PATIENCE = patience
    SAVE_PATH = save_path
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Create save path directory
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)

    # Get training data
    input_data = pd.read_csv(INPUT_DATA)
    output_data = pd.read_csv(OUTPUT_DATA)
    
    # Shuffle and split data
    x = input_data.to_numpy()
    y = output_data.to_numpy()
    x_scaler, x_std = get_std(x)
    y_scaler, y_std = get_std(y)
    x_train, x_valid, y_train, y_valid = train_test_split(x_std, y_std, test_size=0.2, shuffle=True, random_state=42)
    data_train, data_valid = [x_train, y_train], [x_valid, y_valid]

    # Model reset
    torch.manual_seed(42)
    model = torch.load(BEST_MODEL_PKL, weights_only=False)
    model.apply(init_weights)

    # Parse the lr and weight_decay from best_model_params.log
    with open(BEST_MODEL_PARAMS, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'lr:' in line:
                LR = float(line.split('lr:')[1].strip())
            if 'weight_decay:' in line:
                WD = float(line.split('weight_decay:')[1].strip())

    # Retrain model
    model.train()
    optimizer = torch.optim.RMSprop(model.parameters(), lr=LR, weight_decay=WD)
    loss_func = torch.nn.MSELoss()
    best_loss = np.inf
    wait = 0
    train_loss = []
    valid_loss = []
    train_x, train_y = torch.FloatTensor(data_train[0]).to(DEVICE), torch.FloatTensor(data_train[1]).to(DEVICE)
    valid_x, valid_y = torch.FloatTensor(data_valid[0]).to(DEVICE), torch.FloatTensor(data_valid[1]).to(DEVICE)
    for epoch in tqdm(range(EPOCHS), desc='Training'):
        optimizer.zero_grad()
        output_train = model(train_x)
        output_valid = model(valid_x)
        loss_train = loss_func(output_train, train_y)
        loss_valid = loss_func(output_valid, valid_y)
        loss_train.backward()
        optimizer.step()
        train_loss.append([epoch, loss_train.item()])
        valid_loss.append([epoch, loss_valid.item()])

        # Early stopping
        if loss_valid.item() < best_loss:
            best_loss = loss_valid.item()
            wait = 0
        else:
            wait += 1
            if wait >= PATIENCE:
                break
    
    # Plot training loss vs. epoch and validation loss vs. epoch
    train_loss = np.array(train_loss)
    valid_loss = np.array(valid_loss)
    sns.set_theme(font_scale=1.2, style='whitegrid')
    matplotlib.rcParams['xtick.direction'] = 'in'
    matplotlib.rcParams['ytick.direction'] = 'in'
    fig = plt.figure(figsize=(10, 4), constrained_layout=True)
    ax = plt.subplot()
    ax.plot(train_loss[:, 0], train_loss[:, 1], label='Training', color='C0', linewidth=1.5)
    ax.plot(valid_loss[:, 0], valid_loss[:, 1], label='Validation', color='C1', linewidth=1.5)
    ax.set_ylabel('Loss')
    ax.set_xlabel('Epoch')
    ax.legend(loc='upper right', frameon=True)
    plt.savefig(f'{SAVE_PATH}/loss.png', dpi=330)
    plt.close()

    # Save model
    torch.save(model, SAVE_PATH + '/trained_model.pkl')

    # Evaluate model
    model.eval()
    with torch.no_grad():
        pred_y_train = model(train_x).cpu().numpy()
        pred_y_valid = model(valid_x).cpu().numpy()
    pred_y_train_rescaled = y_scaler.inverse_transform(pred_y_train)
    true_y_train_rescaled = y_scaler.inverse_transform(y_train)
    pred_y_valid_rescaled = y_scaler.inverse_transform(pred_y_valid)
    true_y_valid_rescaled = y_scaler.inverse_transform(y_valid)
    
    # Calculate RMSE and R2 on training and validation set
    rmse_train = root_mean_squared_error(true_y_train_rescaled, pred_y_train_rescaled)
    r2_train = r2_score(true_y_train_rescaled, pred_y_train_rescaled)
    rmse_valid = root_mean_squared_error(true_y_valid_rescaled, pred_y_valid_rescaled)
    r2_valid = r2_score(true_y_valid_rescaled, pred_y_valid_rescaled)
    with open(f'{SAVE_PATH}/performance.log', 'w') as f:
        f.write('Model Performance on Training Set:\n')
        f.write(f'RMSE: {rmse_train:.4f}\n')
        f.write(f'R2: {r2_train:.4f}\n\n')
        f.write('Model Performance on Validation Set:\n')
        f.write(f'RMSE: {rmse_valid:.4f}\n')
        f.write(f'R2: {r2_valid:.4f}\n')
    
    # For each output dimension plot predicted vs. true value
    n_outputs = output_data.shape[1]
    headers = output_data.columns.tolist()
    for i in range(n_outputs):
        # Callculate RMSE and R2 for this output
        rmse_train_i = root_mean_squared_error(true_y_train_rescaled[:, i], pred_y_train_rescaled[:, i])
        r2_train_i = r2_score(true_y_train_rescaled[:, i], pred_y_train_rescaled[:, i])
        rmse_valid_i = root_mean_squared_error(true_y_valid_rescaled[:, i], pred_y_valid_rescaled[:, i])
        r2_valid_i = r2_score(true_y_valid_rescaled[:, i], pred_y_valid_rescaled[:, i])

        sns.set_theme(font_scale=1.2, style='whitegrid')
        matplotlib.rcParams['xtick.direction'] = 'in'
        matplotlib.rcParams['ytick.direction'] = 'in'
        fig = plt.figure(figsize=(6, 6), constrained_layout=True)
        ax = plt.subplot()
        
        ax.scatter(true_y_train_rescaled[:, i], pred_y_train_rescaled[:, i], color='C0', label='Training', alpha=0.8, zorder=2)
        ax.scatter(true_y_valid_rescaled[:, i], pred_y_valid_rescaled[:, i], color='C1', label='Validation', alpha=0.8, zorder=2)
        min_val = min(true_y_train_rescaled[:, i].min(), pred_y_train_rescaled[:, i].min(),
                      true_y_valid_rescaled[:, i].min(), pred_y_valid_rescaled[:, i].min())
        max_val = max(true_y_train_rescaled[:, i].max(), pred_y_train_rescaled[:, i].max(),
                      true_y_valid_rescaled[:, i].max(), pred_y_valid_rescaled[:, i].max())
        ax.plot([min_val, max_val], [min_val, max_val], color='C3', linestyle='--', linewidth=1.0, zorder=1)
        ax.set_xlabel('True Value')
        ax.set_ylabel('Predicted Value')
        text = (
            f'Training:\n'
            f'    RMSE: {rmse_train_i:.4f}\n'
            f'    R2: {r2_train_i:.4f}\n\n'
            f'Validation:\n'
            f'    RMSE: {rmse_valid_i:.4f}\n'
            f'    R2: {r2_valid_i:.4f}'
        )
        ax.text(0.7, 0.05, 
                text,
                horizontalalignment='left', 
                verticalalignment='bottom', 
                transform=ax.transAxes,
                fontsize=12,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray')
                )
        ax.legend(loc='upper left', frameon=True)
        ax.set_title(f'Pred vs. True for {headers[i]}')
        plt.savefig(f'{SAVE_PATH}/pred_vs_true_{headers[i]}.png', dpi=330)
        plt.close()

if __name__ == '__main__':
    train(
        input_data=INPUT_DATA,
        output_data=OUTPUT_DATA,
        best_model_pkl=BEST_MODEL_PKL,
        best_model_params=BEST_MODEL_PARAMS,
        epochs=EPOCHS,
        patience=PATIENCE,
        save_path=SAVE_PATH,
    )
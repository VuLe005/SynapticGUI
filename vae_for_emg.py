import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import time
import torch
import torch.nn as nn
# from torchvision import datasets, transforms
from tqdm.auto import tqdm

INPUT_SIZE = 784
WIDTH = 1024

class VAE(nn.Module):
    def __init__(self, latent_dim):
        super(VAE, self).__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(INPUT_SIZE, WIDTH),
            nn.ReLU(),
            nn.Linear(WIDTH, WIDTH),
            nn.ReLU()
        )
        
        self.z_mean_layer = nn.Linear(WIDTH, latent_dim)
        self.z_log_var_layer = nn.Linear(WIDTH, latent_dim)
        
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, WIDTH),
            nn.ReLU(),
            nn.Linear(WIDTH, WIDTH),
            nn.ReLU(),
            nn.Linear(WIDTH, INPUT_SIZE),
            nn.Sigmoid()
        )

        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            if hasattr(m, 'weight') and m.weight is not None:
                if isinstance(m, nn.Sequential) or isinstance(m, nn.ModuleList):
                    pass
                elif m.out_features == INPUT_SIZE:
                    # Output layer before sigmoid — use Xavier for sigmoid
                    nn.init.xavier_uniform_(m.weight)
                else:
                    # ReLU layers — use Kaiming
                    nn.init.kaiming_uniform_(m.weight, nonlinearity='relu')
            if hasattr(m, 'bias') and m.bias is not None:
                nn.init.constant_(m.bias, 0)
        
    def encode(self, x):
        x = self.encoder(x)
        z_mean = self.z_mean_layer(x)
        z_log_var = self.z_log_var_layer(x)
        return z_mean, z_log_var
        
    def reparameterize(self, mean, log_var):
        epsilon = torch.randn_like(mean)
        return mean + torch.sqrt(torch.exp(log_var)) * epsilon
    
    def decode(self, x):
        return self.decoder(x)
        
    def forward(self, x):
        z_mean, z_log_var = self.encode(x)
        z = self.reparameterize(z_mean, z_log_var)
        decoded = self.decode(z)
        return decoded, z_mean, z_log_var


def vae_loss(image, z_mean, z_log_var, reconstruction, beta):
    bce_loss = nn.BCELoss(reduction='none')
    image = image.view(image.size(0), -1)
    recon = reconstruction.view(reconstruction.size(0), -1)
    recon_loss = bce_loss(recon, image)
    recon_loss = torch.sum(recon_loss, dim=1)
    recon_loss = torch.mean(recon_loss)
    
    kl_divergence = torch.sum(-0.5 * torch.sum(1 + z_log_var - torch.square(z_mean) - torch.exp(z_log_var), dim=1))
    
    return recon_loss + beta * kl_divergence


def train(model, train_loader, loss_fxn, latent_dim, batch_size, device, beta=1e-3, lr=1e-3, epochs=10):

    vae = model(latent_dim).to(device)

    optimizer = torch.optim.Adam(vae.parameters(), lr = lr)

    losses = []

    for epoch in tqdm(range(epochs)):
        vae.train()
        overall_loss = 0
        for batch_idx, image in enumerate(train_loader):
            image = image.to(device).float()

            reconstruction, z_mean, z_log_var = vae(image)
            loss = loss_fxn(image, z_mean, z_log_var, reconstruction, beta)  
                
            overall_loss += loss.item()

            #backpropagate through parameters
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        #store losses to plot
        losses.append(loss.detach().cpu().numpy() / (batch_size*len(train_loader)))

        # print(f"Epoch {epoch + 1}/{epochs}, Loss: {overall_loss/(len(train_loader)):.4f}")
        
    return losses, vae

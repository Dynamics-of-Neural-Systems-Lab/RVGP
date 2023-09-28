#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from RVGP.utils import load_mesh
from RVGP.geometry import furthest_point_sampling
from RVGP import data, train_gp
from RVGP.kernels import ManifoldKernel
import numpy as np
import pickle

# =============================================================================
# Parameters and data
# =============================================================================
n_eigenpairs=300
vertices, faces = load_mesh('bunny')
trials=10

# =============================================================================
# Subsample and create data object
# =============================================================================
sample_ind, _ = furthest_point_sampling(vertices, stop_crit=0.01)
X = vertices[sample_ind]
d = data(X, faces, n_eigenpairs=n_eigenpairs)
d.random_vector_field(seed=1)
d.smooth_vector_field(t=100)

# =============================================================================
# Superresolution
# =============================================================================

np.random.seed(0)

results = []
for k in [1,2,5,10,100,200,300]:

    for t in range(trials):
        print(t)
        train_ind =  np.random.choice(np.arange(len(X)), size=int(0.8*len(X)))
        test_ind = set(range(len(X))) - set(train_ind)
        test_ind = list(test_ind)
        
        train_x, train_f = d.evecs_Lc[:,:k].reshape(d.n, -1)[train_ind], d.vectors[train_ind]
        test_x, test_f = d.evecs_Lc[:,:k].reshape(d.n, -1)[test_ind], d.vectors[test_ind]
        
        # =============================================================================
        # Train GP for vector field over manifold
        # =============================================================================
        vector_field_kernel = ManifoldKernel((d.evecs_Lc[:,:k], d.evals_Lc[:k]), 
                                             nu=3/2, 
                                             kappa=5, 
                                             typ='matern',
                                             sigma_f=1.)
        
        vector_field_GP = train_gp(train_x,
                                   train_f,
                                   dim=vertices.shape[1],
                                   kernel=vector_field_kernel,
                                   noise_variance=0.001)
        
        # =============================================================================
        # Predict with GPs
        # =============================================================================
        n = len(test_x)
        test_x = test_x.reshape(-1, k)
        f_pred_mean, _ = vector_field_GP.predict_f(test_x)
        f_pred_mean = f_pred_mean.numpy().reshape(n, -1)
        
        results.append([test_f, f_pred_mean])
        pickle.dump(results, open('ablation_eigenvector_results.pkl','wb'))
    

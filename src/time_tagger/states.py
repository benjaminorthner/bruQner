""" This file serves as a database of 2 particle quantum states to be used in simulating the experiment """

import sympy as sp
from sympy.physics.quantum import TensorProduct 

H = sp.Matrix([1, 0])
V = sp.Matrix([0, 1])

two_particle_states = {
'phi_plus' : (TensorProduct(H, H) + TensorProduct(V, V)) / sp.sqrt(2),
'phi_minus' : (TensorProduct(H, H) - TensorProduct(V, V)) / sp.sqrt(2),
'psi_plus' :(TensorProduct(H, V) + TensorProduct(V, H)) / sp.sqrt(2),
'psi_minus' : (TensorProduct(H, V) - TensorProduct(V, H)) / sp.sqrt(2),
}
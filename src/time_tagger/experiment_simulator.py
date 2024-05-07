"""
Calculates system theoretcally and then
Simulates the ouput of the time tagger 
"""
import numpy as np
import sympy as sp
from sympy.physics.quantum import TensorProduct, Dagger
from sympy.physics.quantum.trace import Tr
from scipy.optimize import minimize
from sys import stdout
from . import states

# Define |H>, |V> in 
H = states.H 
V = states.V 
I2 = sp.eye(2)

# Define Bell state vectors
phi_plus = states.two_particle_states['phi_plus']
phi_minus = states.two_particle_states['phi_minus']
psi_plus = states.two_particle_states['psi_plus']
psi_minus = states.two_particle_states['psi_minus']

def half_wave_plate_sympy(theta):
    """
    returns operator for action of HWP 1 particle state in H,V basis
    note that the angles here are in terms of the angle of the EM field oscillation orientation, not the filter orientation
    the angle for the filter is be half the angle specified here
    """
    c = sp.cos(theta)
    s = sp.sin(theta)
    return sp.Matrix([[c, s], [s, -c]])


class TT_Simulator:
    def __init__(self, initial_state, initial_state_noise=0, debug=True) -> None:
        
        self.debug = debug
        self.initial_state = initial_state
        self.initial_state_noise = initial_state_noise

        if self.debug:
            self._print_div("\nTIME-TAGGER SIMULATOR")
            print("Initialising . . .")

        self.initial_state_density = self._density_operator_from_vector(initial_state)
        
        # apply depolarizing noise (1-noise)*rho + noise * I, where noise from 0 to 1
        self.initial_state_density = (1-self.initial_state_noise) * self.initial_state_density + self.initial_state_noise * sp.eye(4)

        self.correlation_function = self.find_correlation_function(self.initial_state_density)
        self.S, self.CHSH_angles = self.find_CHSH_angles(self.initial_state_density)


        if self.debug:
            stdout.write("\033[F")  # Move the cursor to the previous line
            stdout.write("\033[K")  # clear the line
            stdout.flush()
            self.print_summary()
            self._print_div()



    
    def _print_div(self, title=None):
        if title is not None: print(title)
        print('---------------------------------------------------------------') 

    def _density_operator_from_vector(self, state_vector):
        """
        returns the density matrix corresponding to a specified state vector 
        """
        return TensorProduct(state_vector, Dagger(state_vector))

    def find_correlation_function(self, initial_state_density, lambdify=False):

        # Define sympy variables 
        theta_a, theta_b = sp.symbols('theta_a, theta_b', real=True)

        # Define Operator corresponding to two HWPs
        HWP_operator = sp.simplify(TensorProduct(half_wave_plate_sympy(theta_a), half_wave_plate_sympy(theta_b)))

        # Define coincidence measurement operators
        P_V = V * Dagger(V)  # |V><V| projection operator
        P_H = H * Dagger(H)  # |H><H| projection operator
        VH_operator = TensorProduct(P_V, P_H)
        VV_operator = TensorProduct(P_V, P_V)
        HH_operator = TensorProduct(P_H, P_H)
        HV_operator = TensorProduct(P_H, P_V)

        # Apply HWP operator on initial state density
        state_density = sp.simplify(HWP_operator * initial_state_density * Dagger(HWP_operator))

        # calculate correlation function

        C = Tr(state_density * HH_operator) - Tr(state_density * HV_operator)- Tr(state_density * VH_operator) + Tr(state_density * VV_operator)
        C = C.simplify()

        if lambdify:
            return sp.lambdify([theta_a, theta_b], C)
        else:
            return C 

    def find_CHSH_angles(self, initial_state_density):

        theta_a_0, theta_a_1, theta_b_0, theta_b_1 = sp.symbols('theta_a_0 theta_a_1 theta_b_0 theta_b_1', real=True)

        # get the lambdified correlation function (for faster computation)
        C = self.find_correlation_function(initial_state_density, lambdify=True)

        # build S function from correlation functions (make in terms of multiples of pi)
        def S(x):
            a0 = x[0] * np.pi 
            a1 = x[1] * np.pi 
            b0 = x[2] * np.pi 
            b1 = x[3] * np.pi 
            return -np.abs(C(a0, b0) + C(a1, b0) + C(a0, b1) - C(a1, b1))

        x0 = [0, 1/4, -1/8, 3/8]
        bounds = [(-1,1),(-1,1),(-1,1),(-1,1)]
        constraint = {'type': 'eq', 'fun': lambda x: x[0]} # force first angle to be 0

        result = minimize(fun=S, x0=x0, bounds=bounds, constraints=constraint)
        maximum = -result["fun"]
        angles = result['x']

        return maximum, angles 

    def print_summary(self):

        print("\nFor the initial state:")
        print(self.initial_state)

        print("\nThe correlation function has the form:")
        print(self.correlation_function)

        print("\nWe find the following optimal CHSH angles (in multiples of pi):")
        print(f"a0:\t{self.CHSH_angles[0]:.4f}, a1:\t{self.CHSH_angles[1]:.4f}\nb0:\t{self.CHSH_angles[2]:.4f}, b1:\t{self.CHSH_angles[3]:.4f}")

        print("\nAnd measurements taken at this angle will produce as CHSH value S of")
        print(f"S = {self.S:.4F} ({100*self.S / (2*np.sqrt(2)) : .0f}% of S_bell )\n")
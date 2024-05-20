"""
Calculates system theoretically and then
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
    the angle for the filter is to be half the angle specified here
    """
    c = sp.cos(theta)
    s = sp.sin(theta)
    return sp.Matrix([[c, s], [s, -c]])


class TT_Simulator:
    def __init__(self, initial_state, initial_state_noise=0, debug=True) -> None:
        
        self.debug = debug
        self.initial_state = initial_state
        self.initial_state_noise = initial_state_noise

        # Define coincidence measurement operators
        P_V = V * Dagger(V)  # |V><V| projection operator
        P_H = H * Dagger(H)  # |H><H| projection operator
        self.HH_operator = TensorProduct(P_H, P_H)
        self.HV_operator = TensorProduct(P_H, P_V)
        self.VH_operator = TensorProduct(P_V, P_H)
        self.VV_operator = TensorProduct(P_V, P_V)

        if self.debug:
            self._print_div("\nTIME-TAGGER SIMULATOR")
            print("Initialising . . .")

        self.initial_state_density = self._density_operator_from_vector(initial_state)
        
        # apply depolarizing noise (1-noise)*rho + noise * I, where noise from 0 to 1
        # then renormalise for trace to be 1
        self.initial_state_density = (1-self.initial_state_noise) * self.initial_state_density + self.initial_state_noise * sp.eye(4)
        self.initial_state_density *= 1/Tr(self.initial_state_density)

        self.correlation_function = self.find_correlation_function(self.initial_state_density)
        self.S, self.CHSH_angles = self.find_CHSH_angles(self.initial_state_density)

        # give the angles in terms of the filter angle (not light polarisation angle), and in degrees
        self.CHSH_angles_for_filters = self.CHSH_angles * 90 / np.pi

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


        # Apply HWP operator on initial state density
        state_density = sp.simplify(HWP_operator * initial_state_density * Dagger(HWP_operator))

        # Generate function that gives measurement probabities for each spcm pair
        self.calc_outcome_probabilities(state_density, theta_a, theta_b)

        # calculate correlation function
        C = Tr(state_density * self.HH_operator) - Tr(state_density * self.HV_operator)- Tr(state_density * self.VH_operator) + Tr(state_density * self.VV_operator)
        C = C.simplify()

        if lambdify:
            return sp.lambdify([theta_a, theta_b], C)
        else:
            return C 

    def find_CHSH_angles(self, initial_state_density):
        """
        Finds light polarisation angles that maximise S. Returns max S value reachable and list of angles in the ff. form:
        [angleA1, angleA2, angleB1, angleB2]
        """
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

        # initial guess for angles
        x0 = [0, -1/8, 1/16, -1/16]
        bounds = [(-1,1),(-1,1),(-1,1),(-1,1)]
        constraint = {'type': 'eq', 'fun': lambda x: x[0]} # force first angle to be 0

        result = minimize(fun=S, x0=x0, bounds=bounds, constraints=constraint)
        maximum = -result["fun"] # negative because we acutally want to maximize
        angles = np.array([x * np.pi for x in result['x']]) # give actual angle in radians again (not in multiples of pi)

        return maximum, angles 

    def print_summary(self):

        print("\nFor the initial state:")
        print(self.initial_state)

        print("\nThe correlation function has the form:")
        print(self.correlation_function)

        print("\nWe find the following optimal CHSH angles (in multiples of pi):")
        print(f"a0:\t{self.CHSH_angles[0]/np.pi:.4f}, a1:\t{self.CHSH_angles[1]/np.pi:.4f}\nb0:\t{self.CHSH_angles[2]/np.pi:.4f}, b1:\t{self.CHSH_angles[3]/np.pi:.4f}")

        print("\nAnd measurements taken at this angle will produce as CHSH value S of")
        print(f"S = {self.S:.4F} ({100*self.S / (2*np.sqrt(2)) : .0f}% of S_bell )\n")


    def calc_outcome_probabilities(self, rho, theta_1, theta_2):
        """
        Returns a lambda function that gives probability of measuring click for each possible coincidence pair
        """
        self.outcome_probabilities = sp.lambdify([theta_1, theta_2],
                sp.Matrix([
                    Tr(rho * self.HH_operator),
                    Tr(rho * self.HV_operator),
                    Tr(rho * self.VH_operator),
                    Tr(rho * self.VV_operator)
        ]))

    
    def _measure_entangled_pair(self, theta_a, theta_b) -> int:
        """
        Returns 0, 1, 2, 3 depending on which coincidence was triggered
        0:HH, 1:HV, 2:VH, 3:VV 
        """
        return np.random.choice(a=[0, 1, 2, 3], p=self.outcome_probabilities(theta_a, theta_b)[:,0])
        

    def measure_n_entangled_pairs(self, n, theta_a, theta_b):
        """
        Perform n random entangled pair measurements for one angle setting and then return list showing how often each pair came up
        List index corresponds to pair numbers. 
        0:HH, 1:HV, 2:VH, 3:VV
        """

        N = np.array([0, 0, 0, 0], dtype=int)
        for _ in range(n):
            activated_output = self._measure_entangled_pair(theta_a, theta_b)
            N[activated_output] += 1
        
        return N


    def measure_n_entangled_pairs_filter_angles(self, n, theta_a, theta_b):
        """
        Same as measure_n_entangled_pairs() but with angles in degrees and for filters, so can be used directly in conjunction with real setup code
        """
        return self.measure_n_entangled_pairs(n, theta_a * np.pi/90, theta_b * np.pi / 90)
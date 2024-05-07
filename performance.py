"""
The main script that is run during the performance
"""
import asyncio
import numpy as np
from src.kinetic_mount_controller import KineticMountController
from src.time_tagger import TT_Simulator, two_particle_states


def setup():

    #KMC = KineticMountController(number_of_devices=3)
    pass

def performance_loop():
    pass


if __name__ == '__main__':

    # Setup kinetic mounts and calibrate
    setup()

    # Setup Simulator (TODO put into setup code)
    TTSim = TT_Simulator(two_particle_states['phi_plus'], initial_state_noise=0, debug=True)

    a_angles = TTSim.CHSH_angles[:2]
    b_angles = TTSim.CHSH_angles[2:]

    for _ in range(10):
        print(TTSim.measure_n_entangled_pairs(1000, np.random.choice(a_angles), np.random.choice(b_angles)))
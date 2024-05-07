"""
The main script that is run during the performance
"""
import asyncio
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
    TTSim = TT_Simulator(two_particle_states['phi_plus'], debug=True)
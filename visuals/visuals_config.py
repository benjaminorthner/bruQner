# Configuration file for visuals 
# ------------------------------

# which perforamnce module to load (do not include file extension in name)
PERFORMANCE_MODULE =  "performance_bruqner_v1"# "performance_trial_run_2"

# Screen resolution of output monitor
RESOLUTION = (3072//2, 1920//2)

# GLSL settings (dont go too high, becomes unstable)
MAX_ANIMATIONS = 30

# Should OSC be used? Usually False for testing purposes
USE_OSC = False

# Set IP and port for visual server. Setup and Musicians send visual commands to this address
#MY_IP = "192.168.0.2" # Bruckner Wifi
MY_IP = "128.131.196.0" # ATI Wifi
MY_PORT = 7403

# If true then can update code while its running with changes reflected in the next animation
ENABLE_RUNTIME_UPDATES = True
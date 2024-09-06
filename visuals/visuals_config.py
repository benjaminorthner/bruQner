# Configuration file for visuals 
# ------------------------------

# which perforamnce module to load (do not include file extension in name)
PERFORMANCE_MODULE =  "performance_bruqner_v1"# "performance_trial_run_2"

# Screen resolution of output monitor (affected by display scaling)

# Performance
display_scaling_factor = 1.25
RESOLUTION = (int(1920 / display_scaling_factor), int(1080 // display_scaling_factor))


#RESOLUTION = (int(3072 / 2), int(1920 / 2))

# GLSL settings (dont go too high, becomes unstable)
MAX_ANIMATIONS = 30

# Should OSC be used? Usually False for testing purposes
USE_OSC = True

# Set IP and port for visual server. Setup and Musicians send visual commands to this address
MY_IP = "192.168.0.5" 
MY_PORT = 7401

# If true then can update code while its running with changes reflected in the next animation
ENABLE_RUNTIME_UPDATES = True
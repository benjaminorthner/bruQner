import random

def run_performance(osc_address, *args):

    # extract the animation manager from args
    animation_manager = args[0][0]

    # Phone triggers only snd a single number. So 2 args (animation manager + 1 number). Generate a random state for those
    if len(args) == 2:
        args = [random.choice([1,2]), random.choice([1,2]), random.choice([-1,1]), random.choice([-1,1])]

    # process measurement
    alice_basis = args[0]
    bob_basis = args[1]
    alice_measurement = args[2]
    bob_measurement = args[3]

    # define some colors
    white = (1,1,1)
    red = (1,0.1,0.1)
    blue = (0.2,0.2,1)
    purple = (0.5, 0, 0.5)

    # animation for first section (index sections starting from 1)
    if animation_manager.current_section == 1:
        
        initialSize = 0
        initialThickness = 0.015
        growthSpeed = 0.06
        lifetime = 8
        animation_manager.trigger_animation("ring", {'color': white,
                                                     'lifetime': lifetime,
                                                     'dynamic': {
                                                        'size': lambda t: initialSize + t * growthSpeed,  
                                                        'thickness': lambda t: initialThickness * (1 - t / lifetime) ** 0.5,  
                                                       },
                                                    }
                                            )

    # animation for first section
    elif animation_manager.current_section == 2:
        pass
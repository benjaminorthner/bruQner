import random
import numpy as np

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

    white = (1,1,1)
    red = (1,0.1,0.1)
    blue = (0.2,0.2,1)
    purple = (0.5, 0, 0.5)

    # Measurement animation for first section
    if animation_manager.current_section == 0:
        outer_color = red if alice_measurement == 1 else blue
        
        inner_color = white
        if bob_measurement == -1:
            if outer_color == red:
                inner_color = blue
            else:
                inner_color = red 

        animation_manager.trigger_animation("ring", {'color': outer_color,
                                                      'rotationSpeed' : 0.5,
                                                      'armCount': 10 * (alice_basis - 1),
                                                      'position': (0, 0.5)
                                                    })
        
        animation_manager.trigger_animation("ring", {'color': inner_color,
                                                      'rotationSpeed' : -0.5,
                                                      'armCount' : 10 * (bob_basis - 1),
                                                      'position' : (0, 0.5),
                                                      'delay': 0.8})

    if animation_manager.current_section == 1:
    
        pol = (alice_measurement, bob_measurement)
        
        if pol == (1,1):
            color = white
        elif pol == (1,-1):
            color = red
        elif pol == (-1, 1):
            color = blue
        elif pol == (-1, -1):
            color = purple

        xPosShift = 1.5*(2*random.random() - 1)
        yPosShift = 0.5*(2*random.random() - 1)
        lifetime = random.uniform(0.8, 1.5)
        growthSpeed = random.uniform(0.25, 0.15)

        animation_manager.trigger_animation("ring", {'color': color,
                                                      'rotationSpeed' : alice_basis * 5,
                                                      'armCount': 20 * (bob_basis-1),
                                                      'position': (xPosShift, 0.5 + yPosShift),
                                                      'growthSpeed' : growthSpeed,
                                                      'lifetime' : lifetime,
                                                      'thickness' : 0.1
                                                    })

    if animation_manager.current_section == 2:
        outer_color = red if alice_measurement == 1 else blue
        
        inner_color = white
        if bob_measurement == -1:
            if outer_color == red:
                inner_color = blue
            else:
                inner_color = red 

        xPositions = np.linspace(-0.9, 0.9, 4)
        if random.choice([0, 1]) == 1:
            xPositions = np.flip(xPositions)

        initialSize = random.uniform(0.1, 0.28)
        growthSpeed = random.uniform(-0.03, -0.05) 
        animation_manager.trigger_animation("ring", {'color': outer_color,
                                                      'rotationSpeed' : 0.5 * random.choice([0.5, 1, 2]) * random.choice([1, -1]),
                                                      'armCount': random.choice([10, 30]) * (alice_basis - 1),
                                                      'position': [xPositions[0], 0.45],
                                                      'growthSpeed' : growthSpeed, 
                                                      'size' : initialSize, 
                                                    })

        animation_manager.trigger_animation("ring", {'color': inner_color,
                                                      'rotationSpeed' : 0.5 * random.choice([0.5, 1, 2]) * random.choice([1, -1]),
                                                      'armCount': random.choice([10, 30]) * (alice_basis - 1),
                                                      'position' : [xPositions[1], 0.6],
                                                      'growthSpeed' : growthSpeed,
                                                      'size' : initialSize,
                                                      'delay': random.uniform(0.8, 1),
                                                      })

        animation_manager.trigger_animation("ring", {'color': inner_color,
                                                      'rotationSpeed' : 0.5 * random.choice([0.5, 1, 2]) * random.choice([1, -1]),
                                                      'armCount': random.choice([10, 30]) * (bob_basis - 1),
                                                      'position' : [xPositions[2], 0.6],
                                                      'growthSpeed' : growthSpeed,
                                                      'size' : initialSize,
                                                      'delay': random.uniform(0.8, 1.2),
                                                      })
        
        animation_manager.trigger_animation("ring", {'color': inner_color,
                                                      'rotationSpeed' : 0.5 * random.choice([0.5, 1, 2]) * random.choice([1, -1]),
                                                      'armCount': random.choice([10, 30]) * (bob_basis - 1),
                                                      'position' : [xPositions[3], 0.45],
                                                      'growthSpeed' : growthSpeed,
                                                      'size' : initialSize, 
                                                      'delay': random.uniform(0.8, 1.2),
                                                      })
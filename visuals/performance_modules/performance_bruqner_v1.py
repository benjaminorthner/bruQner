import random
import numpy as np
import math

# FUNCTIONS FOR WIGGLE
# based on https://www.shadertoy.com/view/7ss3RX
def R(v):
    # Generate a random number based on input vector
    random.seed(int(v[0] * 12345 + v[1] * 67890))
    return random.random()

def smoothstep(edge0, edge1, x):
    # Scale, bias and saturate x to 0..1 range
    x = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    # Evaluate polynomial
    return x * x * (3 - 2 * x)

def smoothwiggle(t, frequency, seed):
    t *= frequency
    a = R([math.floor(t), seed]) * 2.0 - 1.0
    b = R([math.ceil(t), seed]) * 2.0 - 1.0
    
    t -= math.floor(t)
    
    # Mix function integrated directly
    return a * (1 - smoothstep(0.0, 1.0, t)) + b * smoothstep(0.0, 1.0, t)

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

        # measurement -> music logic
        outer_color = red if alice_measurement == 1 else blue
        
        inner_color = white
        if bob_measurement == -1:
            if outer_color == red:
                inner_color = blue
            else:
                inner_color = red 

        # parameters
        lifetime = 5.5
        fadeout_length = 0.5
        fadein_length = 0.3

        opacity = lambda t: smoothstep(0, fadein_length, t) * smoothstep(lifetime, lifetime - fadeout_length, t)

        initial_size = 0.7
        growthSpeed = 0.02
        thickness = 0.04

        initial_x = 0.25
        x_speed = 0.1

        wiggle_amplitude = 0.01
        wiggle_frequency = 10

        position_x = lambda seed, t: initial_x + t * x_speed + wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)
        position_y = lambda seed, t: wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)

        animation_manager.trigger_animation("ring", {'color': outer_color,
                                                      'rotationSpeed': 0.5,
                                                      'armCount': 0,
                                                      'thickness': thickness,
                                                      'lifetime': lifetime,
                                                      'dynamic': {
                                                        'size': lambda t: initial_size + growthSpeed * t,  
                                                        'opacity': opacity,
                                                        'position': lambda t: (position_x(seed=0, t=t), position_y(seed=1, t=t)),
                                                    }
                                                    })
        
        animation_manager.trigger_animation("ring", {'color': inner_color,
                                                      'rotationSpeed': -0.5,
                                                      'armCount': 0,
                                                      'thickness': thickness,
                                                      'lifetime': lifetime,
                                                      'dynamic': {
                                                        'size': lambda t: initial_size + growthSpeed * t,  
                                                        'opacity': opacity,
                                                        'position': lambda t: (-position_x(seed=2, t=t), position_y(seed=3, t=t)),
                                                    }
                                                    })

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
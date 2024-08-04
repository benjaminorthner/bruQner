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

def mix(a, b, t):
    return a * (1 - t) + b * t

def smoothwiggle(t, frequency, seed, octaves=1):

    wiggle = 0
    for octave in range(1, octaves + 1):
        t *= frequency * (octave * octave)
        a = R([math.floor(t), seed]) * 2.0 - 1.0
        b = R([math.ceil(t), seed]) * 2.0 - 1.0
        
        t -= math.floor(t)

        wiggle += mix(a, b, smoothstep(0, 1, t))

    return wiggle 

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

    c0 = (1.0, 0.5, 0.5) # red
    c1 = (0.5, 0.5, 1.0) # blue
    c2 = (1.0, 1.0, 0.5) # yellow
    c3 = (1.0, 0.5, 1.0) # purple

    # Measurement animation for first section
    if animation_manager.current_section == 0:

        # measurement -> music logic

        # choose color set based on matching or non matching measurements
        if alice_measurement == bob_measurement:
            left_color = c0 
            right_color = c1 
        else:
            left_color = c2
            right_color = c3

        # based on exact measurement swap the order of the colors
        if alice_measurement == -1: 
            left_color, right_color = right_color, left_color

        # circles move away from each other if basis the same, otherwise towards each other
        direction = 1 if alice_basis == bob_basis else -1


        # parameters
        lifetime = 5.5
        fadeout_length = 0.5
        fadein_length = 0.3

        opacity = lambda t: smoothstep(0, fadein_length, t) * smoothstep(lifetime, lifetime - fadeout_length, t)

        initial_size = 0.7
        growthSpeed = 0.02
        thickness = 0.04

        x_speed = 0.08
        # initial x depends on direction
        nearest_x = 0.25
        initial_x = nearest_x + (0 if direction == 1 else x_speed*lifetime)

        wiggle_amplitude = 0.01
        wiggle_frequency = 10

        position_x = lambda seed, t: initial_x + direction * t * x_speed + wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)
        position_y = lambda seed, t: wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)

        animation_manager.trigger_animation("ring", {'color': left_color,
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
        
        animation_manager.trigger_animation("ring", {'color': right_color,
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

    elif animation_manager.current_section == 1:
        pass

    elif animation_manager.current_section == 2:

        lifetime = 5
        fadeout_length = 0.5
        fadein_length = 2
        initial_thickness = 0.1
        thickness = lambda t: initial_thickness * smoothstep(-0.5, fadein_length, t) * smoothstep(lifetime - fadeout_length, 0, t)

        growthSpeed = 0.22
        x_position = 0.35

        rings_per_trigger = 4
        delay_between_rings = 1.8

        # make set of rings for each trigger
        for i in range(rings_per_trigger):

            # two rings with different x_pos
            for x_pos in [x_position, -x_position]:
                animation_manager.trigger_animation("ring", {'color': white,
                                                            'rotationSpeed': 0.5,
                                                            'armCount': 0,
                                                            'lifetime': lifetime,
                                                            'position': (x_pos, 0),
                                                            'delay' : delay_between_rings * i,
                                                            'dynamic': {
                                                                'size': lambda t: growthSpeed * t,  
                                                                'thickness' : thickness
                                                            }
                                                            })


    elif animation_manager.current_section == 3:
        pass

    elif animation_manager.current_section == 4:
        pass
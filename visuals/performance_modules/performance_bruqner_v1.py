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

def smoothwiggle(t, frequency, seed=random.randint(0, 1e16), octaves=1):

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

    w = 0.7 # whiteness
    c0 = (1.0, w, w) # red
    c1 = (w, w, 1.0) # blue
    c2 = (1.0, 1.0, w) # yellow
    c3 = (1.0, w, 1.0) # purple

    # Measurement animation for first section
    if animation_manager.current_section == 1:
        print(animation_manager.total_trigger_count, animation_manager.section_trigger_count)
        # measurement -> music logic

        # choose color set based on matching or non matching measurements
        if alice_measurement == bob_measurement:
            color_left = c0 
            color_right = c1 
        else:
            color_left = c2
            color_right = c3

        # based on exact measurement swap the order of the colors
        if alice_measurement == -1: 
            color_left, color_right = color_right, color_left

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

        # add wiggle after a certain number of triggers
        wiggle_amplitude = 0
        if animation_manager.section_trigger_count > 1:
            wiggle_amplitude = 0.01 * animation_manager.section_trigger_count

        wiggle_frequency = 10

        position_x = lambda seed, t: initial_x + direction * t * x_speed + wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)
        position_y = lambda seed, t: wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)

        
        animation_manager.trigger_animation("ring", {'color': color_left,
                                                    'rotationSpeed': 0.5,
                                                    'armCount': 0,
                                                    'thickness': thickness,
                                                    'lifetime': lifetime,
                                                    'dynamic': {
                                                        'size': lambda t: initial_size + growthSpeed * t,  
                                                        'opacity': opacity,
                                                        'position': lambda t: (-position_x(seed=0, t=t), position_y(seed=1, t=t)),
                                                    }
                                                    })
        
        animation_manager.trigger_animation("ring", {'color': color_right,
                                                      'rotationSpeed': -0.5,
                                                      'armCount': 0,
                                                      'thickness': thickness,
                                                      'lifetime': lifetime,
                                                      'dynamic': {
                                                        'size': lambda t: initial_size + growthSpeed * t,  
                                                        'opacity': opacity,
                                                        'position': lambda t: (position_x(seed=2, t=t), position_y(seed=3, t=t)),
                                                    }
                                                    })

    elif animation_manager.current_section == 2:
        pass

    elif animation_manager.current_section == 3:

        lifetime = 5
        fadeout_length = 0.5
        fadein_length = 2
        initial_thickness = 0.1
        thickness = lambda t: initial_thickness * smoothstep(-0.5, fadein_length, t) * smoothstep(lifetime - fadeout_length, 0, t)

        growthSpeed = 0.22
        x_position = 0.35

        wiggle_amplitude = 0.05
        wiggle_frequency = 2.3
        x_wiggle = lambda t, seed: wiggle_amplitude * smoothstep(lifetime, 0, t) * smoothwiggle(t, frequency=wiggle_frequency, seed=seed, octaves=1)
        y_wiggle = lambda t, seed: wiggle_amplitude * smoothstep(lifetime, 0, t) * smoothwiggle(t, frequency=wiggle_frequency, seed=seed, octaves=1)

        rings_per_trigger = 4
        delay_between_rings = 1.1

        # make set of rings for each trigger
        for i in range(rings_per_trigger):
            
            color = random.choice([c0, c1, c2, c3])

            animation_manager.trigger_animation("ring", {'color': color,
                                                        'rotationSpeed': 0.5,
                                                        'armCount': 0,
                                                        'lifetime': lifetime,
                                                        'delay' : delay_between_rings * i,
                                                        'dynamic': {
                                                            'size': lambda t: growthSpeed * t,  
                                                            'thickness' : thickness,
                                                            'position': lambda t, seed=4*i: (-x_position + x_wiggle(t, seed), y_wiggle(t, seed+1)),
                                                        }

                                                        })
            animation_manager.trigger_animation("ring", {'color': color,
                                                        'rotationSpeed': 0.5,
                                                        'armCount': 0,
                                                        'lifetime': lifetime,
                                                        'delay' : delay_between_rings * i,
                                                        'dynamic': {
                                                            'size': lambda t: growthSpeed * t,  
                                                            'thickness' : thickness,
                                                            'position': lambda t, seed=4*i: (x_position + x_wiggle(t, seed+2), y_wiggle(t, seed+3)),
                                                        }
                                                        })



    elif animation_manager.current_section == 4:
        pass

    elif animation_manager.current_section == 5:
        pass

    elif animation_manager.current_section == 6:

        color_right = c0 if alice_measurement == 1 else c2
        color_left = c1 if bob_measurement == 1 else c0

        direction_right = 1 if alice_basis == 1 else -1
        direction_left = 1 if bob_basis == 1 else -1
        rotation_speed = 1

        lifetime = 5
        fadeout_length = 0.5
        fadein_length = 0.3
        opacity = lambda t: smoothstep(0, fadein_length, t) * smoothstep(lifetime, lifetime - fadeout_length, t)

        initial_size = 3
        size = lambda t: initial_size - 2.5 * smoothstep(0, fadein_length, t) - 0.06*t


        x_position = 0.35

        animation_manager.trigger_animation("ring", {'color': color_left,
                                                    'armCount': 10,
                                                    'thickness': 0.02,
                                                    'rotationSpeed': direction_right * rotation_speed,
                                                    'lifetime': lifetime,
                                                    'position': (-x_position, 0),
                                                    'dynamic': {
                                                        'size': size,  
                                                        'opacity': opacity,
                                                    }
                                                    })

        animation_manager.trigger_animation("ring", {'color': color_right,
                                                    'armCount': 10,
                                                    'thickness': 0.02,
                                                    'rotationSpeed': direction_left * rotation_speed,
                                                    'lifetime': lifetime,
                                                    'position': (x_position, 0),
                                                    'dynamic': {
                                                        'size': size,  
                                                        'opacity': opacity,
                                                    }
                                                    })
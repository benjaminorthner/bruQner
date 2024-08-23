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
    # -----------------------------------------
    # Fadein-Fade out rings, wiggle more over time
    # -----------------------------------------
    if animation_manager.current_section == 1:

        # measurement -> music logic
        # choose color set based on matching or non matching measurements
        # TODO color choice as discussed
        if alice_measurement == bob_measurement:
            color_left = c0 
            color_right = c0 
        else:
            color_left = c0
            color_right = c1

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

        initial_size = lambda j: 0.1 + j * 0.2 # TODO add limit in size
        growthSpeed = 0.02
        thickness = 0.08

        x_speed = 0.08
        # initial x depends on direction
        nearest_x = 0.25
        initial_x = nearest_x + (0 if direction == 1 else x_speed*lifetime)

        # add wiggle after a certain number of triggers
        wiggle_amplitude = 0
        if animation_manager.section_trigger_count > 5:
            wiggle_amplitude = 0.03

        wiggle_frequency = 4

        position_x = lambda seed, t: initial_x + direction * t * x_speed + wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)
        position_y = lambda seed, t: wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)

        initial_size = initial_size(animation_manager.section_trigger_count)
        animation_manager.trigger_animation("ring", {'color': color_left,
                                                    'rotation_speed': 0.5,
                                                    'arm_count': 0,
                                                    'thickness': thickness,
                                                    'lifetime': lifetime,
                                                    'dynamic': {
                                                        'size': lambda t: initial_size + growthSpeed * t,  
                                                        'opacity': opacity,
                                                        'position': lambda t: (-position_x(seed=0, t=t), position_y(seed=1, t=t)),
                                                    }
                                                    })
        
        animation_manager.trigger_animation("ring", {'color': color_right,
                                                      'rotation_speed': -0.5,
                                                      'arm_count': 0,
                                                      'thickness': thickness,
                                                      'lifetime': lifetime,
                                                      'dynamic': {
                                                        'size': lambda t: initial_size + growthSpeed * t,  
                                                        'opacity': opacity,
                                                        'position': lambda t: (position_x(seed=2, t=t), position_y(seed=3, t=t)),
                                                    }
                                                    })

    # -----------------------------------------
    # 2 persistent rings that grow and shrink 
    # -----------------------------------------
    # TODO randomise at each trial
    # TODO 2 circles
    # TODO in the beginning, only size, then only thickness, then both
    elif animation_manager.current_section == 2:
        
        lifetime = 3

        thickness = 0.03
        t_wiggle_amplitude = 0.7
        t_wiggle_frequency = 1.2
        t_wiggle = lambda seed, t: t_wiggle_amplitude * smoothwiggle(t, t_wiggle_frequency, seed)


        size = 0.7
        wiggle_amplitude = 0.1
        wiggle_frequency = 1.2
        size_wiggle = lambda seed, t: wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)

        animation_manager.trigger_animation("ring", {'color': white,
                                                      'opacity': 1,
                                                      'rotation_speed': 0,
                                                      'arm_count': 0,
                                                      'lifetime': lifetime,
                                                      'position': (0,0),
                                                      'dynamic': {
                                                        'thickness': lambda t: thickness + t_wiggle(t=t, seed=1)**2,
                                                        'size': lambda t: size + size_wiggle(t=t, seed=4),  
                                                    }
                                                    })

    # -----------------------------------------
    #  2x4 nested rings growing from inside out per 1 trigger
    # -----------------------------------------
    # TODO in the beginning no wiggle. Then use wite in between colors
    elif animation_manager.current_section == 3:

        lifetime = 5
        fadeout_length = 0.5
        fadein_length = 2
        initial_thickness = 0.3
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
                                                        'rotation_speed': 0.5,
                                                        'arm_count': 0,
                                                        'lifetime': lifetime,
                                                        'delay' : delay_between_rings * i,
                                                        'dynamic': {
                                                            'size': lambda t: growthSpeed * t,  
                                                            'thickness' : thickness,
                                                            'position': lambda t, seed=4*i: (-x_position + x_wiggle(t, seed), y_wiggle(t, seed+1)),
                                                        }

                                                        })
            animation_manager.trigger_animation("ring", {'color': color,
                                                        'rotation_speed': 0.5,
                                                        'arm_count': 0,
                                                        'lifetime': lifetime,
                                                        'delay' : delay_between_rings * i,
                                                        'dynamic': {
                                                            'size': lambda t: growthSpeed * t,  
                                                            'thickness' : thickness,
                                                            'position': lambda t, seed=4*i: (x_position + x_wiggle(t, seed+2), y_wiggle(t, seed+3)),
                                                        }
                                                        })

    # -----------------------------------------
    # Quantum Rings vs Classical Lines
    # -----------------------------------------
    elif animation_manager.current_section == 4:

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

        # if quantum show circles
        if animation_manager.is_quantum == 1: 


            initial_size = 0.7
            growthSpeed = 0.02
            thickness = 0.08

            x_speed = 0.08
            # initial x depends on direction
            nearest_x = 0.25
            initial_x = nearest_x + (0 if direction == 1 else x_speed*lifetime)

            # add wiggle after a certain number of triggers
            wiggle_amplitude = 0
            if animation_manager.section_trigger_count > 1:
                wiggle_amplitude = 0.1 

            wiggle_frequency = 0

            position_x = lambda seed, t: initial_x + direction * t * x_speed + wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)
            position_y = lambda seed, t: wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)

            animation_manager.trigger_animation("ring", {'color': color_left,
                                                        'rotation_speed': 0.5,
                                                        'arm_count': 0,
                                                        'thickness': thickness,
                                                        'lifetime': lifetime,
                                                        'dynamic': {
                                                            'size': lambda t: initial_size + growthSpeed * t,  
                                                            'opacity': opacity,
                                                            'position': lambda t: (-position_x(seed=0, t=t), position_y(seed=1, t=t)),
                                                        }
                                                        })
            
            animation_manager.trigger_animation("ring", {'color': color_right,
                                                        'rotation_speed': -0.5,
                                                        'arm_count': 0,
                                                        'thickness': thickness,
                                                        'lifetime': lifetime,
                                                        'dynamic': {
                                                            'size': lambda t: initial_size + growthSpeed * t,  
                                                            'opacity': opacity,
                                                            'position': lambda t: (position_x(seed=2, t=t), position_y(seed=3, t=t)),
                                                        }
                                                        })
        # if not quantum show lines
        else:
            # 4s
            # TODO wiggle length, angle, position, size
            # TODO instant transition between circles and lines (no pause)
            # TODO special ending with 2 long notes
            # TODO clemens can send special section end signal
            # TODO lines grow to fill the screen at the end
            thickness = 0.02
            animation_manager.trigger_animation("line", {'color': white,
                                                        'thickness': thickness,
                                                        'lifetime': lifetime,
                                                        'dynamic': {
                                                            'opacity': opacity,
                                                            'angle': lambda t: 0.5 * np.sin(4*t),
                                                            'length': lambda t: 0.7 + 0.4 * np.cos(3*t),
                                                            'position': lambda t: (0, 0),
                                                        }
            })

    # -----------------------------------------
    # 
    # -----------------------------------------
    # TODO test a starry night type animation. slow and dim and in the background
    elif animation_manager.current_section == 5:
        # blank section
        pass

    # -----------------------------------------
    # 
    # -----------------------------------------
    # TODO add variation of arm_count
    # TODO in the beginning circles the same, later circles change from each other, (different arm counts, rotation directions)
    # TODO complex timing needs to be done with Clemens
    # TODO cross disolve between circles
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
        thickness = 0.05
        size = lambda t: initial_size - 2.5 * smoothstep(0, fadein_length, t) - 0.06*t


        x_position = 0.35

        animation_manager.trigger_animation("ring", {'color': color_left,
                                                    'arm_count': 10,
                                                    'thickness': thickness,
                                                    'rotation_speed': direction_right * rotation_speed,
                                                    'lifetime': lifetime,
                                                    'position': (-x_position, 0),
                                                    'dynamic': {
                                                        'size': size,  
                                                        'opacity': opacity,
                                                    }
                                                    })

        animation_manager.trigger_animation("ring", {'color': color_right,
                                                    'arm_count': 10,
                                                    'thickness': thickness,
                                                    'rotation_speed': direction_left * rotation_speed,
                                                    'lifetime': lifetime,
                                                    'position': (x_position, 0),
                                                    'dynamic': {
                                                        'size': size,  
                                                        'opacity': opacity,
                                                    }
                                                    })

    # -----------------------------------------
    # 
    # -----------------------------------------
    elif animation_manager.current_section == 7:
        pass

    # -----------------------------------------
    # 
    # -----------------------------------------
    # TODO build up to climax in the middle with trigger counting
    # TODO special ending with morph to line
    # TODO implement mix of curretn section 8 and 9 animations to make it not boring
    elif animation_manager.current_section == 8:

        lifetime = 5

        dot_thickness = 0.1
        dot_count = 13 - animation_manager.section_trigger_count

        rotation_speed = 0.5

        ring_radius = 0.8
        ring_grow_time = 3

        x_position = 0.35

        max_dot_size = 0.05
        size_fadein_length = 3
        size_fadeout_length = 2
        dot_size = lambda t: max_dot_size * smoothstep(0, size_fadein_length, t) * smoothstep(lifetime, lifetime - size_fadeout_length, t)

        opacity_fadein_length = 2
        opacity_fadeout_length = 2
        opacity = lambda t: smoothstep(0, opacity_fadein_length, t) * smoothstep(lifetime, lifetime - opacity_fadeout_length, t)

        # randomly delay one of the rings to create staggered effect
        delays = [0, random.random()]
        random.shuffle(delays)

        for x_pos, rot_dir, delay in zip([x_position, -x_position], [1, -1], delays):

            animation_manager.trigger_animation("dot_ring", {'color': eval(random.choice(['c0', 'c1', 'c2', 'c3'])),
                                                            'dot_thickness': dot_thickness,
                                                            'dot_count': dot_count,
                                                            'lifetime': lifetime,
                                                            'delay': delay,
                                                            'dynamic': {
                                                                'opacity': opacity,
                                                                'position': lambda t, x_pos=x_pos: (x_pos, 0),
                                                                'angle': lambda t, rot_dir=rot_dir: rot_dir * rotation_speed *  t,
                                                                'ring_radius': lambda t: ring_radius * smoothstep(0, ring_grow_time, t) ,
                                                                'dot_size': dot_size,
                                                            }
                                                            })

    # -----------------------------------------
    # 
    # -----------------------------------------
    elif animation_manager.current_section == 9:

        dot_size = 0.05
        dot_thickness = 0.01
        lifetime = 5
        opacity = 1
        dot_count = 10
        ring_radius = 0.5
        angle = 0
        animation_manager.trigger_animation("dot_ring", {'color': white,
                                                        'dot_thickness': dot_thickness,
                                                        'dot_count': dot_count,
                                                        'lifetime': lifetime,
                                                        'dynamic': {
                                                            'opacity': opacity,
                                                            'position': lambda t: (0.35, 0),
                                                            'angle': lambda t: t,
                                                            'ring_radius': lambda t: 1 * t,
                                                            'dot_size': lambda t: dot_size + 0.1 * t,
                                                        }
                                                        })


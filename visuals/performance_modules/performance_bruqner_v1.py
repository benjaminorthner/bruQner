import random
import numpy as np
import math

# PAPER IDEA: Show each section with property time graphs, can show vertical trigger lines

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

def smoothwiggle(t, frequency, seed=random.randint(0, int(1e16)), octaves=1):

    wiggle = 0
    for octave in range(1, octaves + 1):
        t *= frequency * (octave * octave)
        a = R([math.floor(t), seed]) * 2.0 - 1.0
        b = R([math.ceil(t), seed]) * 2.0 - 1.0
        
        t -= math.floor(t)

        wiggle += mix(a, b, smoothstep(0, 1, t))

    return wiggle 

def perlin(x, seed=0):
    np.random.seed(seed)
    p = np.arange(256, dtype=int)
    np.random.shuffle(p)
    p = np.stack([p, p]).flatten()
    
    def fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    def lerp(t, a, b):
        return a + t * (b - a)

    def grad(h, x):
        g = h & 15
        grad = 1 + (g & 7)  # Gradient value is one of 1, 2, ..., 8
        if g & 8:
            grad = -grad
        return grad * x

    x0 = np.floor(x).astype(int)
    x1 = x0 + 1
    sx = fade(x - x0)

    n0 = grad(p[x0 & 255], x - x0)
    n1 = grad(p[x1 & 255], x - x1)

    return lerp(sx, n0, n1)

def run_performance(osc_address, *args):

    # extract the animation manager from args
    animation_manager = args[0][0]
    state = args[1] # Format [section, alice state (1,4), bob state (1,4), Q/C, note set]

    # For random states current section controlled by keybaord
    # For real experiment data current section is part of data and overrides keyboard
    animation_manager.current_section = state[0]
    animation_manager.is_quantum = 1 if state[3] == "Q" else 0

    alice_basis = 1 if state[1] <= 2 else 0
    bob_basis = 1 if state[2] <= 2 else 0
    alice_measurement = 1 if state[1] % 2 == 0 else 0
    bob_measurement = 1 if state[2] % 2 == 0 else 0

    white = (1,1,1)
    red = (1,0.1,0.1)
    blue = (0.2,0.2,1)
    purple = (0.5, 0, 0.5)

    w = 0.7 # whiteness
    c0 = (1.0, 0.7*w, 0.7*w) # red
    c1 = (0.8*w, 0.8*w, 1.0) # blue
    c2 = (1.0, 1.0, w) # yellow
    c3 = (1.0, w, 1.0) # purple

    y_shift = -0.4

    # Determine the group of colors based on the basis values
    if alice_basis == bob_basis:
        color_group = [c0, c1]
    else:
        color_group = [c2, c3]
    
    # Same measurement (i.e. polarisation) -> same color
    # choice of color depends on alice measurement
    if alice_measurement == bob_measurement:
        alice_color = color_group[0] if alice_measurement == 1 else color_group[1]
        bob_color = alice_color  # Same color for same measurement
    else:
        alice_color = color_group[0] if alice_measurement == 1 else color_group[1]
        bob_color = color_group[1] if alice_measurement == 1 else color_group[0]  


    # Measurement animation for first section
    # -----------------------------------------
    # Fadein-Fade out rings, wiggle more over time
    # -----------------------------------------
    # TODO wiggle starts when, ends when?
    if animation_manager.current_section == 1:

        # circles move away from each other if basis the same, otherwise towards each other
        direction = 1 if alice_basis == bob_basis else -1

        # parameters
        lifetime = 5.3 * 1.33
        fadeout_length = 0.5
        fadein_length = 0.3

        opacity = lambda t: smoothstep(0, fadein_length, t) * smoothstep(lifetime, lifetime - fadeout_length, t)

        initial_size = 0.01 + 0.8* smoothstep(0, 10, animation_manager.section_trigger_count)
        growthSpeed = 0.02
        thickness = 0.02 + 0.06* smoothstep(0, 10, animation_manager.section_trigger_count)

        x_speed = 0.08
        # initial x depends on direction
        nearest_x = initial_size * 0.6
        initial_x = nearest_x + (0 if direction == 1 else x_speed*lifetime)

        # add wiggle after a certain number of triggers
        wiggle_amplitude = 0
        if 5 <= animation_manager.section_trigger_count < 10:
            wiggle_amplitude = 0.008 * animation_manager.section_trigger_count

        wiggle_frequency = 4

        position_x = lambda seed, t: initial_x + direction * t * x_speed + wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)
        position_y = lambda seed, t: wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)

        animation_manager.trigger_animation("ring", {'color': alice_color,
                                                    'rotation_speed': 0.5,
                                                    'arm_count': 0,
                                                    'thickness': thickness,
                                                    'lifetime': lifetime,
                                                    'dynamic': {
                                                        'size': lambda t: initial_size + growthSpeed * t,  
                                                        'opacity': opacity,
                                                        'position': lambda t: (-position_x(seed=0, t=t), y_shift + position_y(seed=1, t=t)),
                                                    }
                                                    })
        
        animation_manager.trigger_animation("ring", {'color': bob_color,
                                                      'rotation_speed': -0.5,
                                                      'arm_count': 0,
                                                      'thickness': thickness,
                                                      'lifetime': lifetime,
                                                      'dynamic': {
                                                        'size': lambda t: initial_size + growthSpeed * t,  
                                                        'opacity': opacity,
                                                        'position': lambda t: (position_x(seed=2, t=t), y_shift + position_y(seed=3, t=t)),
                                                    }
                                                    })

    # -----------------------------------------
    # 2 persistent rings that grow and shrink 
    # -----------------------------------------
    # TODO colors 
    # TODO measurement effects
    elif animation_manager.current_section == 2:
        
        lifetime = 3 * 1.33

        # wiggle_opacity will make sure that wiggles go away at beginning and end of lifetime, to make seamless transitions
        fadeout_length = 0.8
        fadein_length = 0.8
        wiggle_opacity = lambda t: smoothstep(0, fadein_length, t) * smoothstep(lifetime, lifetime - fadeout_length, t)

        thickness = 0.03
        t_wiggle_amplitude = 0.3
        t_wiggle_frequency = 0.35# has to be this way for consecutive triggers to line up
        t_wiggle = lambda seed, t: t_wiggle_amplitude * smoothwiggle(t, t_wiggle_frequency, seed)


        size = 0.5
        wiggle_amplitude = 0.15
        wiggle_frequency = 0.2
        size_wiggle = lambda seed, t: wiggle_amplitude * smoothwiggle(t, wiggle_frequency, seed)

        initial_x = 0.6

        def size_choice(wiggle:bool, seed=None):
            if not seed:
                seed = random.randint(0, 100)
            
            if wiggle:
                return lambda t : size + wiggle_opacity(t) * size_wiggle(t=t, seed=seed)
            return size

        def thickness_choice(wiggle:bool, seed=None):
            if not seed:
                seed = random.randint(0, 100)

            if wiggle:
                return lambda t : thickness + wiggle_opacity(t) * abs(t_wiggle(t=t, seed=seed))
            return thickness
        
        size_left, size_right = size, size
        thickness_left, thickness_right = thickness, thickness

        # only size wiggle, same left and rigth
        if animation_manager.section_trigger_count <= 4:
            seed = random.randint(0, 100)
            size_left, size_right = size_choice(wiggle=True, seed=seed), size_choice(wiggle=True, seed=seed)

        # only thickness wiggle, same left and right
        elif 4 < animation_manager.section_trigger_count <= 8:
            seed = random.randint(0, 100)
            thickness_left, thickness_right = thickness_choice(wiggle=True, seed=seed), thickness_choice(wiggle=True, seed=seed)

        # only size but different left and right
        elif 8 < animation_manager.section_trigger_count <= 12:
            size_left, size_right = size_choice(wiggle=True), size_choice(wiggle=True)
        
        # only thickness but different left and right
        elif 12 < animation_manager.section_trigger_count <= 16:
            thickness_left, thickness_right = thickness_choice(wiggle=True), thickness_choice(wiggle=True)
        
        # Full random
        else:
            size_left, size_right = size_choice(wiggle=True), size_choice(wiggle=True)
            thickness_left, thickness_right = thickness_choice(wiggle=True), thickness_choice(wiggle=True)

        circle_freq = 2
        circle_amp = 0.02
        alice_phase = 2 * np.pi * random.random()
        bob_phase = 2 * np.pi * random.random()
        alice_dir = 1 if alice_basis == 1 else -1
        bob_dir = 1 if bob_basis == 1 else -1
        circle = lambda t, phase, dir: circle_amp * np.array([dir*np.sin(circle_freq*t + phase), np.cos(dir*circle_freq*t + phase)])

        animation_manager.trigger_animation("ring", {'color': alice_color,
                                                      'opacity': 1,
                                                      'rotation_speed': 0,
                                                      'arm_count': 0,
                                                      'lifetime': lifetime,
                                                      'dynamic': {
                                                        'thickness': thickness_right ,
                                                        'position': lambda t, phase=alice_phase, dir=alice_dir: circle(t, phase, dir) + np.array([initial_x, y_shift]),
                                                        'size': size_right,  
                                                    }
                                                    })

        animation_manager.trigger_animation("ring", {'color': bob_color,
                                                      'opacity': 1,
                                                      'rotation_speed': 0,
                                                      'arm_count': 0,
                                                      'lifetime': lifetime,
                                                      'dynamic': {
                                                        'thickness': thickness_left,
                                                        'position': lambda t, phase=bob_phase, dir=bob_dir: circle(t, phase, dir) + np.array([-initial_x, y_shift]),
                                                        'size': size_left, 
                                                    }
                                                    })

    # -----------------------------------------
    #  2x4 nested rings growing from inside out per 1 trigger
    # -----------------------------------------
    # TODO in the beginning no wiggle. Then use wite in between colors
    elif animation_manager.current_section == 3:

        lifetime = 4.8 * 1.33
        fadeout_length = 0.5
        fadein_length = 2
        initial_thickness = 0.14
        thickness = lambda t: initial_thickness * smoothstep(-0.5, fadein_length, t) * smoothstep(lifetime - fadeout_length, 0, t)

        growthSpeed = 0.13

        wiggle_frequency = 2.3
        wiggle_amplitude = 0 
        if animation_manager.section_trigger_count > 3:
            wiggle_amplitude = 0.05

        # x_wiggle = lambda t, seed: wiggle_amplitude * smoothstep(lifetime, 0, t) * smoothwiggle(t, frequency=wiggle_frequency, seed=seed, octaves=1)
        # y_wiggle = lambda t, seed: wiggle_amplitude * smoothstep(lifetime, 0, t) * smoothwiggle(t, frequency=wiggle_frequency, seed=seed, octaves=1)

        rings_per_trigger = 4
        delay_between_rings = 1.1

        position_x = 2 * (0.5 - random.random())
        position_y = 2 * (0.5 - random.random())
        # make set of rings for each trigger
        for i in range(rings_per_trigger):
            
            colors = [alice_color, white, bob_color, white]      
            print(alice_basis, bob_basis)
            alice_arm_count = 6 if alice_basis == 0 else 9
            bob_arm_count = 6 if bob_basis == 0 else 9
            arm_counts = [0, alice_arm_count, 0, bob_arm_count]

            animation_manager.trigger_animation("ring", {'color': colors[i],
                                                        'rotation_speed': 0.5,
                                                        'arm_count': arm_counts[i],
                                                        'lifetime': lifetime,
                                                        'delay' : delay_between_rings * i,
                                                        'dynamic': {
                                                            'size': lambda t: growthSpeed * t,  
                                                            'thickness' : thickness,
                                                            'position': lambda t, seed=4*i: (position_x, position_y + y_shift),
                                                        }

                                                        })

    # -----------------------------------------
    # Quantum Rings vs Classical Lines
    # -----------------------------------------
    elif animation_manager.current_section == 4:

        # circles move away from each other if basis the same, otherwise towards each other
        direction = 1 if alice_basis == bob_basis else -1


        # parameters
        lifetime = 4.8 * 1.33
        

        # if quantum show circles
        if animation_manager.is_quantum == 1: 


            initial_size = 0.3
            thickness = 0.08

            x_speed = 0.08
            # initial x depends on direction
            nearest_x = 0.25
            initial_x = nearest_x + (0 if direction == 1 else x_speed*lifetime)

            initial_x = 0.4
            wiggle_amplitude = 0.3
            wiggle_frequency = 0.2


            fadeout_length = 1.5
            fadein_length = 1.5
            wiggle_opacity = lambda t: smoothstep(0, fadein_length, t) * smoothstep(lifetime, lifetime - fadeout_length, t)


            seed_x = random.randint(0, 100) 
            seed_y = random.randint(0, 100) 

            size_alice = lambda t: initial_size + 0.2 * wiggle_opacity(t) * smoothwiggle(t, 0.4, seed=seed_x)
            size_bob = lambda t: initial_size + 0.2 * wiggle_opacity(t) * smoothwiggle(t, 0.4, seed=seed_y)

            position_x = lambda t, seed: wiggle_opacity(t) * wiggle_amplitude * perlin(t * wiggle_frequency, seed)
            position_y = lambda t, seed: wiggle_opacity(t) * wiggle_amplitude * perlin(t * wiggle_frequency, seed*100 + 1)

            animation_manager.trigger_animation("ring", {'color': alice_color,
                                                        'rotation_speed': 0.5,
                                                        'arm_count': 0,
                                                        'thickness': thickness,
                                                        'lifetime': lifetime,
                                                        'dynamic': {
                                                            'position': lambda t: (initial_x + position_x(seed=seed_x, t=t), position_y(seed=seed_y, t=t)),
                                                            'size': size_alice,
                                                        }
                                                        })
            
            animation_manager.trigger_animation("ring", {'color': bob_color,
                                                        'rotation_speed': -0.5,
                                                        'arm_count': 0,
                                                        'thickness': thickness,
                                                        'size': initial_size,
                                                        'lifetime': lifetime,
                                                        'dynamic': {
                                                            'position': lambda t: (-initial_x + position_x(seed=seed_x+1, t=t), position_y(seed=seed_y+1, t=t)),
                                                            'size': size_bob,
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
            fadeout_length = 0.5
            fadein_length = 0.3
            opacity = lambda t: smoothstep(0, fadein_length, t) * smoothstep(lifetime, lifetime - fadeout_length, t)

            thickness = 0.02
            position_x = 0.8
            lifetime = lifetime * 1.2

            angleoffset = random.random()
            phaseoffset = 2 * np.pi * random.random()
            max_angle = 0.8 * random.random()


            position = (1-2*random.random(), 1-2*random.random())
            animation_manager.trigger_animation("line", {'color': white,
                                                        'thickness': thickness,
                                                        'lifetime': lifetime,
                                                        'dynamic': {
                                                            'opacity': opacity,
                                                            'angle': lambda t: max_angle * np.sin(0.5*t + phaseoffset) + angleoffset,
                                                            'length': lambda t:100,
                                                            'position': lambda t: position,
                                                        }
            })

            #animation_manager.trigger_animation("line", {'color': white,
            #                                            'thickness': thickness,
            #                                            'lifetime': lifetime,
            #                                            'dynamic': {
            #                                                'opacity': opacity,
            #                                                'angle': lambda t: 0.1 * np.sin(2*t + 1.2),
            #                                                'length': lambda t: 0.5,
            #                                                'position': lambda t: (-position_x, y_shift-0.5*np.sin(0.2*t)),
            #                                            }
            #})

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


        direction_right = 1 if alice_basis == 1 else -1
        direction_left = 1 if bob_basis == 1 else -1
        rotation_speed = 2
        
        alice_arms = 6 if alice_measurement == 1 else 3
        bob_arms = 6 if bob_measurement == 1 else 3

        alice_arms = random.randint(2, 10)
        bob_arms = random.randint(2, 10)

        lifetime = 2.820 * 1.33
        fadeout_length = 0.001
        fadein_length = 0.3
        opacity = lambda t: smoothstep(0, fadein_length, t) * smoothstep(lifetime, lifetime - fadeout_length, t)


        initial_size = 3
        thickness = 0.05
        size = 0.5 #lambda t: 0.3 * smoothstep(0, fadein_length, t) - 0.06*t

        initial_x = 0.5
        oscillation_amplitude = initial_x*1.8
        x_alice = lambda t: oscillation_amplitude * np.cos(np.pi * t / lifetime) ** 2
        x_bob = lambda t: oscillation_amplitude * -np.cos(np.pi * t / lifetime) ** 2



        animation_manager.trigger_animation("ring", {'color': alice_color,
                                                    'arm_count': alice_arms,
                                                    'thickness': thickness,
                                                    'rotation_speed': direction_right * rotation_speed,
                                                    'lifetime': lifetime,
                                                    'dynamic': {
                                                        'size': size,  
                                                        'opacity': opacity,
                                                        'position': lambda t: (initial_x + x_alice(t), y_shift),

                                                    }
                                                    })

        animation_manager.trigger_animation("ring", {'color': bob_color,
                                                    'arm_count': bob_arms,
                                                    'thickness': thickness,
                                                    'rotation_speed': direction_left * rotation_speed,
                                                    'lifetime': lifetime,
                                                    'dynamic': {
                                                        'size': size,  
                                                        'opacity': opacity,
                                                        'position': lambda t: (-initial_x + x_bob(t), y_shift),
                                                    }
                                                    })

    # -----------------------------------------
    # 
    # -----------------------------------------
    # TODO build up to climax in the middle with trigger counting
    # TODO special ending with morph to line
    # TODO implement mix of curretn section 7 and 8 animations to make it not boring
    elif animation_manager.current_section == 7:

        lifetime = 3.200 * 1.33
        if animation_manager.is_quantum == 1: 
        
            dot_thickness = 0.1
            dot_count = 1 + abs(25 - 1 * animation_manager.section_trigger_count)

            rotation_speed = 0.25

            ring_radius = 0.8
            ring_grow_time = lifetime * 0.8

            x_position = 0.5

            max_dot_size = 0.01 + 0.08 * smoothstep(0, 26, animation_manager.section_trigger_count)
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
                                                                    'position': lambda t, x_pos=x_pos: (x_pos, y_shift),
                                                                    'angle': lambda t, rot_dir=rot_dir: rot_dir * rotation_speed *  t,
                                                                    'ring_radius': lambda t: ring_radius * smoothstep(0, ring_grow_time, t) ,
                                                                    'dot_size': dot_size,
                                                                }
                                                                })
        elif animation_manager.is_quantum == 0:

            thickness = 0.02
            opacity = 1

            animation_manager.trigger_animation("line", {'color': white,
                                                        'thickness': thickness,
                                                        'lifetime': lifetime,
                                                        'dynamic': {
                                                            'opacity': opacity,
                                                            'angle': lambda t: 0,
                                                            'length': lambda t: 10,
                                                            'position': lambda t: (0, 2 * (np.sin(np.pi * t / (4 * lifetime) + 3*np.pi/4) ** 2 - 0.5))
                                                        }
            })
    # -----------------------------------------
    # 
    # -----------------------------------------
    elif animation_manager.current_section == 8:

        dot_size = 0.05
        dot_thickness = 0.01
        lifetime = 5 * 1.33
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


import TimeTagger
import numpy as np
import asyncio
import plotly.graph_objs as go
from ipywidgets import Button, Output
from time import sleep
from src.kinetic_mount_controller import KineticMountControl
from src.time_tagger import TT_Simulator

class TimeTaggerController:

    def __init__(self, KineticMountController:KineticMountControl = None):

        # if specified connect to kinetic mount controller
        self.KMC = KineticMountController

        # connect to tagger device, get input channels and set trigger levels
        self.tagger = TimeTagger.createTimeTagger()
        input_channels = self.tagger.getChannelList(TimeTagger.ChannelEdge.Rising)
        for ch in input_channels:
            self.tagger.setTriggerLevel(ch, 0.5)

        # dict to store which channels correspond to alice and bob and to reflection and transmission through PBS cubes 
        self.assigned_channels = {
            'Alice_T' : None,
            'Alice_R' : None,
            'Bob_T': None,
            'Bob_R': None
        }

        self.coincidences_vchannels = None
        self.coincidence_channel_names = None
        self.coincidence_window_SI = 0.5e-9

    def set_alice_transmission_channel(self, channel):
        self.assigned_channels['Alice_T'] = channel
    def set_alice_reflection_channel(self, channel):
        self.assigned_channels['Alice_R'] = channel
    def set_bob_transmission_channel(self, channel):
        self.assigned_channels['Bob_T'] = channel
    def set_bob_reflection_channel(self, channel):
        self.assigned_channels['Bob_R'] = channel
    
    def setKineticMountController(self, KMC:KineticMountControl):
        self.KMC = KMC

    def displayCountTraces(self, channels=None, channel_names=None, binwidth_SI=0.1, n_values=1000, trace_width=2, plot_title=None):
        """
        Written to work in an Ipython/Jupyter type environment only
        """
        # find channels if not specified
        if channels is None:
           channels = self.tagger.getChannelList(TimeTagger.ChannelEdge.Rising) 

        # crate counters for each trace
        traces = self._createCounters(channels=channels, binwidth_SI=binwidth_SI, n_values=n_values)
        # make labels for each trace
        trace_labels = []
        for i, ch in enumerate(channels):
            
            # if channel names not none, set either assigned channel name, or otherwise just the unassigned number
            if channel_names is None:
                label = next((key for key, value in self.assigned_channels.items() if value == ch), f"unassigned channel {ch}")
            else:
                label = channel_names[i]
            
            trace_labels.append(label)

        # Init figure
        fig = go.FigureWidget()
            
        # add scatter for each virtual channel
        for i, (trace, label) in enumerate(zip(traces, trace_labels)):
            fig.add_scatter(x=trace.getIndex(), y=trace.getData()[0], name=f"{label}", line=dict(width=trace_width))

        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Counts / s',
            title=plot_title,
            title_font_size=25,
            xaxis_title_font_size=18,
            yaxis_title_font_size=18,
            font=dict(size=16) # ticklabels

        )
        # this is just here so that if a cell gets rerun while a trace is already running 
        # the already running trace will get cancelled first
        try:
            task_trace.cancel()
        except:
            pass
        loop = asyncio.get_event_loop()
        task_trace = loop.create_task(self.update_traces(fig, traces, binwidth_SI))

        # create container to contain figure and button
        output_container = Output()
        with output_container:
            stop_button = Button(description="stop and close")
            display(fig, stop_button)

        # button callback action on click
        stop_button.on_click(lambda a: self._stop_and_close_figure(task_trace, fig, output_container))

        # display figure
        display(output_container)

    async def update_traces(self, fig, traces, binwidth_SI):
        currentMax = 0
        refreshPeriod = binwidth_SI if binwidth_SI > 0.05 else 0.05
        while True:
            try:
                # Batch updates for all traces
                with fig.batch_update():
                    for i, trace in enumerate(traces):
                        y_data = trace.getData()[0] / binwidth_SI

                        ymax = np.max(y_data)
                        if ymax > currentMax:
                            currentMax = 1 * ymax
                            fig.update_layout(yaxis=dict(range=[0, ymax]))

                        fig.data[i].y = y_data

                # do not update faster than binwidth
                await asyncio.sleep(refreshPeriod) 

            except asyncio.CancelledError: # gracefully handle cancellation
                break
                
    def _stop_and_close_figure(self, task, fig, output_container):
        # stop the update task
        task.cancel()
        # wait for stuff to close then close figure
        sleep(0.1)
        fig.close()
        # close output container
        output_container.clear_output()

        # delete coincidence channels if they exist
        #if hasattr(self, 'coincidences_vchannels'):
        #    delattr(self, 'coincidences_vchannels')
        #    self.coincidences_vchannels = None

    def _getDelays(self, referenceChannel, adjustmentChannels, integration_time):

        # Create SynchronizedMeasurements to operate on the same time tags.
        sm = TimeTagger.SynchronizedMeasurements(self.tagger)

        #Create Correlation measurements
        corr_list = list()
        for ch in adjustmentChannels:
            corr_list.append(
                TimeTagger.Correlation(sm.getTagger(), referenceChannel, ch, binwidth=1, n_bins=5000)
            )

        # Adjust mirrors so that all 4 channels have coincidences
        self.KMC.rotate_simulataneously(22.5, 0)
        sleep(1)

        # Start measurements and accumulate data for integration time seconds
        sm.startFor(int(integration_time*1e12), clear=True)
        sm.waitUntilFinished()

        # Determine delays
        delays = list()
        for corr in corr_list:
            hist_t = corr.getIndex()
            hist_c = corr.getData()
            #Identify the delay as the center of the histogram through a weighted average
            dt = np.sum(hist_t * hist_c) / np.sum(hist_c)
            delays.append(int(dt))

        return delays

    def _print_delays(self, C):
        for name, c in zip(['Alice_T', 'Alice_R', 'Bob_T', 'Bob_R'], C):
            print(f"{name:<8}: {c:>5} ps \t/ {c * 0.3:>7.1f} mm")

    def performDelayAdjustment(self, integration_time=2, set=True, manual_delays=None):
        """
        Returns delay in ps
        integration_time is to be given in s 

        Allows for multiple calls and makes an update to the adjustment instead of starting over

        if manual delays are given (list of 4 numbers in pico seconds), then no delay adjustment will be performed

        Only works if coincidences are present between all combinations of SPCMs
        """


        alice_channels = [ self.assigned_channels['Alice_T'], self.assigned_channels['Alice_R']]
        bob_channels = [ self.assigned_channels['Bob_T'], self.assigned_channels['Bob_R']]
        
        # if manual delays given, set them and return
        if manual_delays is not None and set:
            for ch, delay in zip([*alice_channels, *bob_channels], manual_delays):
                self.tagger.setInputDelay(ch, delay)
            return None

        Tdelays = self._getDelays(self.assigned_channels['Alice_T'], bob_channels, integration_time=integration_time)
        Rdelays = self._getDelays(self.assigned_channels['Alice_R'], bob_channels, integration_time=integration_time)

        # print(Tdelays)
        # print(Rdelays)

        C_AT = 0 # reference
        C_BT = -Tdelays[0] # -D_TT
        C_BR = -Tdelays[1] # -D_Tr
        C_AR =  Rdelays[0] - Tdelays[0] # D_RT - D_TT

        C = [C_AT, C_AR, C_BT, C_BR]


        #Compensate the delays to align the signals
        if set:
            
            print("Delays Before Correction")
            self._print_delays(C)

            for ch, dt in zip([*alice_channels, *bob_channels], C):
                currentDelay = self.tagger.getInputDelay(ch)
                newDelay = int(currentDelay - dt)
                self.tagger.setInputDelay(ch, newDelay)

            # measure delays again to see new delays 
            C_new = self.performDelayAdjustment(integration_time=integration_time / 3, set=False)
            print("\nDelays After Correction")
            self._print_delays(C_new)

        self.KMC.home()

        return C

    def createCoincidenceChannels(self, coincidence_window_SI):
        """
        crates coincidence virtual channels and returns list of channelnames
        """
        # make coincidence groups
        try:
            groups = [(self.assigned_channels['Alice_T'], self.assigned_channels['Bob_T']), 
                     (self.assigned_channels['Alice_T'], self.assigned_channels['Bob_R']),
                     (self.assigned_channels['Alice_R'], self.assigned_channels['Bob_T']),
                     (self.assigned_channels['Alice_R'], self.assigned_channels['Bob_R']),
            ]
            
            self.coincidence_channel_names = ['|T,T>', '|T,R>', '|R,T>', '|R,R>']

            # 30ns coincidence window if want to match qutools (coincidence window is in ps)
            # NOTE vchannels need to be a an instance variable (with self.) because otherwise they get auto deleted after some time and no longer exist
            # This means we need to delete them manually when we stop looking at coincidences otherwise they keep existing in the background
            self.coincidences_vchannels = TimeTagger.Coincidences(self.tagger, groups, coincidenceWindow=coincidence_window_SI * 1e12)

            # make translation dict from channel number to 0:TT, 1:TR, 2:RT, 3:RR
            self.coincidence_channel_dictionary = {}
            for i, vch in enumerate(self.coincidences_vchannels.getChannels()):
                self.coincidence_channel_dictionary[vch] = i

        # in case channels are not yet assigned 
        except KeyError as e:
            missing_key = e.args[0]
            raise RuntimeError(f"Error: Channel '{missing_key}' has not been assigned yet") from e

    def displayCoincidenceTraces(self, coincidence_window_SI = 0.5e-9, **kwargs):#, binwidth_SI=0.1, n_values=1000,):

        # make sure coincidence channels are created and exist
        self.createCoincidenceChannels(coincidence_window_SI)

        # display traces of coincidences
        self.displayCountTraces(channels=self.coincidences_vchannels.getChannels(), channel_names=self.coincidence_channel_names, **kwargs) #binwidth_SI=binwidth_SI, n_values=n_values)

    def _createCounters(self, channels, binwidth_SI, n_values):
        counters = []
        for ch in channels:
            counter = TimeTagger.Counter(tagger=self.tagger, channels=[ch], binwidth=binwidth_SI * 1e12, n_values=n_values)
            counters.append(counter)
        
        return counters

    def _makeSingleCounterMeasurement(self, counters, binwidth_SI):
        """
        starts the counters and collects a single datapoint from each, returning as integer np.array
        note binwidth must be the same as the co unter binwidth
        """
        # start all counters and stop again after integration time is over
        for counter in counters:
            counter.startFor(binwidth_SI * 1e12)

        # since this is an async function wait until finished
        for counter in counters:
            counter.waitUntilFinished()

        return np.array([counter.getData(rolling=False)[0][-1] for counter in counters], dtype=int)

    def measureS(self, CHSH_angles, coincidence_window_SI = 0.1e-9, integration_time_per_basis_setting_SI=1, TTSimulator : TT_Simulator=None, debug=True):

        # home all kinetic mounts
        self.KMC.home() 
        
        # make sure coincidence channels are created and exist
        self.createCoincidenceChannels(coincidence_window_SI)

        # create a counter for each virtual coincidence channel
        counters = self._createCounters(channels=self.coincidences_vchannels.getChannels(), binwidth_SI=integration_time_per_basis_setting_SI, n_values=1)

        # an attempt to introduce corrections
        # get max reading for each 

        # TODO need to break symmetry in correction because error is not symmetric
        """ 
        maxCounts1= self._makeSingleCounterMeasurement(counters, binwidth_SI=integration_time_per_basis_setting_SI)
        # rotate so that opposite coincidences should be at max
        KMC.rotate_simulataneously(alice_angle=0, bob_angle=45)

        maxCounts2= self._makeSingleCounterMeasurement(counters, binwidth_SI=integration_time_per_basis_setting_SI)

        maxPerCoincidenceChannel = np.maximum(maxCounts1, maxCounts2)
        minPerCoincidenceChannel = np.minimum(maxCounts1, maxCounts2)
        corrections = max(maxPerCoincidenceChannel) / maxPerCoincidenceChannel - 1

        correctionfunc = lambda a_angle, b_angle : np.array([1 + corrections[0] * (np.cos(np.deg2rad(a_angle - b_angle))**2),
                                                             1 + corrections[1] * (np.sin(np.deg2rad(d_angle - b_angle))**2),
                                                             1 + corrections[2] * (np.sin(np.deg2rad(d_angle - b_angle))**2),
                                                             1 + corrections[3] * (np.cos(np.deg2rad(d_angle - b_angle))**2)])

        print(maxPerCoincidenceChannel)
        print(minPerCoincidenceChannel)
        print(corrections)
        """
        

        alice_angles = CHSH_angles[0:2]
        bob_angles = CHSH_angles[2:4]
        corrs = np.zeros((2,2))
        for i, a_angle in enumerate(alice_angles):
            for j, b_angle in enumerate(bob_angles):
                
                # rotates filters waits for them to finish rotating
                self.KMC.rotate_simulataneously(a_angle, b_angle)

                # make a measurement (real or simulated) 
                # [NTT, NTR, NRT, NRR]
                if TTSimulator is None:
                    N = self._makeSingleCounterMeasurement(counters, integration_time_per_basis_setting_SI) 
                else:
                    N = TTSimulator.measure_n_entangled_pairs_filter_angles(5000, theta_a=a_angle, theta_b=b_angle)

                # calculate correlations 
                corrs[i, j] = (N[0] - N[1] - N[2] + N[3]) / N.sum()
                if debug:
                    print(f"\ncorr[{'a' if i == 0 else 'A'},{'b' if j==0 else 'B'}] = {corrs[i, j]:.5}")
                    for x in range(4):
                        print(f"\tN[{self.coincidence_channel_names[x]}]={N[x]:>6}\t({N[x] / N.sum():<4.3f})")
        
        # Calculate S
        S = np.abs(corrs[0,0] + corrs[0,1] + corrs[1,0] - corrs[1,1])
        print(f"\nS = abs(corrs[0,0] + corrs[0,1] + corrs[1,0] - corrs[1,1]) = {S}")

        # rehome all mounts
        self.KMC.home()

    def measure_S_with_two_ports(self, CHSH_angles, coincidence_window_SI = 0.5e-9, integration_time_per_basis_setting_SI=1, TTSimulator : TT_Simulator=None, debug=True):
        """
        Does a bell measurement with 2 ports only simulates linear polarising filters using the Polarising beam splitter cubes together with the Half Wave Plates
        """

        # home all kinetic mounts
        self.KMC.home() 
        
        # create the virtual channels
        self.createCoincidenceChannels(coincidence_window_SI)

        pair_names = ['TT', 'TR', 'RT', 'RR']

        # create a counter for each virtual coincidence channel
        counters = self._createCounters(channels=self.coincidences_vchannels.getChannels(), binwidth_SI=integration_time_per_basis_setting_SI, n_values=1)


        alice_angles = CHSH_angles[0:2]
        bob_angles = CHSH_angles[2:4]
        corrs = np.zeros((4,2,2))
        print(f"SPCM Pairs: {pair_names[:]}")
        for i, a_angle in enumerate(alice_angles):
            for j, b_angle in enumerate(bob_angles):
            
                # since we now dont have access to all 4 SPCMs we need to rotate the light 90deg to check the other polarisation
                N = np.zeros((4,4), dtype=int)
                for ii, a_angle_perp in enumerate([0, 45]):
                    for jj, b_angle_perp in enumerate([0, 45]):
                        
                        new_a_angle = a_angle + a_angle_perp
                        new_b_angle = b_angle + b_angle_perp
                        # rotates filters waits for them to finish rotating
                        self.KMC.rotate_simulataneously(new_a_angle, new_b_angle)

                        # make a measurement (real or simulated) 
                        # [NTT, NTR, NRT, NRR]
                        if TTSimulator is None:
                            N[:,2*ii + jj] = self._makeSingleCounterMeasurement(counters, integration_time_per_basis_setting_SI)
                        else:
                            N[:, 2*ii + jj] = TTSimulator.measure_n_entangled_pairs_filter_angles(5000, theta_a=new_a_angle, theta_b=new_b_angle)

                # calculate correlations 
                corrs[:, i, j] = (N[:, 0] - N[:, 1] - N[:, 2] + N[:, 3]) / N.sum(axis=1)

                # Debug Printing
                if debug:
                    a_angle_label = 'a' if i==0 else 'A'
                    b_angle_label = 'b' if j==0 else 'B'
                    print(f"\ncorr[{a_angle_label},{b_angle_label}] = {np.array([float(f'{corr:.3f}') for corr in corrs[:, i, j]])}")
                    for x in range(4):
                        print(f"\tN[{a_angle_label} , {b_angle_label} ]={N[:, x]}")
        
        # Calculate S
        S = np.abs(corrs[:,0,0] + corrs[:,0,1] + corrs[:,1,0] - corrs[:,1,1])
        print(f"\nS = abs(corrs[0,0] + corrs[0,1] + corrs[1,0] - corrs[1,1]) = TT, TR, RT, RR : {S}")

        # rehome all mounts
        self.KMC.home()

    def get_single_measurement(self, theta_a, theta_b, integration_time=0.1, coincidence_window_SI=0.5e-9) -> int:
        """
        returns 0, 1, 2, 3 for (TT, TR, RT, RR)
        """

        self.KMC.rotate_simulataneously(theta_a, theta_b)

        eventsByChannel = []
        attemptCounter = 0
        maxAttempts = 10
        while len(eventsByChannel) == 0:

            stream = TimeTagger.TimeTagStream(tagger=self.tagger, n_max_events=1000, channels=self.coincidences_vchannels.getChannels())
            sleep(integration_time)
            streamData = stream.getData()
            eventsByChannel = streamData.getChannels()
            stream.stop()

            # check if anything was measured
            if attemptCounter >= maxAttempts:
                return -1

            if len(eventsByChannel) == 0:
                sleep(0.1)
            else:
                break

            
        # pick out the final event from the set (to prevent startup issues with first event)
        pickedCoincidence = self.coincidence_channel_dictionary[eventsByChannel[-1]]
        return pickedCoincidence



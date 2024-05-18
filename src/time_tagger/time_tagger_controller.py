import TimeTagger
import numpy as np
import asyncio
import plotly.graph_objs as go
from ipywidgets import Button, Output
from time import sleep

class TimeTaggerController:

    def __init__(self):
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


    def set_alice_transmission_channel(self, channel):
        self.assigned_channels['Alice_T'] = channel
    def set_alice_reflection_channel(self, channel):
        self.assigned_channels['Alice_R'] = channel
    def set_bob_transmission_channel(self, channel):
        self.assigned_channels['Bob_T'] = channel
    def set_bob_reflection_channel(self, channel):
        self.assigned_channels['Bob_R'] = channel

    def displayCountTraces(self, channels=[1,2,3,4], binwidthSI=0.1, n_values=1000):
        # convert binwidth to ps
        traces = []
        trace_labels = []
        for ch in channels:
            counter = TimeTagger.Counter(tagger=self.tagger, channels=[ch], binwidth=binwidthSI * 1e12, n_values=n_values)
            traces.append(counter)
            
            # if available assign channel names
            label = next((key for key, value in self.assigned_channels.items() if value == ch), f"unassigned channel {ch}")
            trace_labels.append(label)

        # Init figure
        fig = go.FigureWidget()

            
        # add scatter for each virtual channel
        for trace, label in zip(traces, trace_labels):
            fig.add_scatter(x=trace.getIndex(), y=trace.getData()[0], name=f"{label}")

        try:
            task_trace.cancel()
        except:
            pass
        loop = asyncio.get_event_loop()
        task_trace = loop.create_task(self.update_traces(fig, traces, binwidthSI))

        # create container to contain figure and button
        output_container = Output()
        with output_container:
            stop_button = Button(description="stop and close")
            display(fig, stop_button)

        # button callback action on click
        stop_button.on_click(lambda a: self.stop_and_close_figure(task_trace, fig, output_container))

        # display figure
        display(output_container)

    async def update_traces(self, fig, traces, binwidthSI):
        currentMax = 0
        refreshPeriod = binwidthSI if binwidthSI > 0.05 else 0.05
        while True:
            try:
                # Batch updates for all traces
                with fig.batch_update():
                    for i, trace in enumerate(traces):
                        y_data = trace.getData()[0] / binwidthSI

                        ymax = np.max(y_data)
                        if ymax > currentMax:
                            currentMax = 1 * ymax
                            fig.update_layout(yaxis=dict(range=[0, ymax]))

                        fig.data[i].y = y_data

                # do not update faster than binwidth
                await asyncio.sleep(refreshPeriod) 

            except asyncio.CancelledError: # gracefully handle cancellation
                break
    
    def stop_and_close_figure(self, task, fig, output_container):
        # stop the update task
        task.cancel()
        # wait for stuff to close then close figure
        sleep(0.1)
        fig.close()
        # close output container
        output_container.clear_output()

import numpy as np
from pymodaq.daq_utils.daq_utils import ThreadCommand
from pymodaq.daq_utils.daq_utils import DataFromPlugins
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.daq_utils.parameter import Parameter
from zhinst.toolkit import Session
from pymodaq.daq_utils.parameter import pymodaq_ptypes


session = Session("localhost")
available_devices = session.devices.visible()

class SessionDevice:
    def __init__(self, session:Session, device):
        self.session = session
        self.device = device
        

class DAQ_0DViewer_ZhInst(DAQ_Viewer_base):
    """
    """
    params = comon_parameters+[
        {'title': 'X & Y', 'name': 'x_y_select', 'type': 'list', 'limits': ['X & Y', 'Mag & Phase']},
        {'title': 'Demods', 'name': 'demods', 'type': 'itemselect',
         'value': dict(all_items=[f'Demod_{ind}' for ind in range(8)], selected=[f'Demod_{0}'])},
        ## TODO for your custom plugin: elements to be added here as dicts in order to control your custom stage
        ]

    def ini_attributes(self):
        #  TODO declare the type of the wrapper (and assign it to self.controller) you're going to use for easy
        #  autocompletion
        self.controller: SessionDevice = None

        #TODO declare here attributes you want/need to init with a default value
        pass

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        ## TODO for your custom plugin
        if param.name() == "a_parameter_you've_added_in_self.params":
           self.controller.your_method_to_apply_this_param_change()  # when writing your own plugin replace this line
#        elif ...
        ##

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        if self.settings['controller_status'] == "Master":
            session = Session("localhost")
            device = session.connect_device("dev2218") 
        
        self.ini_detector_init(old_controller=controller,
                               new_controller=SessionDevice(session, device) )

        # # TODO for your custom plugin (optional) initialize viewers panel with the future type of data
        # self.data_grabed_signal_temp.emit([DataFromPlugins(name='Mock1',data=[np.array([0]), np.array([0])],
        #                                                    dim='Data0D',
        #                                                    labels=['Mock1', 'label2'])])

        info = "Whatever info you want to log"
        initialized = True
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """
        ## for multiple demodulators use subscribe and poll rather than calling sample
        inds = []
        labels = []
        for mod in self.settings['demods']['selected']:
            ind = self.settings['demods']['all_items'].index(mod)
            inds.append(ind)
            labels.extend([f'Demod{ind} X(V)', f'Demod{ind} Y(V)'])

        for ind in inds:
            self.controller.device.demods[ind].sample.subscribe()
        data_raw = self.controller.session.poll(0.1)
        self.controller.device.unsubscribe()
            
            
        if self.settings['x_y_select'] == 'X & Y':
            data_tot = []
            for ind in inds:
                data_tot.extend([data_raw[f'/dev2218/demods/{ind}/sample']['x'].mean(),
                                 data_raw[f'/dev2218/demods/{ind}/sample']['y'].mean()])

            self.data_grabed_signal.emit(
                [DataFromPlugins(name='ZHUHFLI',
                                 data=data_tot,
                                 dim='Data0D', labels=labels),])
        else:
            magnitude = np.sqrt(data_raw['x']**2 + data_raw['y']**2)
            phase = data_raw['phase']
            
            self.data_grabed_signal.emit([DataFromPlugins(name='ZHUHFLI_M', data=[magnitude],
                                                      dim='Data0D', labels=['Magnitude (V)']),
                                      DataFromPlugins(name='ZHUHFLI_P', data=[phase],
                                                      dim='Data0D', labels=['Phase (deg)'])])


    def stop(self):
        """Stop the current grab hardware wise if necessary"""

        return ''


if __name__ == '__main__':
    main(__file__)

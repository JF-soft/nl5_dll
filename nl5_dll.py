# -*- coding: utf-8 -*-
'''
NL5 dll class definition
'''
# standard library imports
import os
import ctypes as ct
import inspect
import platform

# third party library imports
import numpy as np


# Exceptions defined for this library
class NL5Exception(Exception):
    pass

class NL5OpenException(NL5Exception):
    pass

class NL5ParamException(NL5Exception):
    pass

class NL5TraceException(NL5Exception):
    pass

class NL5ValueException(NL5Exception):
    pass

class NL5SaveException(NL5Exception):
    pass

class NL5StartException(NL5Exception):
    pass

class NL5DeleteException(NL5Exception):
    pass

class NL5LicenseException(NL5Exception):
    pass

class NL5NotImplementedException(NL5Exception):
    pass


class NL5_dll:
    def __init__(self, name:str='nl5_dll', path:str=os.getcwd()):
        '''! Pythonic class to handle NL5 DLL library.

        @params name dll file name
        @params path dll file path
        @returns
        '''
        # validate path
        self.path = os.path.abspath(path)

        if name.endswith('.dll') or name.endswith('.so'):
            # assume user knows what he's doing
            dll_file = os.path.join(path, f'{name}')
        else:
            # if no ending is provided, check which platform we're running
            if 'linux' in platform.system().lower():
                dll_file = os.path.join(path, f'{name}.so')
            else:
                dll_file = os.path.join(path, f'{name}.dll')

        self.nl5 = ct.cdll.LoadLibrary(dll_file)

        # JF TODO: for now, support only one file at a time, later I can think
        # of a dictionary to hold every simulation opened during a session
        self._ncir = -1

    # Pythonic functions provided by JF
    def get_error(self) -> str:
        '''! Returns text description of last execution error. If no error, returns "OK".

        The content of the string is valid only until execution of the next DLL function.

        @params
        @returns error string
        '''
        c = ct.c_char_p()
        c = self.NL5_GetError()
        return c.decode('utf-8')

    def get_info(self) -> str:
        '''! Returns information about DLL, such as version and date.

        The content of the string is valid only until execution of the next DLL function.

        @params
        @returns information string
        '''
        c = ct.c_char_p()
        c = self.NL5_GetInfo()
        return c.decode('utf-8')

    def get_license(self, name:str='nl5.nll', path:str='') -> bool:
        '''! Gets license to enable NL5 dll full features.

        @params path folder location of NL5 license
        @params name license name
        @returns True if license is valid
        '''
        if path:
            # validate user provided path
            path = os.path.abspath(path)
        else:
            # assume license is located in the same folder as dll
            path = self.path

        # check valid license file name
        if not name.endswith('.nll'):
            name = f'{name}.nll'

        lic_file = os.path.join(path, f'{name}')

        valid = False
        retval = self.NL5_GetLicense(lic_file.encode('utf-8'))
        if retval < 0:
            raise NL5LicenseException('License does not have DLL option activated.')
        else:
            valid = not bool(retval)
        return valid

    def open(self, name:str, path:str='') -> None:
        '''! Open schematic simulation file.

        JF TODO: Only one file at a time is supported for now.

        @param name NL5 simulation circuit file name
        @returns
        '''
        # if there is an open simulation, close it first
        if self._ncir >= 0:
            self.NL5_Close(self._ncir)
            self._ncir = -1

        if path:
            # validate user provided path
            path = os.path.abspath(path)
        else:
            # assume circuit is in current working directory
            path = os.getcwd()

        # check valid circuit file name
        if not name.endswith('.nl5'):
            name = f'{name}.nl5'

        # circuit file name
        cir_file = os.path.join(path, f'{name}')

        ncir = self.NL5_Open(cir_file.encode('utf-8'))
        if ncir >= 0:
            self._ncir = ncir
        else:
            raise NL5OpenException('Error opening NL5 circuit')
        return

    def close(self) -> None:
        '''! Close schematic simulation file.

        @param
        @returns
        '''
        if self._ncir >= 0:
            self.NL5_Close(self._ncir)
        else:
            raise NL5OpenException('Error closing NL5 circuit, not opened.')
        return

    def save(self) -> None:
        '''! Save opened schematic simulation file.

        Use this function to save schematic back to NL5 schematic file. You might want to save the schematic if
        any modification of component parameters were made, IC (Initial Conditions) were saved, or if you want
        to save schematic with transient data (simulation data traces).
        To save schematic with transient data, make sure the "Save with transient data" option is set in the
        schematic file. To set the option, open schematic file in NL5, go to File/Properties/Save, select "Save
        with transient data" checkbox, and save schematic into the file.

        @param
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_Save(self._ncir)
            if retval < 0:
                raise NL5SaveException('Error trying to save the schematic circuit file.')
        else:
            raise NL5OpenException('Error closing NL5 circuit, not opened.')
        return

    def save_as(self, name: str, path:str='') -> None:
        '''! Save opened schematic simulation file using another filename.

        Use this function to save schematic back to NL5 schematic file. You might want to save the schematic if
        any modification of component parameters were made, IC (Initial Conditions) were saved, or if you want
        to save schematic with transient data (simulation data traces).
        To save schematic with transient data, make sure the "Save with transient data" option is set in the
        schematic file. To set the option, open schematic file in NL5, go to File/Properties/Save, select "Save
        with transient data" checkbox, and save schematic into the file.

        @param
        @returns
        '''
        if path:
            # validate user provided path
            path = os.path.abspath(path)
        else:
            # assume circuit will be saved in current working directory
            path = os.getcwd()

        # check valid circuit file name
        if not name.endswith('.nl5'):
            name = f'{name}.nl5'

        cir_file = os.path.join(path, f'{name}')

        if self._ncir >= 0:
            retval = self.NL5_SaveAs(self._ncir, cir_file.encode('utf-8'))
            if retval < 0:
                raise NL5SaveException(f'Error trying to save the schematic circuit file as {name}.')
        else:
            raise NL5OpenException('Error closing NL5 circuit, not opened.')
        return

    def get_value(self, name:str) -> float:
        '''! Get value of component parameter

        Depending on parameter type, the following value is returned:
            - formula : number in double format
            - Initial Condition : number in double format if not blank, not supported if blank
            - "On/Off"   : 1 for "On", 0 for "Off"
            - "High/Low" : 1 for "High", 0 for "Low"
            - "Yes/No"   : 1 for "Yes", 0 for "No"
            - text list : parameter number in the list (zero based)
        Other parameter types are not supported.

        @param name is component parameter name in the format <component >.<parameter> (e.g.: "R1.R" or "V1.V")
        @returns numeric value of parameter
        '''
        if self._ncir >= 0:
            v = ct.c_double()
            retval = self.NL5_GetValue(self._ncir, name.encode('utf-8'), v)
            if retval < 0:
                raise NL5ValueException(f'Parameter {name} not found or parameter type not supported.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return v.value

    def set_value(self, name:str, v: float) -> None:
        '''! Set value of component parameter to v

        Depending on parameter type, number v is interpreted as follows:
            - formula : number in double format
            - Initial Condition : number in double format if not blank, not supported if blank
            - "On/Off" : 1 for "On", 0 for "Off"
            - "High/Low" : 1 for "High", 0 for "Low"
            - "Yes/No" : 1 for "Yes", 0 for "No"
            - text list : parameter number in the list (zero based)
        Other parameter types are not supported.

        @param name is component parameter name in the format <component >.<parameter> (e.g.: "R1.R" or "V1.V")
        @param v value
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_SetValue(self._ncir, name.encode('utf-8'), v)
            if retval < 0:
                raise NL5ValueException(f'Parameter {name} not found or parameter type not supported.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def get_text(self, name:str, buf_size:int=256) -> str:
        '''! Returns text (parameter value in text format) of component parameter into character string text

        Returns text (parameter value in text format) of component parameter into character string text.
        name is component parameter name in the format <component >.<parameter> ("R1.R", "V1.V").
        See NL5 Circuit Simulator Manual for details (User Interface/Data format/Names)

        @param name is component parameter name in the format <component >.<parameter> (e.g.: "R1.R" or "V1.V")
        @returns component parameter as text
        '''
        if self._ncir >= 0:
            c_buf = ct.create_string_buffer(buf_size)
            retval = self.NL5_GetText(self._ncir, name.encode('utf-8'), c_buf, buf_size)
            if retval < 0:
                raise NL5ValueException(f'Parameter {name} not found or parameter type not supported.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return c_buf.value.decode('utf-8')

    def set_text(self, name:str, text:str) -> None:
        '''! Sets text of component parameter name to text.

        Sets text of component parameter name to text.
        name is component parameter name in the format <component >.<parameter> ("R1.R", "V1.V").
        See NL5 Circuit Simulator Manual for details (User Interface/Data format/Names).
        Practically all parameter types are supported. The text provided is expected to be the same as displayed
        in the components window of NL5 Circuit Simulator.
        To enter a formula for parameter of "formula" type, provide text of the formula started with equal sign ‘=‘.

        @param name is component parameter name in the format <component >.<parameter> (e.g.: "R1.R" or "V1.V")
        @param text new text to set into component
        @returns component parameter as text
        '''
        if self._ncir >= 0:
            retval = self.NL5_SetText(self._ncir, name.encode('utf-8'), text.encode('utf-8'))
            if retval < 0:
                raise NL5ValueException(f'Parameter {name} not found or parameter type not supported.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def get_parameter_value(self, name:str) -> float:
        '''! Get parameter value

        @param name name of parameter
        @returns numeric value of parameter
        '''
        if self._ncir >= 0:
            v = ct.c_double()
            npar = self.NL5_GetParam(self._ncir, name.encode('utf-8'))
            if npar >= 0:
                retval = self.NL5_GetParamValue(self._ncir, npar, v)
                if retval < 0:
                    raise NL5ValueException(f'Parameter {name} not found or parameter type not supported.')
            else:
                raise NL5ParamException(f'Parameter {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return v.value

    def set_parameter_value(self, name:str, v:float) -> None:
        '''! Set parameter value

        Depending on parameter type, number v is interpreted as follows:
        - formula : number in double format
        - Initial Condition : number in double format
        - "On/Off" : 1 for "On", 0 for "Off"
        - "High/Low" : 1 for "High", 0 for "Low"
        - "Yes/No" : 1 for "Yes", 0 for "No"
        - text list : parameter number in the list (zero based)
        Other parameter types are not supported

        @param name name of parameter
        @param v new value for parameter
        @returns
        '''
        if self._ncir >= 0:
            npar = self.NL5_GetParam(self._ncir, name.encode('utf-8'))
            if npar >= 0:
                retval = self.NL5_SetParamValue(self._ncir, npar, v)
                if retval < 0:
                    raise NL5ValueException(f'Parameter {name} not found or parameter type not supported.')
            else:
                raise NL5ParamException(f'Parameter {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def get_parameter_text(self, name:str, buf_size:int=256) -> str:
        '''! Get parameter text

        Copies text (parameter value in text format) of component parameter with handle npar into character
        string text. Practically all parameter types are supported. The text returned is the same as displayed
        in the components window of NL5 Circuit Simulator. If parameter is defined as a formula, text of the
        formula will be returned.

        @param name name of parameter
        @returns numeric value of parameter
        '''
        if self._ncir >= 0:
            npar = self.NL5_GetParam(self._ncir, name.encode('utf-8'))
            if npar >= 0:
                c_buf = ct.create_string_buffer(buf_size)
                retval = self.NL5_GetParamText(self._ncir, npar, c_buf, buf_size)
                if retval < 0:
                    raise NL5ValueException(f'Parameter {name} not found or parameter type not supported.')
            else:
                raise NL5ParamException(f'Parameter {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return c_buf.value.decode('utf-8')

    def set_parameter_text(self, name:str, text:str) -> None:
        '''! Sets text of component parameter to text.

        Practically all parameter types are supported. The text provided is expected to be the same as displayed
        in the components window of NL5 Circuit Simulator.
        To enter a formula for parameter of "formula" type, provide text of the formula started with equal sign ‘=‘.

        @param name name of parameter
        @returns numeric value of parameter
        '''
        if self._ncir >= 0:
            npar = self.NL5_GetParam(self._ncir, name.encode('utf-8'))
            if npar >= 0:
                retval = self.NL5_SetParamText(self._ncir, npar, text.encode('utf-8'))
                if retval < 0:
                    raise NL5ValueException(f'Parameter {name} not found or parameter type not supported.')
            else:
                raise NL5ParamException(f'Parameter {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def add_voltage_trace(self, name:str) -> None:
        '''! Creates voltage trace for component name.

        @param name the trace name in the format used by NL5 Circuit Simulator
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_AddVTrace(self._ncir, name.encode('utf-8'))
            if retval < 0:
                raise NL5TraceException(f'Problem trying to add voltage trace for component {name}.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def add_current_trace(self, name:str) -> None:
        '''! Creates current trace for component name.

        @param name the trace name in the format used by NL5 Circuit Simulator
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_AddITrace(self._ncir, name.encode('utf-8'))
            if retval < 0:
                raise NL5TraceException(f'Problem trying to add current trace for component {name}.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def add_power_trace(self, name:str) -> None:
        '''! Creates power trace for component name.

        @param name the trace name in the format used by NL5 Circuit Simulator
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_AddPTrace(self._ncir, name.encode('utf-8'))
            if retval < 0:
                raise NL5TraceException(f'Problem trying to add power trace for component {name}.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def add_variable_trace(self, name:str) -> None:
        '''! Creates trace for schematic variable name.

        See NL5 Circuit Simulator Manual for details on function trace
        (Transient Analysis/Transient Data/Traces/Function trace).

        @param name the trace name in the format used by NL5 Circuit Simulator
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_AddVarTrace(self._ncir, name.encode('utf-8'))
            if retval < 0:
                raise NL5TraceException(f'Problem trying to add trace for variable {name}.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def add_function_trace(self, text:str) -> None:
        '''! Creates trace of function text.

        See NL5 Circuit Simulator Manual for details on function trace
        (Transient Analysis/Transient Data/Traces/Function trace).

        @param name the trace name in the format used by NL5 Circuit Simulator
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_AddFuncTrace(self._ncir, text.encode('utf-8'))
            if retval < 0:
                raise NL5TraceException(f'Problem trying to add function trace {text}.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def delete_trace(self, name:str) -> None:
        '''! Deletes trace defined by name.

        @param name the trace name in the format used by NL5 Circuit Simulator
        @returns
        '''
        if self._ncir >= 0:
            ntrace = self.NL5_GetTrace(self._ncir, name.encode('utf-8'))
            if ntrace >= 0:
                retval = self.NL5_DeleteTrace(self._ncir, ntrace)
                if retval < 0:
                    raise NL5ValueException(f'Problem trying to delete trace {name}.')
            else:
                raise NL5TraceException(f'Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def set_input_value(self, name:str, v:float) -> None:
        '''! Set input value for named component.

        @param name is label or component name for desired output
        @param v value to set into input
        @returns
        '''
        if self._ncir >= 0:
            nin = self.NL5_GetInput(self._ncir, name.encode('utf-8'))
            if nin >= 0:
                v = ct.c_double()
                retval = self.NL5_SetInputValue(self._ncir, nin, v)
                if retval < 0:
                    raise NL5ValueException(f'Input {name} not valid.')
            else:
                raise NL5TraceException(f'Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def set_input_logical_value(self, name:str, v:bool) -> None:
        '''! Get output value for named component.

        Sets voltage or current of the input with handle nin to:
        - low logical level value, if i == 0
        - high logical level value, if i != 0
        Logical levels are set up in the NL5 Transient Settings, Advanced settings, Transient tab.

        @param name is label or component name for desired output
        @param v logical value to set into input
        @returns
        '''
        if self._ncir >= 0:
            nin = self.NL5_GetInput(self._ncir, name.encode('utf-8'))
            if nin >= 0:
                v = ct.c_double()
                retval = self.NL5_SetInputLogicalValue(self._ncir, nin, int(v))
                if retval < 0:
                    raise NL5ValueException(f'Input {name} not valid.')
            else:
                raise NL5TraceException(f'Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def get_output_value(self, name:str) -> float:
        '''! Get output value for named component.

        @param name is label or component name for desired output
        @returns value of voltage of desired output
        '''
        if self._ncir >= 0:
            nout = self.NL5_GetOutput(self._ncir, name.encode('utf-8'))
            if nout >= 0:
                v = ct.c_double()
                retval = self.NL5_GetOutputValue(self._ncir, nout, v)
                if retval < 0:
                    raise NL5ValueException(f'Output {name} not valid.')
            else:
                raise NL5TraceException(f'Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return v.value

    def get_output_logical_value(self, name:str) -> bool:
        '''! Get output logical level value for named component.

        - False if output voltage is below logical threshold
        - True  if output voltage is equal or above logical threshold
        Logical threshold is set up in the NL5 Transient Settings, Advanced settings, Transient tab.

        @param name is label or component name for desired output
        @returns logical value of voltage of desired output
        '''
        if self._ncir >= 0:
            nout = self.NL5_GetOutput(self._ncir, name.encode('utf-8'))
            if nout >= 0:
                v = ct.c_double()
                retval = self.NL5_GetOutputLogicalValue(self._ncir, nout, v)
                if retval < 0:
                    raise NL5ValueException(f'Output {name} not valid.')
            else:
                raise NL5TraceException(f'Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return bool(v.value)

    def set_step(self, step:float) -> None:
        '''! Sets maximum calculation step size.

        If this function was not called, an original calculation step from
        schematic file will be used (Transient/Settings/"Calculation step")

        @param step new maximum calculation step
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_SetStep(self._ncir, abs(step))
            if retval < 0:
                raise NL5ValueException(f'Step not valid.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def set_timeout(self, t:int) -> None:
        '''! Sets maximum time allowed for calculating one simulation step.

        If this function was not called, a default
        time-out value is used (0). If time-out is equal to zero, time-out detection is disabled.
        If time-out occurred due to unresolved switching iterations, the error message will indicate a component
        which started switching process. Time-out may also occur due to infinite while/do/for loops of C-code.

        @param t timeout in seconds
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_SetTimeout(self._ncir, abs(t))
            if retval < 0:
                raise NL5ValueException(f'Timeout not valid.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def get_simulation_time(self) -> float:
        '''! Gets current value of internal simulation_time variable.

        @param
        @returns simulation time t in seconds
        '''
        if self._ncir >= 0:
            t = ct.c_double()
            retval = self.NL5_GetSimulationTime(self._ncir, t)
            if retval < 0:
                raise NL5ValueException(f'Error when reading simulation time.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return t.value

    def start(self) -> None:
        '''! Start simulation.

        The function resets internal simulation_time variable to 0, initializes circuit components, erases
        existing simulation data, and calculates initial state of the circuit according to specified Initial Conditions.
        When function returns, the simulation data consists of circuit state at t=0.
        The function should be called first to start simulation from t=0, prior to calling any simulation functions.
        However, calling "start" is not required. It will be executed automatically if any of simulation
        functions is called, and simulation has not been performed yet.
        The function may return error code if not-DLL enabled schematic contains too many components after
        loading subcircuits.

        @param
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_Start(self._ncir)
            if retval < 0:
                raise NL5StartException('Error trying to start simulation.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def simulate(self, interval:float) -> None:
        '''! Performs transient simulation at least for requested interval.

        The function does not change simulation step in order to stop exactly at the end of requested
        interval, so the time of the last calculated data may exceed requested end time. When next
        simulation function is called, simulation will be continued with simulation step equal to the last simulation
        step.
        The function may return error code if not-DLL enabled schematic contains too many components after
        loading subcircuits.

        @param interval time interval to simulate in seconds
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_Simulate(self._ncir, abs(interval))
            if retval < 0:
                raise NL5StartException(f'Error trying to start simulation with {interval=}.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def simulate_interval(self, interval:float) -> None:
        '''! Performs transient simulation exactly for requested interval.

        The function may adjust (decrease) simulation step in order to stop exactly at the end of requested
        interval. When next simulation function is called, simulation step will be restored, and a new linear
        range will be started.
        Please note that if requested interval is less than simulation step, NL5 may not be able to decrease
        simulation step exactly as needed, and actual simulated interval will be longer than requested. To avoid
        that, it is recommended to use simulation step at least not greater than desired intervals.
        The function may return error code if not-DLL enabled schematic contains too many components after
        loading subcircuits.

        @param interval time interval to simulate in seconds
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_SimulateInterval(self._ncir, abs(interval))
            if retval < 0:
                raise NL5StartException(f'Error trying to start simulation with {interval=}.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def simulate_step(self) -> None:
        '''! Performs one step of transient simulation.

        When the function returns, simulation_time variable is set to the time of last calculated data.
        The function may return error code if not-DLL enabled schematic contains too many components after
        loading subcircuits

        @param
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_SimulateStep(self._ncir)
            if retval < 0:
                raise NL5StartException('Error trying to perform one simulation step.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def save_ic(self) -> None:
        '''! Saves current component states into components' Initial Conditions.

        The function does not save schematic into schematic file.

        @param
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_SaveIC(self._ncir)
            if retval < 0:
                raise NL5SaveException('Error trying to save initial conditions into components.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def delete_old_data(self) -> None:
        '''! Deletes all transient data except the last data point.

        (or two data points, if function NL5_Simulate was used, and the time of last data
        point is greater than requested simulation interval).

        @param
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_DeleteOldData(self._ncir)
            if retval < 0:
                raise NL5DeleteException('Error trying to delete old data.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def save_data(self, name:str, path:str='') -> None:
        '''! Save transient data of the current schematic into the data file

        Use this function to save transient data into the file in NL5 data format. Default file extension is "nlt".
        The data can be loaded into NL5 and shown on the transient graph.

        @param name NL5 data file name
        @returns
        '''
        if path:
            # validate user provided path
            path = os.path.abspath(path)
        else:
            # assume data will be saved in current working directory
            path = os.getcwd()

        # check valid circuit file name
        if not name.endswith('.nlt'):
            name = f'{name}.nlt'

        data_file = os.path.join(path, f'{name}')

        if self._ncir >= 0:
            retval = self.NL5_SaveData(self._ncir, data_file.encode('utf-8'))
            if retval < 0:
                raise NL5SaveException('Error trying to save NL5 data file.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def get_trace(self, name:str) -> int:
        ''' Returns a handle, maybe this shouldn't be implemented directly and use underlying function as a mean to get data.
        '''
        frame = inspect.currentframe()
        raise NL5NotImplementedException(f'function {inspect.getframeinfo(frame).function} not implemented!')

    def get_data(self, name:str, time:float) -> float:
        '''! Get data value at time t

        See NL5 Circuit Simulator Manual for details (User Interface/Data format/Names/Trace).

        @param name the trace name in the format used by NL5 Circuit Simulator
        @returns numeric value of data at time t
        '''
        if self._ncir >= 0:
            ntrace = self.NL5_GetTrace(self._ncir, name.encode('utf-8'))
            if ntrace >= 0:
                d = ct.c_double()
                retval = self.NL5_GetData(self._ncir, ntrace, abs(time), d)
                if retval < 0:
                    raise NL5ValueException(f'Data point does not exist for {abs(time)=} seconds.')
            else:
                raise NL5TraceException(f'Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return d.value

    def get_last_data(self, name:str) -> tuple[float, float]:
        '''! Get last data value and time t at where it happens.

        See NL5 Circuit Simulator Manual for details (User Interface/Data format/Names/Trace).

        @param name the trace name in the format used by NL5 Circuit Simulator
        @returns time t and numeric value of data at time t as tuple (time, data)
        '''
        if self._ncir >= 0:
            ntrace = self.NL5_GetTrace(self._ncir, name.encode('utf-8'))
            if ntrace >= 0:
                d = ct.c_double()
                t = ct.c_double()
                retval = self.NL5_GetLastData(self._ncir, ntrace, t, d)
                if retval < 0:
                    raise NL5ValueException(f'Data point does not exist.')
            else:
                raise NL5TraceException(f'Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return (t.value, d.value)

    def get_data_at(self, name:str, n:int) -> tuple[float, float]:
        '''! Returns time and data of data point with index n.

        Data index is zero-based.

        @param name the trace name in the format used by NL5 Circuit Simulator
        @param n index at which data is expected.
        @returns time t and numeric value of data at time t as tuple (time, data)
        '''
        if self._ncir >= 0:
            ntrace = self.NL5_GetTrace(self._ncir, name.encode('utf-8'))
            if ntrace >= 0:
                d = ct.c_double()
                t = ct.c_double()
                retval = self.NL5_GetDataAt(self._ncir, ntrace, n, t, d)
                if retval < 0:
                    raise NL5ValueException('Index is less than zero, or greater or equal to data size.')
            else:
                raise NL5TraceException(f'Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return (t.value, d.value)

    def get_data_size(self, name:str) -> int:
        '''! Gets the number of data points of the name trace

        Size is a positive number.

        @param name the trace name in the format used by NL5 Circuit Simulator
        @returns data size
        '''
        if self._ncir >= 0:
            ntrace = self.NL5_GetTrace(self._ncir, name.encode('utf-8'))
            if ntrace >= 0:
                size = self.NL5_GetDataSize(self._ncir, ntrace)
                if size < 0:
                    raise NL5ValueException(f'Error occurred when trying to read data size of trace {name}.')
            else:
                raise NL5TraceException(f'Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return size

    def simulate_ac(self) -> None:
        '''! Perform AC simulation with simulation parameters specified in the schematic file.

        Only "Linearize schematic" method is supported.

        @param
        @returns
        '''
        if self._ncir >= 0:
            retval = self.NL5_CalcAC(self._ncir)
            if retval < 0:
                raise NL5StartException('Error trying to start AC simulation')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    def get_ac_trace(self, name:str) -> int:
        ''' Returns a handle, maybe this shouldn't be implemented directly and use underlying function as a mean to get data.
        '''
        frame = inspect.currentframe()
        raise NL5NotImplementedException(f'function {inspect.getframeinfo(frame).function} not implemented!')

    def get_ac_data_size(self, name:str) -> int:
        '''! Gets the number of data points of the AC name trace

        Size is a positive number.

        @param name the trace name in the format used by NL5 Circuit Simulator
        @returns data size
        '''
        if self._ncir >= 0:
            ntrace = self.NL5_GetACTrace(self._ncir, name.encode('utf-8'))
            if ntrace >= 0:
                size = self.NL5_GetACDataSize(self._ncir, ntrace)
                if size < 0:
                    raise NL5ValueException(f'Error occurred when trying to read AC data size of trace {name}.')
            else:
                raise NL5TraceException(f'AC Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return size

    def get_ac_data_at(self, name:str, n:int) -> tuple[float, float, float]:
        '''! Returns frequency [Hz], magnitude, and phase [deg] values of data point with index n.

        Data index is zero-based.

        @param name the AC trace name in the format used by NL5 Circuit Simulator
        @param n index at which data is expected.
        @returns frequency, magnitude and phase as a tuple (freq, mag, phase)
        '''
        if self._ncir >= 0:
            ntrace = self.NL5_GetACTrace(self._ncir, name.encode('utf-8'))
            if ntrace >= 0:
                f = ct.c_double()
                m = ct.c_double()
                p = ct.c_double()
                retval = self.NL5_GetACDataAt(self._ncir, ntrace, n, f, m, p)
                if retval < 0:
                    raise NL5ValueException('Index is less than zero, or greater or equal to data size.')
            else:
                raise NL5TraceException(f'AC Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return (f.value, m.value, p.value)

    def save_ac_data(self, name:str, path:str='') -> None:
        '''! Save AC data of the current schematic into the data file

        Use this function to save transient data into the file in NL5 data format. Default file extension is "nlf".
        The data can be loaded into NL5 and shown on the AC graph.

        @param name NL5 data file name
        @param path location where data file will be saved
        @returns
        '''
        if path:
            # validate user provided path
            path = os.path.abspath(path)
        else:
            # assume data will be saved in current working directory
            path = os.getcwd()

        # check valid circuit file name
        if not name.endswith('.nlf'):
            name = f'{name}.nlf'

        data_file = os.path.join(path, f'{name}')

        if self._ncir >= 0:
            retval = self.NL5_SaveACData(self._ncir, data_file.encode('utf-8'))
            if retval < 0:
                raise NL5SaveException('Error trying to save NL5 data file.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return

    # Functions using numpy vectors to get data more efficiently
    def get_data_slice(self, name:str, t_start:float, t_end:float, t_step:float) -> np.ndarray:
        '''! Get data slice from a given time range

        Tries to get data from t_start to t_end of a given trace, sampled at t_step points.
        If this point does not belong to a simulation data point, NL5 gives a linear approximation
        of between the neareast simulation points.

        @param name the trace name in the format used by NL5 Circuit Simulator
        @param t_start start time for data slice.
        @param t_end end time for data slice.
        @param t_step time step at which data is sampled.
        @returns array for sampled data.
        '''
        if self._ncir >= 0:
            ntrace = self.NL5_GetTrace(self._ncir, name.encode('utf-8'))
            if ntrace >= 0:
                N = int((t_end - t_start) / t_step) + 1
                v = np.zeros(N)
                for i in range(N):
                    t = i * t_step + t_start
                    d = ct.c_double()
                    retval = self.NL5_GetData(self._ncir, ntrace, abs(t), d)
                    if retval < 0:
                        raise NL5ValueException(f'Data point does not exist for time={t} seconds.')
                    v[i] = d.value
            else:
                raise NL5TraceException(f'Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return v

    def get_timedata_vectors(self, name:str) -> tuple[np.ndarray, np.ndarray]:
        '''! Gets time and data vectors for a given trace.

        The returned data is all simulation points and the times t at which they happen.
        Time delta between data points may not be regular and is defined by NL5 solve algorithm.
        This time, data vectors are useful for plotting or calculation purposes.

        @param name the trace name in the format used by NL5 Circuit Simulator
        @returns tuple of (time, data) arrays.
        '''
        if self._ncir >= 0:
            ntrace = self.NL5_GetTrace(self._ncir, name.encode('utf-8'))
            if ntrace >= 0:
                # get data size
                size = self.NL5_GetDataSize(self._ncir, ntrace)
                if size < 0:
                    raise NL5ValueException(f'Error occurred when trying to read data size of trace {name}.')
                # create numpy buffers to hold the data
                t_vec = np.zeros(size)
                d_vec = np.zeros(size)
                # read all the data
                for i in range(size):
                    # get data for i point from NL5
                    d = ct.c_double()
                    t = ct.c_double()
                    retval = self.NL5_GetDataAt(self._ncir, ntrace, i, t, d)
                    if retval < 0:
                        raise NL5ValueException('Index is less than zero, or greater or equal to data size.')
                    # store current data
                    t_vec[i] = t.value
                    d_vec[i] = d.value
            else:
                raise NL5TraceException(f'Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')
        return (t_vec, d_vec)

    def get_freqmagphase_vectors(self, name:str, log:bool=False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        '''! Gets frequency [Hz], magnitude and phase[deg] vectors for a given trace.

        The returned data is all simulation points and the times t at which they happen.
        Time delta between data points may not be regular and is defined by NL5 solve algorithm.
        This time, data vectors are useful for plotting or calculation purposes.

        @param name the trace name in the format used by NL5 Circuit Simulator
        @param log automatically convert to logarithmic scale frequency and magnitude
        @returns tuple of (frequency, magnitude, phase) arrays.
        '''
        if self._ncir >= 0:
            ntrace = self.NL5_GetACTrace(self._ncir, name.encode('utf-8'))
            if ntrace >= 0:
                # get data size
                size = self.NL5_GetACDataSize(self._ncir, ntrace)
                if size < 0:
                    raise NL5ValueException(f'Error occurred when trying to read data size of trace {name}.')
                # create numpy buffers to hold the data
                f_vec = np.zeros(size)
                m_vec = np.zeros(size)
                p_vec = np.zeros(size)
                # read all the data
                for i in range(size):
                    # get data for i point from NL5
                    f = ct.c_double()
                    m = ct.c_double()
                    p = ct.c_double()
                    retval = self.NL5_GetACDataAt(self._ncir, ntrace, i, f, m, p)
                    if retval < 0:
                        raise NL5ValueException('Index is less than zero, or greater or equal to data size.')
                    # store current data
                    f_vec[i] = f.value
                    m_vec[i] = m.value
                    p_vec[i] = p.value
            else:
                raise NL5TraceException(f'AC Trace {name} does not exist in circuit.')
        else:
            raise NL5OpenException('Circuit file not opened or not valid. Try to use open() function first!')

        if log:
            f_vec = np.log10(f_vec)
            m_vec = 20.0 * np.log10(m_vec)

        return (f_vec, m_vec, p_vec)

    # Functions provided by Alexei Smirnov
    def NL5_GetError(self):
        self.nl5.NL5_GetError.argtypes = []
        self.nl5.NL5_GetError.restype = ct.c_char_p
        return self.nl5.NL5_GetError()

    def NL5_GetInfo(self):
        self.nl5.NL5_GetInfo.argtypes = []
        self.nl5.NL5_GetInfo.restype = ct.c_char_p
        return self.nl5.NL5_GetInfo()

    def NL5_GetLicense(self, name):
        self.nl5.NL5_GetLicense.argtypes = [ct.c_char_p]
        self.nl5.NL5_GetLicense.restype = ct.c_int
        return self.nl5.NL5_GetLicense(name)

    def NL5_Open(self, name):
        self.nl5.NL5_Open.argtypes = [ct.c_char_p]
        self.nl5.NL5_Open.restype = ct.c_int
        return self.nl5.NL5_Open(name)

    def NL5_Close(self, ncir):
        self.nl5.NL5_Close.argtypes = [ct.c_int]
        self.nl5.NL5_Close.restype = ct.c_int
        return self.nl5.NL5_Close(ncir)

    def NL5_Save(self, ncir):
        self.nl5.NL5_Save.argtypes = [ct.c_int]
        self.nl5.NL5_Save.restype = ct.c_int
        return self.nl5.NL5_Save(ncir)

    def NL5_SaveAs(self, ncir, name):
        self.nl5.NL5_SaveAs.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_SaveAs.restype = ct.c_int
        return self.nl5.NL5_SaveAs(ncir, name)

    def NL5_GetValue(self, ncir, name, v):
        self.nl5.NL5_GetValue.argtypes = [ct.c_int, ct.c_char_p, ct.POINTER(ct.c_double)]
        self.nl5.NL5_GetValue.restype = ct.c_int
        return self.nl5.NL5_GetValue(ncir, name, v)

    def NL5_SetValue(self, ncir, name, v):
        self.nl5.NL5_SetValue.argtypes = [ct.c_int, ct.c_char_p, ct.c_double]
        self.nl5.NL5_SetValue.restype = ct.c_int
        return self.nl5.NL5_SetValue(ncir, name, v)

    def NL5_GetText(self, ncir, name, text, length):
        self.nl5.NL5_GetText.argtypes = [ct.c_int, ct.c_char_p, ct.c_char_p, ct.c_int]
        self.nl5.NL5_GetText.restype = ct.c_int
        return self.nl5.NL5_GetText(ncir, name, text, length)

    def NL5_SetText(self, ncir, name, text):
        self.nl5.NL5_SetText.argtypes = [ct.c_int, ct.c_char_p, ct.c_char_p]
        self.nl5.NL5_SetText.restype = ct.c_int
        return self.nl5.NL5_SetText(ncir, name, text)

    def NL5_GetParam(self, ncir, name):
        self.nl5.NL5_GetParam.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_GetParam.restype = ct.c_int
        return self.nl5.NL5_GetParam(ncir, name)

    def NL5_GetParamValue(self, ncir, npar, v):
        self.nl5.NL5_GetParamValue.argtypes = [ct.c_int, ct.c_int, ct.POINTER(ct.c_double)]
        self.nl5.NL5_GetParamValue.restype = ct.c_int
        return self.nl5.NL5_GetParamValue(ncir, npar, v)

    def NL5_SetParamValue(self, ncir, npar, v):
        self.nl5.NL5_SetParamValue.argtypes = [ct.c_int, ct.c_int, ct.c_double]
        self.nl5.NL5_SetParamValue.restype = ct.c_int
        return self.nl5.NL5_SetParamValue(ncir, npar, v)

    def NL5_GetParamText(self, ncir, npar, text, length):
        self.nl5.NL5_GetParamText.argtypes = [ct.c_int, ct.c_int, ct.c_char_p, ct.c_int]
        self.nl5.NL5_GetParamText.restype = ct.c_int
        return self.nl5.NL5_GetParamText(ncir, npar, text, length)

    def NL5_SetParamText(self, ncir, npar, text):
        self.nl5.NL5_SetParamText.argtypes = [ct.c_int, ct.c_int, ct.c_char_p]
        self.nl5.NL5_SetParamText.restype = ct.c_int
        return self.nl5.NL5_SetParamText(ncir, npar, text)

    def NL5_GetTrace(self, ncir, name):
        self.nl5.NL5_GetTrace.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_GetTrace.restype = ct.c_int
        return self.nl5.NL5_GetTrace(ncir, name)

    def NL5_AddVTrace(self, ncir, name):
        self.nl5.NL5_AddVTrace.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_AddVTrace.restype = ct.c_int
        return self.nl5.NL5_AddVTrace(ncir, name)

    def NL5_AddITrace(self, ncir, name):
        self.nl5.NL5_AddITrace.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_AddITrace.restype = ct.c_int
        return self.nl5.NL5_AddITrace(ncir, name)

    def NL5_AddPTrace(self, ncir, name):
        self.nl5.NL5_AddPTrace.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_AddPTrace.restype = ct.c_int
        return self.nl5.NL5_AddPTrace(ncir, name)

    def NL5_AddVarTrace(self, ncir, name):
        self.nl5.NL5_AddVarTrace.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_AddVarTrace.restype = ct.c_int
        return self.nl5.NL5_AddVarTrace(ncir, name)

    def NL5_AddFuncTrace(self, ncir, text):
        self.nl5.NL5_AddFuncTrace.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_AddFuncTrace.restype = ct.c_int
        return self.nl5.NL5_AddFuncTrace(ncir, text)

    def NL5_DeleteTrace(self, ncir, ntrace):
        self.nl5.NL5_DeleteTrace.argtypes = [ct.c_int, ct.c_int]
        self.nl5.NL5_DeleteTrace.restype = ct.c_int
        return self.nl5.NL5_DeleteTrace(ncir, ntrace)

    def NL5_SetStep(self, ncir, step):
        self.nl5.NL5_SetStep.argtypes = [ct.c_int, ct.c_double]
        self.nl5.NL5_SetStep.restype = ct.c_int
        return self.nl5.NL5_SetStep(ncir, step)

    def NL5_SetTimeout(self, ncir, t):
        self.nl5.NL5_SetTimeout.argtypes = [ct.c_int, ct.c_int]
        self.nl5.NL5_SetTimeout.restype = ct.c_int
        return self.nl5.NL5_SetTimeout(ncir, t)

    def NL5_GetSimulationTime(self, ncir, t):
        self.nl5.NL5_GetSimulationTime.argtypes = [ct.c_int, ct.POINTER(ct.c_double)]
        self.nl5.NL5_GetSimulationTime.restype = ct.c_int
        return self.nl5.NL5_GetSimulationTime(ncir, t)

    def NL5_Start(self, ncir):
        self.nl5.NL5_Start.argtypes = [ct.c_int]
        self.nl5.NL5_Start.restype = ct.c_int
        return self.nl5.NL5_Start(ncir)

    def NL5_Simulate(self, ncir, interval):
        self.nl5.NL5_Simulate.argtypes = [ct.c_int, ct.c_double]
        self.nl5.NL5_Simulate.restype = ct.c_int
        return self.nl5.NL5_Simulate(ncir, interval)

    def NL5_SimulateInterval(self, ncir, interval):
        self.nl5.NL5_SimulateInterval.argtypes = [ct.c_int, ct.c_double]
        self.nl5.NL5_SimulateInterval.restype = ct.c_int
        return self.nl5.NL5_SimulateInterval(ncir, interval)

    def NL5_SimulateStep(self, ncir):
        self.nl5.NL5_SimulateStep.argtypes = [ct.c_int]
        self.nl5.NL5_SimulateStep.restype = ct.c_int
        return self.nl5.NL5_SimulateStep(ncir)

    def NL5_SaveIC(self, ncir):
        self.nl5.NL5_SaveIC.argtypes = [ct.c_int]
        self.nl5.NL5_SaveIC.restype = ct.c_int
        return self.nl5.NL5_SaveIC(ncir)

    def NL5_GetDataSize(self, ncir, ntrace):
        self.nl5.NL5_GetDataSize.argtypes = [ct.c_int, ct.c_int]
        self.nl5.NL5_GetDataSize.restype = ct.c_int
        return self.nl5.NL5_GetDataSize(ncir, ntrace)

    def NL5_GetDataAt(self, ncir, ntrace, n, t, data):
        self.nl5.NL5_GetDataAt.argtypes = [ct.c_int, ct.c_int, ct.c_int, ct.POINTER(ct.c_double), ct.POINTER(ct.c_double)]
        self.nl5.NL5_GetDataAt.restype = ct.c_int
        return self.nl5.NL5_GetDataAt(ncir, ntrace, n, t, data)

    def NL5_GetLastData(self, ncir, ntrace, t, data):
        self.nl5.NL5_GetLastData.argtypes = [ct.c_int, ct.c_int, ct.POINTER(ct.c_double), ct.POINTER(ct.c_double)]
        self.nl5.NL5_GetLastData.restype = ct.c_int
        return self.nl5.NL5_GetLastData(ncir, ntrace, t, data)

    def NL5_GetData(self, ncir, ntrace, t, data):
        self.nl5.NL5_GetData.argtypes = [ct.c_int, ct.c_int, ct.c_double, ct.POINTER(ct.c_double)]
        self.nl5.NL5_GetData.restype = ct.c_int
        return self.nl5.NL5_GetData(ncir, ntrace, t, data)

    def NL5_DeleteOldData(self, ncir):
        self.nl5.NL5_DeleteOldData.argtypes = [ct.c_int]
        self.nl5.NL5_DeleteOldData.restype = ct.c_int
        return self.nl5.NL5_DeleteOldData(ncir)

    def NL5_SaveData(self, ncir, name):
        self.nl5.NL5_SaveData.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_SaveData.restype = ct.c_int
        return self.nl5.NL5_SaveData(ncir, name)

    def NL5_GetInput(self, ncir, name):
        self.nl5.NL5_GetInput.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_GetInput.restype = ct.c_int
        return self.nl5.NL5_GetInput(ncir, name)

    def NL5_SetInputValue(self, ncir, nin, v):
        self.nl5.NL5_SetInputValue.argtypes = [ct.c_int, ct.c_int, ct.c_double]
        self.nl5.NL5_SetInputValue.restype = ct.c_int
        return self.nl5.NL5_SetInputValue(ncir, nin, v)

    def NL5_SetInputLogicalValue(self, ncir, nin, i):
        self.nl5.NL5_SetInputLogicalValue.argtypes = [ct.c_int, ct.c_int, ct.c_int]
        self.nl5.NL5_SetInputLogicalValue.restype = ct.c_int
        return self.nl5.NL5_SetInputLogicalValue(ncir, nin, i)

    def NL5_GetOutput(self, ncir, name):
        self.nl5.NL5_GetOutput.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_GetOutput.restype = ct.c_int
        return self.nl5.NL5_GetOutput(ncir, name)

    def NL5_GetOutputValue(self, ncir, nout, v):
        self.nl5.NL5_GetOutputValue.argtypes = [ct.c_int, ct.c_int, ct.POINTER(ct.c_double)]
        self.nl5.NL5_GetOutputValue.restype = ct.c_int
        return self.nl5.NL5_GetOutputValue(ncir, nout, v)

    def NL5_GetOutputLogicalValue(self, ncir, nout, i):
        self.nl5.NL5_GetOutputLogicalValue.argtypes = [ct.c_int, ct.c_int, ct.POINTER(ct.c_int)]
        self.nl5.NL5_GetOutputLogicalValue.restype = ct.c_int
        return self.nl5.NL5_GetOutputLogicalValue(ncir, nout, i)

    def NL5_CalcAC(self, ncir):
        self.nl5.NL5_CalcAC.argtypes = [ct.c_int]
        self.nl5.NL5_CalcAC.restype = ct.c_int
        return self.nl5.NL5_CalcAC(ncir)

    def NL5_GetACTrace(self, ncir, name):
        self.nl5.NL5_GetACTrace.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_GetACTrace.restype = ct.c_int
        return self.nl5.NL5_GetACTrace(ncir, name)

    def NL5_GetACDataSize(self, ncir, ntrace):
        self.nl5.NL5_GetACDataSize.argtypes = [ct.c_int, ct.c_int]
        self.nl5.NL5_GetACDataSize.restype = ct.c_int
        return self.nl5.NL5_GetACDataSize(ncir, ntrace)

    def NL5_GetACDataAt(self, ncir, ntrace, n, f, mag, phase):
        self.nl5.NL5_GetACDataAt.argtypes = [ct.c_int, ct.c_int, ct.c_int, ct.POINTER(ct.c_double), ct.POINTER(ct.c_double), ct.POINTER(ct.c_double)]
        self.nl5.NL5_GetACDataAt.restype = ct.c_int
        return self.nl5.NL5_GetACDataAt(ncir, ntrace, n, f, mag, phase)

    def NL5_SaveACData(self, ncir, name):
        self.nl5.NL5_SaveACData.argtypes = [ct.c_int, ct.c_char_p]
        self.nl5.NL5_SaveACData.restype = ct.c_int
        return self.nl5.NL5_SaveACData(ncir, name)

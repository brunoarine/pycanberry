# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 09:54:14 2017

@author: Bruno Arine
@email: bruno.arine@runbox.com
"""

import time
import sys
import numpy as np
import win32com.client
from .codes import bits

# The right way to read the detector's parameters is:
# win32.com.client.constants.CAM_PARAMETER
# You may have some luck fetching the parameters list through
# win32.com.client.constants.__dict__, but unfortunately
# this object is not even registered in some systems (reason
# unknown). Therefore, all CAM bits were dumped into a pickle
# file in order to be accesible in all systems.


class Connector(object):
    """
    This class supplies a simplified alternative to interect with the VDM service
    in a pythonic way through COM libraries, provided you have access to them
    (i.e. you're an authorized Canberra customer. There are no possible ways
    to circumvent the COM libraries, since you need an authorized USB key to
    interact with all Canberra devices (either detectors or saved spectra), and
    I don't believe there is a sane way to do so through Python alone.

    Parameters
    ----------
    source : string
        Detector name as listed on Genie 2000's MCA database

    Functions
    ---------
    energy_to_channel :

    """

    def __init__(self, source):
        # The DeviceAccess library keeps a list of properties and their
        # respective memory addresses in win32com.client.constants, which,
        # unfortunately, are not known to the layman unless he manages to
        # pry at the DLL file via VisualStudio or, more practically,
        # Excel's code editor. Anyway, this library must be called justly
        # after DeviceAccess has been dispatched, otherwise it simply
        # doesn't work. The string name of said properties may also be
        # consulted in the Genie 2000 Customization Tools Manual.
        # self.bits = win32com.client.constants
        self.source = source
        self.det = win32com.client.Dispatch("Canberra.DeviceAccess")

    def _open(self):
        try:
            self.det.Connect(self.source)
        except Exception as ex:
            # template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            # message = template.format(type(ex).__name__, ex.args)
            raise Exception(ex.args[2][2])

    def _close(self):
        self.det.Disconnect()

    def __enter__(self):
        # This gives the user an opportunity to work with the detector in
        # a 'with Connector(detector) as detector' fashion, which is the
        # recommended way to interact with Canberra's detectors anyway.
        # Why? Because whenever you access them, you greedily denies access
        # to any other software else (Genie 2000 included). If your code
        # eventually breaks, the detector may still be hijacked and you won't
        # be able to interact with it unless you shutdown the original kernel
        # where your code was called in the first place.
        self._open()
        # Energy calibration coefficients
        self.energycal_slope = self.get_param("CAM_F_ECSLOPE")
        self.energycal_intercept = self.get_param("CAM_F_ECOFFSET")
        return self

    def __exit__(self, type, value, traceback):
        self._close()

    def energy_to_channel(self, energy):
        """
        Converts energy (keV) to channel number according to the selected
        detector calibration equation.
        """
        return (energy - self.energycal_intercept) / self.energycal_slope

    def channel_to_energy(self, channel):
        return channel * self.energycal_slope + self.energycal_intercept

    def get_status(self):
        # 2080 = idle
        # 2084 = counting
        # 2092 = paused
        # 2224 = finished
        self.status_ = self.det.AnalyzerStatus
        return self.status_

    def get_param(self, param):
        """
        Gets a parameter from the open detector. The list of parameters
        should be consulted in Genie 2000's Customization Manual
        """
        return self.det.Param(bits[param])

    def set_param(self, param, value):
        """
        Modifies a CAM parameter.
        """
        # This is awkward. I don't know what the 2nd and 3rd args mean,
        # but they are needed and they work being 1 and 1, so leave them.
        self.det.SetParam(bits[param], 1, 1, value)

    def get_spectrum(self, leftchan=1, rightchan=-1):
        """
        Returns the spectrum in numerical form.
        """
        return np.array(self.det.GetSpectrum(leftchan, rightchan))

    def start_acquisition(self, time, clear=True, progress_bar=True):
        if clear:
            self.clear()
        self.det.SpectroscopyAcquireSetup(1, time)  # 1 = count to live time
        self.det.AcquireStart()
        if progress_bar:
            self._show_progress()

    def stop_acquisition(self):
        self.det.AcquirePause()

    def clear(self):
        self.det.Clear()

    def _show_progress(self):
        livetime = 0
        preset = self.get_param("CAM_X_PLIVE")
        while livetime < preset:
            livetime = self.get_param("CAM_X_ELIVE")
            progress = int(livetime / preset * 20)
            bar = "\r%3d%% [%-20s]  Tempo est.: %d s       " % (
                livetime / preset * 100,
                "#" * progress,
                (preset - livetime),
            )
            sys.stdout.write(bar)
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\n")

    def online(self, switch=True):
        try:
            self.det.HighVoltage.On = switch
        except com_error:
            pass

    def save(self, filename, overwrite=False):
        self.det.Save(filename, OverWrite=overwrite)

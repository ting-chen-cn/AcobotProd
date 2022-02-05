import sounddevice as sd
import numpy as np

class acousticBot2SoundDevice:
    def __init__(self):
        pass

    def __str__(self):
        return("AcousticBot 2 sound device driver")

    def generateSignal(self,frequency, amplitude, duration):
        """
        Creates a numpy array of a sine wave 
        according to given variables.

        Parameters
        ----------
        frequency : Int
            DESCRIPTION.
        amplitude : TYPE
            DESCRIPTION.
        duration : TYPE
            DESCRIPTION.

        Returns
        -------
        signal : Numpy array
            Numpy float array characterising sine wave.
        """
        f = frequency
        A = amplitude
        t = duration
        fs = 41000 # sampling rate
        signal = A * (np.sin(2*np.pi*np.arange(fs*t)*f/fs)).astype(np.float32)
        return signal
    
    def playSignal(self, frequency, amplitude, duration):
        signal = self.generateSignal(frequency, amplitude, duration)
        sd.play(signal)
    
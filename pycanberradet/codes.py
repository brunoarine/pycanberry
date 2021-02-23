# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 10:14:44 2017

@author: LARE
"""

import pickle

errors = {
    0: "OK! Operation performed successfully. ",
    17: "Error: Could not connect to the desired detector or file (detector already opened by another program?)",
    29: "Error: The certificate file could not be found.",
    31: "Error: recalibration failure with the specified spectrum.",
}

bits = pickle.load(open("bits.pickle", "rb"))

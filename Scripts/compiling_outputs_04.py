#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  3 18:11:53 2025

@author: brunojalowski
"""
from pathlib import Path
import glob
import pandas as pd

outputs_process04_path = Path('../outputs/process04/').resolve()


YEAR = 

# Listing all mcip files
outputs_04 = glob.glob(str(outputs_process04_path / 'industrialAndPavedEmission'))
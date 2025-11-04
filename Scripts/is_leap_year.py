#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 30 16:20:03 2025

@author: brunojalowski
"""

# Function for checking if fabruary has 28 or 29 days
def is_leap_year(year:int):
    '''
    Checks if a given year is a leap year. For it to be true, the year has to
    be divisible by 4, 100 and 400.

    Parameters
    ----------
    year : int

    Returns
    -------
    bool
        True if the referring year is a leap year and False if not.

    '''
    if year % 4 == 0:
        if year % 100 == 0:
            if year % 400 == 0:
                return True
            else:
                return False
        else:
            return False
    else:
        return False
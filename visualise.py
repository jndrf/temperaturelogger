#!/usr/bin/env python3

import argparse
import configparser

from math import log

from calibration_plotter import determine_adc_response


def convert_voltage_to_resistance(voltage, vref=3.3, resistor=10e3):
    '''convert the voltage across the NTC into its resistance

    vref is the total voltage across the voltage divider in V
    resistor is the resistance of the other resistor in the divider in Ohm
    '''

    r_ntc = resistor/(vref/voltage - 1)

    return r_ntc


def ntc_response(resistance, rref=10e3):
    '''return temperature according to extended "Steinhart and Hart" interpolation

    the parameters are valid for NTC with B_{25/85} = 3977, i.e. NTC from the Vishay NTCLE100E3
    series  with R_{25} from 2200 to 10000 Ohm. The rref parameter needs to be set to R_{25}.
    '''

    A_1 = 3.354016e-3
    B_1 = 2.569850e-4
    C_1 = 2.620131e-6
    D_1 = 6.383091e-8

    logratio = log(resistance/rref)

    t_invers = A_1 + B_1*logratio + C_1*logratio**2 + D_1*logratio**3
    return 1/t_invers

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Plotting utility for the temperature logger')
    parser.add_argument('-d', '--data', help='File with temperature data')
    parser.add_argument('-r', '--calibration', help='File with ADC calibration measurements')

    args = parser.parse_args()

    # main(args)

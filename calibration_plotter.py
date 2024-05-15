#!/usr/bin/env python3

import argparse
import pandas as pd
import scipy.optimize as spopt

from matplotlib import pyplot as plt


def linear_function(x, gradient, offset):
    '''linear function for curve fitting'''

    return x*gradient + offset


def determine_adc_response(adc_readout, voltage, voltage_uncertainty=None):
    '''return a linear function that gives the adc response'''

    popt, pcov, infodict, mesg, ier = spopt.curve_fit(
        linear_function, adc_readout, voltage,
        voltage_uncertainty, full_output=True
    )

    if not ier in [1, 2, 3, 4]:
        raise RuntimeError(f'Error (status {ier}) when calibrating ADC response: {mesg}')

    gradient = popt[0]
    offset = popt[1]
    
    def adc_response(x):
        return linear_function(x, gradient, offset)

    return adc_response


if __name__ == '__main__':
    parser = argparse.ArgumentParser('tool to plot the ADC calibration measurements')
    parser.add_argument('data', help='table with calibration data')
    parser.add_argument('-o', '--output', help='Save calibration plot in this file.')

    args = parser.parse_args()

    df = pd.read_excel(args.data)

    adc_response = determine_adc_response(df['ADC Readout'], df['Measured Voltage [V]'])

    fig, ax = plt.subplots(1, 1)

    ax.scatter(df['ADC Readout'], df['Measured Voltage [V]'])
    ax.plot(df['ADC Readout'], adc_response(df['ADC Readout']))

    ax.set_xlabel('ADC Readout')
    ax.set_xlim(left=0)
    ax.set_ylabel('Measured Voltage [V]')

    plt.grid()

    if args.output:
        fig.savefig(args.output)
    else:
        fig.show()

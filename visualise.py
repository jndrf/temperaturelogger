#!/usr/bin/env python3

import argparse
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.dates import ConciseDateFormatter
from matplotlib.ticker import AutoMinorLocator, MultipleLocator

from calibration_plotter import determine_adc_response


def convert_voltage_to_resistance(voltage, vref=3.3, resistor=10e3):
    '''convert the voltage across the NTC into its resistance

    vref is the total voltage across the voltage divider in V
    resistor is the resistance of the other resistor in the divider in Ohm
    '''

    r_ntc = resistor/(vref/voltage - 1)

    return r_ntc


def ntc_response(resistance, rref=10e3):
    '''return temperature in degree Celsius according to extended "Steinhart and Hart" interpolation

    the parameters are valid for NTC with B_{25/85} = 3977, i.e. NTC from the Vishay NTCLE100E3
    series  with R_{25} from 2200 to 10000 Ohm. The rref parameter needs to be set to R_{25}.

    The resistance is accurate to less than 1 % in the [0, 55] °C range. This converts to an uncertainty
    of less than 0.3 °C on the temperature
    '''

    A_1 = 3.354016e-3
    B_1 = 2.569850e-4
    C_1 = 2.620131e-6
    D_1 = 6.383091e-8

    logratio = log(resistance/rref)

    t_invers = A_1 + B_1*logratio + C_1*logratio**2 + D_1*logratio**3
    return 1/t_invers - 273.15  # convert to degree Celsius


def clean_esp_time(series, max_difference=30):
    '''clean wrong entries from the time stamps by averaging

    series: pd.Series containing integer timestamps
    max_difference: if sensible values are further apart than this,
        the row between will be removed.

    returns a list of row indices to be dropped from the dataframe
    '''

    to_delete = []
    windows = series.rolling(window=3, center=True)
    for index, window in enumerate(windows):
        if window.size < 3:
            continue

        # correct for too small timestamps
        if min(window) == window.iloc[2]:
            new = window.iloc[1] + (window.iloc[1] - window.iloc[0])
            series.iloc[index+1] = new
            window.iloc[2] = new

        # correct for too large timestamps
        if max(window) == window.iloc[1]:
            timedelta = window.iloc[0] + window.iloc[2]
            if timedelta > max_difference:
                to_delete.append(index)
            new = (window.iloc[0] + window.iloc[2])/2
            series.iloc[index] = new

    return to_delete

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Plotting utility for the temperature logger')
    parser.add_argument('-d', '--data', help='File with temperature data')
    parser.add_argument('-r', '--calibration', help='File with ADC calibration measurements')
    parser.add_argument('-o', '--output', help='Save plot to here')
    parser.add_argument('-l', '--probe-label', default='Radiator',
                        help='Label for the data on ADC 2 (the sensor on the long cable)')

    args = parser.parse_args()

    df_calib = pd.read_excel(args.calibration)

    # sometimes, a line is garbled. Either it contains too many columns
    # or the columns are not complete and contain NaN values
    df_temp = pd.read_csv(args.data, names=['esp_time', 'ADC_1_raw', 'ADC_2_raw'], on_bad_lines='warn')

    df_temp['ADC_1'] = pd.to_numeric(df_temp['ADC_1_raw'], errors='coerce')
    df_temp['ADC_2'] = pd.to_numeric(df_temp['ADC_2_raw'], errors='coerce')

    df_temp.dropna(inplace=True)

    # Also, some timestamps are nonsensical, either too large or too small
    to_delete = clean_esp_time(df_temp['esp_time'])
    df_temp.drop(index=to_delete, inplace=True)

    # quick-and-dirty fix for bogus ADC readout, probably due to a short in the wire
    # should use something like outlier detection for proper treatment
    df_temp.query('ADC_1 > 20 & ADC_2 > 20', inplace=True)
    # also ignore entries with a disconnected wire
    df_temp.query('ADC_1 <= 4095 & ADC_2 <= 4095', inplace=True)

    # Convert readouts into times and temperatures
    adc_response = determine_adc_response(df_calib['ADC Readout'], df_calib['Measured Voltage [V]'])
    df_temp['esp_time_shifted'] = df_temp['esp_time'] + 7200 # Timezone, I live in UTC+2 atm
    df_temp['time'] = pd.to_datetime(df_temp['esp_time_shifted'], unit='s',
                                     origin='2000-01-01')  # epoch of ESP32 clock
    df_temp['V_1'] = adc_response(df_temp['ADC_1'])
    df_temp['V_2'] = adc_response(df_temp['ADC_2'])

    df_temp['R_1'] = convert_voltage_to_resistance(df_temp['V_1'])
    df_temp['R_2'] = convert_voltage_to_resistance(df_temp['V_2'])
    df_temp['T_1'] = ntc_response(df_temp['R_1'])
    df_temp['T_2'] = ntc_response(df_temp['R_2'])

    # and finally, visualise the results
    fig, ax = plt.subplots(1, 1)

    ax.plot(df_temp['time'], df_temp['T_1'], label='Kitchen')
    ax.plot(df_temp['time'], df_temp['T_2'], label=args.probe_label)
    ax.legend()

    ax.xaxis.set_major_formatter(ConciseDateFormatter(ax.xaxis.get_major_locator()))
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(MultipleLocator(1))

    ax.set_ylabel('Temperature [°C]')

    plt.grid(which='both')

    if args.output:
        fig.savefig(args.output, dpi=300)
    else:
        fig.show()

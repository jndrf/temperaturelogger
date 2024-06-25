import machine
import time

ntc_pins = [32, 35]
ntcs = [machine.ADC(pin, atten=3) for pin in ntc_pins]


def adc_readout(adcs, n_reads=20):
    '''average over several ntc readouts'''
    if type(adcs) != list:
        adcs = [adcs]

    readouts = []
    for adc in adcs:
        readouts.append([adc.read() for i in range(n_reads)])

    return [sum(e)/len(e) for e in readouts]


while True:
    line = [time.time()]
    line.extend(adc_readout(ntcs, n_reads=100))
    line = [str(item) for item in line]
    
    with open('data.csv', 'a') as f:
        writeline = ','.join(line)
        f.write(writeline)
        f.write('\n')       # need to write line separator explicitly
        f.close()

    time.sleep(10)
        

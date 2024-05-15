import machine
import time

ntc_pins = [32, 35]
ntcs = [machine.ADC(pin, atten=3) for pin in ntc_pins]


while True:
    readings = [ntc.read() for ntc in ntcs]
    line = [time.time()]
    line.extend(readings)
    line = [str(item) for item in line]
    
    with open('data.csv', 'a') as f:
        writeline = ','.join(line)
        f.write(writeline)
        f.write('\n')       # need to write line separator explicitly
        f.close()

    time.sleep(10)
        

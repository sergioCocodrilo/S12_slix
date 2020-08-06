"""
Remove all SLIX on the alarm report and add them to an output file.
"""
import serial
import re

def connect():
    """Connects to serial through USB"""
    ser = serial.Serial()
    # parameters
    ser.port = '/dev/ttyS0'
    ser.baudrate =  9600
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = 1 # seconds
    try:
        ser.open()
    except:
        ser.port = '/dev/ttyS1'
        ser.open()
    if ser.isOpen():
        return ser
    else:
        return None

def s12_listen_original(ser):
    """Listens for the answer of the S12 and returns the result"""
    # logging all outputs
    try:
        log_file = open('data/output/s12_raw.log', 'a')
    except:
        print('Error en la estructura de los archivos, descarga de nuevo el proyecto.')
        print('Para descargarlo: git clone https://github.com/sergioCocodrilo/S12_raw.git')
        quit()
    output_ended = False
    while not output_ended:
        for line in ser.readlines():
            print(line[:-1].decode("ascii"))
            log_file.write(line.decode('ascii'))
            if b"<" in line or b">" in line:
                output_ended = True 
    log_file.close()

def s12_listen(ser):
    """
    Listens for the answer of the S12 and returns the S12 state: 
       0: ready for macro 
       1: ready for S12 command
    """
    output_ended = False
    s12_state = None
    slix_alarms = []
    while not output_ended:
        for line in ser.readlines():
            print(line[:-1].decode("ascii"))
            if b">" in line:
                output_ended = True 
                s12_state = 0
            elif b"<" in line:
                output_ended = True 
                s12_state = 1
            elif b"SLIX" in line:
                slix_alarms.append(line[14:30])
    return (s12_state, slix_alarms)

def s12_command(ser, command):
    ser.write((command + '\r\n').enocde('ascii'))

    
if __name__ == "__main__":
    ser = connect()
    if not ser:
        print('Imposible establecer conexión.')
        quit()
        
    print('========== Revisando la lista de alarmas y borrando las SLIX ==========')
    ser.write('\x1b'.encode("ascii"))

    # get S12 ready for command
    while s12_listen(ser)[0] == 0:
        ser.write('MM\r\n'.encode('ascii'))

    # get alarm list
    ser.write('19.\r\n'.encode('ascii'))
    slix_alarms = s12_listen(ser)[1]
    print('SLIX ALARMS:')
    [print(alarm) for alarm in slix_alarms]

    for alarm in slix_alarms:
        while s12_listen(ser)[0] == 0:
            ser.write('MM\r\n'.encode('ascii'))
        ser.write(('DELETE-ALARM:ALMTIME=' + re.sub('\D','&',alarm) + '.').encode('ascii'))

import keithley_smu
import serial
import sys
import config_parse as config_parse # -=-= TODO Move to a sydor_utils package
import math
import time
import numpy as np
import matplotlib.pyplot as plt
import glob

from matplotlib import ticker

def read_curve(port):
    in_bytes = b''
    while True:
        curr_byte = port.read(1)
        if len(curr_byte) == 0:  # Assume finished
            break
        in_bytes = in_bytes + curr_byte

    return in_bytes.decode()

def run_script(port, script):
    for script_line in script:
        print("Sending line: '{}'".format(script_line))
        line_bytes = (script_line + "\r\n").encode()
        port.write(line_bytes)
        time.sleep(1)

def main(argv):

    die_name_cfg = None
    if (len(argv) != 1) and (len(argv) != 2):
        print("Usage: python3 fpd_die_iv.py <config file name> [die name]")
        return 1

    config_name = argv[0]
    if len(argv) > 1:
        die_name_cfg = argv[1]
        
    # Create the script we will need for the reset
    reset_script = ["*RST", ":SOURCE:VOLT 0", ":SOURCE:SWEEP:RANGING BEST", ":SOURCE:VOLT:MODE SWEEP", ":SOURCE:SWEEP:SPACING LIN"]

    # Create the script for the parameters
    param_script = [":SENSE:CURRENT:PROTECTION {:.9f}", ":SOURCE:VOLT:START {:.2f}", ":SOURCE:VOLT:STOP {:.2f}", ":SOURCE:VOLT:STEP {:.2f}", ":TRIG:COUN {:d}"]
    
    config_keys = [ ("I_LIM", 'd'), ("V_START", 'd'), ("V_STOP", 'd'), ("V_STEP", 'd'), ("COM", 's'), ("DIE_ID", 's')]

    while True:
        print("Using file {} for configuration.".format(config_name))

        config_file = open(config_name, "r")
        config_dict, status = config_parse.config_parse(config_file, config_keys)
        config_file.close()
        if (status & 0x2):
            print("Missing configuration keys.  Aborting.")
            return 1

        if die_name_cfg:
            config_dict['DIE_ID'] = die_name_cfg
            print("Die ID overridden by command line.")

        for curr_char in config_dict['DIE_ID']:
            if not (curr_char.isalnum() or (curr_char == '_')):
                print("Invalid DIE_ID: {}".format(config_dict['DIE_ID']))
                print("ERROR: The DIE_ID may contain only letters, numbers, and underscores (_).  Aborting.")
                return 1
                      
        config_parse.config_print(config_dict)

        print("Please verify configuration settings.  Enter 'C' to continue.  Otherwise, adjust configuration file and enter any other key to reload configuration.")
        config_approve_str = input().strip().upper()
        if config_approve_str == 'C':
            break

    curve_filename = config_dict['DIE_ID']+"_curve.csv";
    if len(glob.glob(curve_filename)) > 0:
        while True:
            print("Warning: Datafile '{}' already exists and will be clobbered.".format(curve_filename))
            print("Do you wish to continue?  Input 'y' to continue or 'n' to abort.")
            clobber_approve_str = input().strip().upper()
            if clobber_approve_str == 'Y':
                break
            if clobber_approve_str == 'N':
                return 0
            else:
                continue
                  
    # Open the serial port
    keithley_serial = serial.Serial(config_dict['COM'], 38400, timeout=2);

    # Compute and parse the acquisition parameters
    v_start = config_dict['V_START']
    v_stop = config_dict['V_STOP']
    v_step = config_dict['V_STEP']
    i_lim = config_dict['I_LIM']
    step_count = math.ceil((v_stop-v_start)/v_step)
    if step_count <= 0:
        print("Error: Invalid step count {} calculated.  Aborting.".format(step_count))
        return 1

    # Prepare the script with the parameters
    param_script[0] = param_script[0].format(i_lim)
    param_script[1] = param_script[1].format(v_start)
    param_script[2] = param_script[2].format(v_stop)
    param_script[3] = param_script[3].format(v_step)
    param_script[4] = param_script[4].format(step_count)

    # Send the preparatory scripts
    run_script(keithley_serial, reset_script)
    run_script(keithley_serial, param_script)

    # Time for the curve tracing
    keithley_serial.write(":output on\r\n".encode())

    time.sleep(2)
    print("Commence sweep.")
    keithley_serial.write(":read?\r\n".encode())
    #time.sleep(1)
    #test_string = keithley_serial.read(10)
    #print(test_string)
    curve_string = read_curve(keithley_serial)
    keithley_serial.write(":output off\r\n".encode())
    
    curve_keys = ['v_in', 'i_out', 'r_meas', 'timestamp', 'status']
    curve_dict, ret_status, msg_string = keithley_smu.parse_read(curve_keys, curve_string)

    print("Curve parsing return {}: ".format(ret_status) + msg_string)

    curve_len = len(curve_dict[curve_keys[0]])
    curve_file = open(curve_filename, "w")
    #print(curve_len)
    #print(curve_dict[curve_keys[0]])
    #print(curve_dict[curve_keys[1]])
    for pt_idx in range(curve_len):
        #print(pt_idx)
        #line_string = "{:.6e},{:.6e}\n".format(curve_dict[curve_keys[0]][pt_idx], curve_dict[curve_keys[1]][pt_idx])
        line_string = "{:.6e},{:.6e},{:.6e},{:.6e},{:.6e}\n".format(curve_dict[curve_keys[0]][pt_idx], curve_dict[curve_keys[1]][pt_idx], curve_dict[curve_keys[2]][pt_idx], curve_dict[curve_keys[3]][pt_idx], curve_dict[curve_keys[4]][pt_idx])
        #print(line_string)
        curve_file.write(line_string)

    curve_file.close()

    v_array = np.array(curve_dict[curve_keys[0]])
    i_array = np.array(curve_dict[curve_keys[1]])

    fig, ax = plt.subplots()
    fig.suptitle('Die {} I-V Curve'.format(config_dict['DIE_ID']))
    ax.set_xlabel('Voltage (V)')
    ax.yaxis.set_major_formatter(ticker.EngFormatter(unit='A'))
    ax.set_ylabel('Current')
    ax.plot(v_array, i_array)
    fig.savefig('{}_curve.png'.format(config_dict['DIE_ID']),dpi=200);
    
    plt.show()
    
    return

    
if __name__ == "__main__":
    ret = main(sys.argv[1:])
    sys.exit(ret)

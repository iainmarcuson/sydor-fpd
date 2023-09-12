## keithley_smu.py
#  @file Utilities for controlling a Keithley source meter

## Parse the read results of a run into a dictionary
#  @param[in] dict_keys A list of keys for the dictionary
#  @param[in] smu_string A comma-separated string of the returned values
#  @return A dictionary of the parameters, a return status, and a message string
def parse_read(dict_keys, smu_string):
    msg_string = "Parse OK."
    ret_status = 0;
    
    parse_dict = {}             # Create empty destination dict
    for key in dict_keys:
        parse_dict[key] = []    # Create an empty list for each parameter

    split_list = smu_string.strip().rstrip(',').split(',') # Comma-separated

    #print(split_list)
    #print(len(split_list))
    if (len(split_list) % len(dict_keys)) != 0: # Length mismatch
        msg_string = "Length mismatch."
        ret_status = -1;

    result_idx = 0
    for result in split_list:
        key_idx = result_idx % len(dict_keys) # Assign to keys sequentially
        parse_dict[dict_keys[key_idx]].append(float(result))
        result_idx += 1

    return parse_dict, ret_status, msg_string
        

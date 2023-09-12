## Parse generic configuration files
#  @file A simple parser for a text config file

## Parse the configuration, given either a string or a file handle
#  @param[in] config_data The configuration data, or could be a file handle, or even a list
#  @param[in] config_keys A list of dicts of keys and types to find
#  @return A dictionary of the config values and a return status
def config_parse(config_data, config_keys):
    config_log = {}             # A log of what configurations we have found
    config_dict = {}            # A record of the config values
    ret_status = 0              # Starts out okay
    key_only_list = [];         # A list of just key names, with no types
    type_dict = {}
    
    for keypair in config_keys:  # Note all the parameters to find
        key_name = keypair[0]
        if key_name in config_log:
            print("Error: Duplicated key '{}' in list of parameters.".format(key_name))
            raise KeyError
        config_log[key_name] = 0
        type_dict[key_name] = keypair[1]
        key_only_list.append(key_name)
        
    for line in config_data:
        strip_line = line.strip()
        if len(strip_line) == 0: # Empty line
            continue
        if strip_line.startswith("#"): # A comment
            continue

        split_line = strip_line.split("=",1)
        if len(split_line) < 2:
            print("Invalid line:\n{}\nSkipping.".format(strip_line.rstrip()))
            continue

        curr_key = split_line[0].strip()
        curr_val = split_line[1].strip()

        if curr_key not in key_only_list:
            print("Warning: Unknown key '{}'.  Skipping.".format(curr_key))
            continue
        if config_log[curr_key] != 0:
            print("Warning: Duplicate entry for key '{}'.  Using new entry.".format(curr_key))
            ret_status |= 1

        if type_dict[curr_key] == 'i':
            config_dict[curr_key] = int(curr_val)
        elif type_dict[curr_key] == 'd': # "double"
            config_dict[curr_key] = float(curr_val)
        elif type_dict[curr_key] == 's':
            config_dict[curr_key] = curr_val
        else:
            print("Error: Unknown type {}.".format(type_dict[curr_key]))
            raise ValueError

        config_log[curr_key] = 1

    for curr_key in config_log:
        if config_log[curr_key] == 0:
            print("Warning: Configuration variable '{}' not found.".format(curr_key))
            ret_status |= 2

    return (config_dict, ret_status)

def config_print(config_dict, num_dec=3):
    key_width = 20
    data_width = 20
    bg_color = [40, 107]
    fg_color = [97, 30];        # ANSI Codes for highlighting
    line_idx = 0
    float_pad_fmt = ':.{}f'.format(num_dec)
    float_pad_fmt = '{' + float_pad_fmt + '}'

    for key in config_dict:
        curr_key = key
        curr_val = config_dict[key]

        key_pad = curr_key.rjust(key_width)
        if (type(curr_val) is float):
            val_pad = float_pad_fmt.format(curr_val)
        elif (type(curr_val) is int):
            val_pad = '{:i}'.format(curr_val)
        else:                # -=-= Assume this is just a string
            val_pad = curr_val

        val_pad = val_pad.rjust(data_width)
        out_line = '\033[{}m\033[{}m{} = {}\033[0m'.format(bg_color[line_idx], fg_color[line_idx], key_pad, val_pad)
        print(out_line)
        line_idx = (line_idx + 1) % 2

        

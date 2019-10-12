"""
 ComBat:Module
 maintainer         : Zachary Hudson
 maintainer-email   : zachudson92@gmail.com
 required modules   : os, argparse, datetime, jinja2, xlrd, xlwt, netmiko
"""

#lines longer than 80 characters
# pylint: disable=C0301

import os
import argparse
import datetime
import jinja2
import xlrd
import xlwt
import netmiko


def pull_workbook(project_dir, file):
    """Module to pull excel workbook"""

    input_file = project_dir + "/" + file
    workbook = xlrd.open_workbook(input_file)

    return workbook

def pull_global_vars(global_vars_sheet):
    """Extract global_vars from workbook sheet. A list of non-iterative settings"""

    global_vars = {}

    for row in range(global_vars_sheet.nrows):
        rowvals = global_vars_sheet.row_values(row)
        global_vars[rowvals[0]] = str(rowvals[1])
    return global_vars

def pull_sheet_vars(arg_sheet):
    """Pull vars from workbook sheet. Iterative values """

    return_sheet_vars = []
    var_index_list = []
    var_type_list = []


    for row in range(arg_sheet.nrows):
        if row == 0:
            for index in arg_sheet.row_values(row):
                var_index_list.append(index)

        elif row == 1:
            for vartype in arg_sheet.row_values(row):
                var_type_list.append(vartype)

        else:
            rowvals = arg_sheet.row_values(row)
            new_dictionary = {}
            for i, var in enumerate(rowvals):

                if var_type_list[i] == 'STRING':
                    var = str(var)
                    new_dictionary[var_index_list[i]] = var.strip()

                elif var_type_list[i] == 'INTEGER':
                    try:
                        new_dictionary[var_index_list[i]] = int(var)
                    except:
                        new_dictionary[var_index_list[i]] = str(var).strip()

                elif var_type_list[i] == 'BOOLEAN':
                    new_dictionary[var_index_list[i]] = var

                elif var_type_list[i] == 'SPACE_DELIMITED':

                    if isinstance(var, float):
                        var_list = [int(var)]
                        new_dictionary[var_index_list[i]] = var_list

                    else:
                        new_dictionary[var_index_list[i]] = str(var).split(' ')

            return_sheet_vars.append(new_dictionary)

    return return_sheet_vars

def load_template(arg_device):
    """Load Jinja2 device templates"""

    template_dir = r'C:\Users\ZCONINGFORD\Documents\Projects\ComBat\templates'

    template_loader = jinja2.FileSystemLoader(searchpath=template_dir)
    template_env = jinja2.Environment(loader=template_loader)
    # load template
    # print(device),

    device_template = template_env.get_template(arg_device)

    return device_template

def write_config(snip, config_file):
    """Write to text file"""

    os.makedirs(os.path.dirname(config_file), exist_ok=True)

    file = open(config_file, "w")
    for output_line in snip.split('\n'):
        # if line is not empty write it to file
        if output_line.strip() != "":
            file.write(output_line + '\n')
    file.close()

def chop(arg_config_file, arg_device_type, arg_chop_file, netmiko_session=None):

    wb = xlwt.Workbook()

    page = False

    filter_list = ['firewall_vip',
                   'firewall_address',
                   'firewall_service_custom',
                   'firewall_service_group',
                   'firewall_vipgrp',
                   'firewall_policy',
                   'router_static',
                   'system_interface',
                   'firewall_addrgrp'
                   ]






    for line in arg_config_file:

        line = line.strip().split(' ')



        if line[0] == "config":
            object_index = 2

    # check if  segment is in filter list
            #print("! " +'_'.join(map(str, line[1:])))
            if '_'.join(map(str, line[1:])) in filter_list:
                print("saving: " + '_'.join(map(str, line[1:])), flush=True)

                page = True
                new_object_properties = ['id']

                ws = wb.add_sheet('_'.join(map(str, line[1:])))

                page_name = '_'.join(map(str, line[1:]))


    # enter selectd item  if seed edit and segment is in filter list
        if line[0] == "edit" and  page:
            #print('pop')
            new_object = {}
           # set objext id to text after edit
            new_object['id'] = line[1]




        # check if this is a item setting and check segment active
        if line[0] == "set" and  page:

    # add setting id to poperties list
            if  line[1] not in new_object_properties:
                new_object_properties.append(line[1])


           # set value
            new_object[line[1]] = line[2:]


        if line[0] == "next"  and  page and page_name == 'firewall_policy':
            if  "count" not in new_object_properties:
                new_object_properties.append("count")

            if  "first_hit" not in new_object_properties:
                new_object_properties.append("first_hit")

            if  "last_hit" not in new_object_properties:
                new_object_properties.append("last_hit")

            #print(netmiko_session.find_prompt())
            #print(new_object['id'])
            policy_stats = net_connect.send_command('diagnose firewall iprope show 00100004 ' + new_object['id'])


            policy_stats = policy_stats.split(" ")

            #print(policy_stats, flush=True)
            #print(len(policy_stats), flush=True)


            if len(policy_stats) == 13:
                new_object["count"] = policy_stats[5].split(':')[1].strip('\n')

                new_object["first_hit"] = policy_stats[9].split(':')[1] + " " + policy_stats[10]

                new_object["last_hit"] = policy_stats[11].split(':')[1] + " " + policy_stats[12]

            if len(policy_stats) == 14:
                new_object["count"] = policy_stats[6].split(':')[1].strip('\n')

                new_object["first_hit"] = policy_stats[10].split(':')[1] + " " + policy_stats[11]

                new_object["last_hit"] = policy_stats[12].split(':')[1] + " " + policy_stats[13]




            #print(new_object)
            #pull policy stats
    # check if reached end of items settings
        if line[0] == "next"  and  page:


            #print(new_object)
        #    piece_index =  0

    # iterate over dictionary list of items and setting first is ID followed by settings
            for piece in new_object.items():

                if isinstance(piece[1], list):
                    ws.write(object_index, new_object_properties.index(piece[0]), ' '.join(map(str, piece[1])))
                    #print(' '.join(map(str, piece)))
                else:
                    ws.write(object_index, new_object_properties.index(piece[0]), piece[1])
                    #print(piece)
        #        piece_index = piece_index + 1
            object_index = object_index +1


        if line[0] == "end" and  page:


            for i, item in enumerate(new_object_properties):

                ws.write(0, i, item)
            page = False

    wb.save(arg_chop_file)


if __name__ == '__main__':

#    PROJECT_DIRS = os.path.expanduser('~') + "/Documents/Projects/"

    parser = argparse.ArgumentParser(description='make some configs.')  # pylint: disable=C0103

    parser.add_argument('path', nargs=1, help='dir of the main.xlsx file')

    parser.add_argument('--make', action='store_true', default=False, help='make conifg')
    parser.add_argument('--pull', action='store_true', default=False, help='pull running conifg')
    parser.add_argument('--push', action='store_true', default=False, help='push conifg')
    parser.add_argument('--gather', action='store_true', default=False, help='gather')


    args = parser.parse_args()  # pylint: disable=C0103
    PROJECT_DIR = str(args.path[0])

    project_workbook = {}   # pylint: disable=C0103

    PROJECT_WORKBOOK = pull_workbook(PROJECT_DIR, "main.xlsm")

    for sheet in PROJECT_WORKBOOK.sheet_names():
        project_workbook[sheet] = pull_sheet_vars(PROJECT_WORKBOOK.sheet_by_name(sheet))

    project_workbook['data_global'] = pull_global_vars(PROJECT_WORKBOOK.sheet_by_name('data_global'))


    if args.make:
        print('{:15}{:25}{:25}'.format("device name", "template fille", "input file"))
        print("+--------------------------------------------------------------+")
        for device in project_workbook['MAKE']:

            #print(PROJECT_DIR, "/INPUT/" + device['data_file'])
            device_workbook = pull_workbook(PROJECT_DIR, "INPUT/" + device['data_file'])
            sheet_vars = {}

            # extract data from workbook
            for sheet in device_workbook.sheet_names():
                sheet_vars[sheet] = pull_sheet_vars(device_workbook.sheet_by_name(sheet))
            #set global vars


            sheet_vars['data_global'] = pull_global_vars(device_workbook.sheet_by_name('data_global'))

            sheet_vars['data_global']['site_prefix'] = project_workbook['data_global']['site_prefix']

            device['workbook_data'] = sheet_vars

            print('{:15}{:25}{:25}'.format(device['device'], device['template_file'], device['data_file']))

            template = load_template(device['template_file'])
            Snip = template.render(**sheet_vars)

            CONFIG_FILE = PROJECT_DIR + "/MAKE/" + device['device'] + ".txt"
            write_config(Snip, CONFIG_FILE)

    if args.pull:
        print('{:35}{:15}'.format("device name", "IP"))
        print("+--------------------------------------------------------------+")

        for device in project_workbook['MAKE']:
            print('{:35}{:15}'.format(device['device'], device['ip']))



            devices = {
                'device_type': device['device_type'],
                'ip': device['ip'],
                'username': device['username'],
                'password': device['password'],
            }

            net_connect = netmiko.ConnectHandler(**devices)


            if device['device_type'] == "fortinet":
                output = net_connect.send_command_timing('config vdom', delay_factor=4)
                output = net_connect.send_command_timing('edit ' + device['vslice'], delay_factor=4)
                output = net_connect.send_command('show ')

                ## add chop pass
                
                



            elif device['device_type'] == "cisco_nxos":
                output = net_connect.send_command("show run")


            Pull_FILE = PROJECT_DIR + "/PULL/" + datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S ") + device['device'] + ".txt"
            write_config(output, Pull_FILE)







    if args.push:
        print('{:35}{:15}'.format("device name", "IP"))
        print("+--------------------------------------------------------------+")

        for device in project_workbook['MAKE']:
            print('{:35}{:15}'.format(device['device'], device['ip']))



            devices = {
                'device_type': device['device_type'],
                'ip': device['ip'],
                'username': device['username'],
                'password': device['password'],
            }

            CONFIG_FILE = PROJECT_DIR + "/MAKE/" + device['device'] + ".txt"

            # confirm
            wait = input("YOU ARE ABOUT TO PUSH CHANGES !!! PRESS ENTER TO CONTINUE.")

            net_connect = netmiko.ConnectHandler(**devices)



            if device['device_type'] == "fortinet":
                output = net_connect.send_command_timing('config vdom', delay_factor=4)
                output = net_connect.send_command_timing('edit ' + device['vslice'], delay_factor=4)


                print(net_connect.find_prompt())
                output = net_connect.send_config_from_file(CONFIG_FILE)
                print(output)



                PUSH_LOG_FILE = PROJECT_DIR + "/PUSH/" + datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S ") + device['device'] + ".txt"
                write_config(output, PUSH_LOG_FILE)




    if args.gather:
        print('{:35}{:15}'.format("device name", "IP"))
        print("+--------------------------------------------------------------+")

        for device in project_workbook['MAKE']:
            print('{:35}{:15}'.format(device['device'], device['ip']))



            devices = {
                'device_type': device['device_type'],
                'ip': device['ip'],
                'username': device['username'],
                'password': device['password'],
            }

            net_connect = netmiko.ConnectHandler(**devices)



            if device['device_type'] == "fortinet":
                net_connect.send_command_timing('config vdom', delay_factor=4)
                net_connect.send_command_timing('edit ' + device['vslice'], delay_factor=4)

                output = net_connect.send_command('fnsysctl more  /etc/upd.dat')
                final = output.split("|")[0] + '\n'


                output = net_connect.send_command('get system status')
                output = output.split('\n')



                config_output = net_connect.send_command('show ')

                chop_file = PROJECT_DIR + "/GATHER/" +  datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S ") + device['device'] + ".xls"



                chop(config_output.split("\n"), device['device_type'], chop_file, net_connect)





                for line in output:

                    if "Serial-Number:" in line or "Hostname:" in line or "Version:" in line:
                        final += line + '\n'

                net_connect.send_command_timing('end', delay_factor=4)
                net_connect.send_command_timing('config global', delay_factor=4)
                output = net_connect.send_command('get system ha status')
                output = output.split('\n')

                for line in output:

                    if "Master:" in line or "Slave :" in line:
                        final += line + '\n'


            Gather_FILE = PROJECT_DIR + "/GATHER/" +  datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S ") + device['device'] + ".txt"
            write_config(final, Gather_FILE)

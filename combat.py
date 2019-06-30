# ComBat:Module
#
# maintainer          : Zachary Hudson
# maintainer-email    : zachudson92@gmail.com
# required modules    : jinja2 , xlrd

import jinja2
import xlrd
import os
import argparse
import datetime
import netmiko


def PullWorkbook(PROJECT_DIR, device ):
    INPUT_FILE = PROJECT_DIR + "/" + device


    workbook = xlrd.open_workbook(INPUT_FILE)

    
    return workbook

def PullGlobalVars(sheet):
    # extract globalVars from workbook sheet
    
    globalVars = {}

    for row in range(sheet.nrows):
        rowvals = sheet.row_values(row)
        globalVars[rowvals[0]] = str(rowvals[1])
    return globalVars

def PullSheetVars(sheet):
    sheetVars = []
    varindexList = []
    vartypeList  =  []
    
    for row in range(sheet.nrows):
        if row == 0 :
            for index in sheet.row_values(row):
                varindexList.append(index)
        
        elif row == 1 :
            for vartype in sheet.row_values(row):
                vartypeList.append(vartype)
            
        else:
            rowvals = sheet.row_values(row)
            newDictionary = {}
            for i, var in enumerate(rowvals) :

                if vartypeList[i] =='STRING':
                    var = str(var)
                    newDictionary[varindexList[i] ]          =  var.strip()

                elif vartypeList[i] =='INTEGER':
                    try:
                        newDictionary[varindexList[i] ]          =  int(var)
                    except:
                        var = str(var)
                        newDictionary[varindexList[i] ]          =  var.strip()
                        
                elif vartypeList[i] =='BOOLEAN':
                    newDictionary[varindexList[i] ]          =  var
                
                elif vartypeList[i] =='SPACE_DELIMITED':
                    if type(var) == float  :
                        var_list = [int(var)]
                        newDictionary[varindexList[i] ] = var_list

                    else:
                        newDictionary[varindexList[i] ]          =  str(var).split(' ')
                        
            sheetVars.append(newDictionary)

    return sheetVars
    
def LoadTemplate(device) :
    # jinja template object
    template_dir =r'C:\Users\ZCONINGFORD\Documents\Projects\ComBat\templates'
    
    templateLoader = jinja2.FileSystemLoader( searchpath=template_dir)
    templateEnv = jinja2.Environment( loader=templateLoader )
    # load template
    # print(device),
    TEMPLATE = device
    template = templateEnv.get_template( TEMPLATE )
    
    return template
    
def WriteConfig(snip, config_file):
    # make dir path if it doesnt already exist
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    f = open(config_file, "w")
    for line in snip.split('\n') :
        # if line is not empty write it to file
        if line.strip() != "":
            f.write(line + '\n')
    f.close()
    
if __name__ == '__main__':
    
#    PROJECT_DIRS = os.path.expanduser('~') + "/Documents/Projects/"

    parser = argparse.ArgumentParser(description='make some configs.')
    parser.add_argument('path', nargs=1, help='dir of the main.xlsx file')
    parser.add_argument('--make', action='store_true', default=False,  help='make conifg')
    
    parser.add_argument('--pull', action='store_true', default=False,  help='pull running conifg')
    
    

    parser.add_argument('--push', action='store_true', default=False,  help='push conifg')
    
    args = parser.parse_args()
#    PROJECT = str(args.path[0])
    PROJECT_DIR = str(args.path[0])
    project_workbook = {}

    PROJECT_WORKBOOK = PullWorkbook(PROJECT_DIR, "main.xlsx" )
    for sheet in PROJECT_WORKBOOK.sheet_names() :
        project_workbook[sheet] = PullSheetVars(PROJECT_WORKBOOK.sheet_by_name(sheet))
    project_workbook['data_global'] = PullGlobalVars(PROJECT_WORKBOOK.sheet_by_name('data_global'))

    
    if args.make == True :
        print('{:15}{:25}{:25}'.format("device name", "template fille", "input file"))
        print("+--------------------------------------------------------------+")
        for device in project_workbook['MAKE'] :

            #print(PROJECT_DIR, "/INPUT/" + device['data_file'])
            device_workbook = PullWorkbook(PROJECT_DIR, "INPUT/" + device['data_file'] )
            sheet_vars = {}
            
            # extract data from workbook
            for sheet in device_workbook.sheet_names() :
                sheet_vars[sheet] = PullSheetVars(device_workbook.sheet_by_name(sheet))
            #set global vars
            
            
            sheet_vars['data_global'] = PullGlobalVars(device_workbook.sheet_by_name('data_global'))
            
            sheet_vars['data_global']['site_prefix'] = project_workbook['data_global']['site_prefix']
            
            device['workbook_data']= sheet_vars
                    
            print('{:15}{:25}{:25}'.format(device['device'],device['template_file'], device['data_file']))
    
            template = LoadTemplate( device['template_file'] )
            Snip = template.render(**sheet_vars)
            
            CONFIG_FILE  = PROJECT_DIR + "/MAKE/" + device['device'] + ".txt"
            WriteConfig(Snip , CONFIG_FILE)
        
    if args.pull == True :
        print('{:35}{:15}'.format("device name", "IP"))
        print("+--------------------------------------------------------------+")
        
        for device in project_workbook['MAKE'] :
            print('{:35}{:15}'.format(device['device'], device['ip']))
        
        

            devices = {
            'device_type': device['device_type'],
            'ip': device['ip'],
            'username': device['username'],
            'password': device['password'],
            }
            
            net_connect = netmiko.ConnectHandler(**devices)
            
            
            
            if device['device_type'] == "fortinet" :
                output = net_connect.send_command_timing('config vdom', delay_factor=4)
                output = net_connect.send_command_timing('edit ' + device['vslice'] , delay_factor=4)
                output = net_connect.send_command('show ')
            
            
            Pull_FILE  = PROJECT_DIR + "/PULL/" + device['device'] + datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S") + ".txt"
            WriteConfig(output , Pull_FILE)
        
        

        
        
        wait = input("PRESS ENTER TO CONTINUE.")


        
    if args.push == True :
        print('{:35}{:15}'.format("device name", "IP"))
        print("+--------------------------------------------------------------+")
        
        for device in project_workbook['MAKE'] :
            print('{:35}{:15}'.format(device['device'], device['ip']))
        
        

            devices = {
            'device_type': device['device_type'],
            'ip': device['ip'],
            'username': device['username'],
            'password': device['password'],
            }
            
            CONFIG_FILE  = PROJECT_DIR + "/MAKE/" + device['device'] + ".txt"
            
            # confirm
            wait = input("YOU ARE ABOUT TO PUSH CHANGES !!! PRESS ENTER TO CONTINUE.")
            
            net_connect = netmiko.ConnectHandler(**devices)
            
            
            
            if device['device_type'] == "fortinet" :
                output = net_connect.send_command_timing('config vdom', delay_factor=4)
                output = net_connect.send_command_timing('edit ' + device['vslice'] , delay_factor=4)
                
                            
                print(net_connect.find_prompt())
                output = net_connect.send_config_from_file(CONFIG_FILE)
                print(output)
                        

        
                PUSH_LOG_FILE  = PROJECT_DIR + "/PUSH/" + device['device'] + datetime.datetime.now().strftime(" %Y-%m-%d %H.%M.%S") + ".txt"
                WriteConfig(output , PUSH_LOG_FILE )
            
            
            
        

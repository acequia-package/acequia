

import acequia as aq


if __name__ == '__main__':


    if 1: 

        filepath = r'.\testdata\hydromonitor\hydromonitor_testdata.csv'
        jsondir = r'.\output\json\\'

        print('Test HydroMonitor.from_csv')
        hm = aq.HydroMonitor.from_csv(filepath=filepath)

        print('Test HydroMonitor.to_list')
        mylist = hm.to_list()        

        print('Test HydroMonitor.generator')
        for (loc,fil),data in hm.generator():
            gw = hm.get_series(sr=data,loc=loc,fil=fil)
            gw.to_json(jsondir)

        print('Test HydroMonitor.to_json')
        hm.to_json(jsondir)


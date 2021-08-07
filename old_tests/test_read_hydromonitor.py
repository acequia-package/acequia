

import acequia as aq


if __name__ == '__main__':


    if 1: 

        filepath = r'.\testdata\hydromonitor\hydromonitor_testdata.csv'
        jsondir = r'.\output\json\\'

        print('Test HydroMonitor.from_csv(<filename>)')
        hm = aq.HydroMonitor.from_csv(filepath=filepath)

        print('Test HydroMonitor.to_list()')
        mylist = hm.to_list()        

        print('Test HydroMonitor.iterseries()')
        for (loc,fil),data in hm.iterdata():
            gw = hm.get_series(data=data,loc=loc,fil=fil)
            gw.to_json(jsondir)

        print('Test HydroMonitor.to_json(<filedir>)')
        hm.to_json(jsondir)

        print('Test hm.iterseries')
        itr = hm.iterdata()
        for i in range(len(hm)):
            (loc,fil),data = next(itr)
            print(loc,fil)

        print('Test next(hm)')
        for i in range(len(hm)):
            gw = next(hm)
            print(gw)


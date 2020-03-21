

import acequia as aq


if __name__ == '__main__':


    if 1: 



        path = r'.\testdata\hydromonitor\hydromonitor_testdata.csv'
        hm = aq.HydroMonitor.from_csv(filepath=path)
        mylist = hm.to_list()        
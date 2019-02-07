import pandas as pd
import numpy as np
import linecache
from . import data_converters

class GroupedData:

    def __init__(self, dataset, groups_metadata):
        self.groups = []
        self.groups_metadata = groups_metadata
        for item in groups_metadata:
            group_ids = item[1]
            group_data = dataset[dataset.index.isin(group_ids)]
            self.groups.append(pd.DataFrame(group_data))

    def save_to_file(self):
        file = open(self.fname, "w")
        for group in self.groups:
            file.write(group.to_json(orient='table'))
            file.write('\n')
        file.close()

    def load_from_file(self, group_id):
        line = linecache.getline(self.fname, group_id+1)
        return data_converters.table_to_df(line)

    def set_fname(self, fname):
        self.fname = fname

    def get_fname(self):
        return self.fname

# dataset = pd.DataFrame(np.random.randint(0,100,size=(100, 4)), columns=list('ABCD'))
# groups_meta = [[0, [1,2,3,4,5,6,7]], [1, [9,10,11]]]
#
# gr = GroupedData(dataset, groups_meta)
# gr.save_to_file("test.txt")
# print(gr.load_from_file("test.txt", 0))
import pandas as pd
import linecache
from . import data_converters
import os
from django.conf import settings

class GroupedData:
    def __init__(self):
        pass

    def get_groups(self, dataset, groups_metadata):
        self.groups = []
        self.groups_metadata = groups_metadata
        for item in groups_metadata:
            group_ids = item[1]
            group_data = dataset[dataset.index.isin(group_ids)]
            self.groups.append(pd.DataFrame(group_data))

    def save_to_file(self):
        """
        Each data group, generated after k-means clustering, has unique cluster ID.
        If the number of clusters is 200, then the IDs of groups will be in range of 0 - 199. 
        All groups are saved, sorted by group ID. 
        Each group is saved in file line by line, in accordance with group ID. 
        :return: 
        """
        file = open(os.path.join(settings.MEDIA_ROOT, self.dsID, self.filename+'.groups'), "w")
        for group in self.groups:
            file.write(group.to_json(orient='table'))
            file.write('\n')
        file.close()

    def load_from_file(self, group_id):
        """
        To search the group in file by the group ID the exact line is extracted. 
        :param fname: 
        :param group_id: 
        :return: 
        """
        line = linecache.getline(os.path.join(settings.MEDIA_ROOT, self.dsID, self.filename), group_id+1)
        return data_converters.table_to_df(line)

    def set_dsID(self, dsID):
        self.dsID = dsID

    def get_dsID(self):
        return self.dsID

    def set_filename(self, filename):
        self.filename = filename

    def get_filename(self):
        return self.filename

        # dataset = pd.DataFrame(np.random.randint(0,100,size=(100, 4)), columns=list('ABCD'))
        # groups_meta = [[0, [1,2,3,4,5,6,7]], [1, [9,10,11]]]
        #
        # gr = GroupedData(dataset, groups_meta)
        # gr.save_to_file("test.txt")
        # print(gr.load_from_file("test.txt", 0))

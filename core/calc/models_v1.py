from django.db import models
from . import baseoperationclass
from . import operationshistory


class DataSampleModel(models.Model):
    base_dataset = models.ForeignKey(DataSampleModel, blank=False, null=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=45, blank=True, null=True, default="")
    description = models.TextField(blank=True, null=True, default=None)
    index_name = models.CharField(max_length=45, blank=True, null=False, default="")
    num_columns = models.IntegerField(default=1)
    num_rows = models.IntegerField(default=1)
    data_real = models.TextField(blank=False, null=False)
    data_norm = models.TextField(blank=True, null=True, default=True)
    statistics_real = models.TextField(blank=True, null=True, default=True)
    statistics_norm = models.TextField(blank=True, null=True, default=True)
    class Meta:
       managed = False
       db_table = 'data_sample'
    @staticmethod
    def from_dataframe(data_real, data_norm, stats_real, stats_norm):
        return DataSampleModel.objects.create(data_real=data_real, data_norm=data_norm, statistics_real=stats_real,
                                           statistics_norm=stats_norm)

    def to_dataframe(self):
        return self.data_real, self.data_norm, self.statistics_real, self.statistics_norm


class HistoryModel(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    userid = models.IntegerField(null=False)
    class Meta:
       managed = False
       db_table = 'history'


class BaseOperationModel(models.Model):
    operation_type = models.CharField(max_length=45)
    createdon = models.DateTimeField(auto_now_add=True)
    target_dataset = models.ForeignKey(DataSampleModel, blank=False, null=False, on_delete=models.CASCADE)
    operation_history = models.ManyToManyField(HistoryModel, through=OperationInHistory)
    class Meta:
       managed = False
       db_table = 'operations'


class OperationInHistory(models.Model):
    operation = models.ForeignKey(BaseOperationModel, on_delete=models.CASCADE)
    history = models.ForeignKey(HistoryModel, on_dalete=models.CASCADE)
    parent_operation = models.ForeignKey(OperationInHistory, null=True, default=True, on_delete=models.CASCADE)
    order = models.IntegerField(null=False)
    class Meta:
       managed = False
       db_table = 'operations_history'

class DirectOperationModel(BaseOperationModel):
    parameters = models.TextField(null=False, blank=True, default="")
    chosen_features = models.TextField(null=False, blank=True, default="")
    results = models.TextField(null=False, blank=True, default="")
    binary_pandas = models.BinaryField(null=True)
    class Meta:
       managed = False
       db_table = 'direct_operation'


class ChangeDataSampleOperation(BaseOperationModel):
    parameters = models.TextField(null=False, blank=True, default="")
    value = models.CharField(max_length=45, blank=True, default="")
    features = models.TextField(blank=True, default="")
    agregated_dataset = models.ForeignKey(DataSampleModel, on_delete=models.CASCADE, null=True)
    groups = models.ManyToManyField(DataSampleModel, through=OutputGroups)
    class Meta:
       managed = False
       db_table = 'change_datasample_operation'


class OutputGroups(models.Model):
    group = models.ForeignKey(DataSampleModel, null=False, on_delete=models.CASCADE)
    operation = models.ForeignKey(ChangeDataSampleOperation, null=False, on_delete=models.CASCADE)
    group_metadata = models.TextField(null=True, blank=True)
    class Meta:
       managed = False
       db_table = 'output_groups'
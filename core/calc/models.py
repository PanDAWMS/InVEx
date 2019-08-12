from django.db import models
from django.contrib.postgres.fields import JSONField

from . import baseoperationclass
from . import operationshistory


class DataSampleModel(models.Model):
    data_sample_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45, blank=True, null=True, default="")
    description = models.CharField(max_length=45, blank=True, null=True, default="")
    index_name = models.CharField(max_length=45, blank=True, null=True, default="")
    num_columns = models.IntegerField(default=1, null=True)
    num_rows = models.IntegerField(default=1, null=True)
    data_real = models.BinaryField(blank=False, null=True)
    data_norm = models.BinaryField(blank=False, null=True)
    statistics_real = models.BinaryField(blank=False, null=True)
    statistics_norm = models.BinaryField(blank=False, null=True)
    class Meta:
       db_table = 'data_sample'
    @staticmethod
    def from_dataframe(data_real, data_norm, stats_real, stats_norm):
        return DataSampleModel.objects.create(data_real=data_real, data_norm=data_norm, statistics_real=stats_real,
                                           statistics_norm=stats_norm)

    def to_dataframe(self):
        return self.data_real, self.data_norm, self.statistics_real, self.statistics_norm

class BaseOperationModel(models.Model):
    operation_id = models.AutoField(primary_key=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    input_data_sample_id = models.ForeignKey(DataSampleModel, blank=False, null=True, on_delete=models.CASCADE)
    class Meta:
       db_table = 'operations'

class GroupingOperationModel(models.Model):
    grouping_operation_id = models.AutoField(primary_key=True)
    grouping_type = models.CharField(max_length=45, blank=True, null=True, default="")
    grouping_value = models.CharField(max_length=45, blank=True, null=True, default="")
    grouping_features = models.BinaryField(blank=False, null=True)
    operation_id = models.ForeignKey(BaseOperationModel, null=True, on_delete=models.Case)
    output_data_sample_id = models.ForeignKey(DataSampleModel, null=True, on_delete=models.CASCADE)
    class Meta:
       db_table = 'grouping_operation'

class OutputGroups(models.Model):
    outpur_group_id = models.AutoField(primary_key=True)
    output_group_name = models.CharField(max_length=45, null=True)
    data_sample_id = models.ForeignKey(DataSampleModel, null=True, on_delete=models.CASCADE)
    grouping_operation_id = models.ForeignKey(GroupingOperationModel, null=True, on_delete=models.CASCADE)
    class Meta:
       db_table = 'output_groups'

class DirectOperationModel(models.Model):
    direct_operation_id = models.AutoField(primary_key=True)
    operation_id = models.ForeignKey(BaseOperationModel, null=True, on_delete=models.CASCADE)
    operation_type = models.CharField(max_length=45, blank=True, null=True, default="")
    parametres = JSONField()
    results = JSONField()
    pandas_binary = JSONField()
    selected_features = models.CharField(max_length=45, blank=True, null=True, default="")
    class Meta:
       db_table = 'direct_operation'

class HistoryModel(models.Model):
    history_id = models.AutoField(primary_key=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    userid = models.CharField(max_length=45, null=True)
    class Meta:
       db_table = 'history'

class OperationInHistory(models.Model):
    operation_history_id = models.AutoField(primary_key=True)
    operation_id = models.ForeignKey(BaseOperationModel , null=True, on_delete=models.CASCADE)
    history = models.ForeignKey(HistoryModel, null=True, on_delete=models.CASCADE)
    parent_operation_id = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)
    class Meta:
       db_table = 'operations_history'




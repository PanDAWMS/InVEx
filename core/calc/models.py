from django.db import models
from . import baseoperationclass
from . import operationhistory


class DatasetModel(models.Model):
    base_dataset = models.ForeignKey(DatasetModel, blank=False, null=False, on_delete=models.CASCADE)
    data_real = models.TextField(blank=False, null=False)
    data_norm = models.TextField(blank=False, null=False)
    statistics_real = models.TextField(blank=False, null=False)
    statistics_norm = models.TextField(blank=False, null=False)

    @staticmethod
    def from_dataframe(data_real, data_norm, stats_real, stats_norm):
        return DatasetModel.objects.create(data_real=data_real, data_norm=data_norm, statistics_real=stats_real,
                                           statistics_norm=stats_norm)

    def to_dataframe(self):
        return self.data_real, self.data_norm, self.statistics_real, self.statistics_norm


class OperationHistoryModel(models.Model):
    base_dataset = models.ForeignKey(DatasetModel, blank=False, null=False, on_delete=models.CASCADE)


class BaseOperationModel(models.Model):
    target_dataset = models.ForeignKey(DatasetModel, blank=False, null=False, on_delete=models.CASCADE)
    operation_history = models.ManyToManyField(OperationHistoryModel, through=OperationInHistory)


class OperationInHistory(models.Model):
    operation = models.ForeignKey(BaseOperationModel, on_delete=models.CASCADE)
    history = models.ForeignKey(OperationHistoryModel, on_dalete=models.CASCADE)
    order = models.IntegerField(null=False)


class OperationWithDataset(BaseOperationModel):
    parameters = models.TextField(null=False, blank=True, default="")
    results = models.TextField(null=False, blank=True, default="")
    binary_pandas = models.BinaryField(null=True)


class GroupingOperationModel(BaseOperationModel):
    parameters = models.TextField(null=False, blank=True, default="")
    binary_pandas = models.BinaryField(null=True)
    groups = models.ManyToManyField(DatasetModel, through=OutputGroups)


class OutputGroups(models.Model):
    group = models.ForeignKey(DatasetModel, null=False, on_delete=models.CASCADE)
    operation = models.ForeignKey(GroupingOperationModel, null=False, on_delete=models.CASCADE)
    group_metadata = models.TextField(null=True, blank=True)

from abc import ABC, abstractmethod

from apps.datasets.models import Dataset
from lib.bigquery import ibis_client


class Node(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_query(self):
        pass


class Input(Node):
    def __init__(self, dataset):
        self.dataset = dataset

    def get_query(self):
        dataset = Dataset.objects.get(pk=int(self.dataset))
        conn = ibis_client()
        return conn.table(dataset.table_id)


NODE_FROM_CONFIG = {"input": Input}

from abc import ABC, abstractmethod

from apps.datasets.models import Dataset
from lib.bigquery import ibis_client


class Node(ABC):
    def __init__(self, node):
        self.node = node

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


def get_input_query(node):
    conn = ibis_client()
    return conn.table(node._input_dataset.table_id)


NODE_FROM_CONFIG = {"input": get_input_query}

from abc import ABC, abstractmethod

from apps.datasets.models import Dataset


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
        # TODO: add path to dataset for now hardcoded here
        path = "google_sheets_142f9521_ffbd_47e1_be92_d34995bd16a1.sheets_table"

        return f"select * from {self.dataset}"


NODE_FROM_CONFIG = {"input": Input}

from elasticsearch import Elasticsearch
import pandas as pd


class Politicians:
    def __init__(self, hosts="http://127.0.0.1:9200"):
        self.__es = Elasticsearch(hosts=hosts)

    def load_cantons(self):
        # TODO: Store cantonName as keyword to make aggregation on elasticserach
        politicians = self.load_politicians()
        cantons = list(politicians["_source.cantonName"].unique())
        cantons.sort()
        return cantons

    def load_parties(self, canton_filter=None):
        # TODO: Store cantonName as keyword to make aggregation on elasticserach
        politicians = self.load_politicians(canton_filter=canton_filter)
        parties = list(politicians["_source.party"].unique())
        parties.sort()
        return parties

    def load_politicians(self, party_filter=None, canton_filter=None, group_small_parties=True):
        query = {
            "bool": {
                "must": [
                    {"exists": {"field": "party"}},
                    {"match": {"active": "true"}}
                ],
            }}
        if canton_filter is not None:
            query["bool"]["must"].append({"match": {"cantonName": canton_filter}})
        res = self.__es.search(query=query, index="parliament.politicians", size=1000)
        data = pd.json_normalize(res["hits"]["hits"])
        if group_small_parties:
            others_party_list = list(data["_source.party"].value_counts()[data["_source.party"].value_counts() < (data.shape[0] * 0.05)].index)
            data.loc[data["_source.party"].isin(others_party_list), "_source.party"] = "Sonstige"

        if party_filter is not None and len(party_filter) > 0:
            data = data[data["_source.party"].isin(party_filter)]
        return data

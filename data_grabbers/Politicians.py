from elasticsearch import Elasticsearch
import elasticsearch.helpers
import requests
import time
from tqdm import tqdm


def fetch_politician(politician_id: int, language: str = "de"):
    url = f"http://ws-old.parlament.ch/councillors/{politician_id}?lang={language}&format=json"
    try:
        r = requests.get(url, headers={"Accept": "text/json"}, timeout=3)
    except requests.exceptions.ReadTimeout:
        return None
    if r.ok:
        return r.json()
    else:
        return None


def fetch_and_upload(retries: int = 3, language: str = "de", entry_date: str = "2019/10/20",
                     index="parliament.politicians"):
    json_list = []
    page_counter = 1
    print("LISTING ALL POLITICIANS")
    while True:
        print(".", end="")
        url = f"http://ws-old.parlament.ch/councillors?entryDateFilter={entry_date}&lang={language}" \
              f"&pageNumber={page_counter}&format=json"
        r = requests.get(url, headers={"Accept": "text/json"})

        if not r.ok:
            break

        json_list.extend(r.json())

        page_counter += 1
        time.sleep(0.5)
    print("\nPOLITICIANS LOADED")

    politicians = []
    for politician in tqdm(json_list, desc=f"Fetching detail information"):
        politician_json = None
        trials = 0
        while politician_json is None and trials < retries:
            politician_json = fetch_politician(politician['id'])
            trials += 1
            time.sleep(0.5)

        if politician_json is not None:
            politician_json["_id"] = f"{politician['id']}.{politician['updated']}"
            politician_json["_op_type"] = "create"
            politician_json["_index"] = index
            politicians.append(politician_json)
        else:
            print(f"Error: {politician['id']} could not be loaded")

    es = Elasticsearch(hosts="http://127.0.0.1:9200")

    elasticsearch.helpers.bulk(es, politicians, ignore_status=(409,))

    print("FINISHED")


if __name__ == "__main__":
    fetch_and_upload()

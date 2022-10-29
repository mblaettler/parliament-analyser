from elasticsearch import Elasticsearch
import elasticsearch.helpers
import requests
import time
from tqdm import tqdm


def fetch_affair(affair_id: int, language: str = "de"):
    url = f"http://ws-old.parlament.ch/affairs/{affair_id}?lang={language}&format=json"
    try:
        r = requests.get(url, headers={"Accept": "text/json"}, timeout=3)
    except requests.exceptions.ReadTimeout:
        return None
    if r.ok:
        return r.json()
    else:
        return None


def fetch_and_upload(retries: int = 3, language: str = "de", legislative_period: int = 51,
                     index="parliament.affairs"):
    json_list = []
    page_counter = 1
    print("LISTING ALL AFFAIRS")
    while True:
        print(".", end="")
        url = f"http://ws-old.parlament.ch/votes/affairs?legislativePeriodFilter={legislative_period}&lang={language}" \
              f"&pageNumber={page_counter}&format=json"
        r = requests.get(url, headers={"Accept": "text/json"}, timeout=20)

        if not r.ok:
            print(f"Error on page {page_counter}")
            break

        json_list.extend(r.json())

        page_counter += 1
        time.sleep(0.5)
    print("\nAFFAIRS LOADED")

    affairs = []
    for affair in tqdm(json_list, desc=f"Fetching detail information"):
        affair_json = None
        trials = 0
        while affair_json is None and trials < retries:
            affair_json = fetch_affair(affair['id'])
            trials += 1
            time.sleep(0.5)

        if affair_json is not None:
            affair_json["_id"] = f"{affair['id']}.{affair['updated']}"
            affair_json["_op_type"] = "create"
            affair_json["_index"] = index
            affairs.append(affair_json)
        else:
            print(f"Error: {affair['id']} could not be loaded")

    es = Elasticsearch(hosts="http://127.0.0.1:9200")

    elasticsearch.helpers.bulk(es, affairs, ignore_status=(409,))

    print("FINISHED")


if __name__ == "__main__":
    fetch_and_upload()

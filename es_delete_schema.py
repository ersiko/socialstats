import elasticsearch
from elasticsearch.exceptions import NotFoundError

es = elasticsearch.Elasticsearch()
indices = [ "igusers", "ourusers", "pics", "userdaily", "picsdaily" ]

for index in indices:
    try:
        es.indices.delete(index = index)
    except elasticsearch.exceptions.NotFoundError:
        print(index + " doesn't exist. Continuing...")
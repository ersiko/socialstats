import elasticsearch

es = elasticsearch.Elasticsearch()

igusers_settings = {
    "settings" : {
        "number_of_replicas": 0
    },
    "mappings": {
        "users": {
            "properties": {
                "private": {
                    "type": "boolean"
                },
                "followers": {
                    "type": "string"
                }
            }
        }
    }
}
es.indices.create(index = "igusers", body = igusers_settings)

ourusers_settings = {
    "settings" : {
        "number_of_replicas": 0
    },
    "mappings": {
        "users": {
            "properties": {
                "username": {
                    "type": "string"
                },
                "email": {
                    "type": "string"
                },
                "daily": {
                    "type": "boolean"
                },
                "weekly": {
                    "type": "boolean"
                },
                "monthly": {
                    "type": "boolean"
                },
            }
        }
    }
}

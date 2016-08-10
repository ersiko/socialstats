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
                "subscribed_to": {
                    "type": "string"
                }
            }
        }
    }
}

es.indices.create(index = "ourusers", body = ourusers_settings)

pics_settings = {
    "settings" : {
        "number_of_replicas": 0
    },
    "mappings": {
        "pics": {
            "properties": {
                "username": {
                    "type": "string"
                },
                "dateposted": {
                    "type": "date"
                },
                "thumbnail": {
                    "type": "string"
                },
                "fullpic": {
                    "type": "string"
                },
                "caption": {
                    "type": "string"
                }
            }
        }
    }
}
es.indices.create(index ="pics", body =pics_settings)
 
userdaily_settings = {
   "settings" : {
        "number_of_replicas": 0
    },
    "mappings": {
        "followers": {
            "properties": {
                "number": {
                    "type": "integer"
                }
            }
        },
        "following": {
            "properties": {
                "number": {
                    "type": "integer"
                }
            }
        }
    }
}

es.indices.create(index = "userdaily", body = userdaily_settings)

picsdaily_settings = {
    "settings" : {
        "number_of_replicas": 0
    },
    "mappings": {
        "likes": {
            "properties": {
                "number": {
                    "type": "integer"
                }
            }
        }
    }
}

es.indices.create(index = "picsdaily", body = picsdaily_settings)

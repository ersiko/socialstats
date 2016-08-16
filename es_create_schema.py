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
        },
        "followers_diffs": {
            "properties": {
                "1": {
                    "type": "integer"
                },
                "3": {
                    "type": "integer"
                },
                "7": {
                    "type": "integer"
                },
                "30": {
                    "type": "integer"
                },
                "90": {
                    "type": "integer"
                },
                "180": {
                    "type": "integer"
                },
                "365": {
                    "type": "integer"
                }
            }
        },
        "following_diffs": {
            "properties": {
                "1": {
                    "type": "integer"
                },
                "3": {
                    "type": "integer"
                },
                "7": {
                    "type": "integer"
                },
                "30": {
                    "type": "integer"
                },
                "90": {
                    "type": "integer"
                },
                "180": {
                    "type": "integer"
                },
                "365": {
                    "type": "integer"
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
                "1": {
                    "type": "boolean"
                },
                "3": {
                    "type": "boolean"
                },
                "7": {
                    "type": "boolean"
                },
                "30": {
                    "type": "boolean"
                },
                "90": {
                    "type": "boolean"
                },
                "180": {
                    "type": "boolean"
                },
                "365": {
                    "type": "boolean"
                },
                "subscribed_to": {
                    "type": "string"
                }
            }
        },
        "last_updated": {
            "properties": {
                "date1": {
                    "type": "date"
                },
                "date3": {
                    "type": "date"
                },
                "date7": {
                    "type": "date"
                },
                "date30": {
                    "type": "date"
                },
                "date90": {
                    "type": "date"
                },
                "date180": {
                    "type": "date"
                },
                "date365": {
                    "type": "date"
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
        },
        "likes_diffs": {
            "properties": {
                "1": {
                    "type": "integer"
                },
                "3": {
                    "type": "integer"
                },
                "7": {
                    "type": "integer"
                },
                "30": {
                    "type": "integer"
                },
                "90": {
                    "type": "integer"
                },
                "180": {
                    "type": "integer"
                },
                "365": {
                    "type": "integer"
                }
            }
        }

    }
}
es.indices.create(index ="pics", body=pics_settings)

userdaily_settings = {
    "template": "userdaily-*",
    "settings" : {
        "number_of_replicas": 0
    },
    "mappings": {
        "follows": {
            "properties": {
                "followers": {
                    "type": "integer"
                },
                "following": {
                    "type": "integer"
                }
            }
        }
    }
}

es.indices.put_template("userdaily", body = userdaily_settings)

picsdaily_settings = {
    "template": "picsdaily-*",
    "settings" : {
        "number_of_replicas": 0
    },
    "mappings": {
        "likes": {
            "properties": {
                "number": {
                    "type": "integer"
                },
                "timestamp": {
                    "type": "date"
                }
            }
        }
    }
}

es.indices.put_template("picsdaily", body = picsdaily_settings)

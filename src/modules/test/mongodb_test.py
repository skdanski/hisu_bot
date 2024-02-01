from mongodb import mongodb_util
from util import config

configuration = config.Config()

uri = configuration.mongodb_uri
api_version = configuration.mongodb_api_version

test_results_list = []

# test 1
client = mongodb_util.createClient(uri, api_version)
if client != None:
   test_results_list.append("test 1: createClient() passed")
else:
    test_results_list.append("test 1: createClient() failed")
    exit

mongodb_util.client_ping(client=client)

test_db = client.test_db
test_collection = test_db.test
test_collection.drop()

recipe_documents = [{ "name": "elotes", "ingredients": ["corn", "mayonnaise", "cotija cheese", "sour cream", "lime"], "prep_time": 35 },
                    { "name": "loco moco", "ingredients": ["ground beef", "butter", "onion", "egg", "bread bun", "mushrooms"], "prep_time": 54 },
                    { "name": "patatas bravas", "ingredients": ["potato", "tomato", "olive oil", "onion", "garlic", "paprika"], "prep_time": 80 },
                    { "name": "fried rice", "ingredients": ["rice", "soy sauce", "egg", "onion", "pea", "carrot", "sesame oil"], "prep_time": 40 }]
mongodb_util.insert_into_collection(test_collection, recipe_documents)
if mongodb_util.get_document_count(test_collection, {}) == 4:
    test_results_list.append("test 2: insert_into_collection() passed")
else:
    test_results_list.append("test 2: insert_into_collection() failed")

doc_found = mongodb_util.document_exist(test_collection, { "name": "berto fried rice"})
if doc_found == False:
    test_results_list.append("test 3: document_exist() passed")
else:
    test_results_list.append("test 3: document_exist() failed")

doc_list = mongodb_util.get_documents(test_collection, { "name": "elotes"})
if len(doc_list) == 1:
    test_results_list.append("test 3b: get_documents() passed")
else:
    test_results_list.append("test 3b: get_documents() failed")

doc_list = mongodb_util.get_documents(test_collection, {})
if len(doc_list) == 4:
    test_results_list.append("test 3c: get_documents() passed")
else:
    test_results_list.append("test 3c: get_documents() failed")
    
mongodb_util.update_document(test_collection, {"ingredients": "potato"}, {"$set": { "prep_time": 72 }}, True, True)
found_doc = mongodb_util.document_exist(test_collection, { "prep_time": 72 })
if found_doc:
    test_results_list.append("test 4: update_document() passed")
else:
    test_results_list.append("test 4: update_document() failed")

updated_list = mongodb_util.update_many_documents(test_collection, {"ingredients": "onion"}, {"$set": { "prep_time": 30 }})
if updated_list != None and updated_list.matched_count == 3:
    test_results_list.append("test 5: update_many_documents() passed")
else:
    test_results_list.append("test 5: update_many_documents() failed")

deleted_doc = mongodb_util.delete_document(test_collection, { "name": "berto fried rice"})
deleted_doc_2 = mongodb_util.delete_document(test_collection, { "name": "patatas bravas"})
if deleted_doc == None and deleted_doc_2 != None:
    test_results_list.append("test 6: delete_document() passed")
else:
    test_results_list.append("test 6: delete_document() failed")

deleted_doc_list = mongodb_util.delete_many_documents(test_collection, {"name": "patatas bravas"})
deleted_doc_list_2 = mongodb_util.delete_many_documents(test_collection, {"name": "fried rice"})
if deleted_doc_list.deleted_count == 0 and deleted_doc_list_2.deleted_count == 1:
    test_results_list.append("test 7: delete_many_documents() passed")
else:
    test_results_list.append("test 7: delete_many_documents() failed")    

test_collection.drop()
count = mongodb_util.get_document_count(test_collection, {})
if count == 0:
    test_results_list.append("test 8: get_document_count() passed")
else:
    test_results_list.append("test 8: get_document_count() failed")

for r in test_results_list:
    print(r + '\n')


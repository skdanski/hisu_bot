
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import *

from util import logger as log

logger = log.Logger('mongodb_util', 'mongogdb_util_logger')

'''
util functions that interacts with the mongodb
'''

'''
createClient creates mongodb client

:uri: string
:api: version number as string
:return: MongoClient
'''
def createClient(uri, api_version) -> MongoClient:
    try:
        logger.info('createClient', 'creating MongoDB client: ' + uri + ', ' + api_version)
        return MongoClient(uri, server_api=ServerApi(api_version))
    except pymongo.errors.ConfigurationError:
        logger.error('createClient', 'An Invalid URI host error was received. Is your Atlas host name correct in your connection string?')
        return None

'''
client_ping pings MonogoDB on successful connection

:client: MonogClient
:return: None
'''
def client_ping(client=MongoClient) -> None:
    try:
        client.admin.command('ping')
        logger.info('client_ping', 'Pinged your deployment. You successfully connected to MongoDB!')
    except Exception as e:
        logger.error('client_ping', str(e))

'''
document_exist finds out if a document exist in given collection given json filter

:collection: pymongo.collection.Collection
:filter: json of document filter
return: true if a document matches the filter, false otherwise
'''
def document_exist(collection, filter) -> bool:
    try:
        doc = collection.find_one(filter)
        logger.debug('document_exist', 'filter: ' + str(filter) + ', doc: ' + str(doc))
    except Exception as e:
        logger.error('document_exist', str(e))
    
    if doc is not None:
        return True
    else:
        return False

'''
get_documents gets list of document matching filter

:collection: pymongo.collection.Collection
:filter: json of document filter
return: return list of document matching filter
'''
def get_documents(collection, filter) -> list[any]:
    results = None
    try: 
        results = [ doc for doc in collection.find(filter)]
        logger.debug('get_documents', 'filter: ' + str(filter) + ', results: ' + str(results))
    except Exception as e:
        logger.error('get_documents', str(e))
    return results
    

'''
insert_into_collection adds new documents to collection

:collection: the collection to insert documents
:documents: list of documents to insert into collection
:return: results of insert
'''
def insert_into_collection(collection, documents) -> pymongo.results.InsertManyResult:
    result = None
    try:
        result = collection.insert_many(documents)
        logger.debug('insert_into_collection', 'documents: ' + str(documents) + ', result: ' + str(result))
    except Exception as e:
        logger.error('insert_into_collection', str(e))
    else:
        inserted_count = len(result.inserted_ids)
    return result

'''
update_document matches json filter with a document in collection and updates its data

:collection: pymongo.collection.Collection
:filter: json filter to search collection with
:update_data: json of fields/values to replace/add
:get_updated_doc: bool if find_one_and_update returns orginal document before updated or the update document itself
:upsert: bool; When True, inserts a new document if no document matches the query. Defaults to False.
:return: updated document or the found document before update
'''
def update_document(collection, filter, update_data, get_updated_doc, upsert) -> list[any]:
    doc = None
    try:
        doc = collection.find_one_and_update(filter, update_data, new=get_updated_doc, upsert=upsert)
        logger.debug('update_document', 'filter: ' + str(filter) + 'update_data: ' + str(update_data) + 'get_updated_doc: ' + str(get_updated_doc) + ', doc: ' + str(doc))
    except Exception as e:
        logger.error('update_document', str(e))
    return doc

'''
update_document matches json filter with a document in collection and updates its data

:collection: pymongo.collection.Collection
:filter: json filter to search collection with
:update_data: json of fields/values to replace/add
:get_updated_doc: bool if find_one_and_update returns orginal document before updated or the update document itself
:return: updated document or the found document before update
'''
def update_many_documents(collection, filter, update_data) -> pymongo.results.UpdateResult:
    updated_doc_list = None
    try:
        updated_doc_list = collection.update_many(filter, update_data)
        logger.debug('update_many_documents', 'filter: ' + str(filter) + ', update_data: ' + str(update_data) +', updated_doc_list: ' + str(updated_doc_list))
    except Exception as e:
        logger.error('update_many_documents', str(e))
    return updated_doc_list

'''
delete_document matches json filter with a document in collection and deletes it

:collection: pymongo.collection.Collection
:filter: json filter to search collection with
:return: the deleted document
'''
def delete_document(collection, filter) -> pymongo.results.DeleteResult:
    deleted_doc = None
    try:
        deleted_doc = collection.find_one_and_delete(filter)
        logger.debug('delete_document', ' filter: ' + str(filter) + ', deleted_doc: ' + str(delete_document))
    except Exception as e:
        logger.error('delete_document', str(e))
    return deleted_doc

'''
delete_many_documents matches json filter with all documents in collection and deletes them

:collection: pymongo.collection.Collection
:filter: json filter to search collection with
:return: list of deleted documents
'''
def delete_many_documents(collection, filter) -> pymongo.results.DeleteResult:
    deleted_doc_list = None
    try:
        deleted_doc_list = collection.delete_many(filter)
        logger.debug('delete_many_documents', 'filter: ' + str(filter) + ', deleted_doc_list: ' + str(deleted_doc_list))
    except Exception as e:
        logger.error('delete_many_documents', str(e))
    return deleted_doc_list
    
'''
get_document_count gets how many documents in the collection fits the filter 

:collection: pymongo.collection.Collection
:filter: json filter to search collection with
:return: int of how many documents fits the filter
'''
def get_document_count(collection, filter) -> int: 
    count = 0
    try:
        count = collection.count_documents(filter)
        logger.debug('get_document_count', 'filter: ' + str(filter) + ', count: ' + str(count))
    except Exception as e:
        logger.error('get_document_count', str(e))
    return count

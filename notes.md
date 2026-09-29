- i add to backend docker file installation of the reranker model, but the reranker model is hardcoded in the docker file
so if you want to change the reranker model, you need to change the docker file and rebuild the image.

## TOFIX:
- should create a propre why from the data prossising to save data in the qdrant.  ( knowing taht i fix the test/test_vector_store.py to use the collection name as a temp fix)

- this opirations should not be on the test file.

- the backend should not be dependant on the other compontest to run, like qdrant, ollama, etc.  
if one of them fails, the backend should still be able to run and return an error message.  


## TODO:
- add suport to GPU users in ollama and qdrant.  
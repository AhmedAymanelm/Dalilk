
# laqtha
Hotel reservation program 
 
 ## Reqirments
 - python 3.9 or later 


# (Optional) Setup you command line interface for better readability
```bash
 export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
 ```

 ## Installion packing 
 ###  Install the required libraries
```bash
 $ pip install -r requirments.txt
```

### setup the enviroment variables

```bash
 $ cp .env.example .env
```
Set your environment variables in the `.env` file. Like `your_api_key_here` value.
 
# Run the Fast api serve 
```bash
 $ uvicorn main:app --reload --host 0.0.0.0 --port 8000   #(if 8000 not work use 5000)

```
## Warning: Handling "Address already in use" Error
### Run the following command in your terminal:
```bash
lsof -i :8000
```
### Use the command below, replacing <PID> with the actual process ID:
``` bash
kill -9 <PID>
```
### Run the Fast api serve again
```bash
 $ uvicorn main:app --reload --host 0.0.0.0 --port 8000   #(if 8000 not work use 5000)
```

- update `.env` with credentials


## endpoint Upload File 
```bash
- http://localhost:8000/api/v1/data/Upload/1
```

## endpoint process File 
```bash
- http://localhost:8000/api/v1/data/process/1
```

## postman collection 
Download the postman collection from [/Users/ahmed/BIG_RAG-1/assets/BIG RAG.postman_collection.json] 

## main.py
import uvicorn
import config

server_info = config.SERVER_CONFIG

if __name__ == "__main__":
    # uvicorn.run("app:app", host=server_info['Fastapi_host'], port=server_info['Fastapi_port'], reload=True)
    uvicorn.run("app:app", host='0.0.0.0', port=server_info['Fastapi_port'], reload=True)

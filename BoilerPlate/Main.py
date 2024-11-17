import Client
import Server
import threading
from time import sleep

def run_server() : 
    server_obj = Server.Server()
    server_obj.run_server()

def run_client() :
    client_obj = Client.Client()
    client_obj.run()

if __name__ == '__main__':
    
    server_thread = threading.Thread(target=run_server)
    client_thread = threading.Thread(target=run_client)
    server_thread.start()
    sleep(1)
    client_thread.start()

    client_thread.join()

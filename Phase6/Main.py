import Client
import Server
import threading
from datetime import datetime

packet_size = 1024

client_corruption_chance = 10
client_drop_chance = 10

server_corruption_chance = 10
server_drop_chance = 10


def run_server() : 
    server_obj = Server.Server(buffer_size=packet_size, corruption_chance=server_corruption_chance, drop_chance= server_drop_chance)
    server_thread = threading.Thread(target=server_obj.run_server)
    server_thread.run()

def run_client() :
    client_obj = Client.Client(packet_size=packet_size, corruption_chance= client_drop_chance, drop_chance= client_drop_chance)
    client_obj.run()


if __name__ == '__main__':
    
    NUM_TRIALS = 10
    avg_time_ms = 0
    for i in range (0, NUM_TRIALS):
        t0 = datetime.now()

        server_thread = threading.Thread(target=run_server)
        client_thread = threading.Thread(target=run_client)
        
        server_thread.start()
        
        client_thread.start()
        client_thread.join()
        server_thread.join()
        t1 = datetime.now()
        avg_time_ms += (t1 - t0).total_seconds() * 10 ** 3
    
    avg_time_ms = avg_time_ms / NUM_TRIALS
    print(avg_time_ms)

    # for i in range (0, 100):
    #     server_thread = threading.Thread(target=run_server)
    #     client_thread = threading.Thread(target=run_client)
        
    #     server_thread.start()
        
    #     client_thread.start()
    #     client_thread.join()
    #     print("Client_thread joined")
    #     server_thread.join()
    #     print("Server_thread joined")
    #     sys.exit(0)
    

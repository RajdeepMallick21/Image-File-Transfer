from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread

# def get_header_length(input : int) -> int:
#         return input >> 4

# #print (get_header_length(16))
# #print (get_header_length(1))

# no_queue = bytes()
# some_queue = no_queue[0:0]

# def add_none_to_bytes() -> bytes:
#         array = bytes()
#         some_data = 0
#         nothing = bytes()
#         array = some_data.to_bytes(2) + nothing
#         return array

# #print(add_none_to_bytes())

# dict = { 0 : 1}

# ret = dict.get(1)

# array_swap = [0 , 1 , 2]

# swapped = array_swap

# array_swap = [3, 4, 5]

# print(array_swap)
# print(swapped)

result = 1

flt_data = 0.0
flt_data += .1

def client_thread():
        sk1 = socket(AF_INET, SOCK_DGRAM)
        sk1_add = ('127.0.0.1', 2400)
        sk1.bind(sk1_add)
        #sk1.sendto(result.to_bytes(), ('127.0.0.1', 2500))

def server_thread():
        sk2 = socket(AF_INET, SOCK_DGRAM)
        sk2.settimeout(.0001)
        sk2_add = ('127.0.0.1', 2500)
        sk2.bind(sk2_add)
        data, address = sk2.recvfrom(1024)
        #TimeoutError
        
        print(data)
        print(address)


th1 = Thread(target=client_thread, args=[])
th2 = Thread(target=server_thread, args=[])
th2.start()
th1.start()
th2.join()
th1.join()

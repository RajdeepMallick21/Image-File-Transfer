import threading
from socket import *
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import select

from checksum_gen import generate_16bit_sent_checksum, corrupt
import common_communication

import os
import math

import Unreliable_Transport


class Client:
    
    def __init__(self, server_name : str = 'localhost', server_port : int = 12000, segment_size : int = 2048, 
                 corruption_chance : int = 0, drop_chance : int = 0, timeout : float = .001) -> None:
        # Code adapted from page 156 of Computer Networking, 8th edition by James F. Kurose and Keith W. Ross
        # Server location
        self.server_name = server_name
        self.server_port = server_port
        self.packet_modifier = Unreliable_Transport.packet_corrupter(chance_corrupted=corruption_chance, chance_dropped=drop_chance)
        # Init client location
        self.client_socket = socket(AF_INET, SOCK_DGRAM)
        #print('Inited client')
        #Number of bytes to encode into a packet
        #Accounts for header size: 1 16 bit number for Checksum, addational 16 bits for ack
        self.segment_size = segment_size
        
        #Base, packet number to send    
        self.base_lock = threading.Lock()
        self.base = 1
        
        self.next_sequence_num = 1

        #self.window_size = common_communication.WINDOW_SIZE
        self.window_size = 1
        self.message_buffer = []
        self.message_buffer_lock = threading.Lock()

        self.window_moved = threading.Event()

        self.timeout_time = timeout
        self.timedout = False
        self.stop_timer = False
        self.all_messages_acked = False

        self.check_for_timeout = threading.Event()
        self.message_event = threading.Event()
        
        self.no_packets_left = False
        self.valid_server = True


    def selectfile(self) -> str:
        #init UI
        clientWindow = Tk(baseName='Client')

        filetypes = [('bitmap files','*.bmp')]
        filename = askopenfilename(filetypes=filetypes)
        #print(filename)

        clientWindow.destroy()
        return filename

    def make_packt(self, filename) -> [bytes]:
        #open file, get number of packages needed to transfer file
        file = open(file=filename, mode="rb")
        file_size = os.stat(filename).st_size
        num_of_packets = math.ceil(file_size / self.data_size)
        #list to hold packets prior to send
        packet_list = []
        for i in range(num_of_packets):
            
            #read data from file to var
            curr_packet = file.read(self.data_size)
            packet_list.append(curr_packet)
         
        packet_list.append(common_communication.END_FILE_BYTES)
        #print("Number of packets to send is ", num_of_packets)
        return packet_list


    # return current copy of packet to be
        

    def proccess_return(self) -> None :
        #print("Client recv_worker started")
        try:
            while 1:
                # run check on socket every .001 seconds
                ready = select.select([self.client_socket], [], [], .001)
                
                if (not ready[0]):
                    if self.all_messages_acked:
                        return
                    else:
                        continue
                
                data, addr = self.client_socket.recvfrom(self.buffer_size)
                
                packet_checksum = data[common_communication.CHECKSUM_HEADER_START:common_communication.CHECKSUM_HEADER_END]
                packet_sequence = data[common_communication.CHECKSUM_HEADER_END:common_communication.ACK_HEADER_END]
                    #print("Client on corruption check")
                if (corrupt(packet_checksum, packet_sequence)) :
                    pass
                    #print("Client recieved a corrupted packet.\n" )
                else:
                    #print("Client received valid ack", packet_sequence)
                    #Iterates baseNum upon receiving valid ack
                    new_base = (int.from_bytes(packet_sequence) + 1) % common_communication.MAX_SEQUENCE_NUMBER
                    
                    #No wrap around - treat as normal
                    self.base_lock.acquire()
                    old_base = self.base
                    self.base_lock.release()
                    if (old_base < self.Rollover_Possible
                        or new_base > self.Rollover_Possible):
                        if (new_base <= old_base):
                            continue
                        
                        #remove messages from queue that are acknowledged
                        #Cummalitive ack
                        self.message_buffer_lock.acquire()
                        del self.message_buffer [:new_base - old_base]
                        self.message_buffer_lock.release()

                        self.base_lock.acquire()
                        self.base = new_base
                        self.base_lock.release()

                        self.check_for_timeout.set() 
                        self.window_moved.set()
                        #print("Client received packet with basenumber " + str(new_base))
                    #Garenteed wrap around - do not treat as normal, but do incement base
                    else:
                        elments_untill_end = common_communication.MAX_SEQUENCE_NUMBER - old_base
                        new_message_start = elments_untill_end + new_base
                        self.message_buffer_lock.acquire()
                        del self.message_buffer[:new_message_start]
                        self.message_buffer_lock.release()
                        
                        self.base_lock.acquire()
                        self.base = new_base
                        self.base_lock.release()

                        self.check_for_timeout.set() 
                        self.window_moved.set()
                       #print("Client received packet with basenumber " + str(new_base))

                    if(new_base == self.next_sequence_num):
                        self.stop_timer = True
                        
                        #print("Client is stopping timer for a bit")
                        #print("Client Base: " + str(self.base))
                        #print("Client Sequnce Num: " + str(self.next_sequence_num))
        except OSError:
            # Server can shutdown before sending ack signal correctly to client.
            # If this is the case, an exception can be raised and the function should return.
            #print ("CLIENT CONNECTIION CRASHED")
            self.valid_server = False
            return

    def timeout(self) -> None:
        #timedout works in recv_ack_worker thread to stop message gathering
        self.timedout = True
        self.check_for_timeout.set()

    def timeout_handler(self) -> None:

        recv_worker = threading.Thread(target=self.recv_ack_worker, args=[])
        recv_worker.start()

        while (not self.all_messages_acked):

            if (self.no_packets_left and len(self.message_buffer) == 0 or not self.valid_server):
                self.all_messages_acked = True
                recv_worker.join()
                return
            
            elif (len (self.message_buffer) == 0):
                #Wait for message to be sent, do not want to tie up resources
                #print("Timeout Manager waiting for messages to be added to queue")
                self.message_event.wait()

            if not self.stop_timer:
                #print("Timeout Manager starting thread timer")
                timer_thread = threading.Timer(interval=self.timeout_time, function=self.timeout)
                timer_thread.start()

                self.check_for_timeout.wait()
                self.check_for_timeout.clear()

                #Make sure all threads are not doing anything weird
                timer_thread.cancel()
                timer_thread.join()
                self.message_event.clear()

                if self.timedout:
                #print("Timeout has occured")
                    self.message_buffer_lock.acquire()
                    for obj in self.message_buffer:
                        try:
                            self.udt_send(obj)
                        except OSError:
                            self.all_messages_acked = True
                    self.message_buffer_lock.release()
                    self.message_event.set()
                
                self.timedout = False
        
        self.message_event.set()
        recv_worker.join()

            
            
    def run(self) -> None:
        #User select file to run
        file = "testimg.bmp"
        #Make packets from user selected file
        data = self.make_packt(filename=file)
        
        #Send packets to server
        #current_call = 0
        timeout_thread = threading.Thread(target=self.timeout_handler, args=[])
        timeout_thread.start()

        for i in range(0, len(data)):
            #print("Sending packet")
            self.rdt_send(data[i])

            if not(self.valid_server):
                return
        
        self.no_packets_left = True
        self.message_event.set()
        timeout_thread.join()
        #print("Client exiting")
        self.client_socket.shutdown(0)
        self.client_socket.close()
            

if __name__ == '__main__':
    client = Client()
    client.run()


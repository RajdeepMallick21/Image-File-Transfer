from socket import *
from tkinter import *
from tkinter.filedialog import asksaveasfile

import common_communication
import checksum_gen

from Unreliable_Transport import packet_corrupter
import threading
import queue
import select

def select_file(defualt_name : str) :
    window = Tk()
    
    #Open dialog box to get user to save file
    file = asksaveasfile(mode = "wb", 
                            defaultextension=".bmp", filetypes=[('bitmap files','*.bmp')], 
                            initialfile=defualt_name)
    window.destroy()
    return file

recieving_file = False

class Server:
    
    def __init__(self, server_port : int = 12000, corruption_chance : int = 0, drop_chance : int = 0, expected_files : int = 1, 
                 timeout: float = .001) -> None:
        # port and socket declaration
        # Code adapted from page 158 of Computer Networking, 8th edition by James F. Kurose and Keith W. Ross
        self.ServerSocket = socket(AF_INET, SOCK_DGRAM)

        # Binds ServerSocket to server_port with name given by system
        # Goes to localhost on Windows system
        self.ServerSocket.bind(('', server_port))
        
        self.output_queue = queue.Queue()
        self.timeout_time = timeout
        
        self.expected_seqeunce_number = 1
        seq_start = int(0).to_bytes(length=2)
        self.last_ack = checksum_gen.generate_16bit_sent_checksum(seq_start) + seq_start

        self.packet_corrupter = packet_corrupter(chance_corrupted= corruption_chance, chance_dropped= drop_chance)
        self.msg_received = False
        self.timedout = False

        self.processing_file = False

        self.expected_files = expected_files
        self.received_files = 0

        self.active_file = True
        self.keep_active = True
        #print('Server ready')

        self.ret_adress = []

    def timeout(self) -> None:
        #timedout works in recv_ack_worker thread to stop message gathering
        self.timedout = True

    def udt_send (self, message : bytes, adress) -> None:
        #maybe flip a bit in the message, if required
        sent_message = self.packet_corrupter.maybe_bitflip(message)

        send_message = self.packet_corrupter.drop_packet()

        if (not send_message):
            return
        # Send message to socket with serverName at serverPort
        self.ServerSocket.sendto(sent_message, (adress))

    #returns true if data was received correctly, false otherwise
    def rdt_receive(self):
        self.timedout = False

        timeout_thread = threading.Timer(interval= self.timeout_time, function= self.timeout, args=[] )
        timeout_thread.start()
        
        while (1):
            
            read, write, error = select.select([self.ServerSocket], [], [], .001)
            
            if (not len(read) > 0):
                if (self.timedout):
                    #print("Server Timeout occured")
                    timeout_thread.join()
                    #print("Recieved " + str(packets_received) + " corrupted packets.\n")
                    #Valid adress received
                    if (len(self.ret_adress) == 2):
                        self.udt_send(self.last_ack, self.ret_adress)
                    
                    self.timedout = False
                    
                    timeout_thread = threading.Timer(interval= self.timeout_time, function=self.timeout)
                    timeout_thread.start()
                    continue
            try:
                message, self.ret_adress = self.ServerSocket.recvfrom(self.buffer_size)
            except ConnectionResetError:
                return

            checksum = message[common_communication.CHECKSUM_HEADER_START:common_communication.CHECKSUM_HEADER_END]
            message_sequence = message[common_communication.CHECKSUM_HEADER_END:common_communication.ACK_HEADER_END]

            message_data = message[4:len(message)]
            
            corrupt = checksum_gen.corrupt(checksum, message_sequence + message_data)
            correct_sequence_num = int.from_bytes(message_sequence) == self.expected_seqeunce_number

            if (not corrupt and correct_sequence_num):
                timeout_thread.cancel()
                timeout_thread.join()
                #put data into data out queue - "deliver" data
                self.output_queue.put(message_data)

                if (message_data == common_communication.END_FILE_BYTES):
                    self.active_file = False

                #gen sent ack packet
                ack = self.expected_seqeunce_number.to_bytes(length=2)
                snd_pckt = checksum_gen.generate_16bit_sent_checksum(ack) + ack
                #send ack packet
                self.udt_send(snd_pckt, self.ret_adress)
                #print("Server Ack packet: ", sequence_num)
                #set last ack packet to packet sent
                self.last_ack = snd_pckt

                self.expected_seqeunce_number = (self.expected_seqeunce_number + 1) % common_communication.MAX_SEQUENCE_NUMBER
                #print("Server recieved correct packet")
                return
            else :
                #print("server recieved unexpected/corrupt packet")
                #print("Expected Packet number: " + str(self.expected_seqeunce_number))
                #print("Got packet number: " + str(int.from_bytes(message_sequence)))
                self.udt_send(self.last_ack, self.ret_adress)
            
                
    def clear_last_chksums(self):
        while 1:
            ready = select.select([self.ServerSocket], [], [], self.timeout_time * 5)
            if (ready[0]):
                try:
                    data, addr = self.ServerSocket.recvfrom(self.buffer_size)
                    self.udt_send(self.last_ack, addr)
                except ConnectionResetError:
                    return
            else:
                return True

    def run_server(self):
        
        expected_sequence_num = 1

        output_worker = threading.Thread(target=save_output_worker, args=[self])
        output_worker.start()

        while (self.active_file):
            self.rdt_receive()
                
        output_worker.join()
        self.clear_last_chksums()
        self.ServerSocket.close()
    

#Requires server to hook into
def save_output_worker(server : Server) :
    file = open(file="ServerOutput.bmp", mode='wb')

    while True:
        file_bytes = server.output_queue.get()
        #print("Got bytes: " + str(file_bytes))
        if (file_bytes == common_communication.END_FILE_BYTES):
            return
        else:
            file.write(file_bytes)
        

if __name__ == '__main__':
    server = Server()
    server.run_server()

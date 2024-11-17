from socket import *
import select

from threading import Thread, Lock, Event, Timer
from queue import Queue
from collections import deque



from random import Random
from time import time_ns

from copy import deepcopy

import Unreliable_Transport

from checksum_gen import generate_16bit_sent_checksum, corrupt
from common_communication import *

from multiprocessing import Process

class TCP_Connection :
    def __init__(self, max_data_seg_size_bytes : int = 1024, max_data_queue_size_bytes : int = 8192 ,
                 max_msg_window_size = 1024,
                 port_number : int | None = None, port_name : str | None = None,
                 corruption_chance : int = 0, drop_chance : int = 0) -> None:
        
        self.socket = socket(AF_INET, SOCK_DGRAM)
        
        self.base_lock = Lock()
        self.base = 0
        
        self.requested_byte = 0
        self.num_times_byte_requested = 0
        self.last_byte = 0
        
        self.initial_ack_number = 0
        self.ack_num = 0
        self.sent_bytes = 0

        self.sequence_num = 0
        self.initial_sequnce_num = 0

        self.window_size = 1
        self.window_size_increased = Event()
        
        self.sent_times = {}
        self.average_RTT = 1.0
        self.deviation_RTT = 0
        self.timeout = 4.0
     
        self.active = False
        self.activated_or_deactivated = Event()

        #List of segments sent to TCP interlocketer, not acked
        self.segment_buffer = list()
        #Bytes queue for holding data supplied by usr
        self.raw_send_queue = bytes()
        
        #Sent segments by segment number (sender) or ack number (receiver)
        self.sent_segment_queue = {}

        #Byte array for data that is received out of order / corrupted
        self.receive_buffer = {}
        self.receive_buffer_size_bytes = 0

        #Queue of message data that has been received, validated, and ordered, but not read from
        self.consumer_output_queue_lock = Lock
        self.consumer_output_queue = bytes()

        self.max_segment_bytes = max_data_seg_size_bytes
        self.max_data_queue_size = max_data_queue_size_bytes

        self.segment_acked = False
        self.timedout = False
        self.incoming_msg_event = Event()

        self.other_side_queue_size = 1
        self.other_side_queue_size_after_send = 0

        if port_name is not None: 
            self.port_name = get_true_port_name(port_name)
        else:
            self.port_name = '127.0.0.1'
        
        if port_number is None:
            random = Random()
            random.seed(time_ns())
            self.port_number = 0xFFFF
            bound = False
            while (not bound):
                try:
                    self.socket.bind((self.port_name, self.port_number))
                    self.port_name, self.port_number = self.socket.getsockname()
                    bound = True
                except:
                    self.port_number -= 1
                    bound = False
        else:
            self.port_number = port_number
            self.socket.bind((self.port_name, self.port_number))

        temp_port_number = 0

        self.source_port_bytes = self.port_number.to_bytes(SOURCE_PORT_NUMBER_BYTES)
        self.connected_port_bytes = temp_port_number.to_bytes(DEST_PORT_NUMBER_BYTES)

        self.connected_port = ( '0.0.0.0' , temp_port_number)
        self.connected = False

        self.packet_modifier = Unreliable_Transport.packet_corrupter(chance_corrupted= corruption_chance, chance_dropped= drop_chance)

    # Header Functions

    def check_port_number(self, TCP_Message : bytes) -> bool:
        source_port = TCP_Message[SOURCE_START: SOURCE_START + SOURCE_PORT_NUMBER_BYTES]
        dest_port = TCP_Message[DEST_PORT_START: DEST_PORT_START + DEST_PORT_NUMBER_BYTES]
        if (source_port == self.connected_port_bytes) and (dest_port == self.connected_port_bytes) :
            return True
        return False
    
    def get_sequence_and_ack(self, TCP_Message: bytes) -> tuple[int, int]:
        sequnce_number = int.from_bytes(TCP_Message[SEQUNCE_START:SEQUNCE_START + SEQUNCE_NUMBER_BYTES])
        ack = int.from_bytes(TCP_Message[ACK_START:ACK_START + ACK_NUMBER_BYTES])
        return (sequnce_number, ack)

    def get_header_length(self, TCP_Message: bytes) -> int:
        header_and_unused = int.from_bytes(TCP_Message[HEADER_START: HEADER_AND_UNUSED_BYTES + 1])
        return header_and_unused >> 4

    def get_flags(self, TCP_Message) -> bytes:
        return TCP_Message[FLAGS_START:FLAGS_START + FLAG_BYTES]
    
    def get_receive_window_size(self, TCP_Message: bytes) -> int:
        return int.from_bytes(TCP_Message[RECIEVE_WINDOW_START: RECIEVE_WINDOW_START + RECIEVE_WINDOW_BYTES])
    
    def check_corruption(self, TCP_Message : bytes) -> bool:
        data = TCP_Message[0:CHECKSUM_HEADER_START] + TCP_Message[0:CHECKSUM_HEADER_START + CHECKSUM_HEADER_BYTES: len(TCP_Message)]
        checksum = TCP_Message[CHECKSUM_HEADER_START:CHECKSUM_HEADER_START + CHECKSUM_HEADER_BYTES]
        return corrupt(checksum, data)
    
    def get_urgent_data_end(self, TCP_Message : bytes, header_length : int) -> bytes | None:
        data_pointer_end = int.from_bytes(TCP_Message[URGENT_POINTER_START: URGENT_POINTER_START + URGENT_DATA_POINTER_BYTES])
        if (data_pointer_end > 0):
            return TCP_Message[header_length:data_pointer_end]
        else:
            return None

    def get_options(self, TCP_Message : bytes, header_length : int) -> bytes | None:
        if (header_length > 20):
            return TCP_Message[MIN_HEADER_SIZE: header_length]
        else:
            return None
        
    def get_msg_data(self, TCP_Message : bytes, header_length : int) -> bytes | None :
        msg_length = len(TCP_Message)
        if msg_length > header_length:
            return TCP_Message[header_length:msg_length]
        else:
            return None

    # End Header functions

    # Connection and teardown functions

    # Connection

    def connect(self, server_name : str, server_port_number : int ) -> bool :
        if self.connected :
            return False

        random = Random()
        random.seed(time_ns())
        
        self.sequence_num = random.randint(0, MAX_SEQUENCE_ACK_NUMBER >> 4)
        flags = SYN.to_bytes(FLAG_BYTES)

        true_server_name = get_true_port_name(server_name)

        self.connected_port = (true_server_name, server_port_number)
        self.connected_port_bytes = server_port_number.to_bytes(DEST_PORT_NUMBER_BYTES)
        data = bytes()
        proposed_connection = self.package_data(data=data, flags=flags)
        
        self.connected = True
        self.connection_send(proposed_connection)
        self.initial_sequnce_num = self.sequence_num

        success = False

        timeout_thread = Timer(interval= self.timeout, function=self.timeout_thread(), args=[])
        timeout_thread.start()
        for i in range(0, 400000):
            data = self.rcv_data(.001)
                        
            if data is not None:
                #do parsing for valid data
                if len(data) is not MIN_HEADER_SIZE:
                    #restart loop
                    continue

                rcvd_flags = self.get_flags(data)
                rcvd_sequnce, rcvd_ack = self.get_sequence_and_ack(data)
                
                if not (rcvd_ack == self.sequence_num + 1 or rcvd_flags == flags) :
                    self.connection_send(proposed_connection)
                    #restart loop, skiping rest of loop
                    continue

                self.ack_num = rcvd_sequnce
                self.initial_ack_number = self.ack_num
                self.requested_byte = self.ack_num - self.initial_ack_number
                success = True
                break

            if self.timedout:
                self.connection_send(proposed_connection)
                self.timedout = False
            
        
        if success:
            self.ack_num += 1
            ack_send = self.package_data(data=data, flags= NO_FLAGS)
            self.segment_buffer.append(ack_send)
            self.connection_send(ack_send)
            return True
        return False

    def wait_for_connection(self):
        connected = False
        while (not connected):
            read, write, error = select.select([self.socket], [], [], .001)
            if not len(read) > 0:
                continue

            recieved_message, return_address = self.socket.recvfrom(self.max_data_queue_size)
            if not len(recieved_message) == MIN_HEADER_SIZE:
                print(len(recieved_message))
                continue
            
            corrupt = self.check_corruption(recieved_message)
            if (corrupt):
                continue
            
            self.connected_port = return_address
            self.connected = True

            rcvd_sequnece, trash = self.get_sequence_and_ack(recieved_message)
            self.initial_ack_number = rcvd_sequnece
            self.ack_num = self.initial_ack_number + 1
            random = Random()
            random.seed(time_ns())
            self.initial_sequnce_num = random.randint(0, MAX_SEQUENCE_ACK_NUMBER >> 4)
            self.sequence_num = self.initial_sequnce_num
            proposed_connection = self.package_data(data=bytes(), flags=SYN.to_bytes(FLAG_BYTES))

            self.connection_send(proposed_connection)

        for i in range(0 , 100):
            self.connected = True
            data = self.rcv_data(.001)
            self.connected = False
            if data is None:
                continue
            rcvd_sequnece, rcvd_ack = self.get_sequence_and_ack(data)

            if not (rcvd_sequnece == self.initial_ack_number + 1) or (rcvd_ack == self.initial_sequnce_num + 1):
                self.connection_send(proposed_connection)
                continue

            self.connected = True
            print("Connected")
            break

    # Teardown

    # End connection and teardown
    
    # Sending and Receiving mesages
    
    def package_data(self, data : bytes, flags: bytes, urgent_data_pointer : bytes | None = None, options : bytes | None = None) -> bytes:
        header_length = MIN_HEADER_SIZE
        if options is not None:
            header_length += len(options)
            option_bytes = options
        if options is None:
            option_bytes = bytes()

        if urgent_data_pointer is None:
            data_pointer = NO_URGENT_DATA
        else :
            data_pointer = urgent_data_pointer
        
        self.consumer_output_queue_lock.acquire()
        space = self.max_data_queue_size - (len(self.consumer_output_queue) + self.receive_buffer_size_bytes)

        no_checksum_packet = (self.source_port_bytes + self.connected_port_bytes + self.sequence_num.to_bytes(SEQUNCE_NUMBER_BYTES) + self.ack_num.to_bytes(SEQUNCE_NUMBER_BYTES) + 
                            (header_length * 4).to_bytes(HEADER_AND_UNUSED_BYTES) + flags + space + data_pointer + option_bytes + 
                            data)
        
        checksum = generate_16bit_sent_checksum(no_checksum_packet)

        sent_data = no_checksum_packet[0:CHECKSUM_HEADER_START] + checksum + no_checksum_packet[CHECKSUM_HEADER_START:len(no_checksum_packet)]

        #deepcopy so that input array can be cleared - if this is not done, clearing data out of input array would clear data out of 
        #the sent copy, which is not good
        sent_copy = deepcopy(sent_data)
        #print(len(sent_copy))
        return sent_copy

    
    def tcp_send(self, data : bytes, options : bytes | None = None, flags : bytes | None = None) -> bool:

        if (len(self.raw_send_queue) + len(data) > self.max_data_queue_size or not self.connected):
            return False
        else:
            self.raw_send_queue += data
            data_header_size = MIN_HEADER_SIZE
            if (options is not None):
                data_header_size += len(options)

            sent_flags = flags
            if sent_flags == None:
                sent_flags = NO_FLAGS

            while (len(self.raw_send_queue) > 0):
                if not (len(self.segment_buffer) < self.window_size):
                    self.window_size_increased.wait()

                num_bytes_sent = min(self.other_side_queue_size, len(self.raw_send_queue), self.max_segment_bytes - data_header_size)
                
                if (num_bytes_sent < 1):
                    continue
                #Wait for window to clear here:
                
                sent_data = self.raw_send_queue[0:num_bytes_sent]
                msg = self.package_data(data = sent_data, flags = sent_flags)
                del self.raw_send_queue[0 : num_bytes_sent]
                
                self.sequence_num += num_bytes_sent

            return True

    def get_data(self) -> bytes | None:
        if len(self.consumer_output_queue) > 0:
            
            self.consumer_output_queue_lock.acquire()
            returned_copy = self.consumer_output_queue
            self.consumer_output_queue = bytes()
            self.consumer_output_queue_lock.release()
            
            return returned_copy
        elif self.active:
            return bytes()
        return None

    def receive_data_thread(self):
        while self.active:
            timeout_thread = Timer(interval=self.average_RTT * 4, function=self.timeout_thread(), args=[])

            received_data = False
            received_in_error = 0

            while not self.timedout:
                
                msg = self.rcv_data(.001)
                
                if msg is None:
                    continue
                received_byte, requested_byte = self.get_sequence_and_ack(msg)
                header_length = self.get_header_length(msg)
                msg_data = self.get_msg_data(msg, header_length=header_length)
                
                if received_byte == self.ack_num:
                    self.ack_num += len(msg_data)
                    appended_data = msg_data
                    more_data = self.receive_buffer.get(self.ack_num)
                    while more_data is not None:
                        appended_data += more_data
                        self.ack_num += len(more_data)
                        self.receive_buffer_size_bytes -= len(more_data)
                    
                    self.consumer_output_queue_lock.acquire()
                    self.consumer_output_queue += appended_data
                    self.consumer_output_queue_lock.release()
                        
                elif received_byte > self.ack_num:
                        data = self.receive_buffer.get(received_byte)
                        if data is None:
                            self.receive_buffer[received_byte] = msg_data
                            self.receive_buffer_size_bytes += len(msg_data)
                        received_in_error += 1
                else:
                    received_in_error += 1
                             
                if received_in_error == 3:
                    self.send_ack()
                    
    def send_ack(self):
        ack_pckt = self.package_data(bytes(), NO_FLAGS)


    def timeout_thread(self):
        self.timedout = True

    def rcv_data(self, socket_timeout : float) -> bytes | None:
        readable, write, error = select.select([self.socket], [], [], socket_timeout )
        if (len(readable) > 0):
            time_rcvd = time_ns()
            msg, address = self.socket.recvfrom(self.max_segment_bytes)
            
            if not self.connected:
                return msg
            
            if self.connected:
                if not address == self.connected_port:
                    return None
                
                corrupt = self.check_corruption(msg)
                if corrupt:
                    return None
                
                sequnce_number, ack_number = self.get_sequence_and_ack(msg)
                
                self.base_lock.acquire()
                self.base = ack_number - self.initial_sequnce_num
                self.base_lock.release()
                msg_sent_time = self.sent_times.get(ack_number)
                if (msg_sent_time is not None):
                    sample_RTT = time_rcvd - msg_sent_time
                    self.average_RTT = self.average_RTT * RTT_OLD_WEIGHT + RTT_ALPHA * (sample_RTT)
                    self.deviation_RTT = DEV_OLD_WEIHT * self.deviation_RTT + abs(sample_RTT - self.average_RTT) 
                    self.timeout = self.average_RTT + 4 * self.deviation_RTT
                return msg

    def connection_send(self, message : bytes) -> None :
        start_time = time_ns()
        self.sent_times[self.sequence_num] = start_time
        self.udt_send(message)

    def udt_send (self, message : bytes) -> None:
        #maybe flip a bit in the message, if required
        sent_message = self.packet_modifier.maybe_bitflip(message)

        send_message = self.packet_modifier.drop_packet()

        if (not send_message):
            return
        
        # Send message to socket with serverName at serverPort
        self.socket.sendto(sent_message, self.connected_port)

    # End Sending and recieving mesages




def server_test():
    server = TCP_Connection(port_number= 1200)
    server.wait_for_connection()
    data = bytes
    while data is not None:
        data = server.get_data()
        print(data)
    
    print("Server exited")

def client_test():
    client = TCP_Connection(port_number= 5500)
    client.connect('localhost', 1200)

    data = 0

    client.tcp_send(data.to_bytes(2048))

    client.incoming_msg_event.wait()

if __name__ == '__main__':
    server = Process(target=server_test, args=())
    client = Process(target= client_test, args=())
    server.start()
    client.start()
    server.join()
    client.join()
#declare constatants
ZERO = 0
#TCP Header
SOURCE_PORT_NUMBER_BYTES = 2
DEST_PORT_NUMBER_BYTES = 2
SEQUNCE_NUMBER_BYTES = 4
ACK_NUMBER_BYTES = 4
HEADER_AND_UNUSED_BYTES = 1
FLAG_BYTES = 1
RECIEVE_WINDOW_BYTES = 2

CHECKSUM_HEADER_BYTES = 2
URGENT_DATA_POINTER_BYTES = 2

SOURCE_START = 0
DEST_PORT_START = SOURCE_PORT_NUMBER_BYTES
SEQUNCE_START = DEST_PORT_START + DEST_PORT_NUMBER_BYTES
ACK_START = SEQUNCE_START + SEQUNCE_NUMBER_BYTES
HEADER_START = ACK_START + ACK_NUMBER_BYTES
FLAGS_START = HEADER_START + HEADER_AND_UNUSED_BYTES
RECIEVE_WINDOW_START = FLAGS_START + FLAG_BYTES
CHECKSUM_HEADER_START = RECIEVE_WINDOW_START + RECIEVE_WINDOW_BYTES
URGENT_POINTER_START = CHECKSUM_HEADER_START + CHECKSUM_HEADER_BYTES

MIN_HEADER_SIZE = (SOURCE_PORT_NUMBER_BYTES + DEST_PORT_NUMBER_BYTES + SEQUNCE_NUMBER_BYTES + ACK_NUMBER_BYTES + HEADER_AND_UNUSED_BYTES + 
                FLAG_BYTES + RECIEVE_WINDOW_BYTES + CHECKSUM_HEADER_BYTES + URGENT_DATA_POINTER_BYTES)

NO_FLAGS = ZERO.to_bytes(FLAG_BYTES)
NO_URGENT_DATA = ZERO.to_bytes(URGENT_DATA_POINTER_BYTES)

MAX_SEQUENCE_ACK_NUMBER = 0xFFFFFFFF

RTT_ALPHA = .125
RTT_OLD_WEIGHT = 1 - RTT_ALPHA

DEV_BETA = .25
DEV_OLD_WEIHT = 1 - .25
#ROLLOVER_POSSIBLE = MAX_SEQUENCE_NUMBER - WINDOW_SIZE

END_FILE_BYTES = bytes([0x0F, 0x0F])

FIN = 0x1
SYN = 0x2
RST = 0x4
PSH = 0x8
ACK = 0x10
URG = 0x20
ECE = 0x40
CWR = 0x80

#Functions
#Checks to make sure that ack is correct ack in sequnece number
def corresponds_to_ack(sequnce_num : int, recieved_num : bytes) -> bool:
        if int.from_bytes(recieved_num) == sequnce_num:
            #print("ACK matches")
            return True
        else :
            print("ACK mismatch")
            return False

def get_true_port_name(port_name: str) -> str:
    true_name = port_name
    match port_name:
        case '':
            true_name = '127.0.0.1'
        case 'localhost':
            true_name = '127.0.0.1'

    return true_name

#Test functions
if __name__ == '__main__':
    expected_error_string = "Expected value: {}     actual_value: {}"
    
    for i in range(0 , 0x10000):
        pretend_ack = i.to_bytes(length=2)

        if not (int.from_bytes(pretend_ack) == i):
             print("error in 2 byte translation")
             print(expected_error_string.format(i, pretend_ack))
             break
        
        if not (corresponds_to_ack(i, pretend_ack)):
            print ("Error in function corresponds to ack: expected true, got false")

     
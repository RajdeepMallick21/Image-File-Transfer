from math import ceil
# declare constants
EXPECTED_16BIT_CHECKSUM_SUM = 0xFFFF
SUM_SIZE_BITS = 16
SUM_SIZE_BYTES = 2

MAX_INTEGER_CHECKSUM = 0xFFFF

# Genrates 16 bit (2 byte) checksum for given value
def generate_16_checksum(message : bytes):
    message_bytes = bytearray(message)
    num_addations = ceil(len(message_bytes) / SUM_SIZE_BYTES)
    integer_intermediate = 0

    for i in range(0, num_addations + 1, 2):
        if (i + 1) == len(message_bytes) :
            integer_hold = message_bytes[i]
        else :
            #translate to bytes to integer value in MSB, doing the shift left of n bits
            high = message_bytes[i] << 8
            low =  message_bytes[i + 1]
            integer_hold = high + low
        
        integer_intermediate += integer_hold
        
        if (integer_intermediate > MAX_INTEGER_CHECKSUM):
            #Remove excess bit 
            integer_intermediate -= (MAX_INTEGER_CHECKSUM + 1)
            #Wrap around add bit
            integer_intermediate += 1
            
            
    
    return integer_intermediate.to_bytes(length=2)

#Function for generating checksum sent in a packet header
def generate_16bit_sent_checksum(message: bytes):
    checksum = generate_16_checksum(message=message)
    temp = bytearray(checksum)
    #switch values in both bytes
    for i in range(0 , len(temp)):
        temp[i] ^= 0xFF
    
    return bytes(temp) 

def check_checksum(package_checksum: bytes, generated_checksum: bytes):
    package_sum = int.from_bytes(package_checksum)
    generated_sum = int.from_bytes(generated_checksum)

    checked_sum = package_sum + generated_sum

    if checked_sum == EXPECTED_16BIT_CHECKSUM_SUM:
        return True
    else :
        return False

def corrupt(package_checksum: bytes, package_data: bytes):
    aquired_checksom = generate_16_checksum(package_data)
    return not check_checksum(package_checksum, aquired_checksom)

#Test bench for debuging function
#Note that sometimes bytes may return a letter. This is accaptable.
if __name__ == '__main__':
    
    for i in range (0, 256):
        for j in range(0, 256):
            for k in range(0, 256):
                test = bytearray([i, j, k])   
                checksum = generate_16_checksum(test)
                #print("Checksum is " + str(checksum))

                sent_checksum = generate_16bit_sent_checksum(test)
                #print("Header Checksum is: " + str(sent_checksum))

                valid_packet = check_checksum(sent_checksum, checksum)
                #print("The sent checksum returned: " + str(valid_packet))
                if not valid_packet:
                    print ("Failure: ")
                    print("Checksum is " + str(checksum))
                    print("Header Checksum is: " + str(sent_checksum))
                    print("The sent checksum returned: " + str(valid_packet))





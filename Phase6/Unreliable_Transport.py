import random
import datetime
from bitarray import bitarray
from copy import deepcopy

# PLEASE INSTALL bitarray in order to run. Bitarray is a python package, installed with the following command:
# "pip install bitarray"

class packet_corrupter:
    #initiates self with chance of curruption given by chance corrupted. Can not be greater than 99 (if data can go through) or less than 0
    def __init__(self, chance_corrupted: int = 0, chance_dropped = 0 ) -> None:
        
        if (chance_corrupted > 100 or chance_corrupted < 0):
            raise ValueError("Chance of corruption cannot exceed 100 or be less than 0")
         
        self.fail_chance = chance_corrupted
        self.random = random.Random()
        self.random.seed(datetime.datetime.now().timestamp())

        self.drop_chance = chance_dropped
        
    def drop_packet (self) -> bool:
        random_num = self.random.randint(1, 100)
        if (self.drop_chance < random_num):
            return True
        else:
            return False


    def maybe_bitflip(self, packet : bytes) -> bytes:
        random_num = self.random.randint(1, 100)
        
        new_array = deepcopy(packet)

        if ( random_num > self.fail_chance ):
            #random number is greater than fail chance: do not fail
            return new_array
        
        else :
            #print("Corrupting packet: \n")
            #print(str(random_num) + "\n")
            #little endian file array
            temp_array = bitarray(endian='big')
            temp_array.frombytes(new_array)
            flip_index = self.random.randint(0, len(temp_array) - 1)
            #XOR to flip bit: 1 XOR 0 is 1, 1 XOR 1 is 0
            temp_array[flip_index] = 1 ^ temp_array[flip_index]
            return bytes(temp_array)
        
#Test function: make sure a bit in the array is flipped every call (Check for 1, 2, 4, 8 in every message)
if __name__ == '__main__':
    pass_test = packet_corrupter(0)

    test = packet_corrupter(100)

    array = bytearray()
    zerobit = 0x00
    for i in range (0, 1024):
        array.append(zerobit)
    
    temp_array = bytes(array)

    pass_array = pass_test.maybe_bitflip(temp_array)
    if not sum(pass_array) == 0:
        print("Pass failure")

    for j in range(0, 1000):
        test_array = test.maybe_bitflip(temp_array)
        if not (sum(test_array) > 0):
            print("Failure")
       
        
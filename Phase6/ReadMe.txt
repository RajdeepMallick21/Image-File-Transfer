This project requires the bitarray project from PyPI in oreder to work. bitarray allows for C like behaviors of a python array of bits.
To install PyPI, type "pip install bitarray" into your console application.

Group Member Names:
Conor Duston, Rajdeep Mallick, Spencer Weeden

Files:
Main.py:
    Source code for creating client and server objects and running them on seperate thread, all in 1 file.

Client.py:
    Reads the bytes of the file called testimg.bmp into packets, then sends the packet to the server.

Server.py:
    Receives files from clients talking to it, and saves all recieved packets to serveroutput.bmp.

Unreliable_Transport.py
    Provides functions to create packet corruption

checksum_gen.py 
    Provides functions to create the 16-bit checksum header to the data and ACK sequence number

common_communication.py
    Provides functions to check whether the received ACK sequence number from a packet is equal to the expected number

Data_Transfer_Speed_Tester.py
    Alternate file to Main.py in order to perform program completion time trials with various percentages of packet corruption
    Outputs a csv file and python plot


Steps to run project:
    This project was made using Python 3.11. Please note that older versions of python may not be able to run this script.
   
    1. Unpack all scripts into 1 folder. Using VS Code, python command line, or PyCharm, run Main.py.

    2. Wait for the message "Process finished with exit code 0" in the PyCharm console.

    The bmp image called testimg should be copied to the output location.
    To modify the server drop chance, server corruption chance, client drop chance, and client corrution chance, change the corresponding variable in main.py before running.
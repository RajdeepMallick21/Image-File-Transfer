import Client
import Server
import threading
from datetime import datetime
import time
import matplotlib.pyplot as plot

NUM_TRIALS = 10
MAX_CORRUPTION = 70
MAX_RETRANSMISSION_TIMEOUT = 0.1

packet_size = 1024
client_finished_event = threading.Event()

def run_server(ack_bit_corruption_chance : int = 0, packet_drop_chance : int = 0, server_port : int = 12000, timeout : float = 0.001) :
    server_obj = Server.Server(buffer_size=packet_size, server_port=server_port,
                               corruption_chance= ack_bit_corruption_chance, drop_chance= packet_drop_chance,
                               timeout=timeout)
    server_thread = threading.Thread(target=server_obj.run_server)
    server_thread.run()
    server_obj = None

def run_client(package_bit_corruption_chance :int = 0, packet_drop_chance : int = 0, server_port : int = 12000, timeout : float = 0.001, window_size : int = 10) :
    client_obj = Client.Client(packet_size=packet_size, server_port=server_port, 
                               corruption_chance=package_bit_corruption_chance, drop_chance= packet_drop_chance,
                               timeout=timeout, window_size=window_size)
    client_obj.run()
    client_obj = None


if __name__ == '__main__':
    
    output_file = open("SpeedTestResults.csv" , mode= 'w')
    
    server_port = 12000

    header = "Corruption Chance: , "
    trial_format = "Trial {}:, "
    
    for trial_num in range (0, NUM_TRIALS):
        header += trial_format.format(trial_num + 1)
    
    header += "Average: \n\n"

    output_file.write(header)

    y0 = []
    y1 = []
    y2 = []
    y3 = []
    y4 = []
    y5 = []                                                             #Data for Optimal Timeout Value with 20% loss/error
    y6 = []                                                             #Data for Optimal Window Size with 20% loss/error
    x = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70]
    x1 = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]    #Timeout Values Array
    window_size_array = [1, 2, 5, 10, 20, 30, 40, 50]
    #window_size_array = [50, 40, 30, 20, 10, 5, 2, 1]
    #Chart 1
    # output_file.write("No Loss:\n\n")
    # print("\nNo Loss\n")
    # for i in range(0, MAX_CORRUPTION + 5, 5):
    #     average = 0
    #     output_file.write(str(i) + ",")
    #
    #     for j in range (0, NUM_TRIALS):
    #         server_thread = threading.Thread(target=run_server, args=[0, 0, server_port])
    #         client_thread = threading.Thread(target=run_client, args=[0, 0, server_port])
    #
    #         start = datetime.now()
    #
    #         server_thread.start()
    #         client_thread.start()
    #
    #         client_thread.join()
    #         server_thread.join()
    #
    #         stop = datetime.now()
    #
    #         time_diff = (stop - start).total_seconds() * 10**3
    #
    #
    #         average += time_diff
    #         output_file.write(str(time_diff) + ", ")
    #         server_port += 1
    #         print (j)
    #
    #     average = average / NUM_TRIALS
    #     y0.append(average)
    #     output_file.write(str(average))
    #     output_file.write("\n")


    # output_file.write("Package Error Trials:\n")
    # print("\nPackage Error Trials\n")
    # for i in range(0, MAX_CORRUPTION + 5, 5):
    #     average = 0
    #     output_file.write(str(i) + ",")
    #
    #     for j in range (0, NUM_TRIALS):
    #         server_thread = threading.Thread(target=run_server, args=[0, 0, server_port])
    #         client_thread = threading.Thread(target=run_client, args=[i, 0, server_port])
    #
    #         start = datetime.now()
    #
    #         server_thread.start()
    #         client_thread.start()
    #
    #         client_thread.join()
    #         server_thread.join()
    #
    #         stop = datetime.now()
    #
    #         time_diff = (stop - start).total_seconds() * 10**3
    #
    #
    #         average += time_diff
    #         output_file.write(str(time_diff) + ", ")
    #         server_port += 1
    #         print (j)
    #
    #     average = average / NUM_TRIALS
    #     y1.append(average)
    #     output_file.write(str(average))
    #     output_file.write("\n")
    # output_file.write("\n")

    # output_file.write("ACK Error Trials:\n")
    # print("\nACK Error Trials\n")
    # for i in range(0, MAX_CORRUPTION + 5, 5):
    #     average = 0
    #     output_file.write(str(i) + ",")
    #
    #     for j in range (0, NUM_TRIALS):
    #         server_thread = threading.Thread(target=run_server, args=[i, 0, server_port])
    #         client_thread = threading.Thread(target=run_client, args=[0, 0, server_port])
    #
    #         start = datetime.now()
    #
    #         server_thread.start()
    #         client_thread.start()
    #
    #         client_thread.join()
    #         server_thread.join()
    #
    #         stop = datetime.now()
    #
    #         time_diff = (stop - start).total_seconds() * 10**3
    #
    #         average += time_diff
    #         output_file.write(str(time_diff) + ", ")
    #         server_port += 1
    #         time.sleep(.5)
    #
    #     average = average / NUM_TRIALS
    #     y2.append(average)
    #     output_file.write(str(average))
    #     output_file.write("\n")
    #
    # output_file.write("\n")

    # output_file.write("ACK Packet Loss\n")
    # print("\nACK Packet Loss\n")
    # for i in range(0, MAX_CORRUPTION + 5, 5):
    #     average = 0
    #     output_file.write(str(i) + ",")
    #
    #     for j in range (0, NUM_TRIALS):
    #         server_thread = threading.Thread(target=run_server, args=[0, i, server_port])
    #         client_thread = threading.Thread(target=run_client, args=[0, 0, server_port])
    #
    #         start = datetime.now()
    #
    #         server_thread.start()
    #         client_thread.start()
    #
    #         client_thread.join()
    #         server_thread.join()
    #
    #         stop = datetime.now()
    #
    #         time_diff = (stop - start).total_seconds() * 10**3
    #
    #
    #         average += time_diff
    #         output_file.write(str(time_diff) + ", ")
    #         server_port += 1
    #         print (j)
    #
    #     average = average / NUM_TRIALS
    #     y3.append(average)
    #     output_file.write(str(average))
    #     output_file.write("\n")

    # output_file.write("Data Package loss trials:\n\n")
    # print("\nData Package Loss \n")
    # for i in range(0, MAX_CORRUPTION + 5, 5):
    #     average = 0
    #     output_file.write(str(i) + ",")
    #
    #     for j in range (0, NUM_TRIALS):
    #         server_thread = threading.Thread(target=run_server, args=[0, 0, server_port])
    #         client_thread = threading.Thread(target=run_client, args=[0, i, server_port])
    #
    #         start = datetime.now()
    #
    #         server_thread.start()
    #         client_thread.start()
    #
    #         client_thread.join()
    #         server_thread.join()
    #
    #         stop = datetime.now()
    #
    #         time_diff = (stop - start).total_seconds() * 10**3
    #
    #
    #         average += time_diff
    #         output_file.write(str(time_diff) + ", ")
    #         server_port += 1
    #         print (j)
    #
    #     average = average / NUM_TRIALS
    #     y4.append(average)
    #     output_file.write(str(average))
    #     output_file.write("\n")

    #Chart 2
    # Retransmission Timeout Changes
    # output_file.write("Optimal Timeout Value Trials:\n\n")
    # print("\nOptimal Timeout Value Trials\n")
    # k = 0
    # while(k < 4):
    #     error_chance_array = [0] * 4
    #     error_chance_array[k] = 20
    #     current_timeout_value = 0.01
    #     while (current_timeout_value <= MAX_RETRANSMISSION_TIMEOUT):
    #     # for i in range(0.01, MAX_RETRANSMISSION_TIMEOUT + 0.01, 0.01):
    #         average = 0
    #         output_file.write(str(current_timeout_value) + ",")
    #
    #         for j in range(0, NUM_TRIALS):
    #             server_thread = threading.Thread(target=run_server, args=[error_chance_array[0], error_chance_array[1], server_port, current_timeout_value])
    #             client_thread = threading.Thread(target=run_client, args=[error_chance_array[2], error_chance_array[3], server_port, current_timeout_value])
    #
    #             start = datetime.now()
    #
    #             server_thread.start()
    #             client_thread.start()
    #
    #             client_thread.join()
    #             server_thread.join()
    #
    #             stop = datetime.now()
    #
    #             time_diff = (stop - start).total_seconds() * 10 ** 3
    #
    #             average += time_diff
    #             output_file.write(str(time_diff) + ", ")
    #             server_port += 1
    #             print(j)
    #
    #         current_timeout_value += 0.01
    #         average = average / NUM_TRIALS
    #         y5.append(average)
    #         output_file.write(str(average))
    #         output_file.write("\n")
    #
    #     k += 1

    #Chart 3
    # Window Size Changes
    output_file.write("Optimal Window Size Trials\n\n")
    print("\nOptimal Window Size Trials\n")
    k = 0
    while (k < 4):
        error_chance_array = [0] * 4
        error_chance_array[k] = 20
        #current_window_size = window_size_array[0]
        for i in range(0, len(window_size_array)):
            average = 0
            current_window_size = window_size_array[i]
            output_file.write(str(current_window_size) + ",")
            for j in range(0, NUM_TRIALS):
                server_thread = threading.Thread(target=run_server, args=[error_chance_array[0], error_chance_array[1], server_port, 0.001])
                client_thread = threading.Thread(target=run_client, args=[error_chance_array[2], error_chance_array[3], server_port, 0.001, current_window_size])

                start = datetime.now()

                server_thread.start()
                client_thread.start()

                client_thread.join()
                server_thread.join()

                stop = datetime.now()

                time_diff = (stop - start).total_seconds() * 10 ** 3

                average += time_diff
                output_file.write(str(time_diff) + ", ")
                server_port += 1
                print(j)


            average = average / NUM_TRIALS
            y6.append(average)
            output_file.write(str(average))
            output_file.write("\n")

        k += 1

    output_file.close()

    # #Chart 1
    # plot.figure(1)
    # plot.plot(x, y0, label = "No Error trials")
    # plot.plot(x, y1, label="Package Error Trials")
    # plot.plot(x, y2, label="ACK Error Trials")
    # plot.plot(x, y3, label= "ACK Packet Loss Trials")
    # plot.plot(x, y4, label= "Data Package Loss Trials")
    # plot.ylabel('Completion Time (ms)')
    # plot.xlabel('Error Percentage (%)')
    # plot.legend()
    # plot.show()


    #Chart 2
    # plot.figure(2)
    # plot.plot(x1, y5[0:10], label="ACK Bit Corruption")
    # plot.plot(x1, y5[10:20], label="ACK Packet Drop")
    # plot.plot(x1, y5[20:30], label="Data Bit Corruption")
    # plot.plot(x1, y5[30:40], label="Data Packet Drop")
    # plot.ylabel('File Transfer Completion Time (ms)')
    # plot.xlabel('Retransmission Timeout Value (ms)')
    # plot.legend()
    # plot.show()

    #Chart 3
    plot.figure(3)
    plot.plot(window_size_array, y6[0:8], label="ACK Bit Corruption")
    plot.plot(window_size_array, y6[8:16], label="ACK Packet Drop")
    plot.plot(window_size_array, y6[16:24], label="Data Bit Corruption")
    plot.plot(window_size_array, y6[24:32], label="Data Packet Drop")
    plot.ylabel('File Transfer Completion Time (ms)')
    plot.xlabel('Window Size Value')
    plot.legend()
    plot.show()


    
    
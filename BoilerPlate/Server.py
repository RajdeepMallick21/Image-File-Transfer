from socket import *


class Server:

    def __init__(self):
        # port and socket declaration
        # Code adapted from page 158 of Computer Networking, 8th edition by James F. Kurose and Keith W. Ross
        server_port = 12000
        self.ServerSocket = socket(AF_INET, SOCK_DGRAM)

        # Binds ServerSocket to server_port with name given by system
        # Goes to localhost on Windows system
        self.ServerSocket.bind(('', server_port))

        print('Server ready')

    def run_server(self):
        while True:
            # receive message
            message, client_address = self.ServerSocket.recvfrom(2048)
            # Print that server has received message
            print('Server received message: ' + message.decode())
            # Send message back to client
            self.ServerSocket.sendto(message, client_address)


if __name__ == '__main__':
    server = Server()
    server.run_server()

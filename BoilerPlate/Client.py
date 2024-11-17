from socket import *


class Client:

    def __init__(self):
        # Code adapted from page 156 of Computer Networking, 8th edition by James F. Kurose and Keith W. Ross
        # Server location
        self.serverName = 'localhost'
        self.serverPort = 12000

        # Init client location
        self.clientSocket = socket(AF_INET, SOCK_DGRAM)
        print('Inited client')

    def run(self):
        # Message to sent to server
        message = 'hello'
        # Send message to socket with serverName at serverPort
        self.clientSocket.sendto(message.encode(), (self.serverName, self.serverPort))
        # Receive and print return message
        received, server_address = self.clientSocket.recvfrom(2048)
        print('Client received: ' + received.decode())

        message = 'Running some code... '
        self.clientSocket.sendto(message.encode(), (self.serverName, self.serverPort))
        trash = self.clientSocket.recvfrom(2048)


if __name__ == '__main__':
    client = Client()
    client.run()


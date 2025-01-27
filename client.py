from socket import *

client_socket = socket(AF_INET, SOCK_STREAM)

port_number = 8000
server_addr = "" 

# Client socket connects to proxy server
client_socket.connect((server_addr, port_number))

print("Server connected...")

# Sending http url to proxy server
msg = input("Enter the URL (e.g., http://www.example.com/): ")
client_socket.send(msg.encode())

try:

    # Print all packets received from proxy server
    while True:
        client_response = client_socket.recv(1024)
        if not client_response:
            print("Exiting response mode...")
            break
        print(client_response.decode())

    # Catch any exception
except Exception as e:
    print(f"Error while receiving response: {e}")

# Close connection 
client_socket.close()

"""
Farhan Ansari
"""






import socket 
import time
from threading import Thread
import time

packets_received_count = 0 # Packets received
total_packets = 10000000 # total number of packets to be received
sequence_number = 0 # sequence number
packet_size = 4 # Packet size - a small packet size allows for faster iteration since transmission is expedited
maximum_sequence_number = 65536 # Maximum sequence number 2^16
expected_sequence_number = 1 # next sequence number to be received
missing_packets = [] # List of missing packets
received_packets = [] # List of received packets
goodput_store = [] # List of good put values
sequence_numbers = [] # List of sequence numbers
receiver_buffer = '' # Buffer for received packets
buffer_size = 8192 # Buffer size, Large buffer=consumes memoery but it allows receiver to handle large burst of data
minimum_buffer_size = 1024 # Minimum buffer size = 1 byte
maximum_buffer_size = 32768 # Maximum buffer size. Sequence numbers should be at least twice the buffer size
client_name = '' # Name of the client
start_time = time.time() # Start time

# File handling to store data
received_f = open(f"received_sequence_number_{int(time.time())}.csv", "w")
received_f.write("sequence_number,tm\n")
goodput_f = open(f"goodput_{int(time.time())}.csv", "w")
goodput_f.write("received_packet,sent_packet,goodput\n")
rep_lock = threading.Lock()

# file handling for window size
receiver_window_size_f = open(f"receiver_window_size_{int(time.time())}.csv", "w")
receiver_window_size_f.write("receiver_window_size,tm\n")
win_lock = threading.Lock()

# To set up initial connection
def create_connection():
    global serversocket, host

    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #host = socket.gethostname() # If using Windows
    host="0.0.0.0"               # If using MacOS
    #host = socket.gethostbyname(socket.gethostname()) # 2 different PC's
    port = 4001

    try :
        serversocket.bind((host, port))
    except socket.error as e :
        print(str(e))

    print("Awaiting connection request...")

    serversocket.listen(5) # start listening for incoming connection requests

    print( "Listening on -  " + str(host) + ":" + str(port))

def connect():
    global conn, serversocket, packets_received_count, sequence_number, expected_sequence_number, missing_packets, received_packets, goodput_store, sequence_numbers, receiver_buffer, buffer_size, received_f, goodput_f, rep_lock, client_name, start_time

    if(packets_received_count+(total_packets/100) > total_packets): # check if execution is almost complete
        packets_received_count = total_packets
        execution_complete()
        return

    conn, address = serversocket.accept() # accepts incoming connections
    # conn.setblocking(False)
    start_time = time.time()
    print('Connected to the address - ', address)

    response = (conn.recv(2048)).decode() # get first response from new connection (2048 = max size of data to be received in one call)

    if(response[:3]=="SYN"): # check if the client is requesting a new connection
        if((packets_received_count < 10) or (client_name != response[4:]) or (packets_received_count>(total_packets*0.99))):
            conn.sendall("NEW".encode()) # Client can now send data to the server
            client_name =  response[4:] # Stores the new identity of the client
            reset() # resets all variables

        else:
            conn.sendall("OLD".encode()) # If the client was previously disconnected and is now attempting re-connection
            response = (conn.recv(2048)).decode() # Ask the client to send the remaining data
            if(response[:3]=="SND"):
                data = '{' + f'"packets_received_count" : int({packets_received_count}), "sequence_number" : int({sequence_number})' + '}'
                conn.sendall(data.encode()) # Send data to sync with the client

    elif(response[:3]=="RCN"): # Clients sends a server-disconnected message (reconnect)
        conn.sendall("SND".encode()) # Request client to send synchronization data
        client_name =  response[4:]
        print("Syncing data with the sender/client...")
        response = (conn.recv(4096)).decode() # Get info to sync
        if(response):
            data = eval(response)
            packets_received_count = data['pkt_success_sent'] # Set the packets that have already been received
            sequence_number = data['sequence_number'] # Set the sequence numbers
            expected_sequence_number = data['sequence_number'] + packet_size

        else:
            print("Reconnection request failed!")

    else:
        print("error : client failed to connect")
        exit()

    try:
        process_packets() # Start the process to receive the packets
    except Exception as e:
        print(str(e))

# Calculates throughput and logs the metrics
def reportPacketStats(rcvd_packets, n_missed):
    global goodput_store, received_f, goodput_f, rep_lock

    # Lock the resources
    rep_lock.acquire()

    # Log the sequence numner and timestamp
    for sq, tm in rcvd_packets:
        received_f.write(f"{sq},{tm}\n") 

    n_recv = len(rcvd_packets) # number of received packets
    n_sent = n_recv + len(missing_packets) # number of sent packets
    good_put = n_recv/n_sent # good put

    goodput_store.append(good_put) # store good put in an array
    goodput_f.write(f"{n_recv},{n_sent},{good_put}\n") # store good put in a file

    rep_lock.release()

# Logs the window size changes during data transfer 
def report_window(win_size, tm):
    global window_size_f, win_lock
    win_lock.acquire()
    receiver_window_size_f.write(f"{win_size},{tm}\n")
    win_lock.release()
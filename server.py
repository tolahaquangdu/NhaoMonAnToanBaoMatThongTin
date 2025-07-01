import socket
import threading
import json
import base64
import os

# Server's host and port
HOST = '0.0.0.0' # Listen on all available interfaces
PORT = 65432

# In-memory storage for user public keys (simulating a database like Firestore)
user_public_keys = {}
# In-memory message queue (simulating a pub/sub system like FCM)
message_queue = {}

def handle_client(conn, addr):
    """Handles a single client connection."""
    print(f"Connected by {addr}")
    try:
        while True:
            # Receive data from the client
            # We need to receive a bit more data since the payload is larger now
            data = conn.recv(8192) # Increased buffer size
            if not data:
                break
            
            # Decode the JSON payload
            try:
                request = json.loads(data.decode('utf-8'))
                action = request.get('action')
                
                response = {}
                
                if action == 'register_key':
                    # Action: Register public key
                    user_id = request.get('user_id')
                    public_key_pem_base64 = request.get('public_key')
                    if user_id and public_key_pem_base64:
                        user_public_keys[user_id] = public_key_pem_base64
                        print(f"Registered public key for user: {user_id}")
                        response = {"status": "success", "message": f"Public key for {user_id} registered."}
                    else:
                        response = {"status": "error", "message": "Missing user_id or public_key."}
                        
                elif action == 'get_public_key':
                    # Action: Get public key of another user
                    target_id = request.get('target_id')
                    public_key_pem_base64 = user_public_keys.get(target_id)
                    if public_key_pem_base64:
                        print(f"Sending public key of user: {target_id}")
                        response = {"status": "success", "public_key": public_key_pem_base64}
                    else:
                        print(f"Public key for user '{target_id}' not found.")
                        response = {"status": "error", "message": f"Public key for '{target_id}' not found."}
                        
                elif action == 'send_message':
                    # ACTION: FORWARD THE ENTIRE MESSAGE PAYLOAD
                    recipient_id = request.get('recipient_id')
                    # We store the ENTIRE 'request' dictionary
                    # as it contains all necessary parts for the recipient.
                    message_payload = request 
                    
                    if recipient_id and message_payload:
                        # Simulate a message queue/FCM.
                        if recipient_id not in message_queue:
                            message_queue[recipient_id] = []
                        message_queue[recipient_id].append(message_payload)
                        print(f"Full message payload received for user: {recipient_id}. Added to queue.")
                        response = {"status": "success", "message": "Message sent to queue."}
                    else:
                        response = {"status": "error", "message": "Missing recipient_id or message_payload."}

                elif action == 'get_messages':
                    # Action: Client pulls messages from the queue
                    user_id = request.get('user_id')
                    # We pop the entire list of messages for the user
                    messages = message_queue.pop(user_id, [])
                    print(f"Sending {len(messages)} messages to user: {user_id}")
                    response = {"status": "success", "messages": messages}
                
                else:
                    response = {"status": "error", "message": "Unknown action."}
                    
                conn.sendall(json.dumps(response).encode('utf-8'))
                
            except json.JSONDecodeError:
                print("Received invalid JSON data.")
                break
                
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        print(f"Connection from {addr} closed.")
        conn.close()

def start_server():
    """Starts the TCP server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server is listening on {HOST}:{PORT}...")
        
        while True:
            # Accept new connections
            conn, addr = s.accept()
            # Start a new thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    start_server()
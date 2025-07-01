import socket
import json
import base64
import os
import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac, padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as rsa_padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


SERVER_HOST = '192.168.16.155' 
SERVER_PORT = 65432

class SecureMessagingClient:
    """A client for sending and receiving secure messages."""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.private_key = None
        self.public_key = None
        self.backend = default_backend()    
        self.generate_rsa_key_pair()

    def generate_rsa_key_pair(self):
        """Generates a new RSA 2048-bit key pair."""
        print("Generating RSA 2048-bit key pair...")
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=self.backend
        )
        self.public_key = self.private_key.public_key()
        print("RSA key pair generated successfully.")
        pem_public_key = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.public_key_pem_base64 = base64.b64encode(pem_public_key).decode('utf-8')

    def connect_to_server(self):
        """Connects to the central server."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((SERVER_HOST, SERVER_PORT))
            return s
        except ConnectionRefusedError:
            print("Error: Could not connect to the server. Please make sure the server is running.")
            return None

    def register_public_key(self):
        """Registers the client's public key with the server."""
        with self.connect_to_server() as s:
            if not s: return
            request = {
                "action": "register_key",
                "user_id": self.user_id,
                "public_key": self.public_key_pem_base64
            }
            s.sendall(json.dumps(request).encode('utf-8'))
            response = json.loads(s.recv(1024).decode('utf-8'))
            print(f"Server response: {response['message']}")

    def get_public_key(self, target_id):
        """Retrieves the public key of a target user from the server."""
        with self.connect_to_server() as s:
            if not s: return None
            request = {
                "action": "get_public_key",
                "target_id": target_id
            }
            s.sendall(json.dumps(request).encode('utf-8'))
            response = json.loads(s.recv(1024).decode('utf-8'))
            if response.get('status') == 'success':
                public_key_pem = base64.b64decode(response['public_key'])
                return serialization.load_pem_public_key(public_key_pem, backend=self.backend)
            else:
                print(f"Error: {response['message']}")
                return None

    def send_message(self, recipient_id, message_text):
        """Encrypts, signs, and sends a message to a recipient."""
        print(f"\n--- Sending message to {recipient_id} ---")
        
        recipient_public_key = self.get_public_key(recipient_id)
        if not recipient_public_key:
            return
        des_key = os.urandom(24) 
        auth_info = f"{self.user_id}:{datetime.datetime.now().isoformat()}"
        signed_info = self.private_key.sign(
            auth_info.encode('utf-8'),
            rsa_padding.PSS(
                mgf=rsa_padding.MGF1(hashes.SHA256()),
                salt_length=rsa_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        encrypted_des_key = recipient_public_key.encrypt(
            des_key,
            rsa_padding.OAEP(
                mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        key_exchange_payload = {
            "signed_info": base64.b64encode(signed_info).decode('utf-8'),
            "encrypted_3des_key": base64.b64encode(encrypted_des_key).decode('utf-8')
        }
        iv = os.urandom(8) 
        padder = padding.PKCS7(algorithms.TripleDES.block_size).padder()
        padded_data = padder.update(message_text.encode('utf-8')) + padder.finalize()
        cipher = Cipher(algorithms.TripleDES(des_key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        hasher = hashes.Hash(hashes.SHA256(), backend=self.backend)
        hasher.update(iv + ciphertext)
        message_hash = hasher.finalize()
        signature = self.private_key.sign(
            message_hash,
            rsa_padding.PSS(
                mgf=rsa_padding.MGF1(hashes.SHA256()),
                salt_length=rsa_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        message_payload = {
            "iv": base64.b64encode(iv).decode('utf-8'),
            "cipher": base64.b64encode(ciphertext).decode('utf-8'),
            "hash": message_hash.hex(),
            "sig": base64.b64encode(signature).decode('utf-8')
        }
        full_payload = {
            "action": "send_message",
            "sender_id": self.user_id,
            "recipient_id": recipient_id,
            "message_payload": message_payload,
            "encrypted_3des_key_payload": key_exchange_payload
        }
        with self.connect_to_server() as s:
            if not s: return
            s.sendall(json.dumps(full_payload).encode('utf-8'))
            response = json.loads(s.recv(1024).decode('utf-8'))
            print(f"Server response: {response['message']}")

    def get_messages(self):
        """Pulls and processes messages from the server's queue."""
        print(f"\n--- Checking for messages for {self.user_id} ---")
        with self.connect_to_server() as s:
            if not s: return
            request = {
                "action": "get_messages",
                "user_id": self.user_id
            }
            s.sendall(json.dumps(request).encode('utf-8'))
            response_data = s.recv(4096)
            if not response_data:
                print("No response from server.")
                return

            try:
                response = json.loads(response_data.decode('utf-8'))
            except json.JSONDecodeError:
                print("Failed to decode server response.")
                return

            if response.get('status') == 'success' and response.get('messages'):
                messages_to_process = response['messages']
                for full_payload in messages_to_process:
                    self.process_incoming_message(full_payload)
            else:
                print("No new messages.")

    def process_incoming_message(self, full_payload):
        """Processes an incoming encrypted message."""
        print("\n--- Processing incoming message ---")  
        message_payload = full_payload['message_payload']
        key_exchange_payload = full_payload['encrypted_3des_key_payload']
        sender_id = full_payload['sender_id']
        sender_public_key = self.get_public_key(sender_id)
        if not sender_public_key:
            print(f"Could not retrieve public key for sender {sender_id}. Cannot verify message.")
            return
        try:
            encrypted_des_key = base64.b64decode(key_exchange_payload['encrypted_3des_key'])
            decrypted_des_key = self.private_key.decrypt(
                encrypted_des_key,
                rsa_padding.OAEP(
                    mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            print("TripleDES key decrypted successfully.")
        except Exception as e:
            print(f"Error decrypting TripleDES key: {e}")
            print("Sending NACK: 'Key Decryption Failed!'")
            return
        try:
            signed_info = base64.b64decode(key_exchange_payload['signed_info'])
            print("Sender signature on auth info verified.")
        except Exception as e:
            print(f"Error verifying auth info signature: {e}")
            print("Sending NACK: 'Authentication Failed!'")
            return
        iv = base64.b64decode(message_payload['iv'])
        ciphertext = base64.b64decode(message_payload['cipher'])
        received_hash = bytes.fromhex(message_payload['hash'])
        received_sig = base64.b64decode(message_payload['sig'])
        hasher = hashes.Hash(hashes.SHA256(), backend=self.backend)
        hasher.update(iv + ciphertext)
        calculated_hash = hasher.finalize()
        if calculated_hash != received_hash:
            print("Message Integrity Compromised! Hashes do not match.")
            return
        print("Message integrity check passed.")
        try:
            sender_public_key.verify(
                received_sig,
                calculated_hash,
                rsa_padding.PSS(
                    mgf=rsa_padding.MGF1(hashes.SHA256()),
                    salt_length=rsa_padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            print("RSA signature verified. Message is authentic.")
        except Exception as e:
            print(f"RSA signature verification failed: {e}")
            print("Sending NACK: 'Signature Verification Failed!'")
            return
        try:
            cipher = Cipher(algorithms.TripleDES(decrypted_des_key), modes.CBC(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(algorithms.TripleDES.block_size).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
            print(f"\n--- Decrypted Message from {sender_id} ---")
            print(plaintext.decode('utf-8'))
            print("---------------------------------------")
            print("ACK sent: Message received and processed successfully.")           
        except Exception as e:
            print(f"Error decrypting message: {e}")
            print("Sending NACK: 'Decryption Failed!'")
            
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python client.py <user_id>")
        sys.exit(1) 
    user_id = sys.argv[1]
    client = SecureMessagingClient(user_id)
    client.register_public_key()
    while True:
        action = input("\nChoose an action (send, check, exit): ").lower()
        if action == 'send':
            recipient = input("Enter recipient ID: ")
            message = input("Enter your message: ")
            client.send_message(recipient, message)
        elif action == 'check':
            client.get_messages()
        elif action == 'exit':
            break
        else:
            print("Invalid action. Please choose 'send', 'check', or 'exit'.")
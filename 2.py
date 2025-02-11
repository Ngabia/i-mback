from bitcoin import *
from multiprocessing import Pool
import time
import signal
import sys
import os

# Constants
TARGET_ADDRESS = "1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9"
START_KEY = int("000000000000000000000000000000000000000000000002832ed74f2b5e35ee", 16)
END_KEY = int("0000000000000000000000000000000000000000000000349b84b6431a6c4ef1", 16)
BATCH_SIZE = 100000
NUM_PROCESSES = 8

# Global flags
shutdown_flag = False
key_found = False

def signal_handler(signum, frame):
    """Handle Ctrl+C by setting the shutdown flag"""
    global shutdown_flag
    print("\nShutdown signal received. Cleaning up...")
    shutdown_flag = True

def save_result_to_file(private_key_hex, address):
    """Save the found key and address to a file"""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"bitcoin_key_found_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write(f"Target Address: {address}\n")
        f.write(f"Private Key: {private_key_hex}\n")
        f.write(f"Time Found: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return filename

def private_key_to_addresses(private_key_int):
    """Generate both compressed and uncompressed addresses for a private key"""
    private_key = encode_privkey(private_key_int, 'hex')
    
    # Generate public keys
    pub_key_uncompressed = privtopub(private_key)
    pub_key_compressed = encode_pubkey(privtopub(private_key), 'hex_compressed')
    
    # Generate addresses
    address_uncompressed = pubtoaddr(pub_key_uncompressed)
    address_compressed = pubtoaddr(pub_key_compressed)
    
    return [address_uncompressed, address_compressed]

def process_batch(range_tuple):
    global shutdown_flag, key_found
    start_key, end_key = range_tuple
    start_time = time.time()
    keys_processed = 0
    total_keys_in_batch = end_key - start_key
    
    try:
        for private_key_int in range(start_key, end_key):
            if shutdown_flag or key_found:
                print(f"\nProcess handling range {start_key}-{end_key} shutting down...")
                return None
                
            try:
                addresses = private_key_to_addresses(private_key_int)
                
                keys_processed += 1
                if keys_processed % 1000 == 0:
                    elapsed_time = time.time() - start_time
                    speed = keys_processed / elapsed_time
                    percentage_complete = (keys_processed / total_keys_in_batch) * 100
                    print(f"Keys scanned: {keys_processed} | Progress: {percentage_complete:.2f}% | Speed: {speed:.2f} keys/sec", end='\r')
                
                if TARGET_ADDRESS in addresses:
                    key_found = True
                    private_key_hex = format(private_key_int, '064x')
                    filename = save_result_to_file(private_key_hex, TARGET_ADDRESS)
                    print(f"\nKey found and saved to {filename}")
                    print(f"Private Key: {private_key_hex}")
                    print(f"Target address: {TARGET_ADDRESS}")
                    os._exit(0)  # Immediately terminate all processes
                    
            except Exception as e:
                print(f"\nError processing key {format(private_key_int, '064x')}: {str(e)}")
                continue
                
    except KeyboardInterrupt:
        print(f"\nProcess handling range {start_key}-{end_key} received interrupt signal...")
        return None
            
    return None

def main():
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting Bitcoin Key Search")
    print(f"Target Address: {TARGET_ADDRESS}")
    print(f"Starting from: {format(START_KEY, '064x')}")
    print(f"Ending at: {format(END_KEY, '064x')}")
    
    total_keys = END_KEY - START_KEY
    batch_size = (total_keys + NUM_PROCESSES - 1) // NUM_PROCESSES
    
    ranges = []
    current = START_KEY
    while current < END_KEY:
        end = min(current + batch_size, END_KEY)
        ranges.append((current, end))
        current = end
    
    print(f"\nStarting search through {total_keys} keys using {NUM_PROCESSES} processes")
    start_time = time.time()
    
    try:
        with Pool(processes=NUM_PROCESSES) as pool:
            results = pool.map(process_batch, ranges)
        
        if not key_found:
            print("\nNo matching private key found in the given range.")
            print(f"Total time: {time.time() - start_time:.2f} seconds")
        
    except KeyboardInterrupt:
        print("\nMain process received interrupt signal...")
        print("Shutting down gracefully...")
        sys.exit(0)

if __name__ == "__main__":
    main()
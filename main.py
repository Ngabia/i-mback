from bitcoin import *
from multiprocessing import Pool
import time

# Constants
TARGET_ADDRESS = "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
START_KEY = int("0000000000000000000000000000000000000000000000000000000000000001", 16)
END_KEY = int("0000000000000000000000000000000000000000000000349b84b6431a6c4ef1", 16)
BATCH_SIZE = 100000
NUM_PROCESSES = 8

def private_key_to_addresses(private_key_int):
    """Generate both compressed and uncompressed addresses for a private key"""
    # Convert private key to hex string
    private_key = encode_privkey(private_key_int, 'hex')
    
    # Generate public key (compressed and uncompressed)
    public_key_uncompressed = encode_pubkey(privtopub(private_key), 'hex')
    public_key_compressed = encode_pubkey(privtopub(private_key), 'hex_compressed')
    
    # Generate addresses
    address_uncompressed = pubtoaddr(public_key_uncompressed)
    address_compressed = pubtoaddr(public_key_compressed)
    
    return [address_uncompressed, address_compressed]

def process_batch(range_tuple):
    start_key, end_key = range_tuple
    start_time = time.time()
    keys_processed = 0
    
    for private_key_int in range(start_key, end_key):
        try:
            # Process key and get addresses
            addresses = private_key_to_addresses(private_key_int)
            
            # Update progress
            keys_processed += 1
            if keys_processed % 1000 == 0:
                elapsed_time = time.time() - start_time
                speed = keys_processed / elapsed_time
                print(f"Process range {start_key}-{end_key}: {keys_processed} keys processed. "
                      f"Speed: {speed:.2f} keys/sec", end='\r')
            
            # Check if we found the target address
            if TARGET_ADDRESS in addresses:
                print(f"\nFound matching key: {hex(private_key_int)}")
                return private_key_int
                
        except Exception as e:
            print(f"\nError processing key {hex(private_key_int)}: {str(e)}")
            continue
            
    return None

def main():
    total_keys = END_KEY - START_KEY
    batch_size = (total_keys + NUM_PROCESSES - 1) // NUM_PROCESSES
    
    # Create ranges for each process
    ranges = []
    current = START_KEY
    while current < END_KEY:
        end = min(current + batch_size, END_KEY)
        ranges.append((current, end))
        current = end
    
    print(f"Starting search through {total_keys} keys using {NUM_PROCESSES} processes")
    print(f"Target address: {TARGET_ADDRESS}")
    
    start_time = time.time()
    
    with Pool(processes=NUM_PROCESSES) as pool:
        results = pool.map(process_batch, ranges)
    
    # Check results
    for result in results:
        if result:
            private_key_hex = hex(result)
            print(f"\nSuccess! Private key found: {private_key_hex}")
            # Verify the result
            addresses = private_key_to_addresses(result)
            print(f"Generated addresses: {addresses}")
            print(f"Total time: {time.time() - start_time:.2f} seconds")
            return
    
    print("\nNo matching private key found in the given range.")
    print(f"Total time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
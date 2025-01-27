from socket import *
import os
import hashlib
from urllib.parse import urlparse

"""
    A function to create and return a TCP server for 
    a given port number
"""
def create_server(port):
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)
    print(f"Proxy server running on port {port}")
    return server
 
"""
    A function to generate an unique MD5 hash in hexadecimal
    for a given url. Makes it convinient for storing the retrieved
    http responses in a cache folder
"""
def get_cache_path(url):
    return f"./cache1/{hashlib.md5(url.encode()).hexdigest()}.cache"

"""
    Extract the Last-Modified header from the HTTP response
"""
def get_last_modified(response):
    headers = response.split(b'\r\n\r\n')[0].decode()
    for line in headers.split('\r\n'):
        if line.lower().startswith('last-modified:'):
            return line.split(':', 1)[1].strip()
    return None

"""
    Parse the HTTP request from browser
"""
def parse_http_request(request):
    try:
        lines = request.split(b'\r\n')
        if not lines:
            return None
        
        first_line = lines[0].decode()
        _, url, _ = first_line.split()
        return url
    except:
        return None

"""
    Fetch content from server with conditional GET support
"""
def fetch_from_server(url, if_modified_since=None):
    parsed = urlparse(url)
    web_socket = socket(AF_INET, SOCK_STREAM)
    web_socket.connect((parsed.hostname, 80))
    
    request = f"GET {parsed.path or '/'} HTTP/1.1\r\n"
    request += f"Host: {parsed.hostname}\r\n"
    
    if if_modified_since:
        request += f"If-Modified-Since: {if_modified_since}\r\n"
    
    request += "Connection: close\r\n\r\n"
    
    web_socket.send(request.encode())
    
    response = b''
    while True:
        data = web_socket.recv(4096)
        if not data:
            break
        response += data
    
    web_socket.close()
    return response

"""
    If requested resource is in cache, then just serve it
    to the client
"""
def serve_from_cache(client_socket, cache_path, url):
    print(f"Serving from cache: {url}")
    with open(cache_path, 'rb') as f:
        client_socket.sendfile(f)

"""
    If resource was retrieved from the server, then save it 
    to the cache before sending the response
"""
def save_to_cache(response, cache_path):
    os.makedirs('./cache1', exist_ok=True)
    with open(cache_path, 'wb') as f:
        f.write(response)

"""
    Get the Last-Modified time from cached response
"""
def get_cached_last_modified(cache_path):
    with open(cache_path, 'rb') as f:
        response = f.read()
        return get_last_modified(response)
    
"""
    Handle all client connections with conditional GET support
"""
def handle_client(client_socket):
    request = b''
    while b'\r\n\r\n' not in request:
        chunk = client_socket.recv(4096)
        if not chunk:
            return
        request += chunk
    
    url = parse_http_request(request)

    if not url:
        client_socket.send(b"HTTP/1.0 400 Bad Request\r\n\r\n")
        return

    print(f"Requested URL: {url}")
    cache_path = get_cache_path(url)
    
    if os.path.exists(cache_path):
        last_modified = get_cached_last_modified(cache_path)
        
        if last_modified:
            print(f"Checking if cached content is still valid for: {url}")
            response = fetch_from_server(url, last_modified)
            
            if b"304 Not Modified" in response[:100]:
                print("Cache is still valid")
                serve_from_cache(client_socket, cache_path, url)
                return
            
            print("Cache is outdated, updating...")
            save_to_cache(response, cache_path)
            client_socket.send(response)

        else:
            serve_from_cache(client_socket, cache_path, url)

    else:
        print(f"Fetching: {url}")
        response = fetch_from_server(url)
        save_to_cache(response, cache_path)
        client_socket.send(response)
            

"""
    Main server loop
"""
server = create_server(4000)

while True:
    try:
        client_socket, addr = server.accept()
        print(f"Connection from {addr}")
        handle_client(client_socket)
        client_socket.close()

    except KeyboardInterrupt:
        print("\nShutting down server...")
        break

    except Exception as e:
        print(f"Error: {e}")

server.close()
import netifaces

# json generator
def generate_json(op, src_ip=None, path=None, msg=None, dst_ip=None, port=None, file_id=None):
    return {
        "op": op, 
        "src_ip": str(src_ip), 
        "path": str(path), 
        "msg": str(msg), 
        "dst_ip": str(dst_ip), 
        "port": str(port), 
        "file_id": str(file_id)
        }

def get_ip_address(ifname='enp0s8'):
    try:
        addresses = netifaces.ifaddresses(ifname)
        ip_address = addresses[netifaces.AF_INET][0]['addr']
        return str(ip_address)
    except (KeyError, IndexError) as e:
        print(f"Error getting IP address: {e}")
        return None
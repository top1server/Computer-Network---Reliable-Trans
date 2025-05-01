import socket
import struct
import zlib
from utils import make_packet, parse_packet, HEADER_SIZE

def run(args):
    print(f"[SW run] args={args}")
    if args.mode == 'sender':
        print("[SW run] Sender mode")
        _sw_sender(args)
    else:
        print("[SW run] Receiver mode")
        _sw_receiver(args)


def _sw_sender(args):
    print(f"[SW Sender] Sending to {args.host}:{args.port}, chunk={args.chunk}, timeout={args.timeout}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(args.timeout)
    seq = 0
    with open('input.dat', 'rb') as f:
        while True:
            data = f.read(args.chunk)
            if not data:
                break
            pkt = make_packet(seq, data)
            while True:
                sock.sendto(pkt, (args.host, args.port))
                print(f"[SW Sender] Sent seq={seq}, {len(data)} bytes")
                try:
                    raw, _ = sock.recvfrom(4)
                    ack = struct.unpack('!I', raw)[0]
                    print(f"[SW Sender] Received ACK={ack}")
                    if ack == seq:
                        seq ^= 1
                        break
                except socket.timeout:
                    print("[SW Sender] Timeout, resending seq", seq)
                    continue
    sock.close()


def _sw_receiver(args):
    print(f"[SW Receiver] Listening on {args.host}:{args.port}, chunk={args.chunk}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    expected = 0
    with open('output.dat', 'wb') as f:
        while True:
            packet, addr = sock.recvfrom(HEADER_SIZE + args.chunk)
            seq, chksum, payload = parse_packet(packet)
            ok = (zlib.crc32(payload) & 0xffffffff) == chksum
            print(f"[SW Receiver] Got seq={seq}, checksum_ok={ok}")
            if seq == expected and ok:
                f.write(payload)
                f.flush()
                expected ^= 1
            # always ack last in-order packet
            ack = expected ^ 1
            sock.sendto(struct.pack('!I', ack), addr)
            print(f"[SW Receiver] Sent ACK={ack}")
    sock.close()
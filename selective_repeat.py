import socket
import struct
import threading
import zlib
from utils import make_packet, parse_packet, HEADER_SIZE

def run(args):
    print(f"[RTP-opt run] args={args}")
    if args.mode == 'sender':
        print("[RTP-opt run] Sender mode")
        _sr_sender(args)
    else:
        print("[RTP-opt run] Receiver mode")
        _sr_receiver(args)


def _sr_sender(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.1)
    base = 0
    next_seq = 0
    window = {}
    lock = threading.Lock()
    sender_running = True
    eof_sent = False
    eof_acked = False

    def start_timer(seq):
        if seq not in window:
            return
        pkt, _ = window[seq]
        t = threading.Timer(args.timeout, lambda: timeout_handler(seq))
        window[seq] = (pkt, t)
        t.start()
        print(f"[RTP-opt Sender] Started timer for seq={seq}")

    def timeout_handler(seq):
        nonlocal sender_running
        if not sender_running:
            return
        with lock:
            if seq not in window:
                return
            pkt, _ = window[seq]
            print(f"[RTP-opt Sender] TIMEOUT seq={seq}, retransmitting only this packet")
            sock.sendto(pkt, (args.host, args.port))
            start_timer(seq)

    with open('input.dat', 'rb') as f:
        print(f"[RTP-opt Sender] Sending file with chunk={args.chunk}, window={args.window}")
        while not (eof_sent and eof_acked):
            with lock:
                while next_seq < base + args.window and not eof_sent:
                    data = f.read(args.chunk)
                    if not data:
                        eof_packet = make_packet(next_seq, b'EOF')
                        sock.sendto(eof_packet, (args.host, args.port))
                        print(f"[RTP-opt Sender] Sent EOF packet, seq={next_seq}")
                        window[next_seq] = (eof_packet, None)
                        start_timer(next_seq)
                        next_seq += 1
                        eof_sent = True
                        break
                    pkt = make_packet(next_seq, data)
                    sock.sendto(pkt, (args.host, args.port))
                    print(f"[RTP-opt Sender] Sent seq={next_seq}, {len(data)} bytes")
                    window[next_seq] = (pkt, None)
                    start_timer(next_seq)
                    next_seq += 1
            try:
                raw, _ = sock.recvfrom(4)
                ack = struct.unpack('!I', raw)[0]
                with lock:
                    print(f"[RTP-opt Sender] Received ACK={ack}")
                    if ack in window:
                        pkt, t = window.pop(ack)
                        if t:
                            t.cancel()
                            print(f"[RTP-opt Sender] Canceled timer for seq={ack}")
                        if eof_sent and ack == next_seq - 1 and not window:
                            eof_acked = True
                            print("[RTP-opt Sender] EOF has been acknowledged, transfer complete")
                    if ack == base:
                        base += 1
                        print(f"[RTP-opt Sender] Updated base to {base}")
            except socket.timeout:
                continue
    sender_running = False
    with lock:
        for seq, (_, t) in window.items():
            if t:
                t.cancel()
                print(f"[RTP-opt Sender] Canceled timer for seq={seq}")
    sock.close()
    print("[RTP-opt Sender] Transfer completed.")


def _sr_receiver(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    expected = 0
    buffer = {}
    received_bytes = 0
    eof_received = False

    print(f"[RTP-opt Receiver] Listening on {args.host}:{args.port}, chunk={args.chunk}")
    with open('output.dat', 'wb') as f:
        while not eof_received:
            packet, addr = sock.recvfrom(HEADER_SIZE + args.chunk)
            seq, chksum, payload = parse_packet(packet)
            ok = (zlib.crc32(payload) & 0xffffffff) == chksum
            print(f"[RTP-opt Receiver] Got seq={seq}, checksum_ok={ok}")
            if ok:
                ack_pkt = struct.pack('!I', seq)
                sock.sendto(ack_pkt, addr)
                print(f"[RTP-opt Receiver] Sent ACK={seq}")
                if payload == b'EOF':
                    print(f"[RTP-opt Receiver] Received EOF packet, seq={seq}")
                    eof_received = True
                    continue
                if expected <= seq < expected + args.window:
                    buffer[seq] = payload
                while expected in buffer:
                    data = buffer.pop(expected)
                    f.write(data)
                    f.flush()
                    received_bytes += len(data)
                    print(f"[RTP-opt Receiver] Wrote seq={expected} to file")
                    expected += 1
            else:
                print(f"[RTP-opt Receiver] Checksum failed for seq={seq}, discarding")
    print(f"[RTP-opt Receiver] Received {received_bytes} bytes, exiting.")
    sock.close()
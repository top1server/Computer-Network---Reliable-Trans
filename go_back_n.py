import socket
import struct
import threading
import zlib
import os
import time
from utils import make_packet, parse_packet, HEADER_SIZE

def run(args):
    print(f"[GBN run] args={args}")
    if args.mode == 'sender':
        print("[GBN run] Sender mode")
        _gbn_sender(args)
    else:
        print("[GBN run] Receiver mode")
        _gbn_receiver(args)

def _gbn_sender(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.1)
    base = 0
    next_seq = 0
    window = {}
    lock = threading.Lock()
    timer = None
    eof = False
    max_retries = 10
    retries = 0

    def start_timer():
        nonlocal timer
        if timer:
            timer.cancel()
        timer = threading.Timer(args.timeout, timeout_handler)
        timer.start()

    def timeout_handler():
        nonlocal retries
        with lock:
            print(f"[GBN Sender] TIMEOUT, retransmitting window {base}→{next_seq-1}")
            retries += 1
            if retries > max_retries:
                print(f"[GBN Sender] Max retries exceeded, giving up")
                return
            for s in range(base, next_seq):
                if s in window:  # Kiểm tra xem gói còn trong window không
                    sock.sendto(window[s], (args.host, args.port))
        start_timer()

    with open('input.dat', 'rb') as f:
        while not (eof and base == next_seq) and retries <= max_retries:
            # Gửi gói mới nếu cửa sổ chưa đầy
            with lock:
                while not eof and next_seq < base + args.window:
                    data = f.read(args.chunk)
                    if not data:
                        eof = True
                        # Gửi gói EOF để thông báo kết thúc file
                        eof_packet = make_packet(next_seq, b'EOF')
                        window[next_seq] = eof_packet
                        sock.sendto(eof_packet, (args.host, args.port))
                        print(f"[GBN Sender] Sent EOF packet, seq={next_seq}")
                        next_seq += 1
                        break
                    pkt = make_packet(next_seq, data)
                    window[next_seq] = pkt
                    sock.sendto(pkt, (args.host, args.port))
                    print(f"[GBN Sender] Sent seq={next_seq}, {len(data)} bytes")
                    if base == next_seq:
                        start_timer()
                    next_seq += 1
            # Đợi ACK hoặc timeout
            try:
                raw, _ = sock.recvfrom(4)
                ack = struct.unpack('!I', raw)[0]
                with lock:
                    print(f"[GBN Sender] Received ACK={ack}")
                    # Chỉ cập nhật base nếu ack > base
                    if base < ack <= next_seq:
                        # Xóa các gói đã được xác nhận
                        for s in range(base, ack):
                            if s in window:
                                del window[s]
                        base = ack
                        retries = 0  # Reset số lần thử lại
                        if base == next_seq:
                            if timer:
                                timer.cancel()
                        else:
                            start_timer()
            except (socket.timeout, ConnectionResetError):
                continue

    # Dọn dẹp
    if timer:
        timer.cancel()
    sock.close()
    print("[GBN Sender] Transfer completed.")

def _gbn_receiver(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    expected = 0
    received_bytes = 0
    eof_received = False

    with open('output.dat', 'wb') as f:
        print(f"[GBN Receiver] Listening on {args.host}:{args.port}, chunk={args.chunk}")
        while not eof_received:
            try:
                packet, addr = sock.recvfrom(HEADER_SIZE + args.chunk)
            except ConnectionResetError:
                continue
            
            seq, chksum, payload = parse_packet(packet)
            ok = (zlib.crc32(payload) & 0xffffffff) == chksum
            print(f"[GBN Receiver] Got seq={seq}, checksum_ok={ok}")
            
            # Kiểm tra EOF
            if payload == b'EOF' and seq == expected and ok:
                print("[GBN Receiver] Received EOF packet")
                eof_received = True
                expected += 1
            # Nếu là gói đúng thứ tự và checksum hợp lệ
            elif seq == expected and ok:
                f.write(payload)
                f.flush()
                received_bytes += len(payload)
                expected += 1

            # Luôn gửi ACK cho gói tiếp theo mong đợi
            ack = expected
            sock.sendto(struct.pack('!I', ack), addr)
            print(f"[GBN Receiver] Sent ACK={ack}")

    print(f"[GBN Receiver] Received {received_bytes} bytes, exiting.")
    sock.close()

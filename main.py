import argparse
import sys
from stop_and_wait import run as sw_run
from go_back_n import run as gbn_run
from selective_repeat import run as sr_run

print(f"[Main] sys.argv: {sys.argv}")
parser = argparse.ArgumentParser(
    prog="reliable_transport",
    description="Simple reliable transport: SW, GBN, SR over UDP"
)
parser.add_argument('-p','--protocol', choices=['sw','gbn','sr'], required=True,
                    help="Protocol: sw=Stop-and-Wait, gbn=Go-Back-N, sr=Selective Repeat")
parser.add_argument('--mode', choices=['sender','receiver'], required=True,
                    help="Mode: sender or receiver")
parser.add_argument('--host', default='127.0.0.1',
                    help="Destination IP (sender) or bind address (receiver)")
parser.add_argument('--port', type=int, required=True,
                    help="UDP port to send to or listen on")
parser.add_argument('--window', type=int, default=4,
                    help="Window size for gbn/sr")
parser.add_argument('--timeout', type=float, default=0.5,
                    help="Retransmission timeout in seconds")
parser.add_argument('--chunk', type=int, default=1024,
                    help="Payload size per packet in bytes")

def main():
    args = parser.parse_args()
    print(f"[Main] Parsed args: {args}")
    if args.protocol == 'sw':
        print("[Main] Running SW protocol")
        sw_run(args)
    elif args.protocol == 'gbn':
        print("[Main] Running GBN protocol")
        gbn_run(args)
    else:
        print("[Main] Running SR protocol")
        sr_run(args)

if __name__ == '__main__':
    main()

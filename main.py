import argparse
from go_back_n import run as gbn_run
from selective_repeat import run as sr_run

parser = argparse.ArgumentParser(
    prog="reliable_transport",
    description="Simple reliable transport: GBN, SR(opt) over UDP"
)
parser.add_argument('-p','--protocol', choices=['gbn','opt'], required=True,
                    help="Protocol: gbn=Go-Back-N, opt=Selective Repeat (RTP-opt)")
parser.add_argument('--mode', choices=['sender','receiver'], required=True,
                    help="Mode: sender or receiver")
parser.add_argument('--host', default='127.0.0.1',
                    help="Destination IP (sender) or bind address (receiver)")
parser.add_argument('--port', type=int, required=True,
                    help="UDP port to send to or listen on")
parser.add_argument('--window', type=int, default=4,
                    help="Window size for gbn/opt")
parser.add_argument('--timeout', type=float, default=0.5,
                    help="Retransmission timeout in seconds")
parser.add_argument('--chunk', type=int, default=1024,
                    help="Payload size per packet in bytes")

def main():
    args = parser.parse_args()
    if args.protocol == 'gbn':
        gbn_run(args)
    else:
        sr_run(args)

if __name__ == '__main__':
    main()

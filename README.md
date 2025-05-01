### Option in main.py:
  -h, --help            show this help message and exit
  -p {sw,gbn,sr}, --protocol {sw,gbn,sr}
                        Protocol: sw=Stop-and-Wait, gbn=Go-Back-N, sr=Selective Repeat
  --mode {sender,receiver}
                        Mode: sender or receiver
  --host HOST           Destination IP (sender) or bind address (receiver)
  --port PORT           UDP port to send to or listen on
  --window WINDOW       Window size for gbn/sr
  --timeout TIMEOUT     Retransmission timeout in seconds
  --chunk CHUNK         Payload size per packet in bytes

### Open 2 termials
Example in Go-back-N protocol:
Run test:
- Teminal A:
python main.py -p gbn --mode receiver --host 127.0.0.1 --port 9000 --chunk 1024

- Teminal B:
python main.py -p gbn --mode sender --host 127.0.0.1 --port 9000 --window 5 --timeout 0.2 --chunk 1024
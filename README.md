### Option in main.py:
```
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
```

### Open 2 terminals
Example in Go-back-N protocol:

Run test:
- Seting error in Clumsy

- Reliable Trans base:
+ Teminal A: Init receiver
```
python main.py -p gbn --mode receiver --host 127.0.0.1 --port 9000 --chunk 1024
```

+ Teminal B: Run sender
```
python main.py -p gbn --mode sender --host 127.0.0.1 --port 9000 --window 5 --timeout 2 --chunk 1024
```

+ Check 2 file input.dat and output.dat:
```
fc /b input.dat output.dat && echo PASS || echo FAIL
```
- opt:
```
python main.py -p opt --mode receiver --host 127.0.0.1 --port 9000 --chunk 1024
python main.py -p opt --mode sender --host 127.0.0.1 --port 9000 --timeout 2 --chunk 1024
```
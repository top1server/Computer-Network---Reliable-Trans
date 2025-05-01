### Option in main.py:
```
usage: reliable_transport [-h] -p {gbn,opt} --mode {sender,receiver} [--host HOST] --port PORT [--window WINDOW]
                          [--timeout TIMEOUT] [--chunk CHUNK]

Simple reliable transport: GBN, SR(opt) over UDP

options:
  -h, --help            show this help message and exit
  -p {gbn,opt}, --protocol {gbn,opt}
                        Protocol: gbn=Go-Back-N, opt=Selective Repeat (RTP-opt)
  --mode {sender,receiver}
                        Mode: sender or receiver
  --host HOST           Destination IP (sender) or bind address (receiver)
  --port PORT           UDP port to send to or listen on
  --window WINDOW       Window size for gbn/opt
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

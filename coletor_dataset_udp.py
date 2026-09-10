import socket
import struct
import cv2
import numpy as np
import time
import struct

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

import socket

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

UDP_IP = "0.0.0.0"
UDP_PORT = 5001

sock.bind((UDP_IP, UDP_PORT))
print(" Listening for UDP packets on port {}...".format(UDP_PORT))

CPX_HEADER_SIZE = 4  # 2 bytes length + 1 byte dst + 1 byte src
IMG_HEADER_MAGIC = 0xBC
IMG_HEADER_SIZE = 11  # Magic + Width + Height + Depth + Type + Sizepython udp  

# Track per-address stream state
streams = {}

# Define the ESP32's IP and port (gateway of the drone's AP network, "WiFi streaming example")
ESP32_IP = "192.168.4.1"
ESP32_PORT = 5000           # Port on which ESP32 is listening

# Define the magic byte
MAGIC_BYTE = magic = b'FER'

import os

# Criando a estrutura de pastas do Dataset
pastas = {
    '0_open': 'dataset/0_open',
    '1_close': 'dataset/1_close',
    '2_pointer': 'dataset/2_pointer',
    '3_ok': 'dataset/3_ok',
    'fundo': 'dataset/fundo' #fotos sem a mão!
}

for pasta in pastas.values():
    os.makedirs(pasta, exist_ok=True)

# Contadores de fotos salvas
contadores = {k: 0 for k in pastas.keys()}
print("Modo de Coleta Iniciado! Pressione 0, 1, 2, 3 ou F para salvar as fotos. ESC para sair.\n")


# Send the magic byte to the ESP32
print(f"Sending magic byte to ESP32 at {ESP32_IP}:{ESP32_PORT}")
sock.sendto(MAGIC_BYTE, (ESP32_IP, ESP32_PORT))

while True:
    data, addr = sock.recvfrom(2048)

    if addr not in streams:
        if len(streams) >= 3:
            print(f" Ignoring {addr} — max 3 streams reached")
            continue
        streams[addr] = {
            'buffer': bytearray(),
            'expected_size': None,
            'receiving': False,
            'packet_count': 0,
            'window_name': f"Stream from {addr[0]}:{addr[1]}",
            'last_frame_time': None
        }
        print(f" New stream: {streams[addr]['window_name']}")

    stream = streams[addr]

    # Check for image header
    if len(data) >= CPX_HEADER_SIZE + 1 and data[CPX_HEADER_SIZE] == IMG_HEADER_MAGIC:
        payload = data[CPX_HEADER_SIZE:]
        if len(payload) < IMG_HEADER_SIZE:
            print(" Incomplete image header")
            continue

        _, width, height, depth, fmt, size = struct.unpack('<BHHBBI', payload[:IMG_HEADER_SIZE])
        stream['expected_size'] = size
        stream['width'] = width
        stream['height'] = height
        stream['depth'] = depth
        stream['fmt'] = fmt
        stream['buffer'] = bytearray(payload[IMG_HEADER_SIZE:])
        stream['receiving'] = True
        stream['packet_count'] = 1  # Start counting from the header packet

    elif stream['receiving']:
        stream['buffer'].extend(data[CPX_HEADER_SIZE:])
        stream['packet_count'] += 1

        if stream['expected_size'] is not None and len(stream['buffer']) >= stream['expected_size']:
            now = time.time()
            if stream['last_frame_time'] is not None:
                delta = now - stream['last_frame_time']
                fps = 1.0 / delta if delta > 0 else 0.0
                #print(f" [{addr}] Time since last frame: {delta:.3f}s (FPS: {fps:.2f})")
            stream['last_frame_time'] = now

            #print(f" [{addr}] Image received in {stream['packet_count']} packets")

            try:
                np_data = np.frombuffer(stream['buffer'], np.uint8)
                if stream.get('fmt') == 0:  # RAW_ENCODING: raw grayscale bytes, no container format
                    h, w, d = stream['height'], stream['width'], stream['depth']
                    decoded = np_data.reshape((h, w)) if d == 1 else np_data.reshape((h, w, d))
                else:  # JPEG_ENCODING
                    decoded = cv2.imdecode(np_data, cv2.IMREAD_UNCHANGED)
                if decoded is not None:
                    # 1. Amplia a imagem para enxergar bem os gestos na tela
                    view_img = cv2.resize(decoded, (648, 488), interpolation=cv2.INTER_NEAREST)

                    # 2. Escreve o placar na imagem ampliada (view_img)
                    texto = f"Fotos: Open({contadores['0_open']}) Close({contadores['1_close']}) Pointer({contadores['2_pointer']})"
                    cv2.putText(view_img, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
                    
                    # 3. Mostra a janela ampliada
                    cv2.imshow(stream['window_name'], view_img)
                    
                    # Lógica de Captura pelo Teclado
                    key = cv2.waitKey(1) & 0xFF
                    categoria = None

                    if key == ord('0'): categoria = '0_open'
                    elif key == ord('1'): categoria = '1_close'
                    elif key == ord('2'): categoria = '2_pointer'
                    elif key == ord('3'): categoria = '3_ok'
                    elif key == ord('f'): categoria = 'fundo'
                    elif key == 27: break # Tecla ESC para sair

                    # Se apertou alguma tecla válida, salva a imagem ORIGINAL pequena
                    if categoria:
                        contadores[categoria] += 1
                        caminho = f"{pastas[categoria]}/img_{contadores[categoria]:05d}.png"
                        
                        # Foi salvo a 'decoded' (imagem bruta), para o treinamento do DORY ficar fiel ao hardware!
                        cv2.imwrite(caminho, decoded) 
                        print(f"Salvo: {caminho}")
                else:
                    print(f" [{addr}] Failed to decode image")
            except Exception as e:
                print(f" [{addr}] Decode error: {e}")

            stream['receiving'] = False
            stream['expected_size'] = None
            stream['packet_count'] = 0

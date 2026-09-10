import socket
import struct
import cv2
import numpy as np
import os

# Configurações do Wi-Fi do Drone
deck_ip = "192.168.4.1"
deck_port = 5000

# Criando a estrutura de pastas do Dataset
pastas = {
    '0_open': 'dataset/0_open',
    '1_close': 'dataset/1_close',
    '2_pointer': 'dataset/2_pointer',
    '3_ok': 'dataset/3_ok',
    'fundo': 'dataset/fundo' # Muito importante ter fotos sem a mão!
}

for pasta in pastas.values():
    os.makedirs(pasta, exist_ok=True)

# Contadores de fotos salvas
contadores = {k: 0 for k in pastas.keys()}

print(f"Conectando ao AI-deck em {deck_ip}:{deck_port}...")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((deck_ip, deck_port))
print("Conectado! Pressione as teclas 0, 1, 2, 3 ou F para salvar as fotos. ESC para sair.\n")

def rx_bytes(size):
    data = bytearray()
    while len(data) < size:
        data.extend(client_socket.recv(size-len(data)))
    return data

while True:
    try:
        # Lendo os pacotes da câmera (Protocolo CPX da Bitcraze)
        packetInfoRaw = rx_bytes(4)
        [length, routing, function] = struct.unpack('<HBB', packetInfoRaw)
        imgHeader = rx_bytes(length - 2)
        [magic, width, height, depth, format_img, size] = struct.unpack('<BHHBBI', imgHeader)

        if magic == 0xBC and format_img == 0: # Garante que é a imagem RAW em tons de cinza
            imgStream = bytearray()
            while len(imgStream) < size:
                packetInfoRaw = rx_bytes(4)
                [length_chunk, dst, src] = struct.unpack('<HBB', packetInfoRaw)
                imgStream.extend(rx_bytes(length_chunk - 2))
            
            # Converte os bytes puros para imagem
            bayer_img = np.frombuffer(imgStream, dtype=np.uint8).reshape((244, 324))
            
            # Amplia a imagem APENAS para você enxergar melhor na tela
            view_img = cv2.resize(bayer_img, (648, 488), interpolation=cv2.INTER_NEAREST)
            
            # Mostra o placar na tela
            texto = f"Fotos: Open({contadores['0_open']}) Close({contadores['1_close']}) Pointer({contadores['2_pointer']})"
            cv2.putText(view_img, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
            
            cv2.imshow('Coletor de Dataset (Aperte 0, 1, 2, 3)', view_img)

            # Lógica de Captura pelo Teclado
            key = cv2.waitKey(1) & 0xFF
            categoria = None
            
            if key == ord('0'): categoria = '0_open'
            elif key == ord('1'): categoria = '1_close'
            elif key == ord('2'): categoria = '2_pointer'
            elif key == ord('3'): categoria = '3_ok'
            elif key == ord('f'): categoria = 'fundo'
            elif key == 27: break # ESC

            # Se apertou alguma tecla válida, salva a imagem ORIGINAL (324x244)
            if categoria:
                contadores[categoria] += 1
                caminho = f"{pastas[categoria]}/img_{contadores[categoria]:05d}.png"
                # SALVAMOS A IMAGEM bayer_img PEQUENA, POIS É ELA QUE O GAP8 E O DORY VÃO LER!
                cv2.imwrite(caminho, bayer_img)
                print(f"Salvo: {caminho}")

    except Exception as e:
        print(f"Conexão perdida: {e}")
        break

client_socket.close()
cv2.destroyAllWindows()
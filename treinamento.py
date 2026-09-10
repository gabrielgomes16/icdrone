import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, random_split
import nemo
import os
import numpy as np

# 1. CONFIGURAÇÕES
PASTA_DATASET = 'dataset'
TAMANHO_IMAGEM = (128, 128)
BATCH_SIZE = 32
EPOCAS = 40 

device = torch.device("cpu") 

# A FIX DA ESCALA: Treinar com a mesma escala que a câmera do drone enviará (0 a 255)
transformacoes = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize(TAMANHO_IMAGEM),
    transforms.ToTensor(), # Retorna float de 0.0 a 1.0
    transforms.Lambda(lambda x: x * 255.0) # Mapeia para float 0.0 a 255.0
])

dataset_completo = datasets.ImageFolder(root=PASTA_DATASET, transform=transformacoes)
num_classes = len(dataset_completo.classes)

tamanho_treino = int(0.8 * len(dataset_completo))
tamanho_val = len(dataset_completo) - tamanho_treino
train_ds, val_ds = random_split(dataset_completo, [tamanho_treino, tamanho_val])

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)

# 2. ARQUITETURA
class DroneCNN(nn.Module):
    def __init__(self, num_classes):
        super(DroneCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(2, 2) # Saída: 64x64
        
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(2, 2) # Saída: 32x32
        
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.relu3 = nn.ReLU()
        self.pool3 = nn.MaxPool2d(2, 2) # Saída: 16x16
        
        # O FIX DO COMPILADOR: Dimensão estática em vez de adaptativa
        self.gap = nn.AvgPool2d(kernel_size=16) # Reduz 16x16 para 1x1 estaticamente
        
        self.fc1_conv = nn.Conv2d(64, 64, kernel_size=1) 
        self.relu4 = nn.ReLU()
        
        self.fc2_conv = nn.Conv2d(64, num_classes, kernel_size=1)
        self.flatten = nn.Flatten()

    def forward(self, x):
        x = self.pool1(self.relu1(self.conv1(x)))
        x = self.pool2(self.relu2(self.conv2(x)))
        x = self.pool3(self.relu3(self.conv3(x)))
        x = self.gap(x)
        x = self.fc1_conv(x)
        x = self.relu4(x)
        x = self.fc2_conv(x)
        x = self.flatten(x)
        return x

modelo = DroneCNN(num_classes).to(device)
criterio = nn.CrossEntropyLoss()
otimizador = optim.Adam(modelo.parameters(), lr=0.001)

# 3. TREINAMENTO
print("Treinando o modelo...")
for epoca in range(EPOCAS):
    modelo.train()
    for imagens, rotulos in train_loader:
        otimizador.zero_grad()
        saidas = modelo(imagens)
        perda = criterio(saidas, rotulos)
        perda.backward()
        otimizador.step()
    print(f"Época {epoca+1} concluída.")

# 4. QUANTIZAÇÃO E EXPORTAÇÃO OFICIAL NEMO
print("\nIniciando quantização NEMO PACT...")
modelo.eval()

# O FIX DO DUMMY INPUT: Imagem falsa também precisa refletir valores de 0 a 255
dummy_input = torch.rand(1, 1, 128, 128) * 255.0 

modelo_quantizado = nemo.transform.quantize_pact(modelo, dummy_input=dummy_input)

print("Calibrando...")
modelo_quantizado.eval()
with torch.no_grad():
    for i, (imagens, _) in enumerate(train_loader):
        modelo_quantizado(imagens)
        if i > 5: break

print("Transformando grafo Fake-Quantized para Quantized-Deployable (QD)...")
# Como o dataset treinou com valores de 0 a 255, eps_in=1.0
modelo_quantizado.qd_stage(eps_in=1.0)

print("Transformando QD para Integer-Deployable (ID)...")
modelo_quantizado.id_stage()

# Congelando as variáveis
for param in modelo_quantizado.parameters():
    param.requires_grad = False

caminho_onnx = "cerebro_drone.onnx"
print("Exportando ONNX para DORY...")

if not os.path.exists('test'): os.makedirs('test')

print("Gerando arquivos de teste para todas as camadas...")

# Gera a entrada como Inteiro de 8 bits para o DORY
input_int = dummy_input.detach().numpy().astype(np.int64)
np.savetxt('test/input.txt', input_int.flatten(), fmt='%d')

outputs = []
def hook_fn(module, input, output):
    if isinstance(module, (nn.Conv2d, nn.MaxPool2d, nn.Linear, nn.AvgPool2d)):
        outputs.append(output.detach().numpy())

for layer in modelo_quantizado.modules():
    layer.register_forward_hook(hook_fn)

with torch.no_grad():
    modelo_quantizado(dummy_input)

for i, out in enumerate(reversed(outputs)):
    filename = f'test/out_layer{i}.txt'
    np.savetxt(filename, out.flatten().astype(np.int64), fmt='%d')
    print(f"Gerado: {filename}")

# Exportação ONNX Final
nemo.utils.export_onnx(caminho_onnx, modelo_quantizado, modelo_quantizado, list(dummy_input.shape)[1:])

print(f"\n[SUCESSO] Modelo salvo: {caminho_onnx}")
print("[SUCESSO] Arquivos de teste salvos na pasta 'test/'")
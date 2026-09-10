# Interação humano-drone
## Passo a passo
Aqui está o tutorial de como configurar o drone da Bitcraze e fazer o treinamento de imagem por meio da rede neural **DORY**. Antes de começar os passos, recomendo que faça esses passos em um sistema operacional Linux(particularmente indico o Ubuntu), tenha o Docker instalado e além dos materias físicos do drone, tenha também um J-TAG ou J-link que serão utilizados para fazer o flash do GAP8.


### Passo 1 - Montagem do drone
Primeiro temos que montar o drone. Para isso, indico o [site da Bitcraze](https://www.bitcraze.io/documentation/tutorials/getting-started-with-crazyflie-2-x/), neste link há o tutorial de como montar o drone, além de apresentar alguns idicadores básicos, como o que cada LED faz. Para esse link recomendo ir até o **_getting to know your Crazyflie_**, mas recomendo ler toda a página para já ter uma ideia do que será feito.

### Passo 2 - Baixar drivers do Crazyradio 2.0
Nesse [link](https://www.bitcraze.io/documentation/tutorials/getting-started-with-crazyradio-2-0/) temos o tutorial de como baixar os drivers, de modo geral será necessário configurar as opções de usb no seu computador, fazer o download do firmware e fazer o flash com o crazyradio em modo booloader(está tudo explicado na página).

## Passo 3 - Baixar o Crazyflie Client
Primeiro, crie um ambiente virtual em python, pois o client pode dar conflito com outras bibliotecas. Dessa forma, para criar esse ambiente faça:
```bash
python -m venv /caminho/para/novo/ambiente/virtual
```
ou dependendo da versão:
```bash
python3 -m venv /caminho/para/novo/ambiente/virtual
```

Exemplo para criar na pasta local:
```bash
python -m venv venv_cfclient
```

Após ter criado o ambiente virtual, para ativá-lo basta fazer o seguinte comando:

```bash
source <venv>/bin/activate
```

Caso queira desativá-lo, apenas digite o comando `exit`.

Beleza, agora vamos baixar as bibliotecas necessárias para utilizar o client, faça os comandos a seguir:
```bash
sudo apt install git python3-pip libxcb-xinerama0 libxcb-cursor0
pip3 install --upgrade pip
```

E agora sim baixamos o **Client**(lembrando de que é preciso estar com o ambiente virtual ativado):
```bash
pip install cfclient
```

Para ativá-lo, apenas digite no terminal `cfclient`.
Se tudo der certo, a aba como a imagem abaixo será aberta:
<img width="1697" height="929" alt="image" src="https://github.com/user-attachments/assets/5f1d97f3-83c4-44d0-8c5d-305c4b9b3782" />

Caso tenha tido problemas nesse passo, aqui estão os links que utilizei como base:
- [Ambiente Virtual](https://docs.python.org/pt-br/3/library/venv.html)

- [Instalação do Client](https://www.bitcraze.io/documentation/repository/crazyflie-clients-python/master/installation/install/)

- Caso queira saber mais como o Cfclient: [Guia Cfclient](https://www.bitcraze.io/documentation/repository/crazyflie-clients-python/master/userguides/userguide_client/#firmware-upgrade)

## Passo 4 - Colocar o AI-Deck e atualizar o firmware
Se ainda não tiver colocado o AI-Deck, agora é a hora, apenas o encaixe em cima da placa principal do drone. Se o LED verde do AI-Deck ligar, significa que está funcionando. Para atualizar o firmware, siga os passos da página [Getting started with the AI deck](https://www.bitcraze.io/documentation/tutorials/getting-started-with-aideck/) na seção **_Update Crazyflie and AIdeck firmware_**.

## Passo 5 - GAP8 Bootloader
Nessa etapa, ainda estaremos utilizando como base a mesma página do passo anterior [Getting started with the AI deck](https://www.bitcraze.io/documentation/tutorials/getting-started-with-aideck/), só que agora é a seção **_Gap8 bootloader_**.
Antes de partir para os comandos, conecte o J-link/J-Tag no drone e no PC, observe que o cabo de conexão tem uma faixa vermelha. Ela deve estar inserida, tanto no drone quanto no J-link no lado indicado com ``01``, como mostram as figuras a seguir:


<img width="615" height="486" alt="image" src="https://github.com/user-attachments/assets/38d99f17-298f-47dc-b3c2-4dc25b41b03b" />

<img width="1200" height="1600" alt="WhatsApp Image 2026-09-02 at 19 49 28" src="https://github.com/user-attachments/assets/1c44cc18-1f7a-40f5-a596-9c0664e67740" />

Depois de conectado, faça os passos em **_Gap8 bootloader_**, mas com uma observação, se estiver utilizando o J-link ao invés do J-Tag, o comando de export é diferente, sendo ele:
`export GAPY_OPENOCD_CABLE=interface/jlink.cfg`. O J-link se comunica via USB puro, por isso é preciso trocá-lo também: ``--volume=/dev/bus/usb:/dev/bus/usb``

Seguindo o mesmo modelo do que o feito no guia:
```bash
docker run --rm -it -v $PWD:/module/ --volume=/dev/bus/usb:/dev/bus/usb --privileged -P bitcraze/aideck /bin/bash -c 'export GAPY_OPENOCD_CABLE=interface/jlink.cfg; source /gap_sdk/configs/ai_deck.sh; cd /module/;  make all image flash'
```

Com isso, o flash será feito e toda vez que alterado um programa que será utilizado apenas pelo sistema embarcado(drone) é necessário fazer o flash da aplicação novamente com o comando ``make clean all run``.

## Passo 6 - Wifi, Coletor de Fotos e Treinamento
### Wifi
Ainda com base na mesma página [Getting started with the AI deck](https://www.bitcraze.io/documentation/tutorials/getting-started-with-aideck/), agora na seção **_Flash Wifi Example_**, siga os passos para que consiga assim ligar a câmera do drone e transmitir sua imagem em tempo real para o Computador.
Obeservação: a interface de imagem pode travar após alguns segundos depois de executar o programa `python opencv-viewer.py`, fazendo que tenha que reiniciar o drone para assim poder executar o programa novamente. Se esse problema continuar, talvez seja preciso alterar o protocolo de transporte TCP para UDP. 

**Obs:Se para você, após testar a câmera do drone e não travar utilizando TCP, pode pular para o _Pegar IP e Conda_**


Para isso, troquei fiz o programa de coleta de fotos utilizando UDP com base nessa discussão:[UDP](https://github.com/bitcraze/aideck-gap8-examples/issues/150). Primeiro, você acessará a discussão linkada e irá até a mensagem do gemenerik que começa com: *_@marijana23 from LARICS (University of Zagreb) was so kind to share their workaround in these forks:_* e fazer o que ele diz. De maneira resumida, será preciso baixar o repositório *aideck-esp-firmware-udp* e fazer o flash dele com o J-link. Dentro do repositório *aideck-esp-firmware-udp*, faça esse comando ``docker run --rm -it -v $PWD:/module/ --privileged -P bitcraze/builder /bin/bash -c "source /new_home/.espressif/python_env/idf4.3_py3.10_env/bin/activate && make"`` e depois fazer o flash via rádio com o comando ``cfloader flash build/aideck_esp.bin deck-bcAI:esp-fw -w radio://0/80/2M/E7E7E7E7E7`` . Caso depois que der 100% ficar travado por mais de 20s, pode dar Ctrl+C que não tem problema. Lembrando que se for necessário configurar o wifi, veja a as instruções na discussão.

### Pegar IP e Conda
Após isso, ligue o drone, conecte ao ``WiFi streaming example``, abra um novo terminal linux e faça o comando ``ip route`` para saber qual é o IP do ESP32. A saída que tiver ``default via...`` é a que tem o IP, no caso é o primeiro que aparece - ex: ``default via 192.168.4.1 dev wlp0s20f3 proto dhcp src 192.168.4.2 metric 20600``, o IP do ESP será *192.168.4.1*. Guarde esse IP que será utilizado futuramente.

Todavia, os programas de coleta e treinamento das fotos para o drone já estão feitos e estão na pasta `treinamento_drone`. Portanto, só será preciso baixar a pasta(caso não tenha baixado o repositório ainda):
```bash
git clone treinamento_drone
```
Beleza, após baixar a pasta será preciso primeiro baixar o *_Conda_*(ambiente virtual que será utilizado, pois teremos que utilizar uma outra versão do python), assim para baixar basta verificar a documentação e como instalar por meio desses links: [Instalação Conda](https://www.anaconda.com/docs/getting-started/miniconda/install/linux-install) e [Como utilizar o Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html#managing-python).

Após baixar o Conda, faça os seguintes comandos dentro da pasta ``treinamento_drone``:
```bash
conda create -n treinamento_drone python=3.10
conda activate treinamento_drone
pip install -r requirements.txt
python patch_nemo.py
```
O último comando serve para corrigir alguns bugs de compatibilidade com o PyTorch que dão erro na hora de executar o ``treinamento.py``.

### Coletor de Fotos e Treinamento
Dessa forma, o ambiente será criado com a versão do python e os pacotes adequados para executar os programas. Antes de executá-los, é preciso trocar o local do ESP32_IP na linha 39, pelo IP que foi guardado anteriormente. Depois de trocá-lo execute primeiro o programa ``coletor_dataset_udp.py`` para tirar as fotos com a câmera do drone(o drone deve estar ligado e a crazyradio conectada à sua máquina). Recomendo tirar 300 fotos de cada comando.
Exemplo de cada comando:
1. Tecla ``0`` - Mão aberta
<img width="324" height="244" alt="image" src="https://github.com/user-attachments/assets/8749b3f0-f1d2-41e6-92ca-e4597180852f" />
   
2. Tecla ``1`` - Mão fechada
<img width="324" height="244" alt="image" src="https://github.com/user-attachments/assets/8c135698-be8f-4cb6-b045-866cf9d6570d" />

3. Tecla ``2`` - Dedo indicador
<img width="324" height="244" alt="image" src="https://github.com/user-attachments/assets/440e01b4-8fab-4b2f-ab00-92843403192a" />
   
4. Tecla ``3`` - Sinal de OK
<img width="324" height="244" alt="image" src="https://github.com/user-attachments/assets/984a0a26-8941-4fe2-a6fb-d7e60fc5d373" />
   
5. Tecla ``f`` - Foto sem mão, fundo
<img width="324" height="244" alt="image" src="https://github.com/user-attachments/assets/1e5c097b-368c-4dd6-9578-3fe9d0103093" />

Lembrando também que caso queira adicionar mais ou trocar comanados, basta atualizar a estrutura de pastas do Dataset e lógica de captura do teclado.

Agora, com as fotos coletadas basta executar o ``treinamento.py`` que gerará o arquivo ``cerebro_drone.onnx``.

## Passo 7 - Passar o arquivo para a rede neural DORY via GAP8
### A. Obter a imagem Docker com o DORY pronto (`dory_ready_image`)

Constrir a imagem Docker a partir da imagem oficial da Bitcraze:

```bash
docker pull bitcraze/aideck
docker run --rm -it --privileged --volume=/dev/bus/usb:/dev/bus/usb bitcraze/aideck bash
```

Dentro do container:

```bash
source /gap_riscv_toolchain_ubuntu_18/gap_sdk/configs/ai_deck.sh

apt-get update
apt-get install -y software-properties-common python3-apt
pip3 install --upgrade pip setuptools wheel
pip3 install onnx==1.10.0 --only-binary :all:

cd /gap_riscv_toolchain_ubuntu_18/gap_sdk/tools
git clone https://github.com/pulp-platform/dory.git
cd dory
python3 -m pip install -e .
git config --file .gitmodules submodule.dory/Hardware_targets/PULP/Backend_Kernels/pulp-nnx.url https://github.com/pulp-platform/pulp-nnx.git
git submodule sync
git submodule update --init --recursive
```

Sem fechar esse container, em **outro terminal** no host, transforme-o numa
imagem reutilizável:

```bash
docker ps                              
# anota o CONTAINER_ID do bash acima
docker commit <CONTAINER_ID> dory_ready_image
```

### B. Treinar o modelo e gerar o `.onnx`

Já coberto no `README.md` deste repositório:

```bash
pip install -r requirements.txt
python patch_nemo.py
python treinamento.py
```

Isso gera `cerebro_drone.onnx` (exportado em opset 9) + `test/*.txt`.

### C. Organizar a pasta de exportação

```bash
mkdir -p ~/ic/aideck-gap8-examples/dory_gesture_export
cp ~/Desktop/iczada/treinamento_drone/cerebro_drone.onnx ~/ic/aideck-gap8-examples/dory_gesture_export/
cp ~/Desktop/iczada/treinamento_drone/test/*.txt ~/ic/aideck-gap8-examples/dory_gesture_export/
```

### D. Criar o arquivo de configuração do DORY

```bash
cat > ~/ic/aideck-gap8-examples/dory_gesture_export/config.json << 'EOF'
{
    "BNRelu_bits": 32,
    "onnx_file": "cerebro_drone_dory.onnx",
    "code reserved space": 95000
}
EOF
```

### E. Corrigir o `.onnx` antes de gerar o código

O `torch.onnx.export` cria um nó `Identity` (bias duplicado bit-a-bit) que o parser do DORY não suporta, e nomeia as saídas dos nós de forma "legível" em vez de inteiros sequenciais, que é o que o parser do DORY espera. Crie estes dois scripts auxiliares na pasta de exportação:

```bash
cat > ~/ic/aideck-gap8-examples/dory_gesture_export/fix_onnx.py << 'EOF'
import sys
import onnx
from onnx import numpy_helper

src, dst = sys.argv[1], sys.argv[2]
m = onnx.load(src)
g = m.graph
initializers_by_name = {init.name: init for init in g.initializer}
for node in [n for n in g.node if n.op_type == 'Identity']:
    src_name, dst_name = node.input[0], node.output[0]
    arr = numpy_helper.to_array(initializers_by_name[src_name]).copy()
    g.initializer.append(numpy_helper.from_array(arr, name=dst_name))
    g.node.remove(node)
    print(f"Resolvido: {dst_name} agora tem seu proprio inicializador (copia de {src_name})")
onnx.checker.check_model(m)
onnx.save(m, dst)
print(f"Salvo: {dst}")
EOF

cat > ~/ic/aideck-gap8-examples/dory_gesture_export/rename_outputs.py << 'EOF'
import sys
import onnx

src, dst = sys.argv[1], sys.argv[2]
m = onnx.load(src)
g = m.graph
rename_map, counter = {}, 0
for node in g.node:
    for out in node.output:
        if out not in rename_map:
            rename_map[out] = str(counter); counter += 1
for node in g.node:
    node.input[:] = [rename_map.get(i, i) for i in node.input]
    node.output[:] = [rename_map.get(o, o) for o in node.output]
for out in g.output:
    if out.name in rename_map:
        out.name = rename_map[out.name]
onnx.checker.check_model(m)
onnx.save(m, dst)
print(f"Renomeado: {counter} saidas de nos para inteiros sequenciais -> {dst}")
EOF
```

### F. Entrar no container e gerar o código C

```bash
docker run --rm -it --privileged -v ~/ic/aideck-gap8-examples:/aideck --volume=/dev/bus/usb:/dev/bus/usb dory_ready_image bash
```

Dentro do container:

```bash
pip3 install "protobuf==3.20.0" "numpy==1.23.5" "ortools<9.4" pyelftools

cd /aideck/dory_gesture_export
python3 fix_onnx.py cerebro_drone.onnx cerebro_drone_fixed.onnx
python3 rename_outputs.py cerebro_drone_fixed.onnx cerebro_drone_dory.onnx

cd /gap_riscv_toolchain_ubuntu_18/gap_sdk/tools/dory
rm -rf /aideck/dory_gesture_export/generated
python3 network_generate.py NEMO PULP.GAP8 /aideck/dory_gesture_export/config.json --app_dir /aideck/dory_gesture_export/generated
```

### G. Corrigir dois bugs conhecidos do código gerado

```bash
cd /aideck/dory_gesture_export/generated
sed -i 's/out_mult, out_shift,/out_mult_in, out_shift_in,/g' src/*.c
sed -i '/APP_CFLAGS += -DNUM_CORES=\$(CORE)/a APP_CFLAGS += -DSINGLE_CORE_DMA' Makefile
```
- O primeiro é um tipo de geração do próprio DORY (aparece em qualquer   projeto gerado por essa versão).
- O segundo evita corrupção de dados: o GAP8 tem só um controlador de DMA compartilhado entre os 8 núcleos do cluster, e o Makefile gerado por essa versão do DORY não ativa essa flag sozinho.

## H. Compilar e gravar no drone (via JTAG)

Com o drone conectado por USB/JTAG:

```bash
source /gap_sdk/configs/ai_deck.sh
export GAPY_OPENOCD_CABLE=interface/jlink.cfg
make clean all run platform=board CORE=8
```

## 8. Problema atual

A gravação e o boot funcionam, e os pesos são carregados da flash para a RAM (mensagem `Input in L3` aparece na saída do JTAG) — mas a execução trava sem erro nem timeout, exigindo interromper manualmente (Ctrl+C). Aqui é onde o problema acontece e não consegui avançar mais depois disso. A partir desse ponto, dependendo da época que estiver trabalhando com esse projeto pode ser que a Bitcraze tenha resolvido e trazido uma alternativa mais fácil, visto que o problema atual tem a ver provavelmente com o GAP8 que foi criado por uma empresa chamada [GREENWAVES](https://github.com/orgs/bitcraze/discussions/1854) que faliu em 2025 (pouco tempo desde a postagem desse projeto). Por conta disso, acredito que mais para a frente a Bitcraze trará uma maneira mais fácil de resolver esse problema.

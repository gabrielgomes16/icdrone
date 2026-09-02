# Interação humano-drone
## Passo a passo
Aqui está o tutorial de como configurar o drone da Bitcraze e fazer o treinamento de imagem por meio da rede neural **DORY**. Antes de começar os passos, recomendo que faça esses passos em um sistema operacional Linux(particularmente indico o Ubuntu), tenha o Docker instalado e além dos materias físicos do drone, tenha também um J-TAG ou J-link que serão utilizados para fazer o flash do GAP8.


### Passo 1 - Montagem do drone
Primeiro temos que montar o drone. Para isso, indico o [site da Bitcraze](https://www.bitcraze.io/documentation/tutorials/getting-started-with-crazyflie-2-x/), neste link há o tutorial de como montar o drone, além de apresentar alguns idicadores básicos, como o que cada LED faz. Para esse link recomendo ir até o **_getting to know your Crazyflie_**, mas recomendo ler toda a página para já ter uma ideia do que será feito.

### Passo 2 - Baixar drivers do Crazyradio 2.0
Nesse [link](https://www.bitcraze.io/documentation/tutorials/getting-started-with-crazyradio-2-0/) temos o tutorial de como baixar os drivers, de modo geral será necessário configurar as opções de usb no seu computador, fazer o download do firmware e fazer o flash com o crazyradio em modo booloader(está tudo explicado na página).

## Passo 3 - Baixar o Crazyflie Client
Primeiro, crie um ambiente virtual em python, pois o client pode dar conflito com outras bibliotecas. Dessa forma, para criar esse ambiente faça:
```
python -m venv /caminho/para/novo/ambiente/virtual
```
ou dependendo da versão:
```
python3 -m venv /caminho/para/novo/ambiente/virtual
```

Exemplo para criar na pasta local:
```
python -m venv venv_cfclient
```

Após ter criado o ambiente virtual, para ativá-lo basta fazer o seguinte comando:

```
$ source <venv>/bin/activate
```

Caso queira desativá-lo, apenas digite o comando `exit`.

Beleza, agora vamos baixar as bibliotecas necessárias para utilizar o client, faça os comandos a seguir:
```
sudo apt install git python3-pip libxcb-xinerama0 libxcb-cursor0
pip3 install --upgrade pip
```

E agora sim baixamos o **Client**(lembrando de que é preciso estar com o ambiente virtual ativado):
```
pip install cfclient
```

Para ativá-lo, apenas digite no terminal `cfclient`.
Se tudo der certo, a aba como a imagem abaixo será aberta:
<img width="1697" height="929" alt="image" src="https://github.com/user-attachments/assets/5f1d97f3-83c4-44d0-8c5d-305c4b9b3782" />

Caso tenha tido problemas nesse passo, aqui estão os links que utilizei como base:
[Ambiente Virtual](https://docs.python.org/pt-br/3/library/venv.html)

[Instalação do Client](https://www.bitcraze.io/documentation/repository/crazyflie-clients-python/master/installation/install/)

Caso queira saber mais como o Cfclient: [Guia Cfclient](https://www.bitcraze.io/documentation/repository/crazyflie-clients-python/master/userguides/userguide_client/#firmware-upgrade)

## Passo 4 - Colocar o AI-Deck e atualizar o firmware
Se ainda não tiver colocado o AI-Deck, agora é a hora, apenas o encaixe em cima da placa principal do drone. Se o LED verde do AI-Deck ligar, significa que está funcionando. Para atualizar o firmware, siga os passos da página [Getting started with the AI deck](https://www.bitcraze.io/documentation/tutorials/getting-started-with-aideck/) na seção **_Update Crazyflie and AIdeck firmware_**.

## Passo 5 - GAP8 Bootloader
Nessa etapa, ainda estaremos utilizando como base a mesma página do passo anterior [Getting started with the AI deck](https://www.bitcraze.io/documentation/tutorials/getting-started-with-aideck/), só que agora é a seção **_Gap8 bootloader_**.
Antes de partir para os comandos, conecte o J-link/J-Tag no drone e no PC, observe que o cabo de conexão tem uma faixa vermelha. Ela deve estar inserida, tanto no drone quanto no J-link no lado indicado com ``01``, como mostram as figuras a seguir:


<img width="615" height="486" alt="image" src="https://github.com/user-attachments/assets/38d99f17-298f-47dc-b3c2-4dc25b41b03b" />

<img width="1200" height="1600" alt="WhatsApp Image 2026-09-02 at 19 49 28" src="https://github.com/user-attachments/assets/1c44cc18-1f7a-40f5-a596-9c0664e67740" />

Depois de conectado, faça os passos em **_Gap8 bootloader_**, mas com uma observação, se estiver utilizando o J-link ao invés do J-Tag, o comando de export é diferente, sendo ele:
`export GAPY_OPENOCD_CABLE=interface/jlink.cfg`

Seguindo o mesmo modelo do que o feito no guia:
```
$ docker run --rm -it -v $PWD:/module/ --device /dev/ttyUSB0 --privileged -P bitcraze/aideck /bin/bash -c 'export GAPY_OPENOCD_CABLE=interface/jlink.cfg; source /gap_sdk/configs/ai_deck.sh; cd /module/;  make all image flash'
```

Com isso o flash será feito e toda vez que alterado um programa que será utilizado apenas pelo sistema embarcado(drone) é necessário fazer o flash do GAP8 bootloader novamente.

## Passo 5 - Wifi
Ainda com base na mesma página [Getting started with the AI deck](https://www.bitcraze.io/documentation/tutorials/getting-started-with-aideck/), agora na seção **_Flash Wifi Example_**, siga os passos para que consiga assim ligar a câmera do drone e transmitir sua imagem em tempo real para o Computador.
Obeservação: a interface de imagem pode travar após alguns segundos depois de executar o programa `python opencv-viewer.py`, fazendo que tenha que reiniciar o drone para assim poder executar o programa novamente. Se esse problema continuar, talvez seja preciso alterar o protocolo de transporte TCP para UDP. Para isso, será preciso que siga o tutorial desse repositório: [UDP](https://github.com/larics/aideck-gap8-examples/tree/master)



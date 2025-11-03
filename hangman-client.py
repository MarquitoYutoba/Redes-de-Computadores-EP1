import socket
import sys

# Função para enviar mensagem para o servidor
def enviar_msg_server(socket_client, mensagem_base):
    mensagem_completa = (mensagem_base + '\r\n').encode('ascii',errors='replace')
    socket_client.sendall(mensagem_completa)

# Função para receber mensagem do servidor
def receber_msg_server(socket_client, buffer_do_cliente):
    while True:
        dados = socket_client.recv(1024)

        if not dados:
            return None, buffer_do_cliente

        buffer_do_cliente += dados

        if b'\r\n' in buffer_do_cliente:
            indice_terminador = buffer_do_cliente.find(b'\r\n')
            msg_bytes = buffer_do_cliente[:indice_terminador]
            msg_string = msg_bytes.decode('ascii',errors='replace')
            buffer_do_cliente = buffer_do_cliente[indice_terminador + 2:]

            return msg_string, buffer_do_cliente

def fechar_conexao(socket_client):
    socket_client.close()

def E_UNEXPECTED_MESSAGE(esperado, mensagem, socket_client):
    if mensagem != esperado and mensagem.find('ERROR') == -1:
        enviar_msg_server(socket_client, 'ERROR UNEXPECTED_MESSAGE')
        fechar_conexao(socket_client)
        sys.exit('ERROR UNEXPECTED_MESSAGE')

if len(sys.argv) == 2:
    nome = sys.argv[1]
    host_server = "127.0.0.1"
    porta_server = 6891

elif len(sys.argv) == 3:
    nome = sys.argv[1]
    host_port = sys.argv[2]
    host_server, porta_server = host_port.split(":")
    porta_server = int(porta_server)

else:
    sys.exit(1)

print('Conectando ao servidor...')
socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_client.connect((host_server, porta_server))
buffer_recebimento = b''

enviar_msg_server(socket_client, f'NEWPLAYER {nome}')
mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
E_UNEXPECTED_MESSAGE('STANDBY', mensagem, socket_client)
print('Aguardando o jogo começar...')

mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
partes = mensagem.split()
if partes[0] == 'MASTER':
    print('Você é o mestre do jogo!')
    palavra = str(input('Digite a palavra: '))
    enviar_msg_server(socket_client, f'WORD {palavra}')
    mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
    E_UNEXPECTED_MESSAGE('OK', mensagem, socket_client)
    mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
    partes = mensagem.split()

E_UNEXPECTED_MESSAGE('NEWGAME', mensagem.split()[0], socket_client)
print('Jogo iniciado!')
vidas = int(partes[1])
tamanho_palavra = int(partes[2])
print(f'Vidas para advinhar: {vidas}')
print(f'Tamanho da palavra: {tamanho_palavra}.')
print()

letras_incorretas = []
palavras_incorretas = []
while True:
    mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
    partes = mensagem.split()
    if partes[0] == 'YOURTURN':
        palpite = str(input(r'Digite sua jogada (letra ou palavra), ou \q para sair: '))
        if palpite == r'\q':
            enviar_msg_server(socket_client, 'QUIT')
            mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
            E_UNEXPECTED_MESSAGE('OK', mensagem, socket_client)
            sys.exit(0)
        if len(palpite) == 1:
            enviar_msg_server(socket_client, f'GUESS LETTER {palpite}')
            mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
        else:
            enviar_msg_server(socket_client, f'GUESS WORD {palpite}')
            mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
        E_UNEXPECTED_MESSAGE('OK', mensagem, socket_client)
        mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
        partes = mensagem.split()

    if partes[0] == 'GAMEOVER':
        print('O jogo terminou.')
        if partes[1] == 'WIN':
            print(f'A palavra {partes[3]} foi adivinhada por {partes[2]}!')
        elif partes[1] == 'LOSE':
            print(f'A palavra {partes[3]} não foi adivinhada. Último palpite por: {partes[2]}')
        sys.exit(0)

    elif partes[0] == 'STATUS':
        if vidas != int(partes[1]):
            if len(partes[4]) > 1:
                if partes[4] not in palavras_incorretas:
                    palavras_incorretas.append(partes[4])
            if len(partes[4]) == 1:
                if partes[4] not in letras_incorretas:
                    letras_incorretas.append(partes[4])
                    letras_incorretas.sort()
            vidas = int(partes[1])
        print(f"Jogador {partes[3]} fez uma jogada: {partes[4]}. Restam {partes[1]} vidas")
        print(f"Letras erradas: {' '.join(letras_incorretas)}")
        print(f"Palavras erradas: {' '.join(palavras_incorretas)}")


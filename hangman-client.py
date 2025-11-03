import socket
import sys

# Função para enviar mensagem para o servidor
def enviar_msg_server(socket_client, mensagem_base):
    mensagem_completa = (mensagem_base + '\r\n').encode('ascii')
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

def Contem_invalido(mensagem):
    mensagem = mensagem.split()
    for x in mensagem:
        if not mensagem.isalnum():
            return True
        
def Valida_espaco(mensagem):
    palavras = mensagem.split()
    if len(palavras) == 1:
        return mensagem.count(' ') == 0
    return len(palavras)-1 == mensagem.count(' ')

def E_INVALID_FORMAT(mensagem_original, socket_client):
    if Contem_invalido(mensagem_original) or Valida_espaco(mensagem_original):
        enviar_msg_server(socket_client, 'ERROR INVALID_FORMAT')
        fechar_conexao(socket_client)
        sys.exit('ERROR INVALID_FORMAT')

def E_UNEXPECTED_MESSAGE(esperado, mensagem, socket_client):
    if mensagem != esperado and mensagem.find('ERROR') == -1:
        enviar_msg_server(socket_client, 'ERROR UNEXPECTED_MESSAGE')
        fechar_conexao(socket_client)
        sys.exit('ERROR UNEXPECTED_MESSAGE')

nome = sys.argv[1]
if len(sys.argv) == 3:
    host_server = sys.argv[2].split(':')[0]
    porta_server = int(sys.argv[2].split(':')[1])
elif len(sys.argv) > 3:
    entrada = ''
    entrada = entrada.join(sys.argv)
    nome = entrada[entrada.find(' ')+1:entrada.rfind(' ')-1]
    endereco = entrada[entrada.rfind(' '):]
    host_server = endereco.split(':')[0]
    porta_server = int(endereco.split(':')[1])
else:
    host_server = '127.0.0.1'
    porta_server = 6891

print('Conectando ao servidor...')
socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_client.connect((host_server, porta_server))
buffer_recebimento = b''

enviar_msg_server(socket_client, f'NEWPLAYER {nome}\n')
mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
E_INVALID_FORMAT(mensagem, socket_client)
E_UNEXPECTED_MESSAGE('STANDBY', mensagem, socket_client)
print('Aguardando o jogo começar...')

mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
E_INVALID_FORMAT(mensagem, socket_client)
partes = mensagem.split()
if partes[0] == 'MASTER':
    print('Você é o mestre do jogo!')
    palavra = str(input('Digite a palavra: '))
    enviar_msg_server(socket_client, f'WORD {palavra}')
    mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
    E_INVALID_FORMAT(mensagem, socket_client)
    E_UNEXPECTED_MESSAGE('OK', mensagem, socket_client)
    mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
    partes = mensagem.split()

E_INVALID_FORMAT(mensagem, socket_client)
E_UNEXPECTED_MESSAGE('NEWGAME', mensagem.split[0], socket_client)
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
    E_INVALID_FORMAT(mensagem, socket_client)
    partes = mensagem.split()
    if partes[0] == 'YOURTURN':
        palpite = str(input(r'Digite sua jogada (letra ou palavra), ou \q para sair: '))
        if palpite == r'\q':
            enviar_msg_server(socket_client, 'QUIT')
            mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
            E_INVALID_FORMAT(mensagem, socket_client)
            E_UNEXPECTED_MESSAGE('OK', mensagem, socket_client)
            sys.exit(0)
        if len(palpite) == 1:
            enviar_msg_server(socket_client, f'GUESS LETTER {palpite}')
            mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
            E_INVALID_FORMAT(mensagem, socket_client)
        else:
            enviar_msg_server(socket_client, f'GUESS WORD {palpite}')
            mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
            E_INVALID_FORMAT(mensagem, socket_client)

        E_UNEXPECTED_MESSAGE('OK', mensagem, socket_client)
        mensagem, buffer_recebimento = receber_msg_server(socket_client, buffer_recebimento)
        E_INVALID_FORMAT(mensagem, socket_client)
        partes = mensagem.split()

    if partes[0] == 'GAMEOVER':
        print('O jogo terminou.')
        if partes[1] == 'WIN':
            print(f'A palavra {partes[3]} foi adivinhada por {partes[2]}!')
        elif partes[1] == 'LOSE':
            print(f'A palavra {partes[3]} não foi adivinhada. Último palpite por: {partes[2]}')
        break

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
        print(f'Letras erradas: {' '.join(letras_incorretas)}')
        print(f'Palavras erradas: {' '.join(palavras_incorretas)}')
        print(f'Jogador {partes[3]} fez uma jogada: {partes[4]}. Restam {partes[1]} vidas')

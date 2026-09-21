# Guia de Configuração com Dev Container (ROS 2 Rover)

Este guia destina-se a iniciantes que desejam configurar e executar o projeto **ros2_rover** rapidamente utilizando **VS Code Dev Containers**. 

Com o Dev Container, você não precisa instalar manualmente o ROS 2, Gazebo, Python, C++ ou dependências no seu sistema operacional hospedeiro. Tudo roda de forma isolada e pronta para uso dentro de um container Docker pré-configurado.

---

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter os seguintes programas instalados no seu computador:
0. **Linux**. A distribuição que a gente vai usar vai ser o Ubuntu 24.04 LTS. Então caso você não tenha, é necessario instalar o WSL no windowns.
1. **Docker**:
   - **Linux**: [Docker Engine](https://docs.docker.com/engine/install/)
2. **Visual Studio Code (VS Code)**: [Baixar VS Code](https://code.visualstudio.com/)
3. **Extensão Dev Containers no VS Code**:
   - Abra o VS Code, vá na aba de extensões (`Ctrl+Shift+X` ou `Cmd+Shift+X`) e procure por **Dev Containers** (criada pela Microsoft). Clique em **Instalar**.

---

## 🚀 Como Inicializar o Ambiente (Passo a Passo)

### 1. Permitir acesso à interface gráfica (Apenas no Linux)
Se você estiver utilizando Linux no hospedeiro e quiser visualizar as simulações do Gazebo e o RViz2, execute o seguinte comando no terminal do seu computador antes de abrir o container:

```bash
xhost +local:root
```

### 2. Abrir o Projeto no VS Code
Abra a pasta do repositório `ros2_rover` no VS Code:
- Menu `Arquivo` > `Abrir Pasta...` > selecione a pasta `ros2_rover`.

### 3. Reabrir no Container
Ao abrir a pasta, o VS Code exibirá uma notificação no canto inferior direito perguntando se deseja **"Reopen in Container"** (Reabrir no Container).

Caso a notificação não apareça:
1. Pressione `Ctrl + Shift + P` (ou `Cmd + Shift + P` no Mac) para abrir a Paleta de Comandos.
2. Digite e selecione: **`Dev Containers: Reopen in Container`**.

### 4. Aguardar o Build Inicial
Na primeira vez que você abrir o Dev Container:
- O Docker baixará a imagem base do **ROS 2 Jazzy**.
- O ambiente instalará os pacotes e dependências automaticamente (`rosdep install`).
- O projeto será compilado automaticamente com o `colcon build`.

> ⏳ **Nota:** A primeira compilação pode levar alguns minutos dependendo da sua conexão de internet e processador. Nas execuções seguintes, o carregamento será quase instantâneo.

---

## 🛠️ Como Usar e Testar o Projeto

Quando o container carregar, abra o terminal integrado do VS Code (`Ctrl + '` ou menu `Terminal` > `Novo Terminal`).

O terminal já estará dentro do container (`/workspaces/ros2_ws/src/ros2_rover`) e com as variáveis do ROS 2 devidamente configuradas.

### Compilando o Código (Se você fizer alterações)
Caso faça alterações no código C++ ou Python e precise recompilar:

```bash
cd /workspaces/ros2_ws
colcon build
source install/setup.bash
```

---

### 🌌 Simulações no Gazebo

Você pode iniciar as simulações do rover em diferentes cenários pré-configurados:

#### 1. Simulação na Lua (Moon) - *Funcionando*
```bash
ros2 launch rover_gazebo moon.launch.py
```

#### 2. Simulação em Marte (Mars) e Floresta (Forest) - *Em Manutenção / Com Falha Atualmente*
> ⚠️ **Aviso:** Os arquivos de launch `mars.launch.py` e `forest.launch.py` não estão funcionando no momento.

---

### 🕹️ Teleoperação (Controle por Teclado ou Joystick)

O pacote de teleoperação é o **`rover_teleop`**.

#### 1. Teleoperação por Teclado (Keyboard)
Para controlar o robô usando o teclado (WASD / setas do teclado):
```bash
ros2 run rover_teleop teleop_keyboard_node
```

#### 2. Teleoperação por Joystick / Gamepad (PS3 / USB)
Para controlar o robô com um joystick PS3 / controle USB:
```bash
ros2 launch rover_teleop joy_teleop.launch.py
```

---

## ❓ Resolução de Problemas Comuns (Troubleshooting)

### 1. Erro no RViz2 / Gazebo (`Authorization required, but no authorization protocol specified` ou `could not connect to display :0`)
- **Causa:** O servidor X11 do seu Linux (computador hospedeiro) bloqueia por padrão que containers Docker exibam janelas gráficas sem autorização explícita.
- **Solução Rápida:** No terminal da sua máquina **hospedeira** (no seu Linux, **fora** do container/VS Code), execute o comando:
  ```bash
  xhost +local:root
  ```
  *(Se preferir liberar para qualquer conexão local no seu usuário: `xhost +`)*

- Em seguida, tente rodar o `rviz2` ou as simulações no terminal do container novamente. O RViz2 abrirá normalmente!

### 2. Quero refazer o build do Container do zero
- **Solução:** Pressione `Ctrl + Shift + P` e selecione **`Dev Containers: Rebuild Container`**.

### 3. Conectando dispositivos USB (Motores LX-16A, LiDAR Hokuyo ou Joystick)
- O container foi configurado com `--privileged`, o que significa que portas seriais e dispositivos conectados ao seu computador (como `/dev/ttyUSB0` ou `/dev/input/js0`) são mapeados automaticamente para dentro do container.

---

## 📂 Estrutura do Dev Container

- `.devcontainer/Dockerfile`: Define a imagem base ROS 2 Jazzy e instala os utilitários de sistema e bibliotecas do Gazebo/RViz2.
- `.devcontainer/devcontainer.json`: Configura a integração com o VS Code, mapeamento de pastas do workspace (`/workspaces/ros2_ws`), extensões automáticas de C++, Python e ROS, e permissões de rede/GUI.

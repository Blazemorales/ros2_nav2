---
title: "Comandos Essenciais — Simulação Gazebo do Rover"
meta_title: "Comandos Essenciais"
description: "Passo a passo completo, sequencial e testado para compilar e rodar a simulação do rover Sawppy no Gazebo (mundos Moon/Mars/Forest), com SLAM e exploração autônoma."
draft: false
---

{{< toc >}}

Guia sequencial para sair do zero até o rover explorando sozinho no Gazebo.
Baseado no repositório [`ros2_rover`](https://github.com/mgonzs13/ros2_rover)
(fork `aresunbrovers/ros2_rover`, branch `jazzy`).

## Pré-requisitos

- **Docker** instalado no host. Todo o ROS 2 roda dentro do container — **não
  instale ROS 2 / colcon direto no host**, o `Dockerfile` da raiz do repo já
  cuida disso a partir da imagem `ros:jazzy` (que traz Gazebo Harmonic via
  `ros_gz_sim`).
- **Servidor X11** no host, só se você quiser a GUI do Gazebo. Sem isso, use
  o modo `headless` (ver seção 5).
- O repositório clonado na raiz, onde está o `Dockerfile`.

## 1. Build da imagem Docker

```shell
cd ~/Documentos/ros2_rover   # raiz do repo, onde está o Dockerfile
docker build -t rover .
```

O que esse `Dockerfile` faz por baixo:

1. Parte de `ros:jazzy` e copia o repositório para `/root/ros2_ws/src`.
2. Instala dependências de sistema (`gcc`, `git`, `wget`, `python3`, `python3-pip`).
3. Roda `rosdep install --from-paths src --ignore-src -r -y` para instalar
   todas as dependências ROS declaradas nos `package.xml` de cada pacote
   (inclui `ros2controlcli`, `gz_ros2_control`, `ros_gz_sim`, `ros_gz_bridge`,
   `controller_manager`, `rviz2`, etc.).
4. Compila o workspace inteiro com `colcon build`.
5. Deixa `source /root/ros2_ws/install/setup.bash` já no `~/.bashrc` do container.

## 2. Subir o container

**Uso rápido/efêmero** (some ao sair, bom pra testar a imagem):

```shell
docker run -it --rm rover
```

**Uso de desenvolvimento** (monta o repo do host dentro do container e
habilita a GUI do Gazebo via X11):

```shell
xhost +local:docker   # autoriza o container a abrir janelas no X11 do host
                       # (não persiste entre reboots do host — repita se a GUI
                       # falhar com "Authorization required, but no authorization
                       # protocol specified")

docker run -it --name rover_dev \
  -v $(pwd):/workspaces/ros2_ws \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  rover bash
```

Container já criado antes? Só reabrir:

```shell
docker start rover_dev
docker exec -it rover_dev bash
```

## 3. Compilar o workspace (dentro do container)

```shell
cd /root/ros2_ws          # ou /workspaces/ros2_ws se você montou o volume
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

## 4. Rodar o rover real (bringup, sem simulação)

```shell
ros2 launch rover_bringup rover.launch.py
```

## 5. Rodar a simulação no Gazebo

Três mundos prontos:

```shell
ros2 launch rover_gazebo moon.launch.py
ros2 launch rover_gazebo mars.launch.py
ros2 launch rover_gazebo forest.launch.py
```

### Argumentos úteis (`moon.launch.py`)

| Argumento          | Default      | Descrição                                                                  |
| ------------------ | ------------ | --------------------------------------------------------------------------- |
| `headless`          | `False`      | roda `gz sim -s` (servidor apenas, sem GUI) — evita gastar CPU renderizando |
| `slam`              | `True`       | sobe o `slam_toolbox` (mapeamento)                                          |
| `explore`           | `True`       | sobe o `explore_lite` (exploração autônoma via Nav2, frontier exploration)  |
| `launch_rviz`       | `True`       | abre o RViz2                                                                |
| `nav2_planner`      | `SmacHybrid` | `SmacHybrid` ou `SmacLattice`                                               |
| `nav2_controller`   | `RPP`        | `RPP` ou `TEB`                                                              |

Exemplo — exploração autônoma completa, sem gastar recursos com a GUI (bom
para testar rápido ou rodar em CI):

```shell
ros2 launch rover_gazebo moon.launch.py slam:=True explore:=True headless:=True
```

Ver detalhes de como esse fluxo de SLAM + exploração + Nav2 foi validado (e
os bugs corrigidos no caminho) no [Diário de Bordo](/diario-de-bordo).

## 6. Serviço Linux (opcional, produção/boot automático)

```shell
cd ~/ros2_ws/src/ros2_rover/rover_service
sudo ./install.sh
sudo service rover status
```

## Limpando processos travados

Dentro do container, evite `pkill -f` com padrões genéricos como `ros2`: eles
casam com a própria linha de comando do `docker exec bash -c "..."` (que
contém `/ros2_ws/`) e podem matar o processo errado — inclusive o PID 1 do
container. Prefira matar por PID:

```shell
ps -eo pid=,comm= | awk '$1 != 1 {print $1}' | xargs -r kill
```

## Dependências externas

| Dependência | Onde é usada | Como é resolvida |
| --- | --- | --- |
| Docker | build/execução de tudo | instalar manualmente no host |
| ROS 2 Jazzy | base do workspace | vem na imagem `ros:jazzy` do Dockerfile |
| Gazebo Harmonic | simulação 3D | trazido pelas dependências `ros_gz_sim` / `ros_gz_bridge` via rosdep |
| `gz_ros2_control` | controllers do rover na simulação | rosdep, declarado em `rover_gazebo/package.xml` |
| `ros2controlcli` | ativa os controllers (`ros2 control load_controller ...`) | rosdep, declarado em `rover_gazebo/package.xml` |
| `slam_toolbox` | mapeamento (SLAM) | pacote `rover_slam` |
| `explore_lite` (fork `robo-friends/m-explore-ros2`) | exploração autônoma de fronteiras | pacote `rover_slam` |
| Nav2 (`SmacHybrid`/`SmacLattice` + `RPP`/`TEB`) | navegação/desvio de obstáculos | pacote `rover_navigation`, já existente no repo upstream |
| X11 (`xhost`) | GUI do Gazebo dentro do container | só necessário se `headless:=False` |

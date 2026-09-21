# Status: navegação autônoma (SLAM + exploração + Nav2) — FUNCIONANDO

Objetivo: rover simulado explora sozinho (frontier exploration) e navega com Nav2
evitando obstáculos, sem teleop e sem goals manuais.

**Confirmado funcionando de ponta a ponta** (headless e com GUI): o rover se move
sozinho via `explore_lite` + Nav2, o `/map` do `slam_toolbox` cresce continuamente,
e não aparecem mais avisos de "Robot is out of bounds of the costmap".

## Decisão de escopo

Não recriamos `rover_nav2` (não existia de fato). O repo já tinha `rover_navigation`
(SmacHybrid/SmacLattice + RPP/TEB) funcionando. Estendemos com um pacote novo
`rover_slam` (slam_toolbox + AMCL + explore_lite), sem tocar em
`rover_motor_controller_cpp/serial.cpp` e `.hpp` (edições locais do usuário,
propositalmente não commitadas/tocadas).

## O que foi feito

- Novo pacote `rover_slam/`:
  - `config/slam_toolbox.yaml`, `config/amcl.yaml`, `config/explore_params.yaml`
  - `launch/slam.launch.py` (slam_toolbox como lifecycle node, configure->activate)
  - `launch/amcl.launch.py` (map_server + amcl + lifecycle_manager_localization)
  - `launch/explore.launch.py` (explore_lite, do fork robo-friends/m-explore-ros2)
- `rover_gazebo/launch/gazebo.launch.py` modificado:
  - args novos: `slam` (default True), `explore` (default True), `map`,
    `headless` (default False — roda `gz sim -s`, sem GUI, útil para
    testes/CI sem gastar CPU em renderização)
  - trocou o include único de `rover_localization/launch/localization.launch.py`
    (que também subia o rtabmap) por dois includes separados:
    `rgbd_odometry.launch.py` + `ekf.launch.py` (só odometria, sem SLAM visual)
  - inclui `rover_slam`'s slam.launch.py / amcl.launch.py / explore.launch.py
    condicionalmente
- `rover_gazebo/launch/moon.launch.py`: agora repassa `headless`, `slam`,
  `explore`, `launch_rviz` para `gazebo.launch.py` (antes ficavam presos aos
  defaults, não dava pra sobrescrever via `ros2 launch ... slam:=False` etc.)

## Bugs encontrados e corrigidos

1. **Conflito de dono do `/map`**: `rtabmap` (SLAM visual, dentro do
   `localization.launch.py` original) competia com `slam_toolbox` por
   `map->odom`. Corrigido subindo só `rgbd_odometry` + `ekf` (odometria),
   sem o `rtabmap` completo.
2. **slam_toolbox nunca ativava**: é lifecycle node, launch inicial usava
   `Node` simples. Corrigido com `LifecycleNode` + `EmitEvent`/
   `RegisterEventHandler` (configure -> activate), copiando o padrão do
   `online_async_launch.py` oficial do slam_toolbox.
3. **Processos zumbis entre testes**: `pkill -f` não matava tudo de forma
   confiável; sobravam `robot_state_publisher`/`joint_state_publisher`/
   bridges de execuções anteriores rodando junto com a atual, brigando pela
   tf. **Forma segura de limpar**: dentro do container,
   `ps -eo pid=,comm= | awk '$1 != 1 {print $1}'` e matar cada PID — nunca usar
   `pkill -f` com padrões genéricos tipo `ros2` porque casa com a própria
   linha de comando do `docker exec bash -c "..."` (que contém `/ros2_ws/`) e
   mata o processo errado (já aconteceu de derrubar o PID 1 do container e
   precisar `docker start confident_ellis` de novo).
4. **`/scan` com frame_id errado** (causa raiz do slam_toolbox descartar
   todo scan, mensagens "Message Filter dropping message... frame does not
   exist" / "timestamp earlier than transform cache"): o sensor lidar
   (`rover_description/urdf/sensors/hokuyo.urdf.xacro`) não tinha a tag
   `<gz_frame_id>`, então o Gazebo publicava `/scan` com
   `frame_id: rover/base_link/lidar` — uma frame que **não existe** na
   árvore de tf (o link real se chama `laser_link`). Corrigido adicionando
   `<gz_frame_id>${prefix}_link</gz_frame_id>` dentro do `<sensor>` do lidar,
   igual já era feito pro RGBD (`<optical_frame_id>camera_frame</optical_frame_id>`
   em `asus_xtion.urdf.xacro`).
5. **"Robot is out of bounds of the costmap" / explore_lite "Robot out of
   costmap bounds"**: o `global_costmap` (em `rover_navigation/params/costmaps.yaml`)
   não tinha `rolling_window`, então seus limites vinham direto do `/map` do
   slam_toolbox. No início da exploração, a área bem embaixo/atrás do robô
   ainda não tinha sido varrida pelo lidar (ponto cego atrás do sensor), então
   o `/map` nascia sem cobrir a pose do robô — e como o `explore_lite` também
   lê `/global_costmap/costmap`, isso travava os dois num deadlock: sem
   costmap válido não navega, sem navegar o mapa não cresce. Corrigido
   adicionando `rolling_window: true`, `width: 30`, `height: 30` ao
   `global_costmap` — ele passa a ficar sempre centrado no robô, independente
   de onde o `/map` do SLAM já cresceu.
6. **Gazebo GUI travava com "Authorization required, but no authorization
   protocol specified" / "could not connect to display :0" e o launch matava
   o `gz sim server` inteiro junto com a GUI**: faltava autorização X11 do
   host pro container. Corrigido no host com `xhost +local:docker` (não
   persiste entre reboots do host — rodar de novo se voltar a acontecer).
   Para testes automatizados/CI, use `headless:=True` (novo arg) em vez de
   depender do X11.
7. **Robô nunca se movia fisicamente, mesmo publicando `/cmd_vel` manualmente
   e mesmo com Nav2 enviando goals** (causa raiz de tudo "falhar em progredir"
   e do `explore_lite` esgotar frontiers rapidinho sem o robô sair do lugar):
   o pacote `ros2controlcli` (fornece o verbo `ros2 control`, usado por
   `rover_gazebo/launch/include/spawn.launch.py` pra ativar
   `joint_state_broadcaster`/`position_controller`/`velocity_controller` via
   `ros2 control load_controller --set-state active ...`) não estava
   instalado na imagem/container. Os processos de spawn morriam na hora com
   `invalid choice: 'control'` (exit code 2), e
   `ros2 service call /controller_manager/list_controllers ...` confirmava
   **zero controllers ativos**. Corrigido:
   - instalado `ros-jazzy-ros2controlcli` no container (`apt-get install`;
     não persiste se a imagem for reconstruída do zero)
   - adicionado `<depend>ros2controlcli</depend>` em `rover_gazebo/package.xml`
     pra que `rosdep install --from-paths src --ignore-src -r -y` (chamado no
     `Dockerfile` da raiz do repo) instale isso automaticamente em builds
     futuros da imagem.

## Status atual (CONFIRMADO funcionando)

Testado tanto com `headless:=True` quanto com a GUI normal do Gazebo
(depois do `xhost +local:docker`):
- `/scan` publica de verdade, com `frame_id: laser_link` correto.
- `map->base_link` resolve e atualiza continuamente.
- `/map` cresce sem parar enquanto o robô explora (visto crescendo de
  90x62 pra 173x193+ células em ~1 min de exploração).
- **Zero** ocorrências de "Robot is out of bounds of the costmap" ou
  "[FrontierSearch] Robot out of costmap bounds".
- `explore_lite` conecta no Nav2, manda goals sozinho, e **não** para cedo
  com "All frontiers traversed/tried out" (isso só acontecia antes porque o
  robô ficava fisicamente parado no lugar — bug #7).
- Robô se desloca de verdade (odom saindo de (0,0) e progredindo,
  ex.: (0.33, 2.10) -> (1.72, 3.33) em ~1 min), sem teleop nem goal manual.
- `ros2 service call /controller_manager/list_controllers ...` mostra os 3
  controllers (`joint_state_broadcaster`, `position_controller`,
  `velocity_controller`) com `state='active'`.

## Pendências conhecidas (não bloqueantes, só flagar depois)

- Footprint em `rover_navigation/params/costmaps.yaml` é placeholder
  0.6x0.6m, não é a medida real do chassi Sawppy — só ajustar se o
  comportamento de desvio de obstáculo parecer errado na prática.
- `width`/`height: 30` (metros) do `global_costmap` rolling window é um
  chute razoável pro tamanho do `moon.world` (~100x100m de terreno) — se o
  explore_lite parecer "míope" (só olhando frontiers muito perto), considerar
  aumentar.
- Ainda aparecem alguns "Message Filter dropping message... timestamp
  earlier than transform cache" ocasionais e "Control loop missed its
  desired rate" no `controller_server` — o container está sob carga alta
  (load average bem acima do número de cores com Gazebo + Nav2 + SLAM todos
  juntos); não impede o mapeamento/navegação de progredir, mas é sintoma de
  contenção de CPU. `headless:=True` ajuda bastante.
- Nenhum commit foi feito ainda no fork; tudo isso está em working tree
  (inclui `rover_navigation/params/costmaps.yaml`,
  `rover_gazebo/launch/gazebo.launch.py`, `rover_gazebo/launch/moon.launch.py`,
  `rover_gazebo/package.xml`, além do já existente `rover_slam/` e o fix do
  `hokuyo.urdf.xacro`).
- Se a imagem Docker for reconstruída do zero, o `ros2controlcli` já vem
  incluído via `rosdep install` (fix #7 no `package.xml`) — não precisa mais
  instalar manualmente.

## Como retomar

Container Docker `confident_ellis` (imagem `ros2_rover:latest`/`rover:latest`),
repo montado em `/workspaces/ros2_ws` dentro do container (== este diretório
no host). Usar `docker start confident_ellis` se estiver parado, depois
`docker exec -it confident_ellis bash`. Não instalar ROS2/colcon no host
(Debian Trixie) — tudo roda dentro do container, de propósito.

Pra rodar com GUI: `xhost +local:docker` no host antes (não persiste entre
reboots). Pra rodar sem GUI (CI/testes rápidos): `headless:=True`.

Exemplo:
```
ros2 launch rover_gazebo moon.launch.py slam:=True explore:=True headless:=True
```

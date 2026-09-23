# Diário de Bordo — Rover Sim


> Log técnico do desenvolvimento da simulação do rover: decisões, bugs encontrados e correções.


{{< toc >}}

Log técnico incremental. Cada entrada documenta o estado do projeto num dado
momento — o que foi decidido, o que quebrou e como foi corrigido. Ver também
os [Comandos Essenciais](/comandos-essenciais-simulacao) para rodar o que
está descrito aqui.

## 2026-09-21 — Navegação autônoma (SLAM + exploração + Nav2): funcionando

**Objetivo:** o rover simulado explora sozinho (frontier exploration) e
navega com Nav2 evitando obstáculos, sem teleop e sem goals manuais.

**Resultado:** confirmado funcionando de ponta a ponta (headless e com GUI).
O rover se move sozinho via `explore_lite` + Nav2, o `/map` do
`slam_toolbox` cresce continuamente, e não aparecem mais avisos de "Robot is
out of bounds of the costmap".

### Decisão de escopo

O pacote `rover_nav2` mencionado em planos anteriores nunca chegou a existir
de fato. O repo upstream já trazia `rover_navigation` (SmacHybrid/SmacLattice
+ RPP/TEB) funcionando. A lacuna real era SLAM + exploração autônoma, então
foi criado um pacote novo, `rover_slam` (slam_toolbox + AMCL + explore_lite),
sem tocar em `rover_motor_controller_cpp/serial.cpp` e `.hpp` (edições locais
do usuário, propositalmente preservadas).

### O que foi feito

- Novo pacote `rover_slam/`:
  - `config/slam_toolbox.yaml`, `config/amcl.yaml`, `config/explore_params.yaml`
  - `launch/slam.launch.py` (slam_toolbox como lifecycle node, configure → activate)
  - `launch/amcl.launch.py` (map_server + amcl + lifecycle_manager_localization)
  - `launch/explore.launch.py` (explore_lite, do fork `robo-friends/m-explore-ros2`)
- `rover_gazebo/launch/gazebo.launch.py`:
  - argumentos novos: `slam` (default `True`), `explore` (default `True`), `map`,
    `headless` (default `False` — roda `gz sim -s`, sem GUI, útil para
    testes/CI sem gastar CPU em renderização)
  - trocou o include único de `rover_localization/launch/localization.launch.py`
    (que subia o `rtabmap` junto) por dois includes separados:
    `rgbd_odometry.launch.py` + `ekf.launch.py` (só odometria, sem SLAM visual)
  - inclui os launches do `rover_slam` condicionalmente
- `rover_gazebo/launch/moon.launch.py`: agora repassa `headless`, `slam`,
  `explore`, `launch_rviz` para `gazebo.launch.py` (antes ficavam presos aos
  defaults, sem poder sobrescrever via `ros2 launch ... slam:=False` etc.)

### Bugs encontrados e corrigidos

1. **Conflito de dono do `/map`.** `rtabmap` (SLAM visual, dentro do
   `localization.launch.py` original) competia com `slam_toolbox` pela
   transform `map → odom`. Corrigido subindo só `rgbd_odometry` + `ekf`
   (odometria), sem o `rtabmap` completo.
2. **`slam_toolbox` nunca ativava.** É um lifecycle node; o launch inicial
   usava um `Node` simples. Corrigido com `LifecycleNode` +
   `EmitEvent`/`RegisterEventHandler` (configure → activate), copiando o
   padrão do `online_async_launch.py` oficial do `slam_toolbox`.
3. **Processos zumbis entre testes.** `pkill -f` não matava tudo de forma
   confiável; sobravam `robot_state_publisher`/`joint_state_publisher`/bridges
   de execuções anteriores rodando junto com a atual, brigando pela tf.
   Forma segura de limpar, dentro do container:
   ```shell
   ps -eo pid=,comm= | awk '$1 != 1 {print $1}' | xargs -r kill
   ```
   **Nunca** usar `pkill -f` com padrões genéricos como `ros2`: casa com a
   própria linha de comando do `docker exec bash -c "..."` (que contém
   `/ros2_ws/`) e mata o processo errado — já aconteceu de derrubar o PID 1
   do container e precisar `docker start <container>` de novo.
4. **`/scan` com `frame_id` errado**, causa raiz do `slam_toolbox` descartar
   todo scan (mensagens "Message Filter dropping message... frame does not
   exist" / "timestamp earlier than transform cache"). O sensor lidar
   (`rover_description/urdf/sensors/hokuyo.urdf.xacro`) não tinha a tag
   `<gz_frame_id>`, então o Gazebo publicava `/scan` com
   `frame_id: rover/base_link/lidar` — uma frame que não existe na árvore de
   tf (o link real se chama `laser_link`). Corrigido adicionando
   `<gz_frame_id>${prefix}_link</gz_frame_id>` dentro do `<sensor>` do lidar,
   igual já era feito para o RGBD (`<optical_frame_id>camera_frame</optical_frame_id>`
   em `asus_xtion.urdf.xacro`).
5. **"Robot is out of bounds of the costmap" / "Robot out of costmap
   bounds"** no `explore_lite`. O `global_costmap` (em
   `rover_navigation/params/costmaps.yaml`) não tinha `rolling_window`,
   então seus limites vinham direto do `/map` do `slam_toolbox`. No início
   da exploração, a área embaixo/atrás do robô ainda não tinha sido varrida
   pelo lidar (ponto cego atrás do sensor), então o `/map` nascia sem cobrir
   a pose do robô — e como o `explore_lite` também lê
   `/global_costmap/costmap`, isso travava os dois num deadlock: sem costmap
   válido não navega, sem navegar o mapa não cresce. Corrigido adicionando
   `rolling_window: true`, `width: 30`, `height: 30` ao `global_costmap` —
   ele passa a ficar sempre centrado no robô, independente de onde o `/map`
   do SLAM já cresceu.
6. **Gazebo GUI travava** com "Authorization required, but no authorization
   protocol specified" / "could not connect to display :0", e o launch
   matava o `gz sim server` inteiro junto com a GUI. Faltava autorização X11
   do host para o container. Corrigido no host com `xhost +local:docker`
   (não persiste entre reboots — repetir se voltar a acontecer). Para testes
   automatizados/CI, usar `headless:=True` em vez de depender de X11.
7. **Robô nunca se movia fisicamente**, mesmo publicando `/cmd_vel`
   manualmente e mesmo com Nav2 enviando goals — causa raiz de tudo "falhar
   em progredir" e do `explore_lite` esgotar frontiers rapidamente sem o
   robô sair do lugar. O pacote `ros2controlcli` (fornece o verbo
   `ros2 control`, usado por `rover_gazebo/launch/include/spawn.launch.py`
   para ativar `joint_state_broadcaster`/`position_controller`/
   `velocity_controller` via `ros2 control load_controller --set-state
   active ...`) não estava instalado na imagem/container. Os processos de
   spawn morriam na hora com `invalid choice: 'control'` (exit code 2), e
   `ros2 service call /controller_manager/list_controllers ...` confirmava
   zero controllers ativos. Corrigido:
   - instalado `ros-jazzy-ros2controlcli` no container (não persiste se a
     imagem for reconstruída do zero)
   - adicionado `<depend>ros2controlcli</depend>` em
     `rover_gazebo/package.xml`, para que `rosdep install --from-paths src
     --ignore-src -r -y` (chamado no `Dockerfile` da raiz do repo) instale
     isso automaticamente em builds futuros da imagem.

### Status confirmado

Testado tanto com `headless:=True` quanto com a GUI normal do Gazebo (depois
do `xhost +local:docker`):

- `/scan` publica de verdade, com `frame_id: laser_link` correto.
- `map → base_link` resolve e atualiza continuamente.
- `/map` cresce sem parar enquanto o robô explora (visto crescendo de 90x62
  para 173x193+ células em ~1 min de exploração).
- Zero ocorrências de "Robot is out of bounds of the costmap" ou
  "[FrontierSearch] Robot out of costmap bounds".
- `explore_lite` conecta no Nav2, manda goals sozinho, e não para cedo com
  "All frontiers traversed/tried out" (isso só acontecia antes porque o robô
  ficava fisicamente parado — bug #7).
- Robô se desloca de verdade (odom saindo de `(0,0)` e progredindo, ex.:
  `(0.33, 2.10) → (1.72, 3.33)` em ~1 min), sem teleop nem goal manual.
- `ros2 service call /controller_manager/list_controllers ...` mostra os 3
  controllers (`joint_state_broadcaster`, `position_controller`,
  `velocity_controller`) com `state='active'`.

### Pendências conhecidas (não bloqueantes)

- Footprint em `rover_navigation/params/costmaps.yaml` é placeholder
  0.6x0.6m, não é a medida real do chassi Sawppy — ajustar só se o
  comportamento de desvio de obstáculo parecer errado na prática.
- `width`/`height: 30` (metros) do `global_costmap` rolling window é um
  chute razoável para o tamanho do `moon.world` (~100x100m de terreno) — se
  o `explore_lite` parecer "míope" (só olhando frontiers muito perto),
  considerar aumentar.
- Ainda aparecem alguns "Message Filter dropping message... timestamp
  earlier than transform cache" ocasionais e "Control loop missed its
  desired rate" no `controller_server` — sintoma de contenção de CPU
  (Gazebo + Nav2 + SLAM juntos). Não impede o progresso, mas
  `headless:=True` ajuda bastante.
- Se a imagem Docker for reconstruída do zero, o `ros2controlcli` já vem
  incluído via `rosdep install` (fix do bug #7 no `package.xml`) — não
  precisa mais instalar manualmente.

### Como retomar

Repositório montado dentro do container em `/workspaces/ros2_ws` (mesmo
diretório do host). Não instalar ROS 2/colcon no host — tudo roda dentro do
container, de propósito. Comandos completos em
[Comandos Essenciais](/comandos-essenciais-simulacao).

Para GUI: `xhost +local:docker` no host antes de abrir o container (não
persiste entre reboots). Para rodar sem GUI (CI/testes rápidos):
`headless:=True`.

```shell
ros2 launch rover_gazebo moon.launch.py slam:=True explore:=True headless:=True
```

## 2026-09-22 — `explore_lite` nunca estava de fato no workspace: achado e corrigido

**Objetivo:** validar ao vivo, rodando de verdade dentro do `rover_dev`, que
o `slam:=True explore:=True` da entrada anterior funciona ponta a ponta.

**Resultado:** não funcionava.
`ros2 launch rover_gazebo moon.launch.py slam:=True explore:=True headless:=True`
morria logo no início com `package 'explore_lite' not found`, derrubando
(cascade shutdown) tudo que já tinha subido.

### Causa raiz

`rover_slam/package.xml` declara `<depend>explore_lite</depend>`, mas
`explore_lite` é um fork (`robo-friends/m-explore-ros2`, pacote na subpasta
`explore/`, mais uma dependência dele, `explore_lite_msgs`) que não é uma
chave resolvível pelo `rosdep`. O `Dockerfile` roda
`rosdep install --from-paths src --ignore-src -r -y` — a flag `-r` faz o
`rosdep` **pular em silêncio** dependências que falham em resolver, então o
pacote nunca chegou a existir de fato no workspace, apesar do `package.xml`
parecer completo e do build do Docker terminar sem erro visível.

**Correção:** vendorizados `explore_lite/` e `explore_lite_msgs/` (do fork
acima; `map_merge/`, que não é usado aqui, ficou de fora) como pastas de
pacote no nível raiz do repo, no mesmo padrão flat de `rover_slam`/
`rover_navigation`. Assim o `colcon build` resolve por nome de pacote
dentro do próprio workspace, sem depender do `rosdep` pra isso.

### Bug batido no caminho: processos `gz sim` órfãos

Durante os testes, ficou mais de uma instância de `gz sim` rodando ao mesmo
tempo — o wrapper do `ros2 launch` morre no shutdown (ou quando a sessão do
`docker exec` que o iniciou fecha), mas o processo `gz sim` de baixo escapa
e fica órfão, reparented pro PID 1, continuando a rodar. Sintoma:
`slam_toolbox` soltando "Message Filter dropping message... timestamp
earlier than transform cache" sem parar, com o `/clock` pulando pra frente
e pra trás — duas simulações concorrentes disputando o tempo. Resolvido
listando `ps -ef | grep "gz sim"` e matando por PID exato (repetindo o
aviso já dado acima sobre `pkill -f`: `pkill -f "gz sim"`/`pkill -f "ros2"`
também casa com a própria linha de comando do `docker exec`/`pgrep` usada
pra limpar, e pode matar o processo errado).

### Confirmado funcionando (depois da correção)

- `map` resolve e `map` → `base_link` progride sozinho.
- Os 3 controllers (`joint_state_broadcaster`, `position_controller`,
  `velocity_controller`) ficam `active`.
- `/map` cresceu de 96x80 para 106x83 células em ~40s de exploração.
- Robô andou sozinho de `(0.68, 0.51)` para `(0.79, 1.03)` (tempo de sim
  4.5s → 9.9s), sem teleop nem goal manual.
- Zero ocorrência de "Robot is out bounds costmap" ou crash.


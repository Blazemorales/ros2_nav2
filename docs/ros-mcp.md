# ROS-MCP: comandar o rover em linguagem natural

```
LLM local (Ollama, qwen2.5:7b, no PC)
   ↓ MCP (stdio)                      ollmcp  (cliente MCP p/ Ollama)
rover_mcp_safe                        ← proxy restrito, roda no PC (fora do container)
   └─ ros-mcp 3.1.2 (in-process)
   ↓ WebSocket :9090
rosbridge_server + rosapi             ← dentro do container (PC na simulação, Pi no robô)
   ↓ ROS 2 Jazzy
Nav2 + slam_toolbox/AMCL + explore_lite
```

**Princípio:** o LLM envia *goals* e lê *estado*. Ele nunca publica em
`/cmd_vel`. Exploração autônoma é do `explore_lite`; o LLM só liga/desliga.

## Peças

| Arquivo | Papel |
|---|---|
| `Dockerfile`, `.devcontainer/Dockerfile` | instalam `ros-jazzy-rosbridge-server` |
| `.devcontainer/devcontainer.json` | `forwardPorts: [9090]` (com `--net=host` a porta já é do host) |
| `rover_bringup/launch/rosbridge.launch.py` | rosbridge + rosapi; serve também na Pi |
| `rover_bringup/launch/rover_mcp_sim.launch.py` | entry point único da simulação |
| `tools/rover_mcp_safe/rover_mcp_safe.py` | servidor MCP restrito (o que o LLM enxerga) |
| `tools/rover_mcp_safe/test_policy.py` | teste offline da política (sem ROS) |
| `tools/rover_mcp_safe/smoke_test.py` | teste MCP ponta a ponta contra a simulação |
| `tools/rover_mcp_safe/setup_ollmcp.sh` | configura o `ollmcp` (temp 0.1, prompt, HIL) |

`tools/rover_mcp_safe/` tem `COLCON_IGNORE`: não é pacote ROS e roda no host.

## Uso

Dentro do container:

```bash
ros2 launch rover_bringup rover_mcp_sim.launch.py slam:=true explore:=false
# argumentos: slam, explore (default false), rosbridge (default true),
# use_sim_time, world, initial_pose_z, headless, launch_rviz, map,
# nav2_planner, nav2_controller, rosbridge_port
```

`rover_mcp_sim.launch.py` reaproveita `rover_gazebo/launch/gazebo.launch.py`
inteiro (Gazebo → EKF → slam_toolbox/AMCL → Nav2 → explore_lite) via
`IncludeLaunchDescription` e só acrescenta o rosbridge, 5 s depois. Nenhuma
configuração de Nav2 foi duplicada. O mundo padrão é `moon.world`
(`initial_pose_z:=2.11`).

No robô real (Pi), só o rosbridge:

```bash
ros2 launch rover_bringup rosbridge.launch.py
```

No host (sem ROS instalado):

```bash
pipx install ros-mcp ollmcp
ollama pull qwen2.5:7b
tools/rover_mcp_safe/setup_ollmcp.sh            # robô real: setup_ollmcp.sh <IP da Pi>
ollmcp -j ~/.config/ollmcp/rover-servers.json
```

## Camada de segurança (Fase 4): escolha (b), proxy FastMCP

Opções avaliadas, na ordem do plano:

- **(a) allowlist no cliente:** o `ollmcp` permite desligar tools na
  interface, mas isso fica salvo só no config local do usuário e qualquer
  outro cliente veria as 31 tools. Não serve como garantia.
- **(b) proxy:** escolhida. `rover_mcp_safe.py` registra as tools do ros-mcp no
  mesmo processo e aplica a política em duas camadas:
  1. remove do servidor toda tool fora da allowlist (o LLM nem a vê);
  2. um middleware valida os argumentos das tools de escrita que sobraram.
- **(c) modo readonly por env:** **não existe** no ros-mcp 3.1.2. As únicas
  variáveis lidas são `ROSBRIDGE_IP`, `ROSBRIDGE_PORT` e `ROS_DEFAULT_TIMEOUT`.

| Tool | Política |
|---|---|
| `publish_for_durations`, `set_parameter`, `delete_parameter`, `connect_to_robot`, `view_saved_image`, `get_verified_robot*` | removidas |
| `publish_once` | só tópicos em `ROVER_MCP_PUBLISH_TOPICS` (default `/explore/resume`); recusa sempre `*cmd_vel*`, controllers e tipos Twist/TwistStamped/Ackermann/JointTrajectory/Float64MultiArray |
| `send_action_goal` | só `ROVER_MCP_ACTIONS` (default `/navigate_to_pose`, `/navigate_through_poses`); `/spin`, `/backup`, `/drive_on_heading`, `/follow_path` recusadas |
| `call_service` | bloqueia `/_action/*` (contornaria a allowlist de actions), `set_parameters*`, `load_parameter_file`, `change_state`, `manage_nodes`, `/controller_manager/*` |
| `subscribe_once` / `subscribe_for_duration` | recusa PointCloud2, Image, CompressedImage, OccupancyGrid; duração ≤ 5 s, ≤ 20 mensagens |
| demais (leitura) | liberadas |

24 das 31 tools ficam expostas. O `ollmcp` também está com
*human-in-the-loop* ligado: cada tool call pede confirmação.

### Segunda camada: o próprio rosbridge

O rosbridge 2.7 do Jazzy aceita globs de permissão.
`rover_bringup/launch/rosbridge.launch.py` sobe o `rosbridge_websocket` como
`Node` (e não pelo XML oficial, que não repassa `actions_glob`) com:

| Parâmetro | Default | Efeito |
|---|---|---|
| `topics_pub_glob` | `['/explore/resume']` | nenhum cliente WebSocket publica em `/cmd_vel`, mesmo sem o proxy |
| `actions_glob` | `['/navigate_to_pose', '/navigate_through_poses']` | só goals de navegação Nav2 |

Para liberar (ex.: depuração com outra ferramenta), use
`topics_pub_glob:='' actions_glob:=''`. Os globs não são passados ao `rosapi`,
porque lá eles filtrariam a listagem de tópicos, e não as permissões.
`services_glob` fica livre: o bloqueio de serviços perigosos é feito no proxy.

## Armadilhas

- **rosbridge serializa tudo em JSON.** Nada de assinatura contínua em `/scan`,
  câmera RGBD ou nuvem de pontos: na Pi 3 isso derruba o Nav2. O proxy recusa
  os tipos pesados e limita `subscribe_for_duration`.
- **Temperatura ≤ 0.1.** Acima disso o modelo local inventa nome de tool e gera
  JSON quebrado. O `setup_ollmcp.sh` já grava 0.1.
- **Modelos < 7B** não fazem tool calling confiável. Na Pi não roda LLM.
- **Sem GPU** (caso deste PC) o qwen2.5:7b roda na CPU: algumas a dezenas de
  segundos por resposta, e disputa RAM com Gazebo + Nav2. Use `headless:=true`
  e `launch_rviz:=false` se faltar memória.
- Os exemplos do tugbot no ros-mcp-server são Humble/Gazebo Classic; aqui é
  Jazzy + Gazebo Harmonic (`ros_gz_sim`/`ros_gz_bridge`).

## Validação (Fase 5)

RESULTADOS_PENDENTES

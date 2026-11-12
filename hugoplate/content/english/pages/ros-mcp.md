---
title: "ROS-MCP — Comandar o Rover em Linguagem Natural"
meta_title: "ROS-MCP"
description: "Arquitetura, camada de segurança e validação da integração do rover com LLMs via Model Context Protocol (ros-mcp + rosbridge)."
draft: false
---

{{< toc >}}

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
| `tools/rover_mcp_safe/llm_test.py` | prompts em linguagem natural via Ollama, não interativo |
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

Executada em 2026-11-11 no PC (12 núcleos, 16 GB, sem GPU), container
`rover:latest`, `rover_mcp_sim.launch.py slam:=true headless:=true launch_rviz:=false`.

| # | Passo | Resultado |
|---|---|---|
| 0 | Infra | ✅ handshake WebSocket `101` em `localhost:9090`; `/cmd_vel`, `/odom`, `/scan`, `/map`, `/navigate_to_pose` presentes; 3 controllers `active` |
| 1 | Teleop manual (`/cmd_vel` dentro do container) | ✅ rover andou 0,28 m (ver RTF abaixo) |
| 2 | Goal manual (`ros2 action send_goal /navigate_to_pose`, x=2, y=0,5) | ✅ `SUCCEEDED`, chegou em (1,99; 0,52) |
| 3 | Exploração sem LLM (`explore:=true`) | ⚠️ parcial: `/map` cresceu de 99×81 → 168×130 células em 4 min, rover se moveu sozinho, zero "out of bounds". Não rodou até o mapa fechar (`moon.world` ≈ 100×100 m) |
| 4 | Leitura via MCP | ✅ sem LLM: `smoke_test.py` (topics, actions, `/odom`). Com LLM (qwen2.5:7b, temp 0.1): chamou `subscribe_once('/odom')` e respondeu a posição correta — **14,6 min** para 2 rodadas |
| 5 | Goal via MCP | ✅ sem LLM: `send_action_goal('/navigate_to_pose')` → `success`, rover andou 1,94 m. Com LLM: ✅ "publique Twist em /cmd_vel" → `publish_once` **recusado** pelo proxy e o modelo recorreu sozinho a um goal Nav2. ❌ os goals do LLM (x=1 e x=3,y=3) terminaram em **status 6 (ABORTED)** e o modelo relatou sucesso — ver abaixo |
| 6 | Explore comandado via MCP | ✅ sem LLM: `publish_once('/explore/resume', false→true)` aceito. ❌ com LLM: "pause a exploração" → tentou `/explore/resume` como **action** (recusado 2×) e depois mandou goal para (0,0); explore **não** pausou |

Bloqueio no próprio rosbridge (sem o proxy): 4 s publicando 0,5 m/s em
`/cmd_vel` por WebSocket cru → rover deslocou 0,001 m. ✅

Scripts: `test_policy.py` (offline), `smoke_test.py` (MCP sem LLM),
`llm_test.py` (LLM via Ollama, não interativo).

### Falhas do teste com LLM (qwen2.5:7b)

> **Resolvidas em 2026-11-12** pelas tools dedicadas `navigate_to`,
> `stop_navigation`, `set_exploration` e `get_robot_pose` (ver [Chat Web](/chat-web)).
> O perfil padrão do proxy (`nav`) não expõe mais `publish_once` /
> `send_action_goal`; o comportamento antigo segue em `--profile full`.

1. **Goals abortados com `explore_lite` ativo.** Os goals do LLM terminaram em
   status 6 (ABORTED). Causa provável: o `explore_lite` seguia mandando os
   próprios goals ao Nav2 e preemptava os do LLM. Mitigação: pausar o explore
   antes de um goal manual (e o proxy pode fazer isso automaticamente).
2. **`send_action_goal` responde `"success": true` mesmo com goal abortado.**
   O ros-mcp só reporta que a chamada completou; o estado real está em
   `status`. O modelo leu `success` e afirmou que chegou. Mitigação: o proxy
   reescrever o resultado com o texto do status (`SUCCEEDED`/`ABORTED`/...).
3. **Tópico confundido com action.** Mesmo com o prompt de sistema citando
   `publish_once('/explore/resume', ...)`, o modelo chamou
   `send_action_goal('/explore/resume', 'std_msgs/msg/Bool')`. Mitigação: a
   mensagem de recusa do proxy indicar a tool correta, ou expor uma tool
   dedicada `set_exploration(enabled: bool)`.

Nenhuma dessas falhas furou a camada de segurança: tudo que foi recusado
continuou recusado, e o rover nunca recebeu `/cmd_vel` do LLM.

### Desempenho medido

- **RTF da simulação: 0,09** (medido pelo `/clock`; `gz stats` não existe no
  `gz_tools_vendor` do Jazzy). Mesmo sem LLM o RTF ficou em ~0,16.
- `gz sim` ≈ 300 % CPU; `llama-server` ≈ 190 %. Sem pressão de RAM (sem swap ativo).
- Câmera RGBD: `/camera/depth/image_raw` 1,38 MB/msg a ~30 Hz em tempo
  simulado, mais `/camera/points`. Principal suspeita do RTF baixo, mas
  alimenta o `rgbd_odometry` → EKF, então não dá para só desligar.
- **Contexto do Ollama:** as 24 tools somam ~2,7 k tokens; o padrão de
  4096 estoura depois de 1–2 resultados de tool. `llm_test.py` usa
  `num_ctx: 8192`; no `ollmcp`, ajustar o contexto do modelo também.
- Sem GPU, o LLM ao lado da simulação leva minutos por rodada de tool
  calling: funcional, mas impraticável para uso interativo.

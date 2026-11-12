# Status do projeto (atualizado em 2026-11-12)

Rover Sawppy simulado (ROS 2 Jazzy + Gazebo Harmonic) que explora sozinho
(SLAM + `explore_lite` + Nav2) e pode ser comandado em linguagem natural por um
LLM local via MCP. Tudo abaixo já está em `main` de `Blazemorales/ros2_nav2`.

Documentação detalhada no site Hugo (`hugoplate/`, publicado em
blazemorales.github.io/ros2_nav2): páginas **ROS-MCP** e **Desempenho da
simulação**.

## O que já está pronto

| Entrega | Onde |
|---|---|
| Exploração autônoma: pacote `rover_slam` (slam_toolbox + AMCL + explore_lite), fixes de `/scan` frame_id, `rolling_window` no global costmap, `ros2controlcli`, arg `headless` | commit `6097a97` |
| ROS-MCP: rosbridge no container, `rover_mcp_sim.launch.py`, proxy restrito `tools/rover_mcp_safe` (24/31 tools, `/cmd_vel` bloqueado no proxy **e** no rosbridge) | PR #2 |
| `sim_lite` (perfil leve da câmera RGBD) + `tools/rtf_meter.py`; RTF 0,18 → 0,42 | PR #3 |
| Deploy do site Hugo disparado por push em `main` | PR #4 |
| Tools MCP dedicadas (`navigate_to` → ARRIVED/ABORTED/CANCELED/TIMEOUT, `stop_navigation`, `set_exploration`, `get_robot_pose`) + chat web (Render + Groq grátis + agente local) | `tools/rover_mcp_safe/rover_tools.py`, `tools/rover_web/`, `render.yaml`; página **Chat Web** |

## 1. Subir o container

Não há ROS no host, e isso é de propósito: tudo roda no container **`rover_mcp`**
(imagem `rover:latest`, `--net=host`, repo montado em `/root/ros2_ws/src`).
O workspace já está compilado e o `.bashrc` do container já faz
`source /root/ros2_ws/install/setup.bash`.

```bash
docker start rover_mcp            # se estiver parado (docker ps -a para ver)
docker exec -it rover_mcp bash    # abre um terminal dentro dele
```

Se o container tiver sido apagado, recrie-o:

```bash
docker run -d --name rover_mcp --net=host \
  -v ~/Documentos/ros2_nav2:/root/ros2_ws/src rover:latest sleep infinity
docker exec rover_mcp bash -lc 'cd /root/ros2_ws && colcon build --symlink-install'
```

Depois de mudar código C++, launch ou config, recompile só o necessário:

```bash
docker exec rover_mcp bash -lc 'cd /root/ros2_ws && colcon build --symlink-install --packages-select rover_gazebo rover_bringup'
```

## 2. Subir a simulação

Dentro do container:

```bash
ros2 launch rover_bringup rover_mcp_sim.launch.py \
  slam:=true explore:=false headless:=true launch_rviz:=false sim_lite:=true
```

- `headless:=true`: Gazebo sem janela. O container não tem `DISPLAY`; para usar a
  GUI seria preciso recriá-lo com X11 e rodar `xhost +local:docker` no host.
- `explore:=true`: o rover explora sozinho. Deixe `false` para testar goals
  do LLM, senão o `explore_lite` preempta os goals (ver Pendências).
- O rosbridge sobe 5 s depois, na porta 9090 (`--net=host`, então é a 9090 do host).

Para conferir se está tudo de pé (em outro `docker exec -it rover_mcp bash`):

```bash
ros2 topic echo /odom --once
ros2 action list | grep navigate_to_pose
ros2 service call /controller_manager/list_controllers controller_manager_msgs/srv/ListControllers
# os 3 controllers devem aparecer com state='active'
```

Para parar, use Ctrl+C no launch. Para um reinício limpo, use `docker restart rover_mcp`.
**Nunca** use `pkill -f <padrão>` dentro de `docker exec bash -c "..."`: o padrão
casa com a própria linha de comando e já derrubou o PID 1 do container.

## 3. Testar a IA (no host, fora do container)

Pré-requisitos no host (já instalados neste PC): `ollama` com `qwen2.5:7b`,
e `pipx install ros-mcp ollmcp`.

Com a simulação rodando, faça os passos em ordem, do mais barato ao mais caro:

```bash
cd ~/Documentos/ros2_nav2
PY=~/.local/share/pipx/venvs/ros-mcp/bin/python

# a) política do proxy, offline (não precisa de ROS)
$PY -I tools/rover_mcp_safe/test_policy.py

# b) MCP ponta a ponta SEM LLM: lê /odom, tenta /cmd_vel (deve ser recusado),
#    manda um goal Nav2 2 m à frente, pausa e retoma o explore
$PY -I tools/rover_mcp_safe/smoke_test.py --dx 2.0

# c) LLM de verdade, não interativo (prompts padrão ou os seus)
$PY -u -I tools/rover_mcp_safe/llm_test.py --model qwen2.5:7b \
  "Where is the rover right now? Read its odometry and tell me x and y."

# d) chat interativo
tools/rover_mcp_safe/setup_ollmcp.sh        # uma vez; robô real: setup_ollmcp.sh <IP da Pi>
ollmcp -j ~/.config/ollmcp/rover-servers.json
```

Dicas:
- Sem GPU, o qwen2.5:7b ao lado do Gazebo leva **minutos** por rodada (~15 min
  no pior caso). Teste com prompts curtos. Para liberar CPU: `ollama stop qwen2.5:7b`.
- O `ollmcp` pede confirmação a cada tool call (human-in-the-loop). Isso é intencional.
- Use temperatura ≤ 0.1 (o `setup_ollmcp.sh` já configura) e contexto ≥ 8192
  (as tools ocupam ~2,7 k tokens).
- Ao redirecionar a saída do Python para arquivo, use `python -u`.

## 4. Comandar pelo navegador (chat web)

Passo a passo completo na página **Chat Web** do site
(`hugoplate/content/english/pages/chat-web.md`). Resumo: crie uma chave grátis
no Groq, faça o deploy do `render.yaml` no Render e rode no host:

```bash
~/.local/share/pipx/venvs/ros-mcp/bin/python -I tools/rover_web/agent.py \
  --server wss://<seu-app>.onrender.com --token '<AGENT_TOKEN do Render>'
```

## Pendências

**Navegação no terreno lunar (prioridade):** o Nav2 aborta com frequência
("Start occupied", "exceeded maximum iterations"). O lidar 2D tem alcance de
5 m e marca rampas do terreno como parede no `/map`. Depois o rover passa por
cima delas e fica "dentro" de um obstáculo. Ideias: aumentar o alcance do lidar,
usar a nuvem da câmera com filtro de altura (STVL) em vez do lidar 2D, ou
ajustar o SLAM para limpar células. As tools relatam isso corretamente
(ABORTED), mas a experiência de comandar o rover depende de resolver isso.

**Chat web:** falta validar com Groq e Render reais (precisa da chave e da
conta do usuário). Já foi validado localmente com o Ollama.

**Desempenho:** a meta de RTF ≥ 0,6 não foi atingida (0,42 com `sim_lite`).
O custo restante é fixo: física com passo de 1 ms (o `moon.world` não tem
bloco `<physics>`) e o gpu_lidar. A próxima ideia é testar `max_step_size`
0,002/0,004 com checagens de sanidade.

**Não bloqueantes:**
- O footprint em `rover_navigation/params/costmaps.yaml` é um placeholder de
  0,6×0,6 m, não a medida real do chassi.
- A rolling window do `global_costmap` tem 30×30 m. Se o explore parecer
  "míope", aumente.
- Avisos ocasionais de "Control loop missed its desired rate" e "Message
  Filter dropping message" vêm de contenção de CPU. `headless:=true` e
  `sim_lite:=true` ajudam.

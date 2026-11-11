# Desempenho da Simulação — RTF do Gazebo


> Por que a simulação do rover rodava a 18% do tempo real, como o gargalo foi isolado e o perfil leve sim_lite que dobra o RTF.


{{< toc >}}

O Gazebo rodava a **~0,18 do tempo real** (RTF) com a stack completa
(Gazebo + EKF + slam_toolbox + Nav2). Cada segundo simulado levava ~5,5 s de
relógio: o Nav2 perdia a taxa de controle e um teste com LLM levava minutos
por rodada. Esta página registra o diagnóstico e o perfil leve `sim_lite`.

## Resumo

| | RTF |
|---|---|
| Perfil original (câmera 720×480 @ 30 Hz + nuvem de pontos) | **0,18** |
| `sim_lite:=true` (320×240 @ 10 Hz, sem nuvem) | **0,42** (2,3×) |
| `sim_lite:=true camera_rate:=5` | **0,51** |

A meta inicial era RTF ≥ 0,6. **Não foi atingida só pela câmera**: mesmo a
2 Hz o RTF parou em 0,63, então o resto é custo fixo (física do rocker-bogie
e o `gpu_lidar`).

```bash
# perfil leve (recomendado para Nav2/MCP/testes)
ros2 launch rover_bringup rover_mcp_sim.launch.py sim_lite:=true headless:=true
ros2 launch rover_gazebo moon.launch.py sim_lite:=true

# ajuste fino (vazio = vem do perfil)
... sim_lite:=true camera_rate:=5
... camera_width:=480 camera_height:=360 camera_rate:=15 camera_points:=true
```

## Como medir

`gz stats` **não existe** no `gz_tools_vendor` do Jazzy (o binário está em
`/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz`, mas sem o subcomando `stats`).
O RTF é medido pelo avanço do `/clock` contra o tempo de parede:

```bash
python3 tools/rtf_meter.py 20     # dentro do container
```

Sempre com a mesma carga: **sem LLM**, sem exploração, rover parado, depois
de ~40 s de simulação estabilizada, janela de 20 s, simulação reiniciada do
zero a cada medição.

## Baseline

| Verificação | Resultado |
|---|---|
| RTF | 0,09 com LLM (qwen2.5:7b na CPU); ~0,18 sem |
| CPU | `gz sim` ≈ 300 %, `llama-server` ≈ 190 %, nós do Nav2 8–17 % cada |
| Ociosidade | ~55 % da CPU ociosa → gargalo serial dentro do Gazebo |
| Câmera de profundidade | 1,38 MB/msg; ~30 Hz em tempo simulado |
| `/camera/points` | nuvem de pontos atravessando a bridge |
| Memória | sem swap ativo — **RAM não é o problema** |

## Bisect: renderização ou física?

Teste deliberadamente exagerado: **só** `update_rate` da câmera 30 → 2.

| Configuração | RTF |
|---|---|
| Original | 0,188 |
| Câmera a 2 Hz | **0,630** |

RTF ≥ 0,6 → o gargalo dominante é a **renderização da câmera RGBD**. A
mudança foi revertida (diagnóstico, não solução).

## Uma mudança por medição

Cada linha reinicia a simulação do zero e acumula a mudança anterior.

| # | Mudança | RTF | Ganho |
|---|---|---|---|
| M0 | nada (regressão do código novo com defaults) | 0,178 | — |
| M1 | `/camera/points` fora da bridge; costmap local em `/scan` | 0,196 | +0,02 |
| M2 | + resolução 720×480 → 320×240 | 0,213 | +0,02 |
| M3 | + taxa 30 → 10 Hz (= `sim_lite:=true`) | **0,420** | **+0,21** |
| M4 | + taxa 10 → 5 Hz | 0,507 | +0,09 |

**Leitura:** o custo é **por quadro renderizado**, não por pixel. Cortar os
pixels para um quarto quase não mudou nada; cortar a taxa mudou tudo. O que
pesa é renderizar a cena (terreno lunar) a cada quadro, duas vezes (RGB +
profundidade). Rendimento decrescente: 30 Hz → 0,21; 10 Hz → 0,42;
5 Hz → 0,51; 2 Hz → 0,63.

## O que o `sim_lite` muda

| | Completo (default) | `sim_lite:=true` |
|---|---|---|
| Câmera RGBD | 720×480 @ 30 Hz | 320×240 @ 10 Hz |
| `/camera/points` na bridge | sim | não |
| Obstáculos do costmap local | `voxel_layer` ← `/camera/points` | `obstacle_layer` ← `/scan` |

`/camera/points` **tinha um consumidor real**: o `voxel_layer` do
`local_costmap` era a única fonte de obstáculos locais. Tirar a nuvem da
bridge sem trocar a fonte deixaria o Nav2 cego. No perfil leve, o costmap
local passa a usar o lidar (2D, ±1 rad à frente) via `ObstacleLayer`.

Onde está:

- `rover_description/robots/rover.urdf.xacro` — `xacro:arg` `camera_width`,
  `camera_height`, `camera_rate` (defaults = perfil completo)
- `rover_description/launch/robot_state_publisher.launch.py` e
  `rover_gazebo/launch/include/spawn.launch.py` — repassam os args ao xacro
- `rover_gazebo/launch/gazebo.launch.py` — `sim_lite` + ajuste fino, bridge
  com/sem nuvem, `local_obstacle_source` para o Nav2
- `rover_navigation/launch/bringup.launch.py` — `local_obstacle_source:=camera|scan`

## Validação da localização (perfil leve)

A câmera alimenta `rgbd_odometry` → `/odom_rgbd` → EKF (+ IMU) → `/odom`.
Degradar a câmera não pode quebrar essa cadeia.

| Checagem | `sim_lite` | Completo |
|---|---|---|
| `/odom_rgbd` publica | ✅ ~10 Hz sim, covariância baixa (VO não perdida) | ✅ |
| EKF `/odom` | ✅ | ✅ |
| TF `map→base_link` | ✅ sem `NaN`, sem quebra | ✅ |
| `/map` (slam_toolbox) | ✅ | ✅ |
| Goal `map (2,0; 0,5)` | ✅ `SUCCEEDED` | ✅ `SUCCEEDED` (94 s de parede) |
| Pose final no `map` | (1,52; 0,42) — 0,48 m do alvo | (1,85; 0,62) — 0,19 m do alvo |
| Divergência `/odom` × `map` ao fim | 0,40 m | 0,33 m |

A deriva da odometria (corrigida depois pelo slam_toolbox) **já existia no
perfil completo** — não é efeito do `sim_lite`. A pose final mais longe do
alvo no perfil leve é uma rodada só de cada; precisa de repetições para
separar de ruído.

## Prioridade de CPU (`nice 12`)

Todos os processos do container rodam em `nice 12`. A origem **não está no
repositório**: é o **System76 Scheduler** (`com.system76.Scheduler.service`,
Pop!_OS), que rebaixa `dockerd`/`containerd` como serviço de fundo, e o
container herda. O systemd não define `Nice` para o Docker. Como é
configuração local da máquina, não foi alterada. Entre processos do ROS o
efeito é neutro; contra o desktop em `nice 0`, o Gazebo perde arbitragem.

## Limitações e próximos passos

- **A nuvem continua sendo gerada dentro do Gazebo.** O sensor é
  `rgbd_camera`, que sempre produz `points`; tirar da bridge só elimina a
  serialização. Não há opção no SDF do Harmonic para desligar essa saída.
- **RTF ≥ 0,6 não foi atingido.** O próximo suspeito é o custo fixo: passo
  de física (`moon.world` não tem bloco `<physics>`, usa 1 ms / 1000 Hz) e o
  `gpu_lidar` a 10 Hz. Testar `max_step_size` 0,002 / 0,004 com checagens de
  sanidade (rover não afunda, suspensão estável, teleop coerente).
- Medições com uma rodada cada; o ruído observado entre reinícios foi ~±0,01.


# Chat Web — Comandar o Rover por um Link


> Página pública (Render) onde um LLM gratuito (Groq) comanda o rover simulado no PC, através de um agente local que mantém a camada de segurança.


{{< toc >}}

```
navegador ──ws /chat──▶ server.py (Render, grátis) ──HTTPS──▶ LLM (Groq, grátis)
                             ▲
                             │ ws /agent  (conexão de SAÍDA, aberta pelo PC)
                             │
                        agent.py (PC) ─▶ rover_mcp_safe ─▶ rosbridge :9090 ─▶ ROS 2 / Gazebo
```

O PC fica atrás do roteador, então o site não consegue chamar o PC. Por isso
quem abre a conexão é o **agente no PC**. Nenhuma porta do PC fica exposta na
internet, e a política de segurança (`rover_mcp_safe`) continua rodando no PC:
mesmo que o site fosse comprometido, ele só conseguiria pedir as 4 tools
abaixo, nunca `/cmd_vel`.

## As 4 tools dedicadas

Elas substituem as tools genéricas do ros-mcp que confundiam o modelo (ver
[ROS-MCP](/ros-mcp), seção "Falhas do teste com LLM").

| Tool | O que faz |
|---|---|
| `navigate_to(x, y, yaw_deg, timeout_s)` | pausa o explore, manda o goal ao Nav2, **espera o fim** e responde `ARRIVED` / `ABORTED` / `CANCELED` / `TIMEOUT`, com a posição final e a distância até o alvo. Recusa alvos a mais de 30 m. |
| `stop_navigation()` | pausa o explore e cancela **todos** os goals do Nav2, inclusive os do `explore_lite` |
| `set_exploration(enabled)` | liga/desliga o `explore_lite` |
| `get_robot_pose()` | posição no frame `map`, calculada pelo `/tf` (map→odom→base_link) |

Os perfis do `rover_mcp_safe.py` (`--profile` ou `ROVER_MCP_PROFILE`) são:

- `nav` (padrão): as 4 tools mais as de leitura.
- `minimal`: só as 4 tools. É o perfil usado pelo chat web.
- `full`: inclui as escritas genéricas antigas, só para depuração.

O botão **PARAR** da página chama `stop_navigation` direto, sem passar pelo LLM,
e funciona mesmo enquanto um `navigate_to` está esperando.

## Montar (uma vez)

1. **Chave grátis do Groq:** crie uma conta em console.groq.com → *API Keys* →
   *Create API Key*. Não pede cartão. O modelo padrão é o `llama-3.3-70b-versatile`.
   Para trocar de provedor, mude `LLM_BASE_URL`/`LLM_MODEL` (qualquer API compatível
   com OpenAI serve, por exemplo Gemini ou OpenRouter).
2. **Render:** crie uma conta em render.com com o GitHub → *New* → *Blueprint* →
   escolha o repositório `ros2_nav2`. O `render.yaml` da raiz cria o serviço
   `rover-chat` (plano free). Ele pede:
   - `LLM_API_KEY`: a chave do Groq;
   - `CHAT_PASSWORD`: a senha da página (invente uma);
   - `AGENT_TOKEN`: é gerado automaticamente. Copie em *Environment* para usar no PC.
3. A URL fica algo como `https://rover-chat-xxxx.onrender.com`.

## Usar (toda vez)

```bash
# 1) simulação (container) — explore:=false para a IA comandar sem disputa
docker start rover_mcp
docker exec -it rover_mcp bash
ros2 launch rover_bringup rover_mcp_sim.launch.py \
  slam:=true explore:=false headless:=true launch_rviz:=false sim_lite:=true

# 2) agente (host, outro terminal) — espere o /odom existir (~1 min)
cd ~/Documentos/ros2_nav2
~/.local/share/pipx/venvs/ros-mcp/bin/python -I tools/rover_web/agent.py \
  --server wss://rover-chat-xxxx.onrender.com --token 'COLE_O_AGENT_TOKEN'
# deve imprimir: connected to wss://... with tools: get_robot_pose, navigate_to, ...
```

Depois abra a URL no navegador (funciona no celular também), digite a senha e
mande ordens: "onde você está?", "vá para x=2, y=0", "ative a exploração", "pare".

## Teste local, sem Render

```bash
PY=~/.local/share/pipx/venvs/ros-mcp/bin/python
LLM_API_KEY=... AGENT_TOKEN=t CHAT_PASSWORD=p $PY -I tools/rover_web/server.py   # http://localhost:8000
$PY -I tools/rover_web/agent.py --server ws://127.0.0.1:8000 --token t
```

Sem chave do Groq, dá para usar o Ollama local, que tem API compatível:
`LLM_BASE_URL=http://127.0.0.1:11434/v1 LLM_MODEL=llama3.2 LLM_API_KEY=x`.
Sem GPU, porém, ele leva cerca de 1,5 min por resposta.

## Limites e armadilhas

- **O Render free dorme** depois de cerca de 15 min sem acesso, e acordar leva
  cerca de 1 min. O agente faz um ping a cada 10 min e se reconecta sozinho, com
  espera crescente.
- **A cota do Groq free** é limitada por minuto e por dia. Se estourar, a página
  mostra "the free LLM quota is exhausted". Espere e tente de novo.
- **Um agente por vez:** um agente novo derruba o anterior.
- **A navegação ainda falha no terreno lunar.** As tools relatam isso
  corretamente (`ABORTED`), mas o Nav2 aborta com frequência ("Start occupied",
  "exceeded maximum iterations"). O lidar 2D tem alcance de 5 m e marca rampas do
  terreno como parede no mapa do SLAM. Goals curtos em linha reta, a partir do
  início, funcionam (validado: `ARRIVED` a 2 m).

## Validação (2026-11-12)

| Teste | Resultado |
|---|---|
| `navigate_to(2, 0)` a partir da origem | ✅ `ARRIVED` (28 s; 0,49 m do alvo, dentro da tolerância do Nav2) |
| `navigate_to(6, 0)` + `stop_navigation` após 20 s | ✅ `STOPPED` (1 goal cancelado) e o `navigate_to` respondeu `CANCELED` |
| Goal com o rover sobre um "obstáculo" fantasma | ✅ `ABORTED`, sem afirmar que chegou |
| `get_robot_pose` com o rover parado | ✅ 0,1 s, frame `map` (o `/pose` do slam_toolbox fica mudo nessa situação) |
| Agente com token errado | ✅ recusado (HTTP 403), o agente sai |
| Chat com senha errada | ✅ "senha incorreta" |
| Chat → LLM (Ollama llama3.2, local) → `get_robot_pose` → resposta | ✅ ponta a ponta |
| Botão PARAR | ✅ chama `stop_navigation` direto, sem passar pelo LLM |
| Fluxo com Groq + Render reais | ⏳ falta a chave/conta do usuário |


# SPI Port Registry

> **Single source of truth**: `/opt/projects/spi-manager/config/service_registry.yaml`
> Module: `/opt/projects/spi-manager/app/port_registry.py`

## Scheme

| Range  | Environment | Category      |
|--------|-------------|---------------|
| 65xxx  | Production  | —             |
| 64xxx  | Staging     | —             |
| 650xx  | Production  | Platform      |
| 652xx  | Production  | Coding        |
| 653xx  | Production  | Companion     |
| 654xx  | Production  | Avatar        |
| 655xx  | Production  | Video         |
| 656xx  | Production  | Image         |
| 657xx  | Production  | Audio         |
| 658xx  | Production  | Text/LLM      |

Staging mirrors production category with 64xxx prefix (e.g. parkiet prod=65700, staging=64700).

---

## Platform (650xx)

| Port  | Service         | Legacy | Description |
|-------|----------------|--------|-------------|
| 65000 | spi-manager    | 63115  | Central control plane / AI gateway |
| 65001 | tickets        | 63119  | Task tracking |
| 65010 | ntfy           | 61138  | Push notifications |
| 65020 | neo4j          | 61521  | Graph database |
| 65021 | chromadb       | 61510  | Vector database |
| 65030 | examtool       | 63125  | Exam/assessment tool |
| 65031 | sentimentmeter | 63810  | Sentiment analysis |
| 65040 | uniek_tools    | —      | External tool node for agents (REST API + MCP) |

## Coding (652xx)

| Port  | Service       | Legacy | Description |
|-------|--------------|--------|-------------|
| 65200 | qwen3-coder  | 61628  | Qwen3-Coder-30B Q4 MoE (on-demand GPU) |
| 65201 | cliagent     | 63740  | CLI agent (Claude/Codex/Gemini oneshot) |

## Companion (653xx)

| Port  | Service              | Legacy | Description |
|-------|---------------------|--------|-------------|
| 65300 | wa-bridge-spending  | 61801  | WhatsApp bridge (spending approvals) |
| 65301 | wa-bridge-openclaw  | 61851  | WhatsApp bridge (OpenClaw) |
| 65302 | signal-bridge       | 61853  | Signal bridge |
| 65303 | telegram-bridge     | 61855  | Telegram bridge |
| 65304 | aaa-channels        | 61856  | AAA channels API (WhatsApp/Baileys, Docker) |
| 65310 | sillytavern         | 63918  | AI chat frontend |

## Image (656xx)

| Port  | Service          | Legacy | Description |
|-------|-----------------|--------|-------------|
| 65600 | spi-comfyui     | 63620  | ComfyUI image/video backend |
| 65601 | spi-comfyui-api | 63118  | ComfyUI character REST API |
| 65602 | imgen           | 63145  | Character reference image generator |

## Audio (657xx)

| Port  | Service      | Legacy | Description |
|-------|-------------|--------|-------------|
| 65700 | parkiet-tts | 63618  | Parkiet 1.6B Dutch TTS |
| 65701 | whisper-stt | 63619  | Whisper large-v3 STT |

## Text/LLM (658xx)

| Port  | Service        | Legacy | Description |
|-------|---------------|--------|-------------|
| 65800 | qwen3-heretic | 61611  | Qwen3-4B Heretic (warm, GPU) |
| 65801 | phi35         | 61615  | Phi 3.5 Mini Q4 (CPU fallback) |
| 65802 | dolphin-q4    | 61614  | Dolphin Mistral 24B Q4 (GPU) |
| 65803 | phi4mini-gpu  | 61627  | Phi-4-mini Heretic Q4 (GPU) |

---

## Experimental ranges (agent-allocated)

| Range        | Label              | Description |
|--------------|--------------------|-------------|
| 61700–61799  | agent-experiment-a | Temporary agent-spawned services |
| 61900–61999  | agent-experiment-b | Temporary agent-spawned services |

Register via `POST /v2/registry/allocate-port` to avoid conflicts.

---

## Legacy bridge (Caddy)

During migration, port 63115 is bridged to 65000 via Caddyfile so old callers still work.
Remove bridge once all callers have been updated.

# Fase 2: display e input no R35S Panel 0

Ensaios realizados em **23/10/2026, America/Sao_Paulo**, após autorização para iniciar a Fase 2. Framebuffer e SDL/GLES passaram, com confirmação visual do usuário. O perfil próprio de muinput funcionou em execução nativa, com cobertura dos controles e retorno ao centro. **A verificação estrita da sequência registrou uma ressalva em L3**, detalhada abaixo; não se deve declarar unicidade de todos os acionamentos sem essa ressalva.

O alvo permanece o R35S genuíno, DT model `R36S-V12 2023-08-18 Panel 0`, dArkOSen/Debian 13, kernel 4.4.189. Não foi construída imagem de firmware, nem iniciado o frontend muOS completo. Nenhum arquivo em `refs/` foi alterado.

**Achado posterior na Fase 3:** o dmesg conservava dois `BUG: Bad page map` associados a processos musplash da sessão anterior, além de `Bad rss-counter`. A confirmação visual não aprova a segurança do mmap/BSP; não repetir esse caminho como se estivesse validado integralmente. Erros posteriores MMC/Btrfs também suspenderam a bancada. Ver [registro posterior](phase3-storage-stop.md); isso não estabelece relação causal entre os eventos.

## Inventário real, antes dos testes

Coleta reproduzível: [phase2-inventory.py](../../port/scripts/phase2-inventory.py). Os ioctls usados pelo inventário são getters; não há grab de input nem chamada de `SDL_Init`. A consulta SDL carrega a biblioteca em um subprocesso: seus construtores carregam RGA, abrem seu dispositivo e imprimem diagnósticos nativos. Isso foi observado e registrado; não é correto tratar `dlopen` dessa biblioteca customizada como completamente livre de efeitos de inicialização.

| Item | Observado |
| --- | --- |
| Framebuffer | `/dev/fb0`, 640×480, virtual 640×480, offsets 0,0, 32 bpp, stride 2560, memória 1228800 bytes |
| Canais do pixel | R offset 16/8 bits, G 8/8 bits, B 0/8 bits |
| Identificação fb | `fb_fix_screeninfo.id` vazio; a implementação exata desse fb ainda não foi identificada |
| Backlight | `/sys/class/backlight/backlight`, atual 80, máximo 160, `bl_power=0` |
| DRM | card0, DSI-1 connected/enabled; modo nominal sysfs `640x480p60` |
| Modo CRTC ativo | clock 29000 kHz, htotal 732, vtotal 661, hsync/vsync 2/2; cálculo **59.935683 Hz** |
| SDL de pacote | `libsdl2-2.0-0:arm64` reportado pelo dpkg como `2.32.4+dfsg-1` |
| SDL realmente carregado | `/usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.0.3200.10`, **2.32.10**, revisão `SDL-release-2.32.10-0-g5d2495703` |
| Backends SDL compilados | `KMSDRM`, `offscreen` |
| EGL/GLES | symlinks resolvem para `libmali-bifrost-g31-rxp0-gbm.so`, não para a implementação Mesa instalada em paralelo |
| SDL transitivo | inclui `libsamplerate.so.0`, `librga.so.2`; o loader também resolveu libdrm, libstdc++ e libgcc_s existentes |
| Permissões | usuário `ark` pertence a video/render/input; sudo não interativo disponível; não foram alterados grupos ou modos dos dispositivos |
| Input | gamepad event2/js0; volume em `odroidgo3-keys` event3; power em `rk8xx_pwrkey` event0 |

O CRTC foi consultado por [drm-mode-probe.c](../../port/diagnostics/drm-mode-probe.c), usando `drmModeGetResources/GetCrtc`, sem modeset. Os timings ativos diferem dos DTBs estáticos da auditoria, inclusive do nó chamado `60Hz`. O cálculo do modo e a medição de apresentação são evidências melhores para este ensaio que herdar `screen/refresh` de G350/Pixel. Ainda não foi estabelecido qual componente escolheu esse modo no sistema atual.

Não foi obtido `/sys/kernel/debug/dri/0/state`: esse arquivo não existe no alvo. A consulta libdrm substituiu essa leitura, sem montar debugfs ou instalar ferramentas.

## Build e proveniência

Foram usados os mesmos refs/commits da auditoria, em especial frontend `5e8635b3b485eec9ad2ace141c415fd2df47d8f1`.

- [phase2-toolchain.Containerfile](../../port/packaging/phase2-toolchain.Containerfile) estende a toolchain da Fase 1, mantendo os snapshots Debian de `20261023T000000Z` e acrescentando headers/libs de desenvolvimento arm64 SDL2/libpng/libdrm. Dependências, inclusive as de desenvolvimento de outros backends SDL, foram instaladas **somente no container**.
- [build-phase2-probes.sh](../../port/scripts/build-phase2-probes.sh) copia `musplash.c` e LICENSE por `git archive`, aplica o patch somente em `build/phase2/source/` e compila os probes C. O `musplash` tem dependências suficientes para compilação direta desse arquivo: não foi executado o Makefile global do frontend.
- [build-phase2-input.sh](../../port/scripts/build-phase2-input.sh) usa a toolchain da Fase 1 e cópia de `input/`, aplicando o perfil somente em `build/phase2-input/source/`.
- C11, baseline `-march=armv8-a`, PIE, RELRO/BIND_NOW, stack protector e FORTIFY; input mantém LTO. Fontes, patches, licença GPLv3 upstream, símbolos, inspeção ELF, pacotes e checksums acompanham os artefatos locais.
- Loader e dependências foram verificados no R35S antes da execução. Nenhuma libc, SDL, EGL, GLES, RGA ou outra biblioteca foi transferida para substituir as instaladas.
- Reconstruções completas produziram os mesmos bytes dos binários efetivamente testados.

Os headers SDL Debian usados para compilar não são uma cópia exata da biblioteca customizada do aparelho. A validação aqui é específica das funções efetivamente usadas pelos probes e da execução realizada; não prova ABI de outro rootfs, nem todos os caminhos do frontend.

| Artefato testado | SHA256 |
| --- | --- |
| `dist/phase2/musplash` com patch | `58034c70e14baa97c8cd33e20f1b336117f7983b9d4f069f1ec65fe90fe28259` |
| `dist/phase2/sdl-video-probe` | `2de9670b4e91e7ca430e9ab60d26aaace0a9097020a91a1a8d4209f275e68b59` |
| `dist/phase2/drm-mode-probe` | `415573e5508654604c65117d4f7484cc75239e8344d25d7216c593cd96328d7f` |
| `dist/phase2/panel-test.png` | `a0e284b60d36da31b8761ad0d6f57652fc727d3f4e701d697b279b6d117dc64d` |
| `dist/phase2-input/muinput` | `7cf6f81e83d6033ce929b8741fae3d494916b8ac5e4875e92d2c9b63964ff96a` |

## Framebuffer: falha original e adaptação mínima

O `musplash` upstream sem alterações falhou antes de desenhar:

```text
Failed to open framebuffer: /dev/fb0
failed to open /dev/fb0: mmap: Invalid argument
MUSPLASH_SESSION_EXIT_STATUS=1
```

Em `module/musplash.c:724` do commit analisado, o caminho `pread/pwrite` já existe, mas é escolhido apenas se `fix.id` começa com `rockchip`. O fb deste aparelho anuncia ID vazio; `mmap` falha com EINVAL, enquanto a leitura completa e a restauração por escrita funcionaram.

O [patch 0001](../../port/patches/0001-musplash-fb-read-write-fallback.patch) permite usar esse caminho existente quando `mmap` retorna EINVAL, ENODEV ou ENOSYS; exige leitura completa da memória antes de desenhar. Erros de permissão e outros erros continuam sendo falha. **Foi testado o caso EINVAL deste aparelho**, não todos os drivers ou todos os retornos possíveis. Não houve mudança de kernel/DTB ou implementação paralela do splash.

Com o patch, o teste exibiu o PNG 640×480 gerado por [make-phase2-pattern.py](../../port/scripts/make-phase2-pattern.py), com números e cores nos quatro cantos:

- alto esquerdo: 1/vermelho; alto direito: 2/verde;
- baixo esquerdo: 3/azul; baixo direito: 4/branco.

O usuário confirmou orientação, cores, ausência de cortes/cintilação. Leituras dos pixels de referência do fb retornaram `0xff0000`, `0x00ff00`, `0x0000ff`, `0xffffff`. O trace confirmou 640×480/32 bpp e caminho buffered. O teste `--wait` foi limitado a 45 segundos; o status **124 é do timeout planejado**, e o musplash tratou TERM e registrou `Done`.

Isso comprova pixels via framebuffer neste driver. Não comprova aceleração, EGL ou desempenho do frontend; esses pontos foram ensaiados separadamente.

## SDL/GLES: execução e apresentação

O [sdl-video-probe.c](../../port/diagnostics/sdl-video-probe.c) usa SDL2 e o mesmo formato básico de janela/renderer do frontend em `common/platform/display.c:712–765`: fullscreen 640×480, hint `opengles2`, renderer acelerado e vsync. A execução ocorreu como `ark`, com KMSDRM e as bibliotecas gráficas já instaladas.

```text
video_driver=KMSDRM
display_mode=640x480@60
renderer=opengles2
renderer_flags=0xe
output_size=640x480
gl_vendor=ARM
gl_renderer=Mali-G31
gl_version=OpenGL ES 3.2 v1.r13p0-01rel0...
readback_red_pixel=PASS
frames=1798
elapsed_seconds=30.015
average_fps=59.904
render_failures=0
frame_interval_median_ms=16.680
frame_interval_p95_ms=17.035
sdl_probe_exit_status=0
SDL_SESSION_EXIT_STATUS=0
```

O renderer SDL é `opengles2`; a implementação identifica contexto OpenGL ES 3.2. Não se deve transformar isso em exigência de GLES 3.2 para o frontend. As flags incluem aceleração, vsync e suporte a render target. O usuário confirmou as cores e o retângulo amarelo em movimento contínuo, sem rotação.

Um primeiro lançamento parou no launcher porque `runuser` não estava no PATH recebido por sudo. O launcher foi corrigido para `/usr/sbin/runuser`; houve restauração dos serviços antes da repetição. Esse erro de lançamento não foi atribuído a incompatibilidade SDL.

O ensaio durou 30 segundos e não substitui teste prolongado, LVGL completo, fontes/temas, áudio, suspend ou retomada de conteúdo.

## Input físico e perfil próprio

A captura leu evdev sem grab e sem injeção. EmulationStation, ogage e Fn watcher foram parados temporariamente; `systemd-inhibit` bloqueou o tratamento de power/suspend pelo logind durante a coleta física. A configuração existente também informa `HandlePowerKey=ignore`. A tela preta durante essa captura era esperada: não havia interface gráfica ativa.

O usuário realizou a sequência de controles especificada. Foram registrados **99 eventos relevantes**, com 20 pressões e liberações correspondentes, sem `SYN_DROPPED` ou teclas presas. A coleta foi encerrada por INT após o usuário terminar; esse encerramento foi de operação, não uma falha do driver. Os dados já estavam gravados e os serviços foram restaurados.

| Controle físico | Fonte observada | Saída do perfil |
| --- | --- | --- |
| D-pad | BTN_DPAD_UP/DOWN/LEFT/RIGHT, `0x220–0x223` | ABS_HAT0X/Y, −1/0/+1 |
| A/B/X/Y | BTN_EAST/SOUTH/NORTH/WEST | Mesmos códigos; **sem a troca A/B do G350** |
| L1/R1/L2/R2 | BTN_TL/TR/TL2/TR2 | Mesmos códigos |
| Select/Start | HAPPY1/HAPPY2, `0x2c0/0x2c1` | BTN_SELECT/START |
| Fn | HAPPY5, `0x2c4` | BTN_MODE |
| L3/R3 | HAPPY3/HAPPY4, `0x2c2/0x2c3` | BTN_THUMBL/THUMBR |
| Volume −/+ | KEY_VOLUMEDOWN/UP, `114/115`, event3 | Mesmos códigos no virtual |
| Power curto | KEY_POWER, `116`, event0 | Mantido no nó físico separado; não encaminhado ao gamepad virtual |

Os sticks anunciavam −1800…1800, centro 0, fuzz/flat 32. A sequência isolada confirmou X/Y para o esquerdo, RX/RY para o direito, com esquerda/cima negativas e direita/baixo positivas. O maior RX capturado foi 1788; não se presumiu que toda amostra extrema fosse exatamente o limite anunciado. A saída usa o scaler/calibração já existente em muinput; não copia inversões ou a reorganização de eixos do G350.

O [patch 0002](../../port/patches/0002-muinput-r35s-panel0-profile.patch) acrescenta:

- backend **`rk-r35s-p0`**, source por nome `GO-Super Gamepad`, auxiliar `odroidgo3-keys`;
- identidade virtual `BUS_VIRTUAL=0x0006`, vendor `0x756d`, produto **0x3504**, versão `0x736f`, sem reutilizar IDs existentes no snapshot;
- mapeamento HAPPY1–5 específico, eixos padrão com calibração e leitura auxiliar de volume;
- rumble sem driver e sem capacidades FF no descriptor, evitando qualquer escrita PWM/GPIO por esse perfil.

O contrato está em [input-profile.json](../../port/device/rk-r35s-p0/input-profile.json). Trata-se de um perfil **de input**, não de um perfil de firmware completo. O teste selecionou `--device rk-r35s-p0` explicitamente. Não foi acrescentada autodetecção de placas; a integração futura precisa de board config e da tabela de boards do frontend. O código comum de mapeamento/calibração/isolamento continua sendo o upstream, e os outros backends mantêm seus caminhos.

## Teste normalizado e proteção dos nós existentes

O backend evdev upstream renomeia fontes para `/dev/muinput` e remove links públicos para evitar detecção duplicada por SDL. Executá-lo diretamente no `/dev` do dArkOSen alteraria seus nós durante o teste. Por isso o [launcher de namespace](../../port/scripts/phase2-input-namespace.py) usou `unshare --mount --fork`, propagação privada e tmpfs particulares em `/dev` e `/run`, recriando somente os device nodes necessários. Os dispositivos físicos e ioctls continuam reais; não é emulação da entrada.

O programa confirma que está no diretório temporário autorizado e que seu mount namespace difere do namespace registrado pelo supervisor antes de montar qualquer coisa. O namespace protege nomes/paths; o grab do kernel continua real e é liberado ao encerrar. A criação uinput também é real: um nó virtual temporário aparece no host enquanto o daemon roda, sendo removido quando ele fecha o dispositivo. Não há ocultação desse efeito no relatório.

Foram observados:

```text
Using input backend: rk-r35s-p0 (R35S R36S-V12 Panel 0)
Using evdev source /dev/input/event2 (GO-Super Gamepad, 0019:484b:1100)
Isolated rk-r35s-p0 source under /dev/muinput
Using evdev source /dev/input/event3 (odroidgo3-keys, 0019:0001:0001)
virtual_id=[6, 30061, 13572, 29551]
NORMALIZED_CAPTURE_FINISHED
muinput_exit_status=0
NORMALIZED_SESSION_EXIT_STATUS=0
```

O usuário repetiu a sequência sem Power. Houve **70 eventos relevantes**, incluindo uma conferência adicional de L3. Os hats produziram −1,0,+1,0 em cada eixo; X/Y/RX/RY atingiram −32767/+32767 e retornaram a zero. Pressões/liberações ficaram balanceadas; não houve `SYN_DROPPED` ou tecla presa. A captura e o daemon encerraram normalmente.

### Ressalva em L3

Na primeira passagem normalizada, BTN_THUMBL registrou:

```text
36.7716 s: 1
36.8075 s: 0
36.8204 s: 1
36.9634 s: 0
```

A conferência solicitada de um clique, ainda na mesma captura, gerou somente `1` em 84.1597 s e `0` em 84.1956 s. O primeiro teste físico bruto havia registrado um único par para L3.

**Fato:** dois pares na primeira passagem normalizada, um par na repetição. **Hipóteses:** gesto/pressão ou contato do botão; a causa não foi determinada. Não foi acrescentado filtro temporal para esconder o evento, pois isso pode eliminar cliques curtos legítimos. O [analisador](../../port/scripts/analyze-phase2-input.py) mantém `normalized_button_order=false` e `pass=false` no resultado estrito; as demais verificações passam e `l3_recheck.single_pair=true`.

Decisão posterior do usuário, ao autorizar a Fase 3: tratar a ocorrência isolada como margem de erro e priorizar a investigação se voltar a aparecer. Os eventos e o resultado estrito original são preservados.

Portanto a cobertura e normalização básicas foram demonstradas, mas o critério estrito de unicidade fica com ressalva. Antes de declarar essa parte totalmente aprovada para uso prolongado, convém repetir uma sequência curta de L3 com observação simultânea da fonte e da saída, sem inferir automaticamente defeito de hardware ou bug de mapeamento.

## Restauração e estado final

[phase2-device-session.py](../../port/scripts/phase2-device-session.py) salva framebuffer e serviços previamente ativos, arma um timer **transitório** de recuperação, limita os processos e restaura em `finally`. O timer foi armado e cancelado nos ensaios; seu disparo independente não foi testado matando o supervisor. A restauração normal também funcionou nas falhas iniciais de mmap e launcher.

Uma checagem automática adicional de dois segundos confirmou a inicialização e limpeza do namespace com as proteções finais do launcher, sem nova interação física.

Ao final foram conferidos:

- EmulationStation, ogage e Fn watcher ativos novamente; enabled/disabled não foram alterados.
- brilho 80 e geometria original; não se executou variação de brilho, blank prolongado ou suspend;
- event0–event3 e js0 preservados, sem renomeação no namespace do host;
- nenhum processo de muinput/splash/probe restante e nenhum controller virtual remanescente;
- ausência de `/dev/muinput`, `/run/muinput`, `/opt/muos` e de timers de recuperação ativos;
- coleta dos logs e remoção do diretório temporário do teste; conexão SSH criada pelo agente encerrada.

Não foram gravadas partições, kernel, DTB, firmware, regras udev, units persistentes ou bibliotecas. Não houve instalação de dependências no aparelho ou host. A instalação dArkOSen permanece sendo a bancada temporária, sem transformar esse ensaio no destino do port.

## Evidências e repetição

Evidências locais em `build/phase2/`: `inventory.json`, `graphics-details.txt`, `target-loader-drm.txt`, `framebuffer-session.txt` (falha original), `framebuffer-patched-session.txt`, `framebuffer-readback.txt`, `sdl-session-retry.txt`, `input-events.jsonl`, `device-logs/` e `post-test-state.txt`. A conferência posterior ao smoke test está em `final-target-state.txt`; `cleanup.txt` confirma a remoção do staging e `ssh-close.txt` registra o encerramento da conexão criada pelo agente.

Em `build/phase2-input/`: `target-list.txt`, `normalized-session.txt`, `normalized-events.jsonl`, `validation.json` e `namespace-guard-smoke.txt`. Os logs de build ficam nos respectivos diretórios. `build/` e `dist/` são ignorados pelo Git; este relatório conserva os resultados principais e hashes.

Builds no host, após preparar a toolchain da Fase 1:

```sh
bash port/scripts/build-phase2-probes.sh
bash port/scripts/build-phase2-input.sh
# Reproduz a checagem estrita; retorna 1 pela ressalva de L3 registrada.
python3 port/scripts/analyze-phase2-input.py \
    build/phase2/input-events.jsonl build/phase2-input/normalized-events.jsonl 75
```

Para repetir no aparelho, conferir identidade, checksums e ambiente, transferir apenas artefatos/scripts para um diretório aleatório `/tmp/muos-r35s-phase2.*` e invocar o supervisor por sudo com `framebuffer`, `sdl`, `input` ou `normalized`. O último modo exige também `muinput-r35s` e o launcher de namespace no mesmo diretório; o binário é o de `dist/phase2-input/muinput` renomeado apenas no staging. O supervisor e o launcher recusam execução diretamente no checkout. Não executar muinput em modo daemon sobre os nós globais do dArkOSen como atalho.

## Próximos limites

A Fase 3 ainda precisa integrar board table/config comum+overrides, GUID/mapping SDL, recursos do menu, paths e ações de sistema em staging controlado. Permanecem sem validação frontend completo, áudio, brilho variável/blank, bateria, shutdown, suspend/resume e boot autônomo. A ressalva de L3 e a origem da SDL customizada/timings ativos devem continuar visíveis nessa integração. Nenhum resultado aqui é uma promessa de compatibilidade com outro rootfs, painel, clone ou revisão de R35S/R36S.

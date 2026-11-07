# Fase 3 — primeiro menu muOS em bancada

Trabalho iniciado em 23/10/2026, America/Sao_Paulo, por autorização explícita do usuário. Alvo único: R35S RK3326, `R36S-V12 2023-08-18 Panel 0`, dArkOSen/Debian 13 e kernel 4.4.189. Esta fase usa o Debian como bancada; não produz firmware autônomo.

**Estado: recorte funcional do primeiro menu validado, com ressalva dos sons do tema.** Menu, texto/orientação e navegação foram confirmados após corrigir o mapeamento SDL. Na [retomada de 24/10](phase3-audio-resume.md), navegação/confirmação ficaram audíveis, a reprodução de Fn/B passou com WAV de controle e o corte da confirmação ao encerrar foi corrigido e aprovado. Os sons originais da ajuda continuam inaudíveis no speaker; o pacote mantém esses arquivos e não tem aprovação integral de todos os efeitos. Isso valida o recorte de bancada, não o frontend completo ou firmware. Os erros anteriores de armazenamento/kernel estão no [registro de interrupção](phase3-storage-stop.md).

**Histórico:** a [recuperação autorizada dos cartões](storage-recovery.md) permitiu retomar os ensaios. As descrições de falha de áudio abaixo pertencem à primeira sessão de 23/10; os resultados atuais, a troca temporária de WAVs, a correção do encerramento e os novos hashes estão no [relatório de retomada](phase3-audio-resume.md).

A ocorrência isolada de L3 na Fase 2 foi aceita pelo usuário como margem de erro. Os eventos e a reprovação estrita histórica continuam preservados; uma recorrência futura deve receber prioridade de investigação. Não foi aplicado debounce para ocultar o evento.

## Recorte escolhido e limite da prova

O [executor de bancada](../../port/diagnostics/phase3-menu.c) chama **`muxlaunch_main()` upstream**, com o renderer, widgets, navegação, fontes, tradução, ajuda e input comuns do muOS. O menu não foi reimplementado em outro toolkit. Foram excluídos o dispatcher `muxfrontend`, o boot `sysinit`, hotkey daemon, instalador, terminal, libretro e encaminhador gráfico de 32 bits.

Em `module/muxlaunch.c:520–625`, o menu inicializa a UI e chama `mux_input_task()`. Seleções usam `load_mux()` e encerram esse loop; `muxfrontend.c:562–651` normalmente associa as ações a outros módulos. O executor de bancada intercepta `load_mux` no link, registra a escolha e termina. Assim, selecionar Informações comprova o botão A e a seleção, **não a execução do submenu Informações**. O mesmo limite vale para as outras ações.

`common/ui/common.c:1602–1604` também tenta chamar `script/device/bright.sh` na primeira atualização de brilho. O wrapper de `run_exec` registra e recusa essa execução. A evidência real inclui:

```text
PHASE3_EXEC_BLOCKED=/opt/muos/script/device/bright.sh
PHASE3_SELECTION=info index=4
```

Esses wrappers pertencem somente ao executável de diagnóstico. Não são implementação definitiva de brilho, energia ou serviços do firmware.

## Build e recursos

- Frontend: commit `5e8635b3b485eec9ad2ace141c415fd2df47d8f1`; recursos/internal: `550cc58f9cd3449a17f53ca55efcdc6c473b5a89`.
- [Container da Fase 3](../../port/packaging/phase3-toolchain.Containerfile): estende a toolchain Debian das fases anteriores, com snapshot `20261023T000000Z`. Pacotes SDL_image/mixer/ttf, HarfBuzz, FreeType, curl, FFmpeg e demais headers/libs arm64 foram instalados somente no container. Nenhuma dependência foi instalada no Bazzite ou no R35S.
- [Build](../../port/scripts/build-phase3-menu.sh) e [Makefile do recorte](../../port/packaging/phase3-menu.mk): cópia via `git archive` em `build/phase3/source/`, baseline `-march=armv8-a`, C11/O2, PIE, stack protector, FORTIFY e RELRO/BIND_NOW. Não executa o alvo global do Makefile upstream nem `external/build.sh`.
- LVGL e PlutoSVG/PlutoVG vêm das fontes vendorizadas. Mojibake 0.3.6 usa URL e SHA256 fixados no recipe upstream: `156bb5c0c1f1265c5d75f4ef53ff4aab09c368e358b05f4f780ba6ec2575fed3`. Fonte MIT e licença acompanham o artefato.
- Fontes do frontend: GPLv3; LVGL/PlutoSVG/PlutoVG e Mojibake: MIT; Noto Sans: SIL OFL 1.1, preservada junto à fonte. O archive de fontes conserva as demais licenças vendorizadas. Não se atribui a licença de topo indiscriminadamente a todas as dependências.
- [Preparação de recursos](../../port/scripts/prepare-phase3-assets.py): 1047 blobs selecionados, com OIDs no manifesto. Inclui config comum, schemes 640×480, glyphs, fonte Noto, tradução PT-BR e sons. Não copia scripts de sistema, emuladores ou vídeos do tema.
- `internal` é parcial/sparse. Objetos ausentes necessários ao staging são buscados em um cache Git próprio sob `build/phase3/deps/`, usando o object store de `refs/` somente como alternativa de leitura. Não expande o checkout nem modifica arquivos upstream.
- [Configuração de bancada](../../port/device/rk-r35s-p0/staging-config.json): sobrepõe a configuração comum com resolução/refresh/brilho medidos; não copia o perfil G350. [Patch de board](../../port/patches/0003-frontend-r35s-panel0-board.patch): acrescenta `rk-r35s-p0` à tabela do frontend, sem novos tratamentos especiais de GPIO/PWM.
- Reutiliza o `muinput` exato aprovado na Fase 2, SHA256 `7cf6f81e83d6033ce929b8741fae3d494916b8ac5e4875e92d2c9b63964ff96a`.

O recorte compila fontes comuns, mas elimina funções não alcançadas com `--gc-sections`. Ainda liga as bibliotecas FFmpeg usadas pelo código comum de wallpaper/preview; não é um frontend completamente livre de dependências de vídeo. Vídeos não foram incluídos no staging, nem sua reprodução foi testada. Warnings de possível truncamento de caminhos em fontes upstream foram observados; não se apresenta este build de bancada como aprovação dos checks estritos de release.

O ELF é AArch64/PIE, com interpreter `/lib/ld-linux-aarch64.so.1`; requer símbolos até GLIBC 2.38 no executável. Loader `--verify`, `--list` e execução `--info` com `LD_BIND_NOW=1` passaram no Debian/glibc 2.41 do alvo. As dependências dinâmicas são resolvidas pelas bibliotecas existentes do aparelho; nenhuma libc, SDL, EGL, GLES ou FFmpeg foi substituída. Isso não prova compatibilidade do futuro rootfs.

## Execução temporária e restauração

O [supervisor](../../port/scripts/phase3-device-session.py) salva framebuffer/serviços e reaproveita a restauração da Fase 2. Para cada ensaio, para temporariamente EmulationStation, ogage e Fn watcher, arma timer transitório de recuperação e inicia o [launcher](../../port/scripts/phase3-namespace.py) em mount namespace privado. Os scripts recusam execução diretamente no checkout ou fora do diretório aleatório `/tmp/muos-r35s-phase3.*`.

O launcher usa chroot no staging, binds somente leitura de `/usr`, `/etc`, `/sys`, proc somente leitura e device nodes próprios. Os nomes `/opt/muos`, `/run/muos`, `/tmp` e `/home/ark` vistos pelo menu pertencem à árvore temporária. Não há montagem de `/boot`, cartão/ROMs ou home real no chroot. Isso organiza os acessos do código auditado; não é uma alegação de sandbox de segurança para programas arbitrários.

Muinput roda como root para grab/uinput. O menu roda como `ark` UID/GID 1000, com `CapEff=0` observado e `PR_SET_NO_NEW_PRIVS` solicitado antes do exec. A criação uinput é real e temporariamente visível no namespace do host; nomes físicos event2/js0 são preservados no host. O namespace apenas protege os nomes, não transforma o input ou os ioctls gráficos em emulação.

Há limite de 120 segundos no executor, timeout externo e timer de recuperação de 210 segundos. A restauração normal foi observada inclusive nas falhas de lançamento; o disparo independente do timer não foi testado matando o supervisor. Um primeiro lançamento falhou porque `chroot` não estava no PATH de sudo; foi corrigido para `/usr/sbin/chroot`, sem atribuir o erro a ABI.

## Correção de input SDL

O primeiro menu apresentou corretamente e o D-pad navegou, mas A/B acionaram a barra de volume e Fn não abriu ajuda. O mapeamento inicial de bancada usava índices inadequados, semelhantes aos perfis upstream; esse foi um erro da adaptação SDL, não evidência de erro nos códigos evdev já capturados.

A consulta nativa mostrou:

```text
SDL_JOYSTICK name=muOS-Keys guid=06004ca66d750000043500006f730000 buttons=15 axes=4 hats=1
PHASE3_JOYDEV_BUTTON_CODES=[304,305,307,308,310,311,312,313,314,315,316,317,318]
```

O GUID real contém o CRC `4ca6`; não basta montar uma string com bus/vendor/product/version e zeros. Joydev anuncia 13 botões BTN; o SDL evdev do aparelho expõe também os dois KEY_VOLUME ao final. A primeira hipótese que exigia 15 botões em joydev foi recusada pelo launcher; não se forçou a execução após a divergência.

| Controle | Índice SDL joystick confirmado/proposto | Mapping |
| --- | --- | --- |
| A / B | 1 / 0; confirmados interativamente | `a:b1,b:b0` |
| X / Y | 2 / 3; derivados do mapa joydev, sem novo teste individual nesta fase | `x:b2,y:b3` |
| L1/R1/L2/R2 | 4/5/6/7; derivados do mapa joydev | shoulders/triggers |
| Select / Start / Fn | 8/9/10; Fn confirmado nesta fase | `back:b8,start:b9,guide:b10` |
| L3 / R3 | 11/12; derivados do mapa joydev; sem repetir teste de L3 | leftstick/rightstick |
| Volume −/+ | 13/14; confirmados interativamente | `volumedown:b13,volumeup:b14` |
| Sticks | eixos 0/1 e 2/3; base evdev validada na Fase 2 | leftx/lefty/rightx/righty |
| D-pad | hat0; navegação confirmada nesta fase | bits 1/4/8/2 |

No ensaio corrigido, os logs registraram B como SDL_CONTROLLER_BUTTON_B=1/joystick0, Fn como GUIDE=5/joystick10 e A como A=0/joystick1. D-pad direita/direita/esquerda e B produziram foco `0→1→2→1→0`; baixo selecionou índice4 na grade 4×2, e A registrou `info`. Usuário confirmou texto/orientação, navegação e ajuda. A grade usa deslocamento por linha em cima/baixo, não incremento de um índice linear.

O ensaio corrigido encerrou com status0 após 44,572s, 80052KiB de RSS máximo, CPU user3,540s/system1,444s. Não houve necessidade de executar submenu para confirmar a seleção.

## Volume e áudio

Os botões de volume fazem o frontend mostrar o indicador. O serviço que efetivamente muda volume e persiste seu estado não está integrado nesta bancada; por isso a barra permaneceu estática. O mixer foi conferido sem alteração: inicialmente `Playback=95,95` de máximo237, `Playback Path=SPK_HP`. Não confundir esse ensaio de eventos com validação do ajuste real de volume.

Inventário: codec `rockchip,rk817-codec`, PCM card0/device0; ausência de PulseAudio/PipeWire ativos e de socket Pulse na sessão. ES mantinha o PCM ALSA aberto. A `.asoundrc` real usa plug/dmix a 44100Hz, período1024/buffer4096; não foi sobrescrita. O ensaio usa configuração ALSA própria no home do chroot, inicialmente plug→hw:0,0, após liberar o PCM parando ES.

Primeira execução sonora: backend ALSA abriu, os 12 WAVs do tema carregaram, chunks reduzidos para32/128. O usuário não ouviu sons. Esse resultado **não passou a validação auditiva**. O menu encerrou normalmente após41,496s, RSS máximo86064KiB, CPU user5,760s/system1,784s. Os WAVs contêm PCM não nulo; análise de duração/pico/RMS foi registrada em `build/phase3/wav-analysis.json`.

O usuário confirmou depois que áudio conhecido do dArkOSen era audível, porém baixo, e aumentou o mixer pelo próprio sistema para `142,142` (60%). A repetição manteve plug→hw e chunks32, acrescentando instrumentação. O relato foi incerto: talvez houvesse som, mas somente com o ouvido junto ao speaker. **Isso continua insuficiente para aprovação prática do áudio.**

A saída nativa comprovada nessa repetição foi:

```text
PHASE3_RENDERER driver=KMSDRM renderer=opengles2 flags=0xe size=640x480
PHASE3_AUDIO driver=alsa loaded_sounds=12 chunk_volume=32
PHASE3_AUDIO_SPEC rate=44100 format=0x8120 channels=2
PHASE3_SOUND index=3 enabled=1 bytes=304128 volume=32 playing=1 error=
PHASE3_MIX samples=4005888 energy=395.129827119 peak=0.236244202
```

O callback pós-mix viu dados F32 não nulos e pico abaixo de1, sem clipping. O PCM hardware estava RUNNING, MMAP_INTERLEAVED/S32_LE, estéreo44100Hz, período2048 e buffer4096; seus ponteiros avançavam. O ES observado fora do teste usava S16_LE/período1024. Essa diferença é fato, **não causa demonstrada** do nível baixo.

O ensaio encerrou em45,405s, RSS máximo87140KiB e CPU user7,212s/system1,908s, com status0 do menu, daemon e supervisor. O nível era142 antes do ensaio, mas a conferência posterior encontrou95 depois do retorno dos serviços. Não foi provado que o mixer permaneceu142 durante toda a execução. A restauração anterior preservava serviços/framebuffer, mas não o volume reposto pelo launcher; isso foi corrigido no supervisor para capturar/aplicar/restaurar o valor. O agente repôs142 em ALSA, sem gravar configuração no cartão. O fluxo positivo passou posteriormente nas três execuções de 24/10, preservando o valor então escolhido de157,157.

Foi preparada uma versão retirando a atenuação extra, para usar o ganho original dos WAVs (128). Na sessão original ela ficou somente compilada, porque o diagnóstico de armazenamento suspendeu os testes. Depois da recuperação, foi executada e validou navegação/confirmação audíveis. A versão atual acrescenta espera limitada pelos canais pendentes e pelo buffer de saída antes de encerrar; essa correção também foi executada e aprovada em24/10. A audibilidade dos WAVs originais da ajuda permanece ressalva, conforme o relatório de retomada.

## Estado final e artefatos testados

Ao suspender os ensaios, os serviços originais estavam ativos e brilho80/volume142 foram conferidos. Os nós físicos e o namespace do host foram preservados; o controle uinput temporário e os processos/timers do ensaio foram removidos. Os temporários em tmpfs foram limpos e a conexão SSH do agente encerrada. **Isso não restaurou nem comprovou a integridade do cartão:** naquele momento a raiz permanecia `ro` por erro Btrfs, sem tentativa de reparo ou reboot pelo agente. O estado posterior está no relatório de recuperação vinculado acima.

| Artefato | SHA256 e estado |
| --- | --- |
| Histórico `phase3-menu`, chunks32 | `7b01a79ac5ef4c48ceaeda481bcf7c76ea4e303be98b66717721337625c6c057`; preservado em `dist/phase3/tested-20261023-gain32/`, com fonte correspondente e reconstrução comparada byte a byte na sessão original |
| `muvarctl` | `4feb4980b97f3f78336c577c7326524262bc9d6524f92500892180a7bc5237ca`; build/get nativos passaram; cache versão2, capacidade2048, 135 entradas; `get device board/name` retornou `rk-r35s-p0` |
| Ganho128 antes da correção de encerramento | `c51d1651582c000e822ca6c8cd2faf7c00204b659f8dfc962c75b54386263731`; executado em24/10; preservado em `dist/phase3/tested-20261024-gain128/` |
| `dist/phase3/phase3-menu` corrente e `last-tested/` | `77ab9f57a05320854729cf9bfdb104b54af06f7280c838b4c5f0ce959ea7a537`; ganho128 e espera de saída testados; último ensaio usou WAVs de controle em Fn/B; recursos padrão preservam os originais |

Os binários testados validam os caminhos de inicialização/render/input e áudio observados; não demonstram audibilidade de todos os WAVs, estabilidade prolongada do kernel ou integridade física dos cartões. A recusa da nova trava de saúde foi testada no aparelho antes de qualquer nova parada de serviços. Cenários locais também cobriram raiz `ro`, erros de memória/MMC/aborto com raiz ainda `rw` e baseline limpa; registros em `health-guard-local-checks.txt`. A execução positiva completa, incluindo mixer e serviços, passou na retomada.

## Evidências locais e limites restantes

`build/phase3/`: preflight/inventário de áudio, logs de container/build, auditorias ELF/símbolos, manifestos de recursos, `target-loader.txt`, `input-inspect-session.txt` (falha de launcher), `input-inspect-retry.txt`, `input-order-inspect.txt` (divergência joydev), `input-order-inspect-retry.txt`, `menu-session.txt` (mapping incorreto), `menu-mapping-retry.txt` (navegação aprovada), `audio-menu-session.txt`, `audio-instrumented-session.txt`, `pcm-during-audio.txt`, `varstore-final-artifact.txt`, inventários de mixer, `namespace-during-audio.txt` e `jail-readonly-mounts.txt`. `final-target-state.txt`, `cleanup.txt` e `ssh-close.txt` documentam o encerramento. O incidente tem evidências próprias listadas no [registro de interrupção](phase3-storage-stop.md).

`dist/phase3/`: executáveis e auditorias, staging, fontes upstream/port, patch, licenças, pacotes/compiler, manifestos e SHA256SUMS. É um conjunto experimental local, não uma imagem de firmware. `build/` e `dist/` continuam ignorados pelo Git.

Permanecem fora desta prova: dispatcher completo e submenus, ajuste real de volume/brilho, PipeWire/WirePlumber, fone/hotplug/Bluetooth, áudio prolongado e pós-resume, conteúdo/emuladores, bateria, energia, suspend/resume e boot independente. A Fase 4 não foi iniciada nesses ensaios; sua investigação posterior está no [relatório da base BSP](phase4-bsp-foundation.md).

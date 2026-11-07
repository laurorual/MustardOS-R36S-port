# Fase 3 — retomada de áudio após recuperação

Ensaios de 24/10/2026, America/Sao_Paulo, no R35S RK3326/Panel 0 com dArkOSen Debian 13. Continuação do [primeiro menu nativo](phase3-native-menu.md), após a [recuperação dos cartões](storage-recovery.md).

**Resultado: recorte funcional do primeiro menu validado com ressalvas do tema.** Navegação e confirmação ficaram claramente audíveis com os WAVs originais, sem a atenuação extra. Fn/B reproduziram som audível quando receberam o WAV de confirmação como controle. O corte na confirmação ao sair foi corrigido e aprovado pelo usuário. Os WAVs originais de abrir/fechar ajuda continuaram inaudíveis no speaker; não foram substituídos permanentemente nem aprovados por esse diagnóstico. Isso não valida o frontend completo ou um firmware autônomo.

## Preparação e limites

O usuário confirmou áudio conhecido do dArkOSen audível em volume confortável. Antes do ensaio, modelo exato, raiz `rw`, kernel sem taint e cinco contadores Btrfs em zero foram conferidos. O estágio anterior não existia; foi criado outro diretório aleatório `/tmp/muos-r35s-phase3.*` em tmpfs. Não houve execução de musplash, Power, submenu, instalação de bibliotecas no aparelho ou nova operação de recuperação.

Checksums do pacote, correspondência entre fontes/scripts e arquivos empacotados e loader AArch64 foram conferidos. `ld-linux-aarch64.so.1 --verify`, resolução de dependências e `--info` com `LD_BIND_NOW=1` passaram no aparelho. O binário continuou ligado às bibliotecas Debian/SDL/Mali existentes; a compatibilidade com outro rootfs não foi presumida.

O preflight anterior à confirmação do usuário registrou Playback `127,127`. Imediatamente antes do ensaio, o supervisor capturou `157,157`; esse valor foi aplicado depois da parada dos serviços, observado durante a execução e restaurado depois do retorno do launcher. Não se atribui a melhora inteira ao ganho digital: o volume e a preservação do mixer também diferem da sessão antiga.

## Três execuções curtas

| Execução | Artefato/recursos | Evidência e relato | Duração / RSS máximo |
| --- | --- | --- | --- |
| Ganho 128 | `c51d1651…`, WAVs originais | Navegação e A claramente audíveis; Fn/B sem som percebido. Índices9/10 acionados, sem erro reportado pelo mixer. | 29,248s / 86.728KiB |
| Controle de conteúdo | Mesmo binário; somente os dois WAVs da ajuda trocados por `confirm.wav` no estágio privado | Fn/B claramente audíveis. Usuário percebeu corte no som de A ao encerrar. | 37,009s / 85.052KiB |
| Encerramento corrigido | `77ab9f57…`, mesmo controle de WAVs | Usuário confirmou resultado integralmente correto; canais concluídos e margem de saída antes do fechamento. | 24,372s / 84.772KiB |

As três execuções terminaram com status0 para menu, muinput e supervisor. Rendering permaneceu KMSDRM/`opengles2`, 640×480, aceleração/vsync; áudio ALSA, F32 estéreo a44100Hz, 12 sons carregados. O PCM observado permaneceu S32_LE/MMAP_INTERLEAVED, período2048/buffer4096. A captura de processos no primeiro diagnóstico auxiliar encontrou um nome `/proc/*/comm` com bytes inválidos para UTF-8; a inspeção posterior usou decodificação com substituição. Esse erro do coletor não foi falha do menu.

Trechos do primeiro ensaio:

```text
playback_volume_before_child=[157, 157]
PHASE3_AUDIO driver=alsa loaded_sounds=12 chunk_volume=128
PHASE3_SOUND index=9 enabled=1 bytes=193536 volume=128 playing=1 error=
PHASE3_SOUND index=10 enabled=1 bytes=193536 volume=128 playing=1 error=
PHASE3_MIX samples=2580480 energy=6258.678828132 peak=0.944976807
playback_volume_restored=[157, 157]
```

O pico observado ficou abaixo de1. Isso descreve a amostra instrumentada, não uma medição da saída acústica ou certificação de áudio prolongado.

## Ajuda: eventos funcionam, conteúdo continua como ressalva

Fatos:

- [`module/muxlaunch.c:handle_help`](../../refs/muos/frontend/module/muxlaunch.c) chama `play_sound(snd_info_open)`; o fechamento usa `snd_info_close` em [`common/ui/dialogue.c:dialogue_play_dismiss`](../../refs/muos/frontend/common/ui/dialogue.c). Os logs registraram ambos com chunks válidos e ganho128.
- Os WAVs originais contêm PCM não nulo e seus canais L/R têm correlação positiva próxima de1; a análise dos arquivos não indica cancelamento por soma mono nesses dois sons.
- Com somente `info_open.wav` e `info_close.wav` trocados pelo mesmo `confirm.wav`, o usuário ouviu ambos nos mesmos eventos. Nem o código de input, nem o renderer, nem o backend ALSA foram alterados para essa comparação.

Uma análise local com FFmpeg comparou RMS antes/depois de um filtro passa-altas de200Hz. Esse filtro é apenas uma comparação do conteúdo dos arquivos, não um modelo medido do speaker:

| WAV | RMS normalizado original | Redução após o filtro |
| --- | --- | --- |
| navigate | 0,006806 | −0,89dB |
| confirm | 0,063330 | −0,002dB |
| info_open | 0,159674 | −12,47dB |
| info_close | 0,197110 | −19,02dB |

**Hipótese:** a concentração em graves dos WAVs de ajuda e a resposta do speaker/rota explicam a diferença de audibilidade. O controle por substituição delimita o problema ao conteúdo/reprodução desses sons, mas não mede resposta acústica, EQ do codec ou saída de fones. Não declarar defeito de Fn/B nem falha geral de ALSA com base nesses WAVs. Escolher/adaptar os sons do tema para o speaker continua pendente.

SHA256 dos arquivos: `info_open.wav` original `dbee71b1dad910c29bef1d3ad91fb0926d7bf4675c7c178ea13b533b74b23322`; `info_close.wav` original `8d219fe69d1421a9e4ee289c0f2a58722dd5698d08b6da620a846bdc3069bba3`; controle `confirm.wav` `1d8e4cc72ebba11a7d3804d8ffc9f0893d90a15e63dcc3377d9314c64b946ba3`. Os originais foram restaurados e conferidos por hash antes de remover o estágio. O pacote padrão continua com os WAVs upstream.

## Correção do corte ao sair

O executor de diagnóstico retornava de `muxlaunch_main()` e liberava os chunks imediatamente após a seleção. `Mix_FreeChunk` interrompe os canais que ainda usam aquele chunk ([SDL_mixer](https://wiki.libsdl.org/SDL2_mixer/Mix_FreeChunk)). O WAV de confirmação dura cerca de79ms, e o encerramento começava antes de sua conclusão. Esse comportamento pertence ao executor de bancada; não foi demonstrado como bug do dispatcher completo upstream.

A mudança está somente em [`port/diagnostics/phase3-menu.c`](../../port/diagnostics/phase3-menu.c): ao selecionar e sair normalmente com áudio, aguardar os canais já enfileirados, até1000ms, sem repetir o efeito. [`Mix_Playing(-1)`](https://wiki.libsdl.org/SDL2_mixer/Mix_Playing) fornece o número de canais ainda ativos. Depois de zerarem, manter150ms de silêncio para escoar o buffer ALSA observado de4096 frames/44100Hz, aproximadamente93ms. Essa margem é específica da bancada medida, não uma solução universal de drain para outro backend/rootfs. Se persistirem canais no limite, o diagnóstico retorna status11. Os limites externos de tempo permanecem.

O rebuild usou o mesmo container/sysroot, sem instalar dependências no host/aparelho. O último teste aprovou o áudio subjetivamente e registrou:

```text
PHASE3_AUDIO_DRAIN elapsed_ms=179 remaining_channels=0 tail_ms=150
PHASE3_MENU_END status=0 selected=1 focus_changes=4 elapsed_ms=24372 maxrss_kib=84772 cpu_user=3.664 cpu_system=0.928
PHASE3_MIX samples=2150400 energy=150.540467107 peak=0.676086426
PHASE3_MENU_EXIT_STATUS=0
PHASE3_MUINPUT_EXIT_STATUS=0
PHASE3_SESSION_EXIT_STATUS=0
playback_volume_restored=[157, 157]
```

## Estado final e evidências

Após os ensaios: raiz `rw`, cinco contadores Btrfs em zero, tainted0 e ausência dos erros MMC/Btrfs/Bad page/Bad rss anteriores. EmulationStation, ogage e Fn watcher ativos; brilho80, Playback `157,157`; event2/event3 físicos preservados, sem muinput/menu ou controle virtual remanescentes e sem timers do ensaio. O novo fluxo de preservação do mixer passou em três restaurações normais; a recuperação por disparo independente do timer ainda não foi exercitada. Essas execuções curtas não comprovam estabilidade prolongada do BSP/cartões.

Artefato final testado: SHA256 `77ab9f57a05320854729cf9bfdb104b54af06f7280c838b4c5f0ce959ea7a537`, preservado com sua fonte em `dist/phase3/last-tested/` e `tested-20261024-drain/`. As versões anteriores estão em `tested-20261023-gain32/` e `tested-20261024-gain128/`. O manifesto de checksums foi atualizado; a fonte/manifesto do pacote padrão correspondem ao novo executor, com os sons originais.

Evidências em `build/phase3/resumed/`: `preflight.txt`, `staging-transfer.txt`, `audio-gain128-session.txt`, `during-gain128.txt`, `after-gain128-health.txt`, `stereo-analysis.json`, `frequency-analysis.json`, `help-sound-substitution.json`, `audio-help-control-session.txt`, `drain-build.txt`, `drain-candidate-transfer.txt`, `audio-drain-session.txt`, `final-health.txt` e os arquivos `*-target.tar.gz` com estado/log do muinput. O estágio foi removido após conferir ausência de mounts/processos remanescentes; `cleanup.txt` confirma raiz/mixer/serviços após a remoção. A conexão SSH do agente foi encerrada, com registro em `ssh-close.txt`.

Não foram validados submenus/dispatcher completo, ajuste real de brilho/volume, PipeWire, fone, áudio após resume, energia, firmware ou outro sysroot. L3 não foi reensaiado; a ressalva histórica permanece como margem de erro até recorrência. Musplash/mmap permanece excluído. A Fase 4 não foi iniciada nesses ensaios; o trabalho posterior está no [relatório da base BSP](phase4-bsp-foundation.md).

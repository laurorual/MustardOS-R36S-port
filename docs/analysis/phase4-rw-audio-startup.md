# C33–C37 — áudio e primeira inicialização do PCM

## Resultado observado

Em 31/10/2026, C33 trocou o acesso do sink RK817 de MMAP para RW, mantendo
IRQ, quantum1024, codec215 e preferências55/70. A audição em RAM57 foi limpa,
mas baixa em55. Esse resultado não qualificou boot: a retomada encontrou59/C07,
com boot58 sem confirmação física. Seus recibos não foram repetidos nem completados
artificialmente; apenas fallback59 foi coletado e aprovado.

No boot60, a configuração estava ativa e sem avisos de buffers, mas o PCM
avançava22050.540153frames/s para44100 declarados. A amostragem exigiu mesmo
owner/trigger, timestamps crescentes e intervalo superior a1segundo. Não foi
solicitada audição nesse estado. Clocks I²S tinham os mesmos11289600Hz nominais
do ensaio saudável; isso não prova uma causa específica no driver.

Após lease180, coleta e restauração, uma segunda sessãoC22 noMESMO60, sem
qualquer override, mediu44099.219737frames/s. Usuário: “Som limpo e audível”.
Stop/coleta/mixer/DRM/cache/prefs/rede passaram. Fallback61 passou97hashes,
rootRO0755, brilho80, taint0, erros selecionados0 e FAT+p3 desmontadas.
Prova imutável: `dist/phase4/pcm-startup-comparison`.

## C35 — reprodução direta com zeros

`alsa-zero-params.c` usa o SDK isolado/Cortex-A35/PIE/RELRO/NOW/libasound,
RW/S32_LE/44100/stereo/period1024/buffer4096 e os parâmetros software observados:
timestampENABLE, avail_min3072, startLONG_MAX, stop4096, silêncio0. Não altera
mixer, não captura microfone e transmite apenas bytes zero. Compilação-Werror,
readelf/loader e --infoQEMU passaram; --info nativo também.

Primeiro stream61 iniciou, mas `snd_pcm_wait` retornouEPIPE antes da amostragem.
Não calcular taxa nem apresentar isso como equivalência saudável com PipeWire.
Wrapper restaurou mixer byte-exato; PCMclosed, helpers removidos, raizRO/rede
íntegras. Stage `build/phase4/audio-clock-audit/zero-trial.d9xf4on4`, incluindo
failure-cleanup. Runner foi ajustado para recolher falha e limpar também nesse
caminho. O utilitário permanece diagnóstico privado, sem novoELF instalado.

## C36/C37 — alteração instalada e áudio após reboot aprovado

A segunda inicialização saudável motivou um workaround específico do Panel0:
antes do PipeWire, S95 completa um ciclo direto com44100frames de zeros usando
`aplay` existente, S32_LE/stereo/44100/MMAP/period1024/buffer4096. O chamadorC22
limita a árvore inteira de start a45segundos. Hook exigePCMclosed antes/depois,
recusa player falho e só marca sucesso ao terminar. Não recupera automaticamente
um PCM estranho nem aplica ganho ou preferências. Legacy quantum0 pula esse hook.

Rehearsal61 passou; seus arquivosRAM foram removidos.5checks do hook,
6quantum e14transação/rollback passaram. Somente S95 e fundação97 foram
instalados em61; raizRO e privados preservados. C33RW/IRQ, perfil21/215,
payload15 e55/70 continuam. Backup privado2: `c24-backup.zqk7wvsb`,
SHA3b122a90f041bd935089ed0b4f03a827e181ff5d2e27a09809e2672e5756e0a1.
Não repetir apply: stage `rootfs-candidate/c36-update.m4ji3sr0`.

C37 usa contrato próprio para os dois deltas S95/fundação versusC33 e confere
marcador de prime, RW, IRQ, ganho, quantum e preferências reais.20checks host
passaram. Stage `rootfs-candidate/c25-physical.tycto8q2`, base61/boot62/fallback63.
Boot62 mediu44101.822160frames/s antes e44098.406600 após navegação,
mesmo owner/trigger. Usuário confirmou “Imagem e navegação normais; som limpo
e audível”. Sem override host ou recalibração. Lease/coleta62 e retorno63/C07 passaram: mixer/DRM/caches/prefs55/70,
rootRO0755, brilho80,97hashes, taint0, rede e erros selecionados0. Provas
`dist/phase4/pcm-prime-installed`, `primed-launcher-boot` e
`primed-launcher-fallback`. Não repetir pedidos/ensaios desses stages.
Causa raiz, coldboot, fones, Power/suspend e longa duração seguem não qualificados.

## Limites preservados

Nenhum flash, reparticionamento, kernel/DTB, mudança de ELF instalado, credencial,
seed ou contador restaurado. Original32 e Steam Deck não foram usados. C12
continua inativo e launcher permanenteoff. A imagem privadaC27/96 é histórica;
não inclui C36 e não foi testada como imagem inteira.

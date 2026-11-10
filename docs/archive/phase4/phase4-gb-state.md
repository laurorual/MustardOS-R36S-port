# C51 — quicksave e quickload nativos em RAM

Concluído em02/11/2026, C07/boot68/IP192.168.15.14:2222. Este incremento
usa o hostC50, Gambatte e conteúdo privadoC49 byte-idênticos. Não recompila
frontend/core, não instala arquivos, não reinicia e não habilita persistência.
O usuário confirmou **“Tudo certo!”** à sequência específica de salvar,
mover, restaurar posição e sair pelo atalho. A coleta e limpeza passaram.

## Escolha e limites

O frontend GPLv3 já possui quicksave Fn+R2, quickload Fn+L2 e saída Fn+Start.
Foram conferidos os defaults em settings/settings.c, o detector de borda em
input/hotkeys.c e os caminhos em core/main.c, core/core.c e core/paths.h no
stage privado gb-exit/host.uuixcmie. Fn deve ser pressionado antes do botão;
Start sem Fn entra no jogo. Nenhum botão é injetado remotamente. Autosave,
timeline e flush periódico continuam desligados pela políticaC50 em RAM.

O nome do core neste diagnóstico é core.so; o caminho esperado é
/run/muos/storage/pickles/state/core.so/GB/private. A árvore de storage tem
symlinks legítimos para a mídia tmpfs privada. O workerC46 mantém MUOSDATA
montado ro,noload para copiar preferências; os writers usam a cópia em RAM.
Root instalado, preferências55/70, áudio215/q1024/IRQ/RW, clocks e refs ficam
preservados. Original32 e SteamDeck não participam.

## Validação sem exportar o estado

O helper próprio MIT phase4-state-metadata.c é somente leitura. Abre o
diretório e os três arquivos por descritores, recusando folha symlink, hardlink,
tipo/modo/proprietário inesperado, tamanho fora dos limites e filesystem que
não seja tmpfs. A exigência vale para cada arquivo, além do diretório. Não
publica bytes, CRC ou valores do manifesto.

Confere envelope PKST v1 de32bytes, padding, flags sem achievements, tamanho
exato e CRC32 do payload do core com zlib. Confere campos não vazios/únicos de
[quicksave] no states.ini e assinatura PNG da miniatura. A assinatura não é
uma validação completa da imagem. Não confunde “Quick Save” com persistência:
o writer é assíncrono; a inspeção ocorre após a saída/flush do host, e o fluxo
exige também “Saved state to”, “Loaded state from” e os dois logs de hotkey.

O seletor C51 conserva A/B e quarentena de opçõesC46. Após o jogo, executa o
helper dentro do namespace privado, retorna ao launcher mesmo se a inspeção
falhar e só então propaga o erro. Coleta permitida inclui somente
state-metadata.txt, logs e CSV; .state, .png e .ini não são exportados. A
cápsula e todos os dados privados desaparecem na limpeza. Estado em RAM não
qualifica saves duráveis, SRAM, recuperação após reboot ou Power.

## Checks e sessão

check-phase4-gb-state.py compila AArch64/A35 com SDKcontainer, sem mudanças no
host, e executa18fixtures sintéticas no QEMU: válido, magic/version/flags/
padding/CRC/tamanho/truncamento incorretos, manifesto incompleto/duplicado,
PNG inválido, modos, links, FIFO e filesystem persistente. Nenhuma ROM é usada.
Stage checks.3dn_w575 passou18/18. O helper limita leituras a8MiB de estado,
16KiB de manifesto e2MiB de PNG, sem alocar a partir de tamanhos não limitados.

check-phase4-gb-state-dispatch.py testa retorno antes de falha do helper,
logs save/load ausentes e erro do app, além do caminho válido:5/5, stage
dispatch-check.lg1_yd5y. Um primeiro fixture detectou uma lista AND de shell
que não propagava erro do app; foi substituída por condição explícita antes
do teste no aparelho. Não houve falha de escrita no cartão.

As provas imutáveis C49/API e C50/deadline/exit são reutilizadas por SHA para
os mesmos ELFs/conteúdo. Não se repete API, cancelamento, rollback, áudio ou
USB já aprovados. Sessão de seleção120s, conteúdo45s, retorno20s, owner210s e
supervisor externo240s permanecem iguais. O tempo de saída voluntária não é
inferido dividindo frames por45. Estabilidade prolongada e novo boot seguem
fora da qualificação.

## Próximo incremento proposto

Desenhar persistência limitada a saves
com recuperação e backup, mantendo a camada de preferências existente. Fazer
auditoria do contrato de storage antes de habilitar escritores duráveis; não
misturar Power, suspend, flash ou nova calibração nesse passo.

## Resultado nativo e limites de áudio

Stage gb-state/observe.dj2lowrs registrou uma gravação completa e dois loads
reais: core_state_restore retornou restored nas duas chamadas. Payload26861
bytes, CRC válido, envelope/manifesto/assinatura PNG válidos emtmpfs; nenhum
estado, miniatura ou manifesto foi copiado ao computador. O usuário aprovou
restauração e saída. Fn+Start encerrou com2453frames/expired0/reasonhotkey;
launcher foi apresentado e encerrado normalmente. Isso não equivale a uma
medição2453/45fps, pois o encerramento foi voluntário.

CSV registrou core_hz recente59,9401, screenshot3amostras (média11,77ms),
state_save1 (0,525ms), state_load2 (média23,51ms, pico25,38ms). O tempo interno
somente de read/deserialise foi0,29/0,24ms. São escopos distintos, não tempos
de resposta física. Houve8callbacks de underrun,5eventos e3471frames ausentes
(0,106s em32768Hz). O CSV é agregado, sem timestamps desses eventos; não
permite atribuir sua causa a save, load, screenshot ou encerramento. O código
nativo state_load chama audio_bridge_clear_queued e o callback conta falta
de ring; isso é uma hipótese de investigação, não prova de causalidade. Não
declarar áudio sem faltas nesta rodada nem alterar C36 por inferência.

Operação0/cleanup0, retorno técnico e físico aprovados. RootRO0755/fundação97/
taint0/PCMclosed, preferências55/70/mixer/DRM/WirePlumber/infraPIDs e mounts
globais idênticos. RAM removida, nenhum processo UI/core/áudio/input residual,
página final C51 enviada. Saves duráveis, novo boot, longa duração e desempenho
NES continuam sem qualificação. Prova pública gameboy-ram-state contém apenas
fontes, análises redigidas e recibos permitidos, sem estado bruto ou ROM.

# C53 — integração seletiva de quicksave no cartão de teste

Concluído em 02/11/2026, C07/boot68/IP192.168.15.14:2222. Usuário autorizou
a integração planejada no cartão128 e confirmou disponibilidade física. O
cartão original32 e o SteamDeck não participam. Nenhum reboot, token ou
instalação permanente faz parte deste incremento.

## Implementação

Host C50, Gambatte C49, ROM privada, UIlibC46 e runner permanecem byte-idênticos.
WorkerC46 e seu journal/restore também são reutilizados sem modificação. O
novo fluxo gb-persist adiciona seed antes do menu e commit ou verificação
depois de saída nativa limpa, antes do retorno normal ao launcher.

Identidade privada: SHA256 do domínio `MUOS-R35S-GB-SNAPSHOT-V1` seguido de NUL
e dos hashes binários exatos de core e ROM, nesta ordem. Valores reais não são
publicados. A árvore de storage continua tmpfs; apenas três folhas são
copiadas ao caminho nativo core.so/GB/private ou ao bundleC52. Autosave,
timeline, flush periódico e autoload continuam desligados; --fresh é mantido.
SRAM, histórico, resume index, core options, CSV e preferências não entram no
caminho de commit. A segunda sessão é somente leitura do store, mesmo que
quickload gere histórico novo em RAM.

Novo helper MIT phase4-save-directory.c abre componentes por descritores,
valida root/proprietário/modos/FS e cria staging próprio exclusivo. Publica
MUOS/port-saves-v1 com marker próprio, gb e folha de identidade0700, marker600,
fsyncs dos arquivos/diretórios e renameat2(RENAME_NOREPLACE), seguido de fsync
do pai. Nunca substitui diretório existente nem limpa staging desconhecido.
Helper produtivo exige ext4 RW; a variante de fixture permite somente tmpfs.
O chamador deve fornecer o guard de cartão/mount C20/C22.

store.sh confere identidade/role root600 e mídia/layout/UUID/ext4/mountnamespace,
sob lifetime lock do worker. Para inicializar ou publicar um snapshot, desmonta
a montagem privada ro,noload e monta p3 RW privadamente, sem bind do volume ao
runtime. Ao terminar ou falhar, tenta desmontar RW e remontar RO/noload,
confere hashes de preferências antes/depois e propaga qualquer erro. Worker
restaura o restante do sistema e desmonta p3. Não há remount RW do root global.

Role save exige store vazio validamente inicializado; saída deve ser hotkey
com frames reais, log de Quick Save e conclusão do writer. InspetorC51 valida
PKST/CRC/manifesto/assinatura PNG antes do CLI C52 publicar geração1. Role load
exige geração1, exporta a RAM, valida novamente, exige Quick Load/restauração
real e compara inventário/hash de todo o store antes/depois, sem commit.
Falha de app/inspetor/transação ainda permite o retorno ao launcher antes de
propagar falha; não declara sucesso a partir apenas de log de hotkey.

## Checks e recusa inicial

checks.o2w1sbb5 passou32 fixtures A35/QEMU: bootstrap válido, modos, symlinks,
travessia, identidade, diretório/staging existentes, recusa produtiva a tmpfs,
pipeline real C52/C51 sob mocks explícitos de mount/card, commit/seed, recusa
de corrupção/deadline, preservação byte-exata e retorno ao launcher em falhas.
Não são operações reais de mount nem testes físicos do jogo. C52/34fixtures e
laboratório ext4 nativo são reutilizados por hashes, sem repetição.

A primeira preparação prepare.9e0hu87x foi recusada pelo helper antes de criar
port-saves-v1; operação64/cleanup0. O MUOS existente era root0755, enquanto o
helper inicial exigia0700. Auditoria RO confirmou o pai e ausência de target
e staging. A guarda passou a aceitar pai root0700/0755, mantendo a árvore
nova0700; não foi aplicado chmod ao pai. Um diagnóstico inicial tentou stat -f,
opção ausente no BusyBox; a correção usou findmnt, e sua cápsula vazia foi
removida após conferir ausência de mounts. Nada foi copiado do estado do jogo.

## Resultado nativo

prepare.d9p3tciz: criação exclusiva da árvore nova e inicialização HEAD0,
remontagem RO e desmontagem completas; operação0/cleanup0. O recibo de
ausência anterior demonstra que nenhum save existente foi sobrescrito. Não
repetir prepare sobre a árvore já publicada: a guarda recusará corretamente.
Não há backup anterior comercial porque esse store foi criado vazio; o
formato C52 preserva gerações e ponteiros anteriores em commits subsequentes,
sem substituir uma geração já publicada. Snapshot1 é mantido no cartão.

save.hi07rjg_: menu nativo confirmado ativo antes da pergunta. Usuário usou
A/Start, foi a uma posição reconhecível, salvou Fn+R2 e saiu Fn+Start, sem
quickload. Respondeu **“Voltei ao menu”**. Log comprovou Quick Save, conclusão
do writer e saída hotkey/expired0/1216frames. Inspetor validou26861bytes do
core/PKST/CRC/manifesto/assinatura PNG. C53 publicou geração1, restaurou p3RO,
retornou ao launcher e limpou a sessão; operação0/cleanup0. CSV registrou
zero callbacks/frames ausentes e core_hz recente59,9401.

Após remoção integral da RAM da primeira sessão, load.i2to6dts montou p3RO,
exportou geração1 com identidade conferida e validou os metadados antes de
abrir o menu. Usuário moveu Mario para outra posição, acionou Fn+L2 e
confirmou **“Tudo certo!”** à restauração exata da posição da primeira sessão
e saída/retorno por Fn+Start. Log comprovou load real, sem Quick Save; saída
hotkey/expired0/1214frames. Inventário/hash de todos os arquivos do store
ficou byte-idêntico antes/depois; HEAD permaneceucurrent1/previous0/next2.
Metadados do estado carregado e os inspecionados ao encerrar coincidiram.
Operação0/cleanup0, retorno e restauração física aprovados. Isso qualifica
persistência entre sessões com desmontagem/remontagem, não após reboot.

CSV do load contou4callbacks de underrun/1971frames ausentes (~0,060s na
taxa32768Hz) e core_hz recente59,8802. São contadores agregados, não timestamps
dos eventos; não atribuir causalidade ao load nem declarar continuidade de
áudio sem faltas. Usuário não relatou problema audível. Nenhuma calibração
de IRQ/codec215/quantum1024/volume55 ou clocks foi alterada. Saídas voluntárias
não permitem calcular fps dividindo1216 ou1214 por45.

Todas as etapas preservaram rootRO0755/fundação97/taint0/PCMclosed, prefs55/70,
mixer/DRM/WirePlumber, infraPIDs e mounts globais. p3 desmontado, nenhum
core/menu/áudio/input residual; cápsulas/ROM/helpers RAM removidos, tela final
C53 enviada. A geração1 comercial permanece somente no cartão128; não foi
transferida ao host. Prova gameboy-selective-persistence contém apenas fontes,
análises/observações/recibos permitidos, com identidade e hashROM redigidos,
sem estado/manifesto/PNG/ELF/PCM/segredos. C51/C52 permanecem congelados.

## Próximo C54 preparado

Validar a mesma geração1 depois de um reboot normal controlado C07, com
supervisão física. Não rearmar C12/C25 ou autostart. Antes do reboot: console
quiescente, p3 desmontado, rootRO, recibos C53 e hash dos assets conferidos.
Depois: novo contador C07/rede/fundação/taint/rootRO; novo adaptador de ensaio
deve aceitar recibo C53 de boot anterior explicitamente, preservando identidade
e checagem de geração. O runner C53 exige mesmo boot e não deve ter sua guarda
removida por conveniência. Abrir somente role load, observar Fn+L2, comparar
store antes/depois e limpar. Nada C54 armado ou rebootado neste incremento.

Continuam pendentes: novo boot, perda elétrica, recuperação de corrupção em
save comercial, GC, estabilidade prolongada, SRAM e integração permanente na
imagem. Não corromper a geração comercial para repetir o teste sintéticoC52.
Power/suspend/flash e desempenhoNES permanecem trabalhos separados.

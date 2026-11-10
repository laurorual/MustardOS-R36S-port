# C20 — volume de dados pelo leitor do Steam Deck

## Estado atual — offline concluído e coleta aprovada

Retomada com Deck192.168.15.17 e mesma chaveSSH(alias16). Inspect confirmou
PART_ENTRY_* semFS; resume revalidou os backups e recebeu novoack. Format do
pacote b3km738d criou ext4/MUOSDATA/UUID prevista e markers; verify passou nos
três volumes. Os640MiB protegidos continuaram idênticos, normalizando só slotp3.

Reparo de root0777→0755 foi executado. A leitura pelo aliasp2 mostrou0755, mas
whole-device ainda devolvia cacheantigo e gerou relatório com0diferenças. Esse
relatório NÃO comprova preservação; foi mantido como evidência negativa.
[systemd também documenta caches separados de whole-device/partições](https://github.com/systemd/systemd/blob/main/src/shared/dissect-image.c).
A [interface Linux BLKFLSBUF](https://github.com/torvalds/linux/blob/master/include/uapi/linux/fs.h)
é usada para sync/invalidate dos aliases identificados, não drop_caches global.

Helper parado; usuário executou localmente o auditor fixo
`audit-phase4-userdata-alias-cache.py`, sem format/reparticionar/editarinode.
Sincronização p1/p2/p3→whole, CID/tamanho/geometria/MBR/UUID/features, root0755 e
comparação de TODO o prefixo passaram. Resultado fresco: EXATAMENTE5bytes em
134385920/134386044/134386045/134386050/134386051 (modo echecksums inode2).
SHAcanônico mudou de142440c6…6f15e39 para
`ec7e9eda435369276f3379a362fadc9c0d872663a639cd6b0b578c381063c32c`, igual à
fixture privada anterior. Nenhum byte de dados/FAT/boot alterado.

Auditor validou markers por mountprivado ro,noload,nosuid,nodev,noexec e depois
fsckoffline dos3volumes. `root-mode-repair-cache-confirmed.json` supera a leitura
antiga; `result-after-mode-repair.json` usa o digest fresco. Coleta aprovada em
`build/phase4/preferences/offline-complete.xsay7jtk`/latest-offline-complete.
Backups privados antigos não foram sobrescritos. Carddesmontado, helpers/socket/
snapshot ausentes e auditor concluído. Usuário devolveu128 aoR35S; coldbootC07 e prova nativa do store foram
aprovados no41→42, conforme a seção seguinte.

Código futuro do helper/IO sincroniza aliases antes de abrirwhole; após write
porp2 fecha/reabre pela guarda e recusa mudança de modo com0bytes no readback.
11IO+21protocolo e5regressões de ordem/identidade/falha de cache passaram.
Não foi reenviado/iniciado como serviço noDeck. Não chamar resume/format/partition
novamente neste cartão já preparado. A integração C11/C12/permanente continua off.

## Validação no R35S — C20 aprovado no41→42

Usuário retornou128 ao slotOS doR35S, IP192.168.15.19:2222/chavefixada(alias17).
Coldboot41/C07 passou com root0755/RO, taint0,55 hashes/Wi-Fi/brilho80 e p3UUID/
geometria corretos. O original32 permaneceu guardado. Nenhum helper foi instalado
no init e nenhum tokenC12 foi armado.

`audit-phase4-preferences-data.py initialize` passou no41, stage
`build/phase4/preferences/data-native.7cc5i4ee`. Em namespace de montagem privado,
guarda de mountausente recusou o store, mountp3RO validou markers, mountRW criou
defaults100/80 SOMENTE sem registro anterior e salvou60/75. Unmount/mount/init/
load preservaram o par. MountRO recusou save64, sem alterar o registro. Cleanup
removeu todos os payloads/dadosRAM; p3 ficou desmontada, mountinfo global igual,
root continuouRO e brilho físico80. Nenhum setter de áudio/brilho foi chamado.

Preflight garantiu C07/quiescência/55 hashes/root0755RO/seedstopped/FAT e p3
não montadas antes de `/sbin/reboot`. Pedido retornou0; boot42 voltou no mesmo
IP/chave, C07/rootRO/rede prontos. Esse reboot tinha o propósito novo de provar
o store persistente; não foi repetição da investigação USB já encerrada.

`verify-after-reboot` passou no42, stage `data-native.jc8ptzxk`. Esse modo exige
registro existente ANTES de init, portanto não mascara perda com defaults.
Init/load retornaram exatamente MUOS-PREFS-1/VOLUME=60/BRIGHTNESS=75+LF após
reboot e remontagens; ausente/RO continuaram recusados. Binário/scripts/RAM
removidos, p3/FAT desmontadas, rootRO0755, quiescência/rede/55 hashes/taint0 e
brilho80 aprovados. Saúde finalC07STATUS0 e erros selecionadoskernel-storage0.
Primeiro filtro Oops: casou a linha normal ramoops:attached; evidência inicial
retida e filtro corrigido com limite de palavra. Não houve fault de kernel.

C20 agora comprova ABI nativa, identidade/ownership, IOext4 e retenção do par
no cartão por unmount/remount/reboot controlado41→42. Não prova queda elétrica
no meio de write, estabilidade prolongada, aplicação das preferências pela UI
ou novo ciclo completo de áudio. `persistent_mode_enabled` segue false para
runtime/firmware; apenas o diagnóstico opt-in usa o volume real.

Próximo: C11 consome o par após validar perfilC10/21, aplica overridesRAM,
policy0/slotspeaker coerentes e checkpoint de valores limpos antes do shutdown.
S80ALSA/S90 e demais writers precisam de bindRAM/ownership antes de remover
rootRW privado; não persistir cache/ready/PIDs/seed/flags de rota. Qualificar
start/stop e hardware soblease, mantendo C12/permanente desabilitados até prova.

## Contrato e escopo

Continuação de [C19 ext4](phase4-preferences-ext4.md), em29/10/2026. O usuário
manteve autorização para o cartão de teste128 e ofereceu o leitor do Steam Deck
por SSH. O original dArkOSen32 deve permanecer guardado. Não há autorização para
usar o NVMe do Deck como destino de firmware ou modificar seu sistema operacional.

Plano puro em `build/phase4/preferences/layout.ro4dgdtg`/latest-layout, produzido
por phase4_userdata_layout.py e validado em oito grupos. Diskid4d554432, p1
bootable80/tipo0c/start32768/len204800 e p2tipo83/start262144/len1048576 preservados.
Nova p3tipo83/start1310720/len248561664/PARTUUID4d554432-03. Somente os bytes
478..493 diferem no MBR proposto; os demais bytes são copiados exatamente.
O planner não abre block devices e seu execution_enabled=false continua correto.
O helper offline separado é uma opção explícita de bancada, não parte do init.

Volume planejado: ext4/MUOSDATA/UUID6d756f73-c020-4000-8000-000000000001,
bloco4096/inode256/ratio65536/reserva0, journal e features explícitas antigas,
sem64bit/metadata_csum/orphan_file/fast_commit. Inicialização de inode/journal
eager evita deixar trabalho de formatação para o boot do kernel4.4. O espaço
remanescente completo permite conteúdo futuro; não houve redução de p1/p2.

## Operação privilegiada temporária

DeckJupiter/x86_64/kernel7.2.7-valve2-2-neptune-72-g31504582a073, IP anterior192.168.15.16,
usuáriodeck/22/chave dedicada fixada. Python3.14.6 e ferramentas nativas já
existentes, mke2fs1.47.4. Nenhuma dependência instalada; NVMe512GB identificado
como armazenamento do Deck e usado somente para o backup privado em /home.

sudo do Konsole não é válido na sessão SSH. A solução não altera sudoers:
usuário inicia localmente `sudo /usr/bin/python3 /home/deck/muos-r35s-c20/phase4-userdata-offline-server.py serve`.
O helper confere o pacote, copia snapshot root0700 para /run e cria namespace
de montagem privado. Socket local rootcriado,0600/uiddeck, SO_PEERCRED. Só aceita
inspect/backup/resume/ack-backup/partition/format/repair-root-mode/verify/restore/stop e campos tipados;
não aceita shell, paths/dispositivos/comandos arbitrários nem rede adicional.
Stop remove socket/snapshot. Backup privado é retido; Konsole deve permanecer
aberto enquanto uma transação está em andamento.

Antes de block IO: Deck/DMI/arquitetura, único MMC identificado128, CID exato,
capacidade249872384setores/logical512, ausência de mounts em TODOS os namespaces,
swap/holders, nóblock real sem symlink e open exclusivo. MBR inteiro e hash dos
primeiros16MiB precisam coincidir com o survey real do R35S antes do backup.
NVMe, outro MMC, tamanho/tabela/prefixo diferentes são recusados.

Backup copia os primeiros640MiB atuais para
`/home/deck/muos-r35s-c20-private/prefix.backup`, verifica readback/hash e executa
fsck.fat-n/e2fsck-fn offline. O controller recolhe uma segunda cópia em
`build/phase4/private/c20-backup.*`, tamanho/hash/fsync conferidos. Só depois
envia ack do digest, requisito para partition/format/restore. Essas cópias
CONTÊM root/seed/credenciais: nunca incluir em dist nem em saída de ferramentas.

O commit fica limitado a512bytes do MBR, com diferença somente no slotp3,
write completo/fsync/readback. Hash canônico de TODO o prefixo640MiB normaliza
apenas esse slot e precisa continuar igual ao backup antes/depois. BLKRRPART só
é permitido no cartão offline sem consumidores. Formatação usa apenas p3 após
revalidar geometria e recusar assinatura preexistente; não usa -F no dispositivo.
UUID/label/features, fsck-fn e marker são conferidos. O mount para os marcadores
é privado/rw/nosuid/nodev/noexec, com identidade do major:minor e sem vazamento
ao namespace global do Deck. Não se executa nenhum binário da mídia montada.

Markers previstos: `.muos-r35s-data-v1` root0600, conteúdoMUOS-R35S-DATA-V1+LF;
`MUOS/preferences` root0700 e `.muos-preferences-v1` root0600 com conteúdo C19.
Nenhum registro preferences é criado pelo formatador; init/defaults uma vez
ficam a cargo do store tipado no R35S. Sem seed, credenciais, cache, ready ou PID
nesse volume. Integração C11/C12/firmware continua desabilitada.

Erro após escrita retorna incerteza e mantém backup; não faz rollback automático.
Restore explícito só aceita alterações no slotp3 e exige digest do prefixo
protegido e backup independente. Não é prova de tolerância a queda elétrica.

## Verificações e adaptações reais

Oito fixtures de IO em arquivos regulares exercitaram commit, preservação de
todo o prefixo, refusas, short writes, fsync falho, slot parcialmente escrito e
recuperação explícita.14 casos de protocolo/sysfs validaram cartão original/
desconhecido, tamanho/setor/host/arquitetura, holders, mounts e ausência de backup.
Formatador/UUID/label/features/markers0700/600 passaram em imagem regular16MiB
com fsck-fn e debugfs. Containers existentes/sem rede/dispositivos; não houve
repetição dos16 testes C19 já aprovados.

Primeiro pacote `offline-package.ehgfexs6` não passou a escritas: o inventário
mostrou CID diferente no leitor SDHCI do Deck. HashR35S12d2c78f…aa193 e
hashDeckddf40781…ee04 diferem SOMENTE no último byte da representação (`7d` versus
`00`); substituir esse byte no CID lido no Deck reproduziu exatamente o hash
antigo. Hash dos primeiros15bytes normalizados:
f13f5d5b91abd907caa67b654ae71bd4e0693e5eb019ba1faa4bacb3ad81a427.
Foi pinado um SEGUNDO hash completo exato para esse leitor, sem aceitar CID
truncado ou qualquer cartão do mesmo tamanho. As guardas do R35S não mudaram.
O tratamento distinto é consistente com o caminho SDHCI que desloca a resposta
R2 sem o CRC, versus DW-MMC lendo RESP0..3; conferir também o
[driver Linux de referência](https://github.com/torvalds/linux/blob/v4.4/drivers/mmc/host/sdhci.c)
e `build/phase4/linux-base/drivers/mmc/host/{sdhci.c,dw_mmc.c}`. Isso é uma
explicação apoiada no código/observação, não prova de identidade por tamanho.

O Deck montou ROOTFS automaticamente em /run/media/deck/ROOTFS; foi desmontado
via udisksctl antes de backup/alterações. Pode ter havido escrita de metadados
pelo automount; não afirmar igualdade bruta com p2 antes dessa passagem. O
backup e o hash canônico da transação são do estado offline após desmontar.
Hashes de código/perfil serão reconferidos no retorno ao R35S.

Segundo pacote `offline-package.5o0ieyn9` foi interrompido no preflight por
EINVAL lendo /proc/1917/mountinfo: bwrap zumbi, sem namespace. Nenhum block fd
ou diretório de backup havia sido criado. Tratamento restrito de ENOENT/ESRCH/
EINVAL foi acrescentado; EACCES/EIO continuam abortando. Fixtures negativas
correspondentes passaram. Helpers anteriores foram parados, snapshots/socket
removidos e pacotes user-only preservados como before-cid/before-proc.

Pacote atual `build/phase4/preferences/offline-package.tl602v5x`/latest-offline-package:
8 IO +14 guardas +formatação regular passaram, upload e hashes conferidos.
Usuário reiniciou o helper atualizado. Console desligado normalmente pelo
C07 após preflight40/rootRO/quiescência/55 hashes/RNGstopped/FAT desmontada.
Usuário confirmou transferência do128 ao Deck. C12 não foi armado nem chamado.

## Marco anterior — p3 criada, bloqueio conservador antes de formatar

A transação real do pacote tl602v5x fez backup640MiB, fsck.fat-n/e2fsck-fn0,
segunda cópia privada neste host eack do SHA256
`142440c613e1ec7f77cfe6eafa1c06ea03a5932deab42a7b052b4507a6f15e39`.
O commit da p3 PASSOU: readback do MBR, geometria e hash de TODO o prefixo640MiB
normalizando apenas o slotp3 coincidiram com o backup. Logo, esse commit não
alterou p1/p2, bootloader ou outros bytes protegidos. BLKRRPART/udevsettle e
quiescência passaram. Não executar partition novamente: o slot já existe.

A chamada format foi recusada ANTES do mke2fs porque o helper interpretava
qualquer rc0 de blkid como assinatura existente. lsblk/UDisks mostraram p3
sem FSTYPE/UUID/IdUsage, somente a entrada DOS. Fonte primária local
`build/phase4/graphics-config/output/build/host-util-linux-*/libblkid/src/partitions/partitions.c:776–815`
e `misc-utils/blkid.c:504–580` mostra que PART_ENTRY_* também geram valores/rc0.
Esse caso explica uma recusa sem filesystem. A exportação detalhada do probe
será conferida pelo novo inspect, antes de tentar formatar novamente.

O usuário precisou se ausentar e deixou o cartão no Deck. O helper antigo foi
parado pelo socket; snapshotroot e socket removidos. Todas as partições do
cartão estão desmontadas. R35S continua desligado após40; original32 guardado.
SSH do Deck permanece ativo conforme solicitado. Nenhuma operação crítica ou
processo privilegiado C20 foi deixado executando. Nenhuma nova escrita no
cartão foi realizada durante a preparação abaixo.

## Marco anterior — correções preparadas durante a ausência

Pacote final `build/phase4/preferences/offline-package.b3km738d`/latest-offline-package.
Payload idêntico ao já transferido0vxmq3xc, com qualificação final atualizada e
hash de CADA arquivo revalidado no Deck (deployment-revalidation.json). Ainda
NÃO iniciado como root. O tar difere por metadados de empacotamento; não foi
necessária outra transferência dos mesmos arquivos.

- Probe distingue filesystem/nestedPTTYPE/USAGE de uma exportação estrita de
  PART_ENTRY_*; cada tag precisa coincidir com p3/PARTUUID/parentmajor:minor.
  Campos extras, TYPE/UUID de filesystem, duplicatas ou ambivalência continuam
  recusados. Não adiciona -F nem wipefs para contornar uma assinatura real.
- inspect novo expõe export/rc/classificação e fase do MBR, após as guardas.
- resume reabre por leitura, verifica backup400/owner/nlink/tamanho/hash/MBR,
  prefixo completo atual e p3 ainda sem filesystem; exige NOVO ack do hash da
  cópia independente. Não cria outro backup nem sobrescreve o antigo.
- A ROOTFS real no backup ficou root0777 pelo chmod do automounter do Deck.
  Original aprovado é root0755. repair-root-mode é uma transação separada,
  somente após format válido: fsck-fn, inode2/owner/mode0777/mapa/geometria
  conferidos, comando debugfs fixo para mode040755, fsync/readback/fsck-fn.
  Compara byte a byte TODO o prefixo contra o backup: só permite modo/checksums
  do inode2 e tempo/checksum do superbloco primário, além da normalização p3.
  Conteúdo dos arquivos, FAT e boot não são isentados dessa comparação.
- verify posterior usa o novo digest explicitamente registrado da correção de
  permissão e grava resultado separado; o backup original permanece intacto.
- Foram preparados data-functions.sh/diagnostic.sh e
  audit-phase4-preferences-data.py para o R35S depois de storage pronto. Exigem
  root0755/RO, CID/Panel0/kernel, geometria/UUID/label p3, markers0600/root e
  diretório0700, namespace privado e source/major:minor/options exatos. Store
  inicial deve estar ausente; init100/80→save60/75→unmount/remount. Modo separado
  verify-after-reboot nunca recria defaults. Sem aplicação ao áudio/backlight,
  C11/C12, serviço ou init. Esses testes reais ainda NÃO foram executados.

Qualificação final:11 casos IO (incluindo limite byte a byte),21 protocolo/
identidade/probe/resume e formatter16MiB/markers/fsck passaram. Shell AArch64/
QEMU e recusa do entrypoint fora do diretório próprio passaram. O teste de
permissão usou uma CÓPIA REGULAR PRIVADA da ROOTFS real:0777→0755, fsck antes/
depois0, exatamente cinco bytes alterados (modo echecksums do inode2), nenhum
byte de dados/FAT/boot. Alterar um byte de FAT na fixture foi recusado.
Extrações/fixtures privadas foram removidas. Root-mode stage bhy0s79j;
IO5spzuo2e/protocolmv68ljer. Não é uma execução da correção no cartão.

## Procedimento offline anterior — já executado; não repetir

Estado histórico deste procedimento: p3 ainda sem filesystem e raiz0777.
SUPERADO pelo estado atual no início deste documento.
Primeiro ativar localmente o helper já preparado, no Konsole do Deck, com o
mesmo comando serve. Não há necessidade de reinstalar pacotes ou reenviar chave.
Na retomada o IP mudou para192.168.15.17; chave fixada e hashes do payload
conferidos no novo endereço. O alias16 do cliente SSH continua fixando a mesma
identidade. O controller usa `--host 192.168.15.17` e latest-offline-package:

```sh
python3 port/scripts/run-phase4-userdata-offline.py inspect --host 192.168.15.17
python3 port/scripts/run-phase4-userdata-offline.py resume --host 192.168.15.17
python3 port/scripts/run-phase4-userdata-offline.py format --host 192.168.15.17
python3 port/scripts/run-phase4-userdata-offline.py verify --host 192.168.15.17
python3 port/scripts/run-phase4-userdata-offline.py repair-root-mode --host 192.168.15.17
python3 port/scripts/run-phase4-userdata-offline.py verify --host 192.168.15.17
python3 port/scripts/run-phase4-userdata-offline.py stop --host 192.168.15.17
```

Avaliar cada resultado antes do próximo comando; não executar a lista cegamente.
Resume só qualificado para o estado atual (p3 aplicada, semfilesystem, root ainda
igual ao backup pós-automount). Não usar como adoção de volume preexistente nem
reformatar se houver dados/markers fora do esperado. Após format/permissionfix,
se houver interrupção, inspecionar relatórios/estado antes de qualquer retomada.

Fonte do automount do Deck foi lida: block-device-event.sh ignora add por
reparticionamento quando TimeMediaDetected é antigo (>5s). Não foi necessário
alterar udev, serviços globais ou configuração do desktop. Novo mount/repair
inesperado deve abortar pela guarda, sem rebasear o backup silenciosamente.

Somente após verify/root0755/helperstop/carddesmontado, devolver128 ao R35S e
validar C07/rootRO/Wi-Fi/55 hashes/geometria p3. Executar o diagnóstico native
initialize, depois reboot controlado justificado pela persistência e
verify-after-reboot. Ainda não comprova retenção das preferências pela UI: esse
é o incremento seguinte, com RAM overrides/policy0/slot e writers ALSA auditados.
Manter menu permanente/C12/persistência de runtime desabilitados. Original32
continua preservado. Não fazer fsck na raiz viva nem exportar backups privados.


## Limpeza do Steam Deck após C20/C21 — concluída

A pedido do usuário, o Deck deixou de ser necessário. Antes da limpeza foram
conferidos o backup privado local de640MiB (SHA142440c613e1ec7f77cfe6eafa1c06ea03a5932deab42a7b052b4507a6f15e39),
a cópia remota com o mesmo hash e os manifestos dos proofs públicos C20.
Foram removidos exatamente /home/deck/muos-r35s-c20, os três diretórios
.before-cid/.before-proc/.before-probe e muos-r35s-c20-private:671261976bytes.
Também foi removida somente a entrada da chave SSH muos-r35s-offline-c20;
outras entradas foram preservadas. O serviço SSH não foi alterado. Helper,
socket e snapshot root já estavam ausentes. Recibo público com hashes em
dist/phase4/deck-cleanup; stage local deck-cleanup.sgx4ns1o.

As referências históricas a dois backups não representam o estado atual:
agora o backup privado íntegro permanece apenas no host de desenvolvimento.
O caminho está em independent-backup.json do pacote offline-package.b3km738d.
Nenhuma credencial nem conteúdo do backup foi exportado. O cartão128 continua
no R35S; não solicitar troca de cartão nem repetir o procedimento offline.

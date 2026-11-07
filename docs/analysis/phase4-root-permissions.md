# C83 — reparo limitado das permissões das raízes

Concluído em **04/11/2026**. Inspeção, aplicação real e cópia independente
dos metadados aprovadas. Raízes p2/p3 agora root:root0755.
Test128 no Steam Deck Jupiter, IP192.168.15.13. Original32 fora do fluxo.

O [backup C82](phase4-backup-native.md) preservou fielmente as raízes p2/p3
root:root0777, alteradas pelo automount do SteamOS. Este incremento corrige
somente esses dois modos para0755. Não instala C79, restaura partições, formata,
carrega seed, gera chave, altera contador nem solicita boot.

## Contrato e inspeção

`phase4_root_metadata.py` implementa o cálculo puro de CRC32C e do inode2 ext4.
Foram consultados somente para leitura os campos e regras de checksum em
`build/phase4/linux-base/fs/ext4/ext4.h` e `inode.c`. A implementação própria
tem licença MIT; código GPL não foi copiado. Apenas os dois formatos ext4
observados são aceitos: blocos4096, inodes256, descritores32, sem64bit nem
checksum_seed. Superblock e checksum do inode são validados quando presentes.

O helper nativo exige sudo local no Deck, snapshot root com fontes pinadas,
namespace privado e identidade exata CID/capacidade/geometria. Reutiliza as
guardas somente leitura C82 para mounts em todos os namespaces, swap, holders,
aliases e cache. Verifica novamente o backup no Deck, o vínculo da cópia host,
o prefixo640MiB completo e nove arquivos de prefs/saves da p3 por montagem
`ro,noload,nosuid,nodev,noexec`. Fsck `-fn` das duas ext4 deve retornar0.

Inspeção real guardou seis folhas pequenas: superblock1024, primeiro bloco de
descritores4096 e setor do inode512, para cada partição. Cópias independentes
no Deck e host foram conferidas por hash, conteúdo e reconstrução do plano.
Não são incluídas na prova pública: contêm identificadores/metadados privados.

| Partição | Offset absoluto do setor | Bytes que mudam dentro do setor |
| --- | ---: | --- |
| p2 | 134385664 | 256 (modo), 380/381/386/387 (checksum) |
| p3 | 675295232 | 256 (modo) |

São seis bytes diferentes em dois setores lógicos de512bytes. UID/GID,
timestamps, contador e todos os demais bytes desses setores são preservados.
O hash esperado do prefixo pós-reparo é calculado no host substituindo somente
o setor da p2 em memória, sem modificar a cópia C82.

## Aplicação e proteção contra automount

O pacote `apply` fica vinculado à inspeção, à cópia independente e às fontes
aprovadas. O helper reconfere os bytes imediatamente antes da escrita e abre
somente o dispositivo inteiro identificado, com exclusividade. Faz exatamente
um `pwrite` de512bytes por setor, seguido de fsync/readback; escrita curta,
erro de sincronização ou divergência aborta, sem repetição/rollback automático.
Isso não garante atomicidade física da memória flash contra perda de energia.

Antes de escrever, instala uma regra temporária somente em
`/run/udev/rules.d/99-holo-automount.rules`. O prefixo casa o CID exato deste
cartão e seus aliases, marca `UDISKS_IGNORE` e salta para o fim da regra;
o conteúdo original de `/usr/lib` é preservado como sufixo. `udevadm verify`
e reload são obrigatórios, sem trigger nem desativação global de serviços.
Outros cartões seguem as regras originais. A regra permanece até a transferência
do cartão; não alterar o arquivo original do SteamOS.

Depois de iniciar a escrita, o bloco inteiro e seus três aliases são colocados
em somente leitura no kernel, inclusive na saída por erro. O helper nunca
limpa um flag RO preexistente. Essa proteção pertence ao dispositivo presente
no Deck e não acompanha a mídia após sua remoção física.

A pós-verificação exige prefixo640MiB integral igual ao hash previsto, ambos
setores iguais ao plano, superblocks/descritores intactos, fsck0 e mesmos nove
arquivos da p3 com raiz0755. Não calcula um hash integral dos118GiB da p3;
a afirmação de preservação nessa partição limita-se ao setor escrito,
metadados examinados, fsck e inventário de prefs/saves. Backups C82 continuam
imutáveis e representam o estado anterior0777, não firmware canônico0755.

## Validação e estado da execução

**44 verificações passaram**, incluindo vetor CRC conhecido, formatos ext4
reais sintéticos com/sem metadata_csum, limites/owners/checksums inválidos,
fonte alterada, escrita curta sem retry, fsync/readback falhos, replay recusado,
diferença integral das imagens sintéticas e fsck0. Verificação de bootstrap,
recusa de arquivo regular pelo opener de produção, regra de CID exato e
BLKROSET somente para1 também passaram. Containers existentes sem rede ou
dispositivos; nenhum rebuild de SDK nem dependência nova no host.

Checks: `build/phase4/root-permissions/checks.49cw8hbo`.
Inspeção host: `inspect.volechl_`; Deck:
`/var/tmp/muos-r35s-c83-inspect.hufva29t`.
Pacote aplicação: `package-apply.vk9nnawf`, destino
`/home/deck/muos-r35s-c83-apply-5366568c6e5c`.

O usuário executou o pacote e recebeu `C83 APPLY COMPLETE`. Coleta host
`apply.hw9i5_we` conferiu relatório, cápsulas e plano; resultado no Deck
`/var/tmp/muos-r35s-c83-apply.llripjtk`. As duas escritas512, modo0755,
fsck0, prefixo previsto e preservação dos nove arquivos passaram. Nenhum
snapshot root permaneceu. SSH não dispõe de sudo sem senha; os dois
comandos privilegiados foram executados pelo usuário no Konsole, com senha
somente no Deck.

Prova pública `dist/phase4/root-permissions` contém fontes,44casos, fixtures
sintéticas e resumo redigido. O empacotador também reconfere identidade,
ausência de mounts/snapshot, RO dos quatro aliases e regra temporária válida
com sufixo original intacto. Provas C79–C82 são revalidadas sem modificação.
Cópias privadas C82 e cápsulas C83 permanecem no Deck e no host. Manter o
cartão no Deck para preparar a recuperação pósboot; não limpar flags RO nem
remover a regra antes de concluir o trabalho offline.

Após este reparo, o próximo incremento continua sendo recuperação pósboot com
seed fresco/sem crédito e contador monotônico, antes da migração C79. Restore
byte-exato da p2 depois de uma tentativa de boot continua inelegível por replay
de seed/recuo de contador. Nenhum novo teste físico do launcher é necessário
para verificar esta correção de metadados.

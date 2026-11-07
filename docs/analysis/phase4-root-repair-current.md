# C96 — reparar permissões a partir do preimage atual

05/11/2026. O C95 confirmou nova intervenção do automount do SteamOS: ambas
as raízes0777 no boot76. A guarda temporária foi restaurada, quatro aliases
estão RO, userdata permanece igualC82 e há cópia independente do prefix atual
e cápsulas em `card-rearm/copy.xiayo6hd`. [Captura/proteção](phase4-card-rearm.md).

O novo `phase4-root-repair-current.py repair` trata somente inode2 de p2 e p3,
0777→0755. Usa os utilitários de metadados C83 congelados e os controles,
descritores verificados, exclusividade, verificação de FDs externos, cache e
retorno a RO do C87. Não chama `Controller.apply`, seu writer p2 ou o modo de
recuperação C89, e não altera essas fontes/provas. Código novo próprio MIT.

O pacote finito18folhas vincula contexto/recibo/ACK C95, mapa de fontes,
prefix atual e plano independente. O recibo C95 precisa afirmar que não houve
unlock, reparo, escrita de payload ou seed. Um claim exclusivo impede repetir
deployment automaticamente. Cópia root protegida e namespace privado seguem
o mesmo contrato já usado em C94/C95.

Antes da escrita, o helper verifica novamente backup remoto, fsck sem escrita,
contador76, userdata RO/noload igualC82, guarda, geometria test128 e todos os
aliases RO. Abre controles verificados e claim exclusivo da mídia. Recalcula
prefix640MiB e deriva os dois setores atuais por superblocks, GDT e inode2;
exige igualdade integral ao plano independente. Payload de setor vem dessas
cápsulas recém-lidas, não de um caminho ou offset arbitrário do usuário.

Um journal persistente e sincronizado antecede SETRO0. Somente whole/p2/p3
são liberados, p1 permanece RO. Reabre claim RW, revalida prefix e cápsulas,
grava intenção de escrita e chama `apply_sector` uma vez por setor. Qualquer
escrita curta, erro ou fsync interrompe; não há repetição ou rollback. Cada
setor é sincronizado e relido. Depois os controles voltam a RO, claim é
reaberto por leitura fria e são conferidos prefix640 completo, setores,
superblocks e GDT. Fsck0 p2/p3 e userdata igualC82 completam a operação.

O plano real altera6bytes dentro de1024bytes escritos: p2offset134385664 e
p3offset675295232. A prova declara preservação do prefix e userdata; não alega
um hash de todos os setores livres da p3. O C94 posterior continua comparando
integralmente o complemento da p2 durante sua própria migração.

O `finally` restaura RO por FDs verificados, inclusive se o desbloqueio foi
parcial; fecha claim/controles. Falhas conservam estágio, snapshot e journal,
publicando relatório privado. Se a falha vier após os dois setores, continua
sem recibo de conclusão: não repetir o comando automaticamente. A guarda
temporária permanece ativa. Nenhum seed é restaurado, gerado ou creditado;
contador não é alterado; não há reboot nem autorização de entrega ao console.

## Verificações offline

29casos em container isolado sem rede/dispositivos. Dois ext4 reais32MiB,
um com metadata_csum e outro uninit_bg, ficam em arquivo regular esparso.
Os controles/identidade/backup/userdata/namespace físicos são substituídos;
os cálculos de cápsula, escritas512bytes, fsync, releituras e hashes do prefix
são reais. Os arquivos extraídos depois do reparo passaram e2fsck e root0755,
com SB/GDT preservados. Imagens sintéticas são descartadas após os logs.

Casos cobrem contador, cápsulas, prefix, falha de journal antes de unlock,
unlock parcial, escrita curta sem repetição, falha no segundo setor, fsync,
userdata pós-escrita, fechamento de FDs/RO e ausência de conclusão. Conferem
também recibos e lineage independente C95, inventário de fontes e recusa de
captura suja, opções extras, ausência de ACK e hash de prefix divergente.
Os mains positivos de preparador/coletor e o namespace privilegiado só serão
qualificados pela execução real; o teste não afirma acesso a hardware.

## Execução física

Somente test128 no Deck, sem mounts e com a guarda C95 ativa. O preparador
revalida todas as folhas da cópia atual, fontes testadas e provas ancestrais;
kernel/RO/guard e hashes do pacote são conferidos antes de imprimir o sudo
local. Senha fica somente no Deck; não há sudo sem senha pelo SSH.

Depois de REPAIR COMPLETE, coletar journal/cápsulas/recibo e verificar
independentemente os setores, preimage, fontes e proteções. Preservar pointers
C83 originais: o prefix dele ainda descreve o estado72. O C96 deve ter sua
própria prova e pointers. Em seguida, a captura C86 postboot com fence C89
EXISTENTE pode ser refeita no estado root0755/boot76, preparando C93/C94.


## Resultado físico

O usuário executou o pacote `root-repair-current/package.t03kf_sn` pelo Konsole
e informou REPAIR COMPLETE. A coleta independente passou em
`root-repair-current/copy.9uyv21bh`, latest-complete:18folhas do pacote,
recibo, journal de unlock/write, seis cápsulas iguais ao preimage C95,
1024bytes em dois setores, prefix após igual ao esperado, fsck0 p2/p3,
root0755, userdata igualC82 e SB/GDT preservados. Quatro aliases RO1,
guarda intacta, mesmo kernel, nenhum mount/helper ativo. Boot76 preservado,
sem seed novo/boot ou migração C79. Prova sanitizada separada de C83/C95.

# C95 — restaurar proteção após novo automount do SteamOS

05/11/2026. O R35S respondeu em192.168.15.16 no boot76. Guardas C76 passaram,
raiz0755/RO, p3 desmontada e PCM fechado; desligamento normal solicitado com
SSHexit0. Usuário confirmou o test128 no Deck192.168.15.13 e iniciou sshd.

A inspeção recusou p2 e p3 montadas automaticamente em RW. A regra em `/run`
não existia e os aliases estavam RO0; o kernel continuava o qualificado.
Após solicitação, o usuário desmontou ROOTFS e MUOSDATA. Original32 não foi
acessado. Este é um motivo concreto para repetir a correção de permissões:
o guard temporário não sobrevive ao reboot do Deck. O pacote C83 antigo não
serve para reaplicar reparo no prefix atual, que mudou desde o boot72.

O novo helper `phase4-card-rearm.py protect` oferece somente proteção/captura.
Reutiliza funções C83/C82 congeladas para verificar backup, identidade, mounts,
geometry, instalar exatamente o mesmo override temporário de udev e forçar
RO1 nos quatro aliases. Preserva `/usr`; não dispara udev trigger ou muda
serviços globais. Se já houver override diferente, recusa sem sobrescrevê-lo.

Com cartão RO, executa fsck sem escrita, confere contador observado76 e
userdata montada apenas RO/noload contra C82. Copia prefix640MiB para SSD do
Deck e coleta superblocks, descritores e dois setores de inode2. Reconfere
prefix/cápsulas por leitura e publica folhas0400/deck em diretório0700.
Não tem reparador, modo RW, SETRO0, restore, RNG, crédito de seed ou reboot.
Em falha preserva snapshot/estágio e tenta reforçar RO; não repete operações.

Passaram27casos offline em container isolado: contexto/roles, contador,
override desconhecido ou já correto, ordem guarda/RO/captura, falhas de
fsck/counter/hash/cápsula sem conclusão e recibos com side effects recusados.
IO físico e utilitários C83 foram substituídos nesses testes; namespace e
bootstrap privilegiados ficaram para a execução real. C83 não foi alterado.

**Execução real aprovada:** pacote `card-rearm/package.y4zvuazg`, helper
executado com sudo local pelo usuário, PROTECT COMPLETE. Cópia independente
em `card-rearm/copy.xiayo6hd`, latest-complete: prefix640MiB com hash igual,
seis cápsulas reconstruídas no host, boot76, fsck0 p2/p3, userdata igualC82,
guarda restaurada, quatro aliases RO1 e nenhum mount/helper ativo.

Ambas as raízes estavam0777. O plano atual identifica6bytes dentro de dois
setores512bytes: offset134385664 na p2 (5bytes modo/checksum) e675295232 na
p3 (1byte modo). `repair-inputs.json` vincula prefix atual antes/depois,
cápsulas, contexto, recibo nativo e cópia independente. Seu campo
`payload_write_authorized=false` permanece falso: é uma entrada verificada
para o próximo reparador, não autorização genérica de escrita.

O C96 deve rederivar esses setores do cartão antes de liberar escrita,
com journal, FDs verificados, retorno a RO, leitura fria, prefix completo,
SB/GDT, fsck e userdata preservados. Não reutilizar C83plan antigo nem
atualizar seus pointers/provas para fingir que ele reparou o estado novo.
Só depois de root0755 cabe nova captura C86 para C93/C94. As imagens C79
antigas, os backups e os fences existentes continuam preservados.

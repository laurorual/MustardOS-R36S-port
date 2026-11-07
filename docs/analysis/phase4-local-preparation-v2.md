# C110 — modo real das bibliotecas locais

Data: 07/11/2026. Correção incremental encontrada durante a integração C109.
O preparador C107/C108 esperava0755 nas bibliotecas locais; a instalação
qualificada usa0644. A inspeção nativa confirmou os quatro arquivos distintos
nessa condição. A primeira tentativa `prepared-capsule-session/load.pjofljbw`
recusou o preparo com64 antes de criar preparation.once ou abrir UI/jogo.
As cinco entradas RAM foram conferidas e removidas; raizRO e C07 preservados.

C107/C108 e sua prova permanecem congelados. A revisão aditiva usa o prefixo
`/usr/libexec/muos-capsule-v2`: seis arquivos, sem substituir arquivos antigos
ou mudar permissões das bibliotecas instaladas. Funções de preparo C107 são
idênticas; a tabela muda o contrato das sete cópias locais para0644. A entrada
fixa o novo manifesto e prefixo. Preserva as quatro entradas públicas0700,
ROM somenteRAM, geração local de identidade e stage/run C105 original.

A fixture mantém os42 casos anteriores e acrescenta recusa de biblioteca
local em0755. Agora exige explicitamente0644 nas sete linhas antes de rodar
qualquer caso. Isso cobre a divergência real que o contrato sintético C107
não verificou contra a mídia. O instalador aditivo confere166 arquivos antes
de aplicar, com claim único, rollback de seis folhas próprias, fingerprint
privado e fechamento RO. Não executa jogo/ROM/UI ou reboot.

43 casos passaram em `capsule-prepare-v2/checks.pjsbqtpw`.
Instalação concluída no boot81, `capsule-prepare-v2/install.pfsk2m5s`:
seis folhas/10.545bytes, sem substituições; check e recusa vazia nativos0,
fingerprint/infraestrutura/montagens preservados, RAM removida e raizRO.
`dispatch.claim` está consumido: não repetir apply.

Revisão do callback antes da UI identificou um segundo ponto: c105_staged
chama caller_exec capsule, ausente no callback final. C111 acrescenta essa
validação de tmpfs e um teste da entrada real. C110 não executou preparo
positivo nem recebe aprovação gráfica; o caminho C109 seguirá C111.

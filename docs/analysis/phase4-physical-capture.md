# C86 — captura física somente leitura para recuperação

Concluído em **04/11/2026**.48verificações passaram; execução física de
referência e cópia independente com análise C85 aprovadas. Ainda não há
validação física pósboot nem writer p2-only/C79.

Survey real no Deck Jupiter/IP192.168.15.13 confirmou test128, nenhuma montagem
do cartão ou snapshot antigo, quatro aliases kernelRO e regra C83 intacta.
Original32 fora do fluxo. Nenhuma proteção é limpa ou serviço global alterado.

## Implementação

| Componente em port/scripts | Função |
| --- | --- |
| phase4-physical-capture.py | Helper local sudo finito, reference/postboot |
| prepare-phase4-physical-capture.py | Provas/backup, pacote selado e transporte SSH pinado |
| collect-phase4-physical-capture.py | Cópia host/fsync/hash e nova análise C85 |
| check-phase4-physical-capture.py | Guardas, protocolo, recibos e bootstrap |

Reutiliza somente leitura C82 (`identity`, `open_card`, cache/aliases e cópia
delimitada), contrato C84 e scanner C85, com fontes pinadas. Nenhum código
upstream modificado/copiado. Novos componentes próprios MIT. As guardas C82
já cobrem original/CID/geometria, mounts em todos os namespaces, swap/holders,
MBR/prefixo e abertura exclusivamente O_RDONLY; não foi repetida a bateria
antiga sem mudança nessas fontes. As verificações novas cobrem a integração.

Bootstrap exige sudo local/Deck, payload exato/hash/metadados, snapshot root0700
com fontes0400 e ambiente fixo. Não há servidor/RPC, format/restore, execução
de init ou operação para gerar/carregar seed/chave. Clone de código em /run
é removido no final quando não existe mount sob ele. Preflight interrompido,
SIGKILL ou queda podem deixar parcial/snapshot privado; não assumir conclusão.

Antes de qualquer flush/cópia, exige CID e ausência de consumidores, regra
temporária C83 root0644 com hash exato. Aplica BLKROSET=1 nos três aliases e
no bloco inteiro por FDs O_RDONLY, confirma GETRO e nunca SETRO=0. Isso reforça
proteção na reinserção posterior. Se o Deck perdeu a regra /run ou automontou
o cartão, aborta; não desmonta volumes alheios nem reinstala a regra implicitamente.
O primitivo C82 fsync/BLKFLSBUF pode concluir IO pendente anterior, não é uma
garantia física de ausência absoluta de IO. Não existe writer de payload.

Após namespace privado/propagação isolada, estágio persistente /var/tmp fora
do cartão e2GiB livres, abre o bloco inteiro identificado O_RDONLY|O_EXCL.
Guarda esse FD exclusivo, copia **somente p2**, offset128MiB/tamanho512MiB,
e confere fsync/hash/readback. Analisa a cópia regular com C85: fsck0, raiz0755,
árvore integral, privados e históricos consumidos. Não monta/copia p3 ou FAT.
Ao fim relê p2 inteira e MBR/prefixo16MiB no mesmo FD, repete identidade/RO/
guarda e só publica recibo depois dessas conferências.

## Referência versus pósboot

`reference` exige hash exato da raiz após C83 e os seis privados/contador72 do
backup C82. O hash esperado é calculado no host sobre a cópia C82 imutável,
substituindo em memória somente o setor corrigido da p2. Não regrava o backup
nem repete o reparo. Esse modo nunca publica capture-context.json ou observação
pósboot, mesmo que alguém tenha reiniciado o console anteriormente.

`postboot` exige um fence C84 já selado antes da entrega da mídia, pinado por
hash, com identidade privada/backup/contador. O preparador não o cria. Copia
essa intenção para o snapshot root, reconfere forma canônica e hash e deriva
contexto C85 do IO real: CID/capacidade, estado offline/cache/RO, hash/tamanho
da p2 recém-copiada e identidade do fence. Contador/privados vêm do scanner;
política C84 precisa aprovar a recuperação antes de exportar a observação.

A intenção é conservadora e marca possível boot antes da entrega. Não é prova
independente de que o usuário fisicamente transferiu/iniciou a mídia, nem JSON
autentica o dono do host. O fluxo só aceita esse registro de origem revisada,
não infere ausência de boot por rede/tela nem recupera p2 automaticamente.
Modo pósboot está testado com protocolo sintético; ainda não executado no Deck.

## Cópia independente e validação

O recibo nativo inclui hashes de todas as fontes seladas e dos artefatos. Só
após terminar as verificações o helper entrega diretório0700/folhas0400 ao
usuário deck, com fsync dos diretórios. O coletor usa chave SSH/host pinadas,
nomes fixos, FD NOFOLLOW, tipo/link/UID/modo/tamanho e hashes antes/depois do
stream privado. Não imprime imagens, chaves, seeds ou hashes privados.

No host, fsync/hash de cada cópia, análise C85 independente em container sem
rede/dispositivos e comparação da árvore completa com o resultado nativo.
Referência continua referência; pósboot recria a observação/plano por `collect`
do C85 e compara com o nativo. Não chama `compose`, não gera seed real nem
inicia firmware. Só depois cria host-copy.json/pointer de conclusão.

48casos passaram: gateRO e todos os aliases, ausência/perda de proteção,
schema/contexto/fence/recibos, fonte regular recusada no entrypoint interno,
payload/code hash/ambiente selado e IO de cópia/scan/fsck reais sobre ext4
sintéticas32MiB. Os descritores do protocolo são regulares com guardas físicas
stubadas; isso não qualifica controlador MMC, sudo/namespace ou captura física.
Os casos de pósboot derivam75 da imagem sintética, gerando plano76, sem seed.
Mudança da p2 após scan, falha de cópia/fsck e referência diferente abortam
antes de exportar contexto. Não há retry/rollback automático.

## Artefatos e estado nativo

Privados `build/phase4/physical-capture`: survey.9_hmbur0,
checks.b1lwecu4, package-reference.8fogtnhh. Destino Deck
`/home/deck/muos-r35s-c86-reference-995499b67f8b`.
Usuário executou o comando local porque SSH não dispõe de sudo sem senha e
confirmou `C86 CAPTURE COMPLETE`. Resultado Deck:
`/var/tmp/muos-r35s-c86-capture.f_gz9vwf`; snapshot /run removido. Host
`copy-reference.5zp_8jgi`, pointer latest-complete-reference.

Execução real aprovou536.870.912bytes, fsck0, contador72, seis privados e
3.669entradas. Hash da p2 foi igual ao previsto após C83 e permaneceu estável
nas releituras; MBR/prefixo16MiB conferidos. Transporte pinado/hash/fsync e
scanner C85 independente passaram; árvores completas nativa/host iguais.
Recibo propagou referência, sem contexto ou observação pósboot. Nenhum novo
seed/chave/candidata/restore/reboot ou montagem de userdata. A confirmação de
proteção final faz parte do empacotamento da prova pública.

`dist/phase4/physical-capture` contém somente fontes, casos e resumo redigido.
Root.ext4, árvores, privados, contextos e hashes reais ficam privados no Deck
e host. Essa cópia nova é snapshot da p2, não substitui o backup C82 completo
prefixo640MiB+userdata. C82/C83/C84/C85 e SDK/imagens/ROM preservados.

Manter cartão no Deck e original32 fora do fluxo. Próximo incremento: backend
p2-only e qualificação do ciclo de captura pósboot/recuperação antes de bootar
C79, com transição explícita das proteções C83. Não reutilizar restore/formatter
C20 nem generalizar escrita na p3.

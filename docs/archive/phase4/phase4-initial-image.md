# C88 — candidata privada provisionada, sem gravação de mídia

Em **04/11/2026**, a factory C79 foi provisionada como arquivo ext4 regular
de512MiB. O compositor usa a captura física C86 já conferida de forma
independente, preservando os seis arquivos privados, contador72, seed existente,
identidade de rede e nove marcadores consumidos. Não gera seed/chave, carrega
entropia, executa init, monta cartão ou cria fence de possível boot.

A leitura da factory percorre inodes pelo debugfs, incluindo conteúdo,
symlinks, owners, modos, links e flags. Essa entrada C79 não contém xattrs ou
inodes especiais; uma factory futura com esses recursos é recusada até ser
qualificada. A saída passa pelo scanner C85 completo e fsck sem reparo.
Comparação integral exige a árvore pública/metadados da factory, com a única
mudança de nlink em var/lib causada pelos dois diretórios privados novos.
Payloads privados/EAs/contador coincidem com C86; os históricos têm bytes e
metadados iguais e nenhum `.once` é criado. Fontes C79/C86 permanecem iguais.

A implementação é própria MIT e reutiliza os leitores/clonador regulares do
port. A rede upstream `refs/muos/internal/script/init/async/S02network.sh`
(GPLv3) foi consultada; nenhum trecho foi copiado. A candidata conserva o
contrato privado C07 existente, que exige diretórios0700, rede/host key0600,
chave autorizada0644 e seed0400; não transplanta o gerenciador upstream.

**17casos passaram:** imagens ext4 reais32MiB, preservação pública/privada/
históricos/symlink/fontes, tamper de modo público, clone interrompido, factory
com counter incorreto/privados já presentes/token ativo/xattrs, bindings e
caminhos inválidos antes de criação de arquivo. A fixture inicialmente herdou
security.selinux do host por mke2fs-d. Foi corrigida com no_copy_xattrs; a raiz
C79 real foi lida e confirmada sem atributos, mantendo recusa explícita de EAs.

Execução real com as fontes512MiB passou fsck0 e comparação completa. Privados:
`build/phase4/initial-image/provision.evbj4tey`; checks `checks.3zx9m7um`;
pointers latest-complete/latest-checks. A imagem privada foi transferida por
SSH pinado para `/home/deck/muos-r35s-c88-candidate.pp__3brn/candidate.ext4`,
sob700/600, com hash do stream, releitura integral independente, fsync de
arquivo e diretórios. Nenhum dispositivo foi aberto pelo receiver.

**Preparada não significa liberada para boot.** O arquivo contém o estado
privado do boot72 e não pode ser usado depois de outro boot sem revalidar e
atualizar seed/contador. O ciclo físico de recuperação prévio ainda é
necessário; ele poderá tornar esta candidata de preparação obsoleta. Não
gravar raw640MiB, restaurar byte a byte após possível boot nem creditar seed
antigo. C89 prepara a entrada p2-only de recuperação; a entrada de migração
inicial e sua elegibilidade física permanecem separadas.

O cartão real segue desmontado/quatro aliasesRO/regra C83, sem payload escrito.
Original32/SDK/refs/backups C82/C83/C86/ROM preservados. Imagens, conteúdos de
rede/seed/chaves, árvore e hashes privados permanecem apenas no build ignorado
e nos diretórios privados do Deck. A prova pública contém fontes/testes/resumo.

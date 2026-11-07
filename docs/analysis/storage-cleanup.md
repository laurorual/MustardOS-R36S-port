# Limpeza de armazenamento — 04/11/2026

Executada a pedido urgente do usuário, limitada a `/home/lauro/dev`, cujo
único projeto nesta máquina é `muos-r35s-port`. O backup no Steam Deck foi
interrompido em favor desta tarefa; nenhuma operação adicional foi feita no
Deck ou no cartão durante a limpeza.

Resultado: cerca de **15,6GiB físicos recuperados**, com espaço livre de
aproximadamente9,4 para25GiB. O uso reportado de `dev` caiu de64 para40GiB.

## Itens removidos

- 145 árvores sintéticas de testes concluídos: `case-NNN`, `fixture` e
  equivalentes sob stages `*checks*` com `analysis.json` aprovado. Eram cópias
  de payloads/raízes e materiais de reprodução dos testes, incluindo os140
  casos C71. Relatórios agregados e provas congeladas foram preservados;
  árvores descartadas podem ser recriadas pelos respectivos checkers.
- 191 diretórios de intermediários de compilação de pacotes em
  `build/phase4/rootfs-output/build` e
  `build/phase4/graphics-config/output/build`. Fontes extraídas e objetos
  gerados são reproduzíveis pelos recipes e downloads já guardados.

Foram mantidos os SDKs instalados (`output/host`, incluindo sysroots), targets,
imagens, `.config`, logs de build e licenças. Diretórios `muos-*`,
`buildroot-config`, `host-skeleton`, Rockchip Mali e libnl foram preservados
porque scripts ainda os referenciam diretamente. `glibc-*/COPYING.LIB` foi
reposto com os mesmos bytes para o auditor histórico que usa esse caminho.

A limpeza não remove código original em `port`, docs, refs, Git, dist, ROMs,
chaves, backups privados ou planos de migração. A medição global encontrou
grande uso fora de `dev`, principalmente Steam; nenhum arquivo dessa outra
área foi alterado.

## Imagens esparsas

`sparsify-phase4-images.py` usa `fallocate --dig-holes` somente em imagens
regulares grandes de `build`, com link único, excluindo áreas privadas,
root-migration e offline-backup. Regiões alocadas contendo apenas zeros
viram holes; continuam sendo lidas como os mesmos zeros. Tamanho, inode,
permissão e SHA-256 integral precisam permanecer iguais. O script verifica
o hash antes e depois de cada arquivo e preserva seus timestamps.

Foram processadas **53 imagens**; todas mantiveram seu SHA-256. Essa etapa
recuperou aproximadamente3,25GiB adicionais aos12,38GiB da remoção de caches.

Nenhuma imagem foi recomprimida ou substituída por outra versão. Isso mantém
compatíveis os caminhos e hashes dos scripts, incluindo C78/C79.

## Evidências e retomada

Auditoria detalhada em `build/cleanup/`: manifestos dos diretórios removidos,
bytes alocados, espaço livre antes/depois e hashes das imagens esparsas.
A comparação com `df` mede o ganho físico real; a soma de `du` inclui blocos
compartilhados por CoW e não equivale ao espaço recuperado.

Os dois SDKs compilaram novamente um programa mínimo com `-mcpu=cortex-a35`
em container existente, sem rede ou instalação de dependências. `readelf`
confirmou ELF64/AArch64. Configuração gráfica permaneceu igual ao baseline;
SHA256SUMS das provas C78/C79/C80/C81 passaram. Resultado em
`build/cleanup/verification.json`.
Hashes raw C78/C79 e gzip C79 também foram conferidos contra as provas;
ROM de GB, chaves de acesso e backup de recuperação C20 continuam presentes.
Resumo final em `build/cleanup/summary.json`.

Para recompilar versões históricas completas, regenerar os intermediários
removidos a partir dos recipes/arquivos em `rootfs-downloads`, preferindo uma
nova árvore de output. Não interpretar os caches removidos como corrupção de
provas nem reconstruir o SDK congelado sem uma tarefa específica. Os
compiladores instalados continuam disponíveis para os incrementos seguintes.

O estado do backup pendente está em [C82](phase4-backup-native.md). Não existe
backup C81 completo ou segunda cópia independente validada nesta retomada.

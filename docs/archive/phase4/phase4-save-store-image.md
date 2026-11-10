# Fase 4 — C56: imagem ext4 privada com o pacote de saves

Em 02/11/2026 foi gerada e conferida offline uma imagem ext4 de 512 MiB que
contém a árvore C55, incluindo o pacote opcional `muos-save-store`. O fsck,
a releitura integral e os contratos de boot/manifests passaram. O trabalho
não acessou o console, cartões físicos ou Steam Deck. A imagem ainda não
foi iniciada no R35S.

## Artefato e origem

Imagem privada no host:
`build/phase4/save-store-image/image.nlnmgzzb/images/rootfs.ext4`

SHA256:
`07a18d14ef54c91b7e463a016155165deff33296fdf833b8dbca51ff38780ef6`.

Origem C38 de 512 MiB:
`build/phase4/rootfs-candidate/composition.w59vz7vo/images/rootfs.ext4`,
SHA256 `7b2718beec0aa75fd5b6d81570c9e98857efa00f01638d7f04159a73d711320d`.
A composição fonte é `save-store-package/composition.d0qpit_q`, cujo relatório
coincide byte a byte com a prova congelada C55.

É uma imagem de rootfs, sem tabela de partições, bootloader ou FAT de um
cartão completo. Preserva a base e os módulos existentes; não acrescenta
kernel/DTB, ROM, core de Game Boy, estado comercial, credenciais, seeds ou
chaves privadas. A chave pública de diagnóstico já existente na base C07
continua presente; provisionamento e credenciais não são reproduzidos pelo
compositor. O GPU R13 da base mantém as pendências já registradas em
`port/packaging/pending-licenses.json`. O rootfs continua privado em `build/`,
sem nova decisão de publicação ou redistribuição.

## Método e verificações

O script original MIT `compose-phase4-save-store-image.py` exige a composição
C55 explicitamente. Confere SHA256SUMS e relatório congelado, fontes, imagem
C38 e inventário C55. Foi consultado `fs/ext2/ext2.mk` do Buildroot e o fluxo
local C23/C38 antes de escolher uma alteração aditiva em cópia da imagem.
O formato ext4 e os recursos compatíveis com o BSP 4.4 são os mesmos da base;
não se cria outro filesystem com defaults potencialmente diferentes.

Somente um arquivo regular novo sob `build/phase4/save-store-image/` recebe
escrita via `debugfs -w`. Os comandos acrescentam os quatro arquivos e três
diretórios C55, com uid/gid 0 e modos previstos. Não há mount, loop, SSH,
acesso a dispositivos de bloco ou execução de init. Todas as ferramentas
rodam no container existente, sem rede ou instalação no sistema hospedeiro.

Resultados de `image.nlnmgzzb`:

- `e2fsck -fn`: cinco passes, status 0, sem reparar ou alterar a imagem;
- raiz 0755/uid0/gid0 e todos os sete inodes novos com dono/grupo 0 e modos
  conferidos diretamente por `debugfs stat`;
- extração integral por `rdump` para uma árvore nova: 3.330 itens coincidem
  com tipos, conteúdo/hash, modos e destinos de symlinks da árvore C55;
- todos os itens anteriores C38 preservados; só quatro arquivos/três
  diretórios adicionais; imagem e árvores de origem permanecem inalteradas;
- fundação97, payload15, perfil21 e manifesto do novo pacote com três hashes
  válidos após a releitura;
- gate de boot aprovado antes e depois da serialização, C07 selecionado,
  contador de fábrica 0, sessões/preferências automáticas desativadas, sem
  token C12/C25 ou bootstrap de saves;
- auditoria estática: 306 ELFs userspace AArch64, 555 módulos AArch64 ET_REL
  da release `4.4.189-muos-r35s-p4`, intérprete AArch64 e glibc ABI 4.4.0;
- ext4 `ROOTFS`, 536870912 bytes, compat `0x3c`, incompat `0x242`, ro_compat
  `0x46b`, iguais à base, sem `64bit`, `orphan_file`, `metadata_csum_seed`
  ou `fast_commit`;
- loader A35/QEMU com `LD_BIND_NOW=1` resolveu zlib/libc da árvore relida e
  executou o CLI sem argumentos, que recusou com status 64;
- `.config` compartilhado do SDK e provas anteriores conferidos intactos.

O CLI permanece byte-idêntico ao C52. Os 172 checks de loader C38 e as
transações/laboratório ext4 C52 são reutilizados para os mesmos bytes e
bibliotecas; não foram repetidos. A auditoria estática e a comparação completa
são novas verificações da serialização C56. Não houve recompilação de
binários nem rebuild completo do Buildroot. O `.config` copiado ao stage é
somente o baseline de auditoria; o pacote extra vem das macros opt-in C55,
não de uma alegação de build completo com essa opção habilitada.

## Reprodução e prova

```sh
python3 port/scripts/compose-phase4-save-store-image.py \
  --source-composition build/phase4/save-store-package/composition.d0qpit_q
python3 port/scripts/package-phase4-save-store-image.py
```

A composição sempre cria um stage novo. O empacotador recusa sobrescrever
`dist/phase4/save-store-image`, verifica a prova C55 e congela apenas fontes,
relatórios, comandos e recibos das ferramentas com SHA256SUMS. Não publica
ELF, rootfs, ROM ou saves. O hash de imagem identifica esta execução; não
foi qualificada reprodutibilidade bit a bit das datas/metadados ext4.

C56 não consultou o estado vivo do console. O último estado verificado é o
C55: C07/boot69/IP192.168.15.14, rootRO/fundação97/PCMclosed/p3desmontado,
sem o pacote instalado; não interpretar esse registro como nova leitura da
rede ou do contador. Nenhum reboot, token, sessão gráfica, teste acústico,
montagem de p3 ou alteração nos cartões foi solicitado neste incremento.

## Próximo incremento

C57: preparar a implantação seletiva dos quatro arquivos C55 no cartão de
teste de 128 GB, com inventário, backup e rollback vinculados aos hashes do
pacote. Primeiro conferir o estado real e a ausência dos destinos; preservar
fundação97, configuração de áudio, preferências e store comercial. Manter o
CLI sem serviço, autostart ou chamada automática a init/commit/recover.
Não usar a imagem de rootfs inteira para sobrescrever a raiz viva. Uma
verificação nativa do pacote deve usar somente RAM sintética e encerrar em
rootRO/p3desmontado; não repetir sessões de jogo já aprovadas por rotina.

Não há C57 armado ou instalado. Boot desta imagem, coldboot controlado,
perda elétrica, SRAM/GC, Power/suspend, continuidade de áudio e desempenho
NES permanecem fora da qualificação C56.

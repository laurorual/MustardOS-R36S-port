# Fase 4 — C64: imagem ext4 privada com store e muxretro

Em03/11/2026 foi produzida uma imagem de rootfs ext4 de512MiB com o pacote
de saves C56 e os treze arquivos do host C60/C62. A releitura integral,
fsck e os contratos de boot/manifests passaram. O console não foi acessado;
o novo IP informado pelo usuário,192.168.15.10, fica registrado para uma
operação posterior. Nenhum teste físico foi repetido neste incremento.

## Artefato e origem

Imagem privada no host:
`build/phase4/muxretro-image/image.n_uthilw/images/rootfs.ext4`.

SHA256 `671a738792d5a6b718d698f8386488d14216c8f539541f2b6160e1bbc98a62a6`.

Origem C56 de512MiB:
`build/phase4/save-store-image/image.nlnmgzzb/images/rootfs.ext4`, SHA256
`07a18d14ef54c91b7e463a016155165deff33296fdf833b8dbca51ff38780ef6`.

A árvore planejada é a composição C60
`build/phase4/muxretro-package/build.mdou4mqr/composition`: os3.330itens C56
mais13arquivos/13diretórios do pacote muxretro. Seus hashes/modos coincidem
com o plano de instalação C62; o hash do host coincide também com a prova
nativa C63. As provas C56/C60/C62/C63 e essas ligações são verificadas antes
de permitir qualquer escrita na nova cópia local da imagem.

O host é o ELF já aprovado, SHA256
`8d519958cdb1ae599e2b2af2f6ee90053bca1a83cce0380baa3a1d7150983f05`.
O CLI de saves conserva os bytes C52/C55/C56/C57. Licenças e metadados do
host são os nove avisos e três arquivos instalados no C62. Bibliotecas,
kernel/módulos, perfil de painel e contratos existentes são preservados.

Trata-se de uma imagem de **rootfs**, não de cartão completo com tabela de
partições, FAT e bootloader. Continua privada em `build/`, com as pendências
gráficas/vendor de `port/packaging/pending-licenses.json`. Não há decisão nova
de publicação. A prova em `dist/` contém só fontes e recibos, sem a imagem.

## Método e verificações

O compositor MIT `compose-phase4-muxretro-image.py` adapta o método C56 sem
editar seus scripts/provas. Foram consultados o fluxo C56, o auditor estático,
os validadores de composição e `fs/ext2/ext2.mk` do Buildroot da bancada.
A escolha é aditiva: preservar os recursos ext4 conhecidos pelo BSP4.4 em
vez de recriar o filesystem com outros defaults.

Somente um arquivo regular novo com link1 recebe escrita via debugfs; a
imagem C56 permanece inalterada. Treze diretórios são criados em ordem de
pais e treze folhas são acrescentadas, com modos/uid/gid explícitos. Todas
as ferramentas rodam no container existente sem rede. Não há mount/loop,
acesso a bloco/cartão, SSH, init ou novo build de toolchain/frontend.

Resultados de `image.n_uthilw`:

- `e2fsck -fn`: cinco passes/status0, sem reparar ou alterar a imagem;
- root0755/uid0/gid0 e26inodes novos com modos e donos/grupos conferidos
  diretamente via debugfs; as13folhas regulares têm link1;
- rdump para uma árvore nova:3.356itens coincidem em conteúdo/hash, tipo,
  modos e destinos de symlinks com a composição C60 aprovada;
- os3.330itens C56 permanecem idênticos; só13arquivos/13diretórios adicionados;
- fundação97, payload15, perfil21, manifestos do store/host e quatro links
  privados de frontend conferidos depois da releitura;
- contrato C07 aprovado antes/depois da serialização, contador de fábrica0,
  sessões/preferências automáticas desativadas e ausência de tokens/seeds/
  credenciais/estado privado gerado;
- auditoria estática:307ELFs userspace AArch64 e555módulos AArch64 ET_REL,
  release4.4.189-muos-r35s-p4, intérprete AArch64/glibc ABI4.4.0;
- ROOTFS/536870912bytes, compat0x3c/incompat0x242/ro_compat0x46b, iguais C56;
- imagem/árvores/provas de origem e `.config` compartilhado SDK intactos.

Fsck e inventário são verificações novas da serialização. Loaders não foram
repetidos: todos os ELFs, dependências e caminhos/symlinks são os mesmos da
composição qualificada. Reutilizam-se os172checks C38, o check do CLI store
C56 e o check do host C60, além da evidência nativa C63 dos mesmos bytes.
Isso não transforma os testes dos componentes em um teste de boot da imagem.
O `.config` no stage é baseline de auditoria, não alegação de fullrebuild
Buildroot com o provider completo de frontend integrado.

Não entram nesta imagem core/ROM/estado comercial, preferências do cartão,
caller/dispatcher C63 ou biblioteca diagnóstica C46 em RAM. O host fica
instalado/passivo; o gate continua C07 e não abre um jogo automaticamente.
A chave pública de diagnóstico existente na base continua presente; seeds,
chaves privadas, credenciais e redes do console não são reproduzidas.

## Reprodução, provas e estado do console

```sh
python3 port/scripts/compose-phase4-muxretro-image.py \
  --source-build build/phase4/muxretro-package/build.mdou4mqr
python3 port/scripts/package-phase4-muxretro-image.py
```

Cada composição cria um stage novo, apontado por
`build/phase4/muxretro-image/latest-image`. O empacotador recusa sobrescrever
`dist/phase4/muxretro-image`, confere os hashes e congela fontes, auditoria,
comandos e recibos com SHA256SUMS. A imagem e os ELFs ficam fora dessa prova.
O hash identifica esta execução; datas/metadados ext4 não foram qualificados
como reprodutíveis bit a bit.

O IP192.168.15.10 foi informado pelo usuário e não conferido por SSH no C64.
Última saúde verificada foi C63/boot70, então no IP192.168.15.14: rootRO0755,
PCMclosed/p3desmontada, host C62 e CLI C57 passivos, página C63 e store
geração1/HEAD1/0/2 intactos. Não inferir o contador/UUID ou a saúde atual a
partir da mudança de IP. Antes de nova operação física, reler estado real
com chave SSH fixada; não afrouxar os vínculos antigos caso o boot tenha mudado.

Cartão128, original32 e Steam Deck não foram acessados; não houve flash,
reboot, remount ou alteração da instalação. A imagem C64 não foi iniciada
no R35S e não deve ser usada para sobrescrever a raiz viva por rotina.

## Próximo incremento

C65 proposto: preparar a integração Buildroot das quatro bibliotecas muOS
que ainda são pré-requisito do SDK privado C60. Fixar origem/licenças/patches,
dependências e ABI, distinguindo a fundação da variante C46 usada na seleção
diagnóstica. Trabalhar offline e em stages separados; um ELF reconstruído
diferente exige qualificação própria antes de substituir bytes aprovados.

Provider completo/frontend permanente, boot da imagem, host após novo boot,
Power/suspend, SRAM/GC/perda elétrica, áudio contínuo e longa duração continuam
fora desta qualificação. Nada C65 armado ou implantado.

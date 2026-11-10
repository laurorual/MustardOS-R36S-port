# C78 — imagem ext4 com Gambatte integrado

Concluído inteiramente offline. A composição C75 foi serializada em uma nova
ext4 privada de 512 MiB, preservando a imagem C69 como base. SHA256:
`a09edf63ac5397b0adc5bdf7d9eb7413f6e02e7963e569b915df0ffe674d08fc`.

O [compositor](../../port/scripts/compose-phase4-gambatte-image.py) cria uma
cópia exclusiva em um stage novo e aplica somente nove arquivos e oito
diretórios. Não aceita destino de dispositivo ou imagem existente. As fontes
e recibos C69/C70/C75/C76/C77 são conferidos antes da composição. O delta C75
congelado, unido ao inventário C69 congelado, define os 3.403 itens esperados;
o target C75 e a releitura da imagem precisam coincidir integralmente.

O core fica em `/opt/muos/share/core/gambatte_libretro.so`, modo0644, SHA256
`3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57`.
É o mesmo core instalado pelo C76 e usado pelo caller aprovado fisicamente
no C77. A imagem inclui também a revisão de licença, seis avisos/fontes de
licença e o manifesto do pacote. Não incorpora ROM, snapshot, caller
diagnóstico C77, credenciais, seed ou host keys.

## Verificações

`e2fsck -fn` terminou com código zero, sem alterar o hash da imagem. A extração
integral por debugfs/fakeroot coincidiu com os 3.403 itens previstos: todos os
3.386 itens C69 preservados, nove arquivos e oito diretórios novos, nenhuma
substituição. Inspeção direta de 18 inodes verificou owner root e modos da raiz
e dos 17 acréscimos. As nove folhas são regulares e têm link único.

Fundação97/perfil21/payload15 e os manifestos de core/provider/host/store
passaram. O contrato de boot foi executado sobre a composição e sobre a
extração: C07, contador de fábrica zero, UI/sessão/preferências automáticas
desabilitadas. A auditoria estática encontrou 308 ELFs AArch64 de userspace
e os mesmos 555 módulos; intérprete, ABI Linux4.4.0, release do kernel/módulos
e features ext4 permanecem iguais à base C69.

Os 174 programas dinâmicos C69 mantêm seus bytes e os hashes de todas as
dependências transitivas. Nenhum arquivo foi acrescentado aos diretórios
pesquisados pelo loader (`/opt/muos/frontend/lib`, `/lib`, `/usr/lib`). Por isso,
os recibos C69 de resolução desses programas foram reaproveitados, sem
repetir execuções. A adição do core recebe sua própria checagem: um probe MIT
novo, compilado com o SDK existente e o header fixado no pacote extraído,
confirmou dlopen eager/Gambatte/API1/conteúdo em memória sob QEMU Cortex-A35.
RELRO/NOW do core também foram conferidos. O probe não chama `retro_init` nem
carrega ROM. Essa checagem não é execução de jogo nem aprovação de boot.

Ao final, os hashes das imagens C69 e C70, os inventários da composição e da
base e a configuração compartilhada do SDK continuaram iguais. Não houve
contato SSH com o console ou Steam Deck, reconstrução completa do Buildroot,
montagem de cartão ou teste físico repetido. O último estado observado do
console continua sendo o registrado no C77, sem nova alegação de saúde atual.

Uma primeira execução parou antes de criar stage/imagem porque exigia
`expected-tree.json` na prova C75, que não inclui esse arquivo. O vínculo foi
corrigido para reconstruir a expectativa usando a árvore C69 e o delta C75,
ambos congelados, além de comparar com a composição privada C75. As provas
históricas permaneceram intactas.

## Artefatos e limites

Stage privado: `build/phase4/gambatte-image/image.zal39n7u`; imagem em
`images/rootfs.ext4`. O [empacotador](../../port/scripts/package-phase4-gambatte-image.py)
congela fontes e recibos em `dist/phase4/gambatte-image`, sem imagem, ELF,
ROM, save ou dado privado. O SDK e as imagens anteriores permanecem intactos.
O cartão original32 e o cartão de teste128 não foram acessados neste recorte.

A revisão conjunta GPLv2/GPLv3/MIT permanece pendente e o pacote continua
privado, `REDISTRIBUTE=NO`. Não foram qualificados bit-reprodutibilidade,
boot desta imagem, provisionamento, autostart, caller permanente, SRAM,
longa duração ou perda elétrica. A aprovação física C77 pertence ao conjunto
de componentes e ao caller diagnóstico daquele ensaio.

Próximo recorte proposto C79: montar uma nova imagem privada completa de
cartão usando esta raiz e o bootchain/kernel/DTB/layout já fixados no C70,
conferindo regiões, FAT e extração da raiz. A imagem de cartão C70 permanece
com sua raiz C69 original. Provisionamento e boot supervisionado da nova
imagem ficam em etapa própria, sem gravar automaticamente no cartão ativo.

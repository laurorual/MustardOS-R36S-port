# C75 — core Game Boy em receita Buildroot

Concluído em03/11/2026, inteiramente offline. A nova árvore
`port/buildroot-libretro` fornece `BR2_PACKAGE_MUOS_GAMBATTE`, desabilitado
por padrão e dependente de AArch64/C++. As árvores e provas dos pacotes
anteriores não foram alteradas. Não há ROM, caller, boot hook, política de
save, seleção automática de core ou instalação no console.

O [builder](../../port/scripts/build-phase4-gambatte-package.py) usa o mesmo
archive C49, revisão77f2567d718b8973d02caa2daa8dce4953faf811/SHA
45e63bc79390093b78de025172ea289ded139f4ecf1e8072242f34d7dd540338.
Exercitou Kconfig/download do cache/extract/legal-info reais do Buildroot,
com rede desabilitada no container. São148arquivos de fonte. Configuração
defaultoff, seleção explícita e recusa de i386 passaram. O SDK compartilhado
continuou na baseline; não foi reconstruída toda a toolchain/dependências.

As macros reais de build/install usam o SDK já existente e os flags da
compilação qualificada C49: Cortex-A35/O2/stack protector/RELRO/NOW,
platform=unix, RGB565=1 e HAVE_NETWORK=0. O valor sentinela upstream de
GIT_VERSION é fixado para não injetar revisão de outro repositório pai.
Flags adicionais do Makefile upstream permanecem ativos. Uma futura build
com flags de outra configuração completa deve conferir seus próprios bytes.

O ELF final tem SHA256
`3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57`,
**byte a byte igual ao core C49 utilizado no C73**. O vínculo C73→C63 confirma
esse hash. Foram verificados AArch64/shared, RELRO/NOW, conjunto de exports
idêntico e dlopen eager/API1/metadata de conteúdo em memória via QEMU/A35.
O probe não chama retro_init nem carrega ROM. Não foi necessário repetir a
sessão física já aprovada com esses mesmos bytes. A escolha de caminho de
instalação ainda não foi executada num fluxo gráfico no aparelho.

A receita instala o core em `/opt/muos/share/core/gambatte_libretro.so`,0644,
seguindo `MUOS_SHARE_DIR/core` dos launchers muOS upstream. Acrescenta uma
folha de revisão de licença, seis avisos/fontes com licença e um manifesto:
nove arquivos e oito diretórios novos na composição. Todos os3386itens C69
permaneceram intactos; resultado3403itens. Fundação97/perfil21/payload15,
C07/contador0/defaultsoff e manifestos anteriores passaram. Essa composição
não é uma nova ext4 ou imagem completa de cartão.

O levantamento por arquivo encontrou um detalhe que a etiqueta histórica
GPLv2/COPYING do C48 não capturava: cpu.cpp declara GPLv2, enquanto os fontes
compilados cc_resampler.c/h declaram GPLv3; blipper e partes libretro-common
trazem MIT. O novo pacote registra esses fatos e deixa a revisão conjunta
pendente em `license-review.json`, com `MUOS_GAMBATTE_REDISTRIBUTE=NO`.
Os seis arquivos de licença são retidos pelo legal-info e conferidos por hash;
o archive original fica no cache privado. Não se declarou resolvida a condição
de redistribuição do binário combinado. As anotações históricas permanecem
imutáveis; consultar este registro para o escopo atualizado da licença.

A primeira tentativa `build.8ba6ov5u` parou numa fixture de arquitetura:
utils/config convertia símbolos minúsculos para maiúsculos sem --keep-case,
portanto não havia realmente selecionado i386. Corrigida a preparação da
fixture; stage novo `build.tgnlr06f` comprovou i386 ativo e pacote recusado.
Nenhum core dessa tentativa inicial foi apresentado como aprovado.

Stage final: `build/phase4/gambatte-package/build.tgnlr06f`.
Prova: `dist/phase4/gambatte-package`, somente receitas/fontes do port/
metadados/logs, sem ELF, rootfs ou ROM. O [empacotador](../../port/scripts/package-phase4-gambatte-package.py)
confere fontes, composição e provas pais antes de congelar o recibo.

Console permanece no último estado C74/boot72/IP18/rootRO/quieto. Original32,
Steam Deck, imagens e conteúdo comercial não foram acessados neste incremento.
Próxima integração: plano seletivo de instalação do core com ausência inicial,
backup de ausência e rollback próprios; somente depois adaptar o caller para
o caminho instalado. Não repetir o jogo C73 por rotina. Instalação, chamada
gráfica pelo novo caminho, serialização da composição e boot continuam pendentes.

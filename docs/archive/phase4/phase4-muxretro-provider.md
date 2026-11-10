# C67 — muxretro consome o provider frontend no Buildroot

Concluído offline em 03/11/2026. A receita muos-muxretro-provider declara
dependência em muos-frontend-libs e liga o host contra o staging desse
provider, dispensando o antigo SDK privado das quatro bibliotecas muOS.
Configuração, fontes/licenças, guardas, compilação, composição e CLI passaram.
O novo host difere do instalado e ainda precisa de qualificação nativa.

Stage: build/phase4/muxretro-provider/build.f9a1ac69.
ELF SHA256:
cd67ce605cfa406f6084c7348ebf27d475b73340edd981c1343f07b00a995e9d.
O host C60/C62/C66 continua SHA8d519958...; não foi substituído.

## Receitas e origem

Nova árvore externa port/buildroot-muxretro, nome MUOS_R35S_MUXRETRO. A opção
BR2_PACKAGE_MUOS_MUXRETRO_PROVIDER começa desativada, exige AArch64 e os
requisitos do provider, seleciona MUOS_FRONTEND_LIBS e recusa coexistência
com o pacote histórico MUOS_MUXRETRO. Os arquivos Config.in C60 e C65 estão
fixados nas provas; uma árvore adicional permite preservar esses vínculos.

Uso conjunto dentro do container:

    BR2_EXTERNAL="/port/buildroot /port/buildroot-frontend /port/buildroot-muxretro"

O grafo Buildroot real inclui muos-frontend-libs como dependência do consumidor;
staging precisa ser instalado antes do link. Nenhum core, ROM, estado, service,
caller diagnóstico ou token de boot é selecionado/instalado pelo consumidor.

Fontes C60 somente de texto foram reutilizadas após verificar o manifesto e
a prova congelada, sem repetir extração/patches já aprovados. Origem:
frontend5e8635b3b485eec9ad2ace141c415fd2df47d8f1 e
rcheevos2ad0b8672f68a48148620164510b963039e49eb1, com patches C60 existentes.
C60-input-provenance.json na prova mantém hashes de arquivos de origem,
patches e header diagnóstico. São 1.302 textos no SITE e arquivo legal-info,
incluindo 982 arquivos compartilhados com o provider verificados byte a byte.
Os headers compartilhados coincidem; alterações retro específicas do host
continuam as mesmas de C60.

Dez licenças/avisos do consumidor são fixados, incluindo GPLv3 frontend,
MIT rcheevos/libretro e LVGL/LICENCE, mais avisos dos vendors C60. O provider
mantém suas onze licenças separadas. Arquivo legal-info do consumidor SHA256:
a7a7f4093734e79d558388d1fca5c3f677e186243ec6bc5b6fc7f44417d682c7.
Não há objetos, arquivos estáticos ou ELFs no SITE/archive de fontes.

## Staging, link e erro corrigido

A compilação usa o SDK/container existentes. Uma cópia local do sysroot recebe
as quatro bibliotecas pelo macro INSTALL_STAGING da receita C65; as bibliotecas
não são recompiladas nem copiadas de um SDK muOS externo. Seus hashes são
exatamente os qualificados em RAM pelo C66. O sysroot compartilhado não recebe
as bibliotecas nem alterações de configuração.

O consumidor confere os quatro hashes no staging antes de executar qualquer
compilador. Cinco guardas negativas passaram: ausência do provider e corrupção
individual de cada biblioteca. O compilador substituto não foi chamado nesses
casos. O manifesto runtime fixa os mesmos hashes em /opt/muos/frontend/lib.

Primeira tentativa build.ispvtcnb compilou fontes, mas o linker recusou scripts
glibc da cópia do sysroot: seus caminhos absolutos /lib64 eram interpretados
fora do sysroot original. A correção passa --sysroot explicitamente nos comandos
de compilação e link. Nenhum arquivo glibc/GPU foi editado. O primeiro SITE foi
preservado como source.before-explicit-sysroot; a prova registra a falha.
Depois da mudança nas entradas de compilação, configuração/guardas/build foram
revalidados em stage novo.

Não houve reconstrução integral de toolchain/dependências pelo Buildroot:
Kconfig/rsync/legal-info são reais e os macros reais de build/install são
executados com o SDK existente em harness isolado. O grafo de dependência está
validado, mas um full build de firmware ainda é trabalho separado. As condições
privadas do provider gráfico continuam as documentadas nas imagens anteriores.

## Resultado e composição

Kconfig confirma default off, dependências transitivas, ausência do antigo
SDK/host/serviços, rejeição i386 e recusa do consumidor quando o host histórico
é selecionado. O= termina restaurado à configuração opt-in AArch64.

ELF AArch64/PIE, intérprete /lib/ld-linux-aarch64.so.1, GNU ABI Linux4.4.0,
RELRO/NOW e RUNPATH /opt/muos/frontend/lib, sem caminho de build no RUNPATH.
NEEDED contém as quatro bibliotecas do provider. CLI version/help passou em
QEMU/Cortex-A35 com resolução eager; LD_DEBUG confirmou os quatro caminhos
da composição, sem usar bibliotecas muOS do SDK histórico.

Target tem 31 arquivos: 17 do provider e 14 do consumidor, com manifestos
independentes. O consumidor instala o host e seus metadados/licenças; o provider
é o único dono das bibliotecas. Warnings de compilação:74 de possível
truncamento de formatos, zero erros finais; o linker também emite sete avisos
de símbolos locais no ELF EGL privado já existente. Não foram suprimidos
diagnósticos nem feitas alterações em fontes upstream para contorná-los.

A composição parte de C56, antes do host C60, para não manter metadados antigos
que fixariam bibliotecas diferentes. C64 permanece como recuperação intocada.
A cópia C67 contém 3.386 itens: base C56 de3.330 +27arquivos/29diretórios novos,
zero itens removidos. Apenas quatro folhas anteriores mudam:

| Bibliotecas | Hash | Modo |
| --- | --- | --- |
| libui.so e libmuxcom.so | novos hashes C65/C66 | 0755 → 0644 |
| libmuxmod.so e libplutosvg.so | mesmos bytes da fundação | 0755 → 0644 |

Os outros 3.326 itens C56 são preservados. Fundação97, payload15, perfil21,
manifestos provider/consumidor/store e contrato C07/contador0/autostart off
passaram. O store C57 permanece igual. Não foi criada imagem, rodado init,
montado volume de bloco ou acessado console/cartões/Steam Deck.

A CLI do novo host passou; isso não transfere a aprovação física C66 para um
ELF diferente. Não se reivindica reuso indiscriminado dos 172 loaders C38:
duas dependências frontend mudaram. Uma futura imagem deve validar os loaders
afetados, além da qualificação nativa do novo host. Nenhum novo replay gráfico,
áudio, core ou jogo foi executado nesta etapa.

## Reprodução e próximo passo

    python3 port/scripts/build-phase4-muxretro-provider.py
    python3 port/scripts/package-phase4-muxretro-provider.py

Scripts exigem as entradas históricas preservadas. Um SITE diferente é
recusado; não é sobrescrito silenciosamente. A prova de empacotamento também
recusa sobrescrever o destino final. Prova em dist/phase4/muxretro-provider,
somente fontes/licenças/recibos: sem ELF/rootfs/ROM/estado/PCM/imagem.

Provas C56/C60/C64/C65/C66, imagens anteriores e SDK .config foram verificadas
intactas. C64 continua SHA671a738792d5a6b718d698f8386488d14216c8f539541f2b6160e1bbc98a62a6.
Estado vivo não foi consultado: último confirmado C66/boot71/IP192.168.15.10,
rootRO/p3off/UIoff/PCMclosed. Não presumir que esse boot/IP continua atual.
Cartão original32 e instalação original preservados; nada foi instalado no128.

Próximo C68 proposto: qualificar o novo ELF C67 em RAM, mantendo bibliotecas
C65 já qualificadas, seleção C46 dos menus e CLI store C57 instalado/load-only.
Usar guardas novas que não substituam o host C62; reler estado real e exigir
boot/UUID exatos. Se o boot mudou, amarrar nova observação sem editar vínculos
históricos. Usar GB existente, Fn+L2/Fn+Start, sem novo save. Nada C68 armado.
Boot da imagem, frontend permanente, Power/suspend, SRAM/GC, perda elétrica,
áudio contínuo e longa duração continuam separados.

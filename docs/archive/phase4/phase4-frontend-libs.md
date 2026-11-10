# C65 — bibliotecas do frontend como provider Buildroot

Incremento offline, em 03/11/2026. Integra uma receita opt-in para `libui.so`,
`libmuxcom.so`, `libmuxmod.so` e `libplutosvg.so`, compiladas de fontes limpas.
Não substitui as bibliotecas qualificadas, não instala no console e não altera
a imagem C64. A variante diagnóstica C46 continua separada.

**Resultado:** concluído em `build/phase4/frontend-libs/build.84o1r4aj`.
Kconfig/rsync/legal-info, compilação limpa, target/staging, ABI, carregamento
eager das quatro bibliotecas e CLI C60 passaram. Prova em
`dist/phase4/frontend-libs/SHA256SUMS`, sem ELF, ROM, estado ou imagem.

## Implementação e reprodução

Árvore externa nova: `port/buildroot-frontend`, nome `MUOS_R35S_FRONTEND`.
Pode coexistir com `port/buildroot` usando
`BR2_EXTERNAL="/port/buildroot /port/buildroot-frontend"` dentro do container.
Essa separação preserva byte a byte as receitas/Config.in vinculadas às provas
C60–C64. Não há modificação em `refs/`.

`BR2_PACKAGE_MUOS_FRONTEND_LIBS` começa desativado, exige AArch64, bibliotecas
compartilhadas e os requisitos das dependências SDL/FFmpeg/gráficas. Seleciona
SDL2/image/mixer/ttf, HarfBuzz, FreeType, PNG, curl, FFmpeg/swscale, archive,
OpenSSL e zlib. Dependências de compilação também incluem pkgconf, EGL/GLES.
Não seleciona o SDK privado, muxretro, serviços, boot ou launcher automático.

```
python3 port/scripts/build-phase4-frontend-libs.py
python3 port/scripts/package-phase4-frontend-libs.py
```

O preparador usa o container/SDK já existentes, sem rede nem instalação de
dependências no host. Cria stages em `build/phase4/frontend-libs/build.*` e um
SITE local somente de fontes em `build/phase4/frontend-libs/source`. Fontes
existentes diferentes são recusadas, não sobrescritas. `latest-attempt` e
`latest-build` distinguem tentativa e conclusão. A ferramenta de empacotamento
também recusa sobrescrever a prova final existente.

## Origem e licenças

Frontend `5e8635b3b485eec9ad2ace141c415fd2df47d8f1`, arquivo já disponível
`build/phase4/menu/frontend-source.tar`, SHA256
`c638d1afd4d995792f5ee09ea647de6976a60ca80e82014591a3fdff400ee5ff`.
Aplicam-se somente os patches 0003 (Panel 0) e 0006 (volume normalizado).
Os textos reconstruídos são comparados individualmente à fundação aprovada;
o makefile C65 deriva do makefile do port, com somente quatro alvos de
bibliotecas e propagação explícita de LDFLAGS. Não inclui patches C46 0010/0011.

mojibake 0.3.6 vem de `build/phase3/deps/mojibake-0.3.6.tar.gz`, SHA256
`156bb5c0c1f1265c5d75f4ef53ff4aab09c368e358b05f4f780ba6ec2575fed3`.
Fontes e headers usados são comparados à fundação, recompilados com PIC e
arquivados estaticamente no stage novo; nenhum `.o`, `.a` ou ELF prévio é
admitido no SITE ou no arquivo legal-info.

SITE tem 1.274 arquivos de texto, incluindo 1.195 textos do frontend iguais
à fundação. O arquivo legal-info releitura contém exatamente esses arquivos,
SHA256 `b18feeda16c9e276ab7a0d102674db1649531b84192aa991299b3e5c93a0ff02`.

Há onze avisos de licença com hashes: GPLv3 do frontend; MIT de LVGL,
plutosvg/plutovg, JSON, stb e mojibake; BSD de mini/xxhash; avisos miniz e
mdns preservados integralmente. Inclui `vendor/lvgl/LICENCE`, com a grafia
original. Nenhuma autorização de redistribuição dos componentes gráficos
privados da imagem é inferida desta receita.

## Instalação isolada e verificações

Buildroot real valida Kconfig, rsync, metadados e legal-info em O= separado.
São conferidos default off, dependências selecionadas, ausência de ativação
indireta do SDK/serviços/host e rejeição da opção em i386. O último `.config`
desse O= pertence ao teste i386; `opt-in.config` guarda a configuração AArch64.
Não usar esse diretório de testes como configuração de firmware.

A compilação e as instalações executam os macros reais da receita num harness
com o SDK AArch64/Cortex-A35 existente. Isso não equivale a uma reconstrução
integral de toolchain, dependências e firmware pelo Buildroot. O sysroot
compartilhado é somente entrada: staging instala em diretório próprio.

Target contém apenas as quatro bibliotecas em `/opt/muos/frontend/lib`, onze
licenças, proveniência e manifesto. Staging contém somente as quatro bibliotecas
em `/usr/lib`; consumidores devem fornecer headers da mesma revisão/patches.
Não é uma API pública de headers nem uma mudança automática da receita C60,
que continua fixada ao SDK privado histórico.

Para cada ELF: AArch64/shared object, RELRO/NOW, RUNPATH `$ORIGIN` onde já
existia, mesmas dependências NEEDED, mesmos símbolos exportados, tamanhos dos
objetos exportados e versões GLIBC da fundação. O teste QEMU/Cortex-A35 carrega
o conjunto com RTLD_NOW e confirma os caminhos novos; executa ainda version/help
do muxretro C60 com as novas bibliotecas à frente das dependências originais.
Isso verifica resolução dinâmica/CLI, sem abrir vídeo, entrada ou áudio.

Primeira tentativa `build.fr0v680t` parou no probe: abrir `libui` isoladamente
não resolve `mux_tick`, referência fornecida por `libmuxcom`, que por sua vez
usa símbolos da UI. A correção do probe carrega primeiro `libmuxmod`, permitindo
resolver o grupo de dependências numa operação. Não foi aplicado stub ou patch
às bibliotecas para ocultar o erro. Os recibos da tentativa permanecem em build/.

## Limites e próximo incremento

As bibliotecas desta receita ainda precisam de qualificação nativa quando os
bytes diferirem dos aprovados. ABI/loader/CLI não aprovam imagem, entrada,
som, estabilidade ou boot. Nenhuma biblioteca é instalada automaticamente;
C64 e a fundação anterior permanecem as referências de recuperação.

| Biblioteca | SHA256 C65 | Igual à fundação | Símbolos exportados conferidos |
| --- | --- | --- | --- |
| libui.so | `639c1df8c75dc5007abfb87817d8cb1ea6b3ed7e0366f008e976a0e74491791e` | não | 1.080 |
| libmuxcom.so | `2913dbf7d901a258d338995e0d937c2f6559465c41a3bd0e097072820f57cd21` | não | 1.653 |
| libmuxmod.so | `bfd909c6eae5d6d692025e8a0b489840c9a552d3ad22e902183b6265d700ae17` | sim | 2.402 |
| libplutosvg.so | `99377c313fdb5401e4535be4750afb8db9c6c6acc052818a2eee0c956cbe8683` | sim | 264 |

As duas compilações limpas produziram as quatro bibliotecas byte a byte iguais
entre si; `repeat-build.json` registra a comparação. Essa repetibilidade
observada não qualifica uma reconstrução completa do firmware. A causa da
diferença das duas bibliotecas em relação à fundação anterior não foi isolada;
ABI igual não torna os novos ELFs aprovados nativamente. Houve 254 warnings de
compilação: 253 de possível truncamento de formatos e uma redefinição da macro
miniz já presente nas fontes. Zero erros; não foram alteradas fontes upstream
para eliminar warnings neste incremento.

Próximo C66 proposto: qualificar o conjunto novo em RAM no runtime supervisionado,
preservando o override diagnóstico C46 dos menus e o host instalado. Começar
pela inspeção real de boot/IP/root/manifestos, sem afrouxar os vínculos de C63;
se o boot mudou, adaptar o caller em incremento próprio. Uma futura receita
consumidora deve declarar dependência deste provider e fixar seus hashes,
sem reescrever a C60 histórica. Boot da imagem, frontend permanente, Power,
suspend, SRAM, perda elétrica e estabilidade prolongada continuam separados.

Console/cartões/Steam Deck não são acessados no C65. O IP informado pelo usuário
continua 192.168.15.10, sem confirmação nova. Original de 32 GB preservado.

# Fase 4 — C60: receita opt-in do host muxretro

Em 03/11/2026, o host foi reconstruído a partir das fontes C50 qualificadas e
integrado como pacote opcional `BR2_PACKAGE_MUOS_MUXRETRO`. A receita permanece
desativada por padrão. A validação C60 é offline: compilação, licenças,
carregamento/CLI e instalação numa cópia da árvore privada C56. O novo ELF
**ainda não tem qualificação nativa**; as aprovações físicas C50–C59 continuam
vinculadas ao ELF antigo.

## Fontes, licenças e fronteira do pacote

O preparador `port/scripts/build-phase4-muxretro-package.py` verifica as provas
C50/C59 e a cadeia C41 → C44 → C47 → C50, incluindo os hashes dos scripts e
recibos de origem. Reconstrói o frontend `5e8635b3b485eec9ad2ace141c415fd2df47d8f1`
do arquivo local fixado, aplica os patches 0003/0006/0007/0008/0009/0012/0015 e
acrescenta `phase4-diagnostic-exit.h`. A lista e os bytes dos 1.195 arquivos de
fontes/build/licenças assim preparados coincidem com a árvore C50 qualificada.
Os ramos experimentais 0013/0014 não pertencem a essa linhagem.

Rcheevos é fixado em `2ad0b8672f68a48148620164510b963039e49eb1`, com verificação
do hash do arquivo local e da licença MIT. São declaradas GPL-3.0, MIT,
BSD-2-Clause e Unlicense, com nove arquivos de licença fixados por hash,
incluindo o aviso de libretro.h e os vendors usados. As referências consultadas
foram os Makefiles do frontend/retro, os avisos de licença e as implementações
`pkg-generic.mk`, Kconfig e `legal-info` do Buildroot da bancada.

No método `local`, `legal-info` arquiva a árvore SITE inteira. Por isso o SITE
contém apenas fontes, licenças, script e proveniência: 1.300 arquivos, todos
conferidos antes do build. O arquivo legal produzido pelo Buildroot tem essa
mesma lista e esses mesmos bytes. Não inclui ELFs, objetos ou bibliotecas
precompiladas. O preparador reutiliza um SITE existente somente se seu
inventário/hash coincidir exatamente; divergências são recusadas.

## SDK privado explícito

O host depende das bibliotecas muOS `libui.so`, `libmuxcom.so`, `libmuxmod.so` e
`libplutosvg.so`, já qualificadas na fundação C38. Não existe ainda um provider
Buildroot completo dessas bibliotecas. C60 exige o opt-in separado
`BR2_MUOS_PRIVATE_FRONTEND_SDK` e prepara um SDK de link em
`build/phase4/muxretro-package/platform/lib`, fora do SITE. Antes de compilar,
a macro verifica os quatro hashes. Não instala essas bibliotecas.

A receita declara SDL2/image/mixer/ttf, Harfbuzz, FreeType, PNG, curl, archive,
OpenSSL, zlib e os providers EGL/GLES, além de host-pkgconf. Kconfig exige
AArch64, C++, wchar, threads, operações atômicas, GCC compatível e link
dinâmico. A configuração mínima isolada usa ROCKCHIP_MALI para exercitar os
símbolos EGL/GLES reais; não compila nem baixa esse provider. A compilação
usa o SDK gráfico privado existente, com seu provider já preparado. Portanto
isso não qualifica um build completo partindo apenas dessa configuração.
As pendências de licença da imagem gráfica privada continuam em vigor.

## Instalação e verificações

A macro real de instalação acrescenta treze arquivos:

- `/opt/muos/frontend/muxretro`, modo 0755;
- proveniência, manifesto dos quatro links e manifesto do payload sob
  `/usr/share/muos-muxretro/`, modo 0644;
- nove avisos de licença em `/usr/share/licenses/muos-muxretro/`, modo 0644.

O manifesto do payload cobre os outros doze arquivos. O manifesto de links
usa caminhos relativos `lib/...`: a composição verifica esses caminhos em
`/opt/muos/frontend`, enquanto o build os verifica no SDK. Não há core, ROM,
save, serviço, seletor, writer ou autostart instalado pelo pacote.

O ensaio usa container sem rede, somente o `port/` montado para leitura e
`O=` isolado, preservando o `.config` compartilhado do SDK. Passaram:

- Kconfig real: padrão desativado, seleção recusada sem SDK, opt-in com
  dependências, i386 confirmado com seleção do host recusada;
- rsync e `legal-info` reais, inventário exato e nove licenças/hash válidos;
- SDK ausente ou com `libui.so` adulterada recusado pela macro antes do
  compilador, comprovado por um compilador-sentinela que não foi chamado;
- compilação limpa de rcheevos e host pelas macros reais usando o SDK;
- ELF AArch64 PIE, intérprete `/lib/ld-linux-aarch64.so.1`, RELRO/NOW e
  RUNPATH `/opt/muos/frontend/lib`, sem caminho de build no RUNPATH;
- loader A35/QEMU com `LD_BIND_NOW=1`, `--version` e `--help`, sem iniciar
  gráficos/core/conteúdo;
- instalação numa nova cópia C56, acrescentando 13 arquivos e 13 diretórios,
  com todos os 3.330 itens anteriores
  preservados, manifests do store/host válidos, fundação97/payload15/perfil21,
  contador de fábrica0/defaults desativados e contrato C07 preservados;
- loader/CLI do host nessa composição, sem replay dos 172 loaders antigos.

O novo ELF difere do C50
(`4f230ad1ca347a889e5eda2b5171aba4568670ae28a1b2d294abf4a95e8a44dd`).
O novo hash é
`8d519958cdb1ae599e2b2af2f6ee90053bca1a83cce0380baa3a1d7150983f05`,
no recibo `build/phase4/muxretro-package/build.mdou4mqr/analysis.json`.
Igualdade de fontes não permite
transferir a aprovação física para esse ELF. A causa da diferença binária e
reprodutibilidade bit a bit não foram qualificadas. Não foi feito rebuild
completo do Buildroot, imagem ext4 nova, boot ou sessão nativa.

O compilador emitiu avisos em fontes upstream, inclusive truncamento de
strings, e o linker avisou sobre símbolos locais na dynsym do `libEGL.so`
do SDK gráfico existente. O stderr foi conservado na prova. O build não é
declarado livre de avisos; o sucesso do loader/CLI não valida a execução GPU.

As provas C50/C59/C56 e os inputs qualificados permanecem intactos. O novo
menu é acrescentado ao `Config.in`; compositores históricos que fixam a
lista antiga podem recusá-lo por sua guarda de linhagem. C60 usa seu próprio
adaptador aditivo sobre a árvore C56, sem relaxar essas guardas ou refazer
provas antigas. O lint `check-package` não foi repetido: permanece a ausência
conhecida do módulo Python `magic` no container; nada foi instalado no host.

## Reprodução e próximo incremento

Com os mesmos arquivos locais e SDK já preparados, na raiz do repositório:

```sh
python3 port/scripts/build-phase4-muxretro-package.py
python3 port/scripts/package-phase4-muxretro-package.py
```

Cada build usa um stage novo, apontado por
`build/phase4/muxretro-package/latest-build`. A etapa de empacotamento recusa
sobrescrever `dist/phase4/muxretro-package`. Essa prova contém fontes próprias,
licenças, inventários e recibos, sem ELF, SDK, arquivo de fontes compactado,
rootfs, ROM ou saves.

O console não foi consultado neste incremento. O último estado observado é
o C59: C07/boot70, IP 192.168.15.14:2222, root RO, p3 desmontada e pacote C57
passivo. Esses valores precisam ser relidos antes de uma operação futura;
não são uma conferência atual de rede/console. Não houve acesso aos cartões
nem ao Steam Deck, rearmamento de C12/C25 ou alteração do store.

Próximo C61 proposto: qualificar o novo ELF primeiro em RAM, com guardas e
proveniência próprias, comparando imagem/entrada/áudio/hotkeys/retorno na
sessão GB limitada. Usar o backend instalado em leitura e não produzir novo
save; respeitar os vínculos de boot e consultar o estado real antes. Só
depois considerar instalação seletiva com recuperação. O provider completo
das bibliotecas frontend, frontend permanente, boot da imagem, Power/suspend,
SRAM/GC/perda elétrica e continuidade de áudio permanecem separados.

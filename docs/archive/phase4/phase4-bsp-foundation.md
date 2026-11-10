# Fase 4 — base BSP próxima ao dArkOSen

Iniciada em 24/10/2026, America/Sao_Paulo, seguindo a decisão do roadmap. **Estado: em andamento.** Foram compilados kernel, módulos e um DTS próprio Panel 0; a configuração preliminar do rootfs passou no Kconfig. Na etapa BSP inicial não havia rootfs compilado; a continuação abaixo gerou e auditou o rootfs headless. Ainda não há firmware completo ou validação de boot. Na etapa BSP o console foi consultado somente por leitura; a continuação executou um probe com bibliotecas próprias temporárias em tmpfs, sem parar serviços ou trocar arquivos do sistema.

**Continuação:** o [registro de userspace/init](phase4-rootfs.md) acompanha agora
o rootfs/sysroot compilados offline, a auditoria ELF/ext4/QEMU e o probe nativo
da nova libc, além dos contratos pendentes do init. Os resultados acima descrevem o primeiro incremento
do BSP; o estado do novo build deve ser consultado nesse registro e no job.

## Decisão e escopo da prova

Manter inicialmente a família BSP 4.4 usada pelo aparelho, com uma candidata construída de fontes identificadas. Isso reduz a troca simultânea de kernel, bindings e stack gráfica. Não equivale a reconstruir byte a byte o dArkOSen instalado, nem transforma o kernel antigo em escolha definitiva. ROCKNIX continua como alternativa caso os requisitos de fonte, estabilidade ou redistribuição inviabilizem esta base.

O [manifesto de fontes](../../port/device/rk-r35s-p0/phase4-sources.json) separa os componentes conhecidos das pendências. Os fontes externos foram obtidos somente em `build/phase4/`; `refs/` permaneceu intacto, incluindo suas alterações preexistentes.

## Kernel e configuração: fatos e lacunas

O [README do kernel dArkOSen](../../refs/darkosen/KERNEL/README.md) aponta `christianhaitian/linux:rg351`, `rg351p_tweaked_defconfig` e Linaro 6.3.1. O snapshot dArkOSen tem somente dois fontes alterados de CPU/OPP, módulos e binários; não contém uma árvore completa nem o commit exato da compilação instalada. Uma cópia de configuração foi recuperada posteriormente do rootfs do aparelho.

| Componente da prova | Revisão fixada | Observação |
| --- | --- | --- |
| Linux BSP | `d8402159c04b1044106b4f27b7ed7c22ed09228f` | branch `rg351`, observada em 24/10; commit de 04/10/2026, posterior ao banner do kernel instalado |
| exFAT, submódulo do Linux | `68072a2dc3bf9d73e8bda9b82fa3f93a7e9ff0a5` | necessário ao build completo de módulos |
| Compilador de kernel | `46d00ad5a58edae59b2bc16f4694510b93d51889` | Linaro GCC 6.3.1/20170404; separado da futura toolchain de userspace |
| Buildroot, configuração preliminar | `4f924fd52841608d68ac3dcb83fccee8b8c90316` | tag 2025.02.19, commit de 22/10/2026 |

Fontes primárias: [Linux](https://github.com/christianhaitian/linux/tree/d8402159c04b1044106b4f27b7ed7c22ed09228f), [toolchain](https://github.com/rockchip-toybrick/gcc-linaro-6.3.1-2017.05-x86_64_aarch64-linux-gnu/tree/46d00ad5a58edae59b2bc16f4694510b93d51889), [Buildroot](https://github.com/buildroot/buildroot/tree/4f924fd52841608d68ac3dcb83fccee8b8c90316). Essas revisões identificam a candidata, não a origem exata do `Image` instalado.

A consulta inicial não encontrou `/proc/config.gz`, configuração no `/boot` FAT ou nos links de módulos. Os links `build/source` apontam para um diretório inexistente de outra máquina. O `Image` lido do cartão não contém marcador `IKCFG_ST`.

A [receita upstream de build](https://github.com/christianhaitian/dArkOS/blob/daecf488075f0194c164578b90617fa7002ce8bd/build_kernel.sh) mostrou que a configuração é salva no diretório `/boot` **do rootfs**, separado da partição FAT. Um bind não recursivo da raiz, em mount namespace privado, permitiu ler a cópia escondida sem desmontar o `/boot` do console. Foram encontrados `config-4.4.189` e `initrd.img-4.4.189`; a configuração de 120.594 bytes tem SHA256 `f2f05dedb85831b47ae8bd1c3e86819f6e1a640a81e27f088b4fb3cec6326361`. O bind e seu diretório temporário foram removidos.

Comparada com o defconfig público, a cópia difere somente em dois símbolos de uma configuração antiga de Wi-Fi. Após resolução pelo Kconfig, a configuração da prova difere dela em cinco campos intencionais: `LOCALVERSION`, `LOCALVERSION_AUTO`, `IKCONFIG`, `IKCONFIG_PROC` e `BUILD_BIN2C` (este selecionado pela exportação de config). Não apareceu diferença de configuração de hardware nessa comparação. A cópia é evidência forte da configuração usada, mas não há vínculo criptográfico embutido com o `Image`; o commit e a reconstrução exata do binário continuam não comprovados.

| Binário examinado | SHA256 | Banner |
| --- | --- | --- |
| `/boot/Image` instalado | `31bdb671d640863448b59f79801277fe486fa6c78c326bd4ebb51a54559b0577` | `#1 SMP Thu Oct 1 02:03:12 UTC 2026` |
| `refs/darkosen/boot/Image` | `7b8b2b466cd7596c4fc059d55874569afb9973e50e01aaccdb4d3d6d9f3a58bd` | setembro/2026 |
| `refs/darkosen/KERNEL/Image`, alteração local preexistente | `8c3b27588f2d875fb3e45045f2f20597209e70abe4cb4634e9cdc8074b0fa259` | julho/2026 |

Os três diferem. O último não foi usado como entrada do build. A candidata usa o defconfig declarado e um [fragmento explícito](../../port/device/rk-r35s-p0/phase4-bsp.fragment): versão própria e exportação de configuração para facilitar auditorias futuras. As alterações de overclock dArkOSen foram comparadas e registradas, mas não aplicadas. Os cabeçalhos desses dois fontes declaram GPLv2/GPLv2+, apesar da licença MIT de topo do dArkOSen; não se generalizou a licença de topo.

## Compilação executada

O [script de build](../../port/scripts/build-phase4-bsp-probe.sh) usa [container próprio](../../port/packaging/phase4-kernel.Containerfile), pacotes Debian fixados por snapshot, Linaro fixado, build fora da árvore, rede desabilitada na compilação, timestamp/usuário/host controlados e sufixo `-muos-r35s-p4`. Nenhuma dependência foi instalada no Bazzite ou no console.

Resultado:

```text
kernelrelease: 4.4.189-muos-r35s-p4
MODPOST 555 modules
vermagic: 4.4.189-muos-r35s-p4 SMP mod_unload aarch64
```

Os 555 módulos foram conferidos como ELF64 little-endian/AArch64 e com esse mesmo vermagic. O kernel gerado tem SHA256 `780935823cb8c86e4330c8c8157ebb4005fb5580e68e72c4b0c4e480bab42d2f`. A configuração inclui Mali Bifrost e ext4 embutidos. Os artefatos ficam em `dist/phase4/bsp-probe/`, junto de fontes do port, manifesto, config, versões, licença Linux e checksums. O aviso `NOT-FOR-DEVICE-BOOT.txt` identifica seu estado de prova; não há bootloader, rootfs ou configuração de boot no pacote.

A receita está fixada e pode ser repetida; ainda não foi demonstrada reprodução byte a byte com dois builds completamente limpos. Reexecuções incrementais não substituem essa prova.

Ajustes de ambiente necessários: alias `python` para Python3 no container, `HOSTCFLAGS=-O2 -fcommon` para ferramentas antigas e `KBUILD` apontando para a saída, como exige o Makefile do esp8089. Uma inspeção concorrente com volume `:Z` privado provocou erros de permissão; o volume passou a usar `:z` compartilhado, sem desabilitar SELinux ([documentação Podman](https://docs.podman.io/en/latest/markdown/podman-run.1.html)). O kmod moderno avisou sobre `modules.builtin.modinfo`, formato não gerado por essa árvore antiga; `modules_install` terminou com status0. Esses eventos de host não foram falhas do console.

## DTS próprio e comparação com o Panel 0 instalado

O [DTS do port](../../port/device/rk-r35s-p0/rk3326-muos-r35s-panel0.dts) inclui `rk3326-r35s-linux.dts` da revisão fixada. Esse fonte de base declara `GPL-2.0+ OR MIT`; o delta conserva essa licença. Não foi copiado um DTS completo decompilado do binário.

A fonte R35S já contém a sequência de inicialização correta:370 bytes, SHA256 `972f614858caa119329cffdafc07c3a610b92343090ee7acf65e68c21d131a91`. O delta reproduz modelo, modo nativo de 29 MHz, deadzone384, propriedades de bateria/carregador e LED observadas no aparelho. Capacidade3140/qmax3454 são dados do DTB, não medições da célula. O perfil mantém OPPs da base até CPU 1296MHz/GPU 520MHz e teto CPU 1,35V, excluindo os acréscimos de overclock do dArkOSen e os modos 50/75Hz não ensaiados.

```text
640×480; clock 29000000
hfront 46, hsync 2, hback 44
vfront 165, vsync 2, vback 14
refresh nominal 59.935682812 Hz
```

Esses timings coincidem com o modo medido na Fase 2, não com os50MHz do preset estático inicial. O novo DTB tem SHA256 `496bbe3591f8619f059ebc384277ecdd17fd41f956aef40de20afb46b92d5b49` e foi compilado a partir da mesma árvore usada para kernel/módulos.

O [verificador](../../port/scripts/verify-phase4-dtb.py) compara propriedades com o DTB instalado fixado por hash, resolvendo referências de phandles por caminho. Isso evita confundir renumeração de referências com mudança de GPIO, clock ou regulador. Fora de metadados do compilador, somente a remoção explícita dos modos/OPPs e os tetos de tensão planejados podem diferir. A comparação passou; testes negativos rejeitaram o DTB genérico de modelo diferente, hsync alterado e arquivo truncado. Isso comprova consistência estática; **o novo DTB ainda não iniciou o aparelho**. A fonte correspondente ao DTB separado de U-Boot permanece pendente.

## GPU/SDL: identidade conhecida não basta para outro rootfs

O `libmali` instalado não pertence a um pacote dpkg. Seu identificador Git de blob, calculado por leitura no aparelho, coincide com `2083f5386c201abc8f2e697e8004a14e59524a86` em [rk3326_core_builds/mali/aarch64](https://github.com/christianhaitian/rk3326_core_builds/tree/5b00a35296321c32900b91191498d7036448e967/mali/aarch64). SHA256 `2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea`,40.867.064 bytes. Não foi necessário copiar esse blob para o pacote de saída. A [retomada r13p0](phase4-r13-runtime.md) encontrou o mesmo blob no ZIP original Hardkernel, com checksum de origem fixado por receita Batocera. Seu overlay temporário passou em EGL/SDL no userspace próprio; o ZIP não contém licença e não foi incorporado a uma imagem ou pacote de firmware.

O ELF requer libc/libm/dl/pthread/rt, libdrm, libstdc++ e libgcc_s, com versões observadas até GLIBC 2.17/GLIBCXX 3.4.20. **Correção após o ensaio gráfico:** a candidata contém `bifrost_for_linux` com handshake UK **11.7**, definido em `mali_kbase_ioctl.h` e incluído por `mali_kbase_core_linux.c:51`, conforme o `.cmd` do objeto compilado. A anotação anterior 10.6 veio de `mali_kbase_uku.h`, header legado que não define esse caminho. O kernel instalado também informou 11.7 ao provider experimental. A combinação com a libmali Buildroot, que exige 10.6, falhou antes do contexto EGL; detalhes e provas no [relatório gráfico](phase4-graphics.md). Isso não autoriza alterar versões ou transportar blobs sem conferir contratos/licenças.

O [recipe Buildroot de rockchip-mali](https://github.com/buildroot/buildroot/blob/4f924fd52841608d68ac3dcb83fccee8b8c90316/package/rockchip-mali/rockchip-mali.mk) usa uma biblioteca de mesmo nome, porém de 38.901.128 bytes e blob `4078f62898b4db11b1915f0cdb01a7f59958def7`: não é byte a byte o arquivo instalado. Esse pacote declara licença proprietária e um [EULA](https://github.com/JeffyCN/mirrors/blob/721653b5b3b525a4f80d15aa7e2f9df7b7e60427/END_USER_LICENCE_AGREEMENT.txt). A MIT de topo de `rk3326_core_builds` não fecha sozinha a licença específica do blob instalado. Identidade, licença aplicável e ABI devem ser resolvidas para o artefato efetivamente escolhido, sem presumir equivalência pelo nome.

A receita de SDL foi localizada em [scripts/sdl2.sh](https://github.com/christianhaitian/rk3326_core_builds/blob/5b00a35296321c32900b91191498d7036448e967/scripts/sdl2.sh): fonte `5d249570393f7a37e037abf22cd6012a4cc56a71`, patches, alterações de controller/revert e ligação com RGA. O SDL instalado customizado tem SHA256 `ae22e9a309f838172aa2e4b08b0195d2084436195ff5672969c58af4eb270e33`, requer símbolos até GLIBC 2.38 e depende também de libsamplerate/librga. A receita encontrada ainda não foi executada nem comparada byte a byte com esse binário.

## Rootfs e init: configuração própria preliminar

Esta seção registra o primeiro incremento, limitado ao Kconfig. A compilação
e auditoria posteriores do rootfs/sysroot foram concluídas e estão no
[relatório de continuação](phase4-rootfs.md); as ausências descritas abaixo
referem-se à etapa inicial, salvo os contratos muOS ainda pendentes.

Não foi identificada receita completa oficial do rootfs muOS nos três refs nem nas buscas públicas delimitadas. Isso não prova inexistência em outros materiais. Os scripts muOS de imagem continuam operando sobre imagens existentes. A alternativa própria em avaliação usa Buildroot 2025.02.19 fixado; não é o rootfs Debian do dArkOSen com outro launcher.

O [defconfig preliminar](../../port/device/rk-r35s-p0/phase4-rootfs.defconfig) seleciona AArch64/Cortex-A35, GCC 13.4, glibc 2.41 da versão fixada, headers da mesma árvore BSP com série4.4, BusyBox init, eudev, Bash, D-Bus, ALSA, PipeWire/WirePlumber e ext4. O [script de configuração](../../port/scripts/configure-phase4-rootfs.sh) passou no Kconfig e confirmou cada seleção solicitada. Esse perfil ainda é de bring-up sem gráficos: SDL, Mali e payload/init muOS não estão incluídos.

A receita glibc do Buildroot usa `--enable-kernel` derivado da série dos headers; a configuração resolvida anuncia4.4. A ferramenta Linaro 6.3 usada no kernel **não** foi adotada como sysroot de userspace. O futuro frontend será recompilado e terá loader/símbolos/dependências conferidos de novo. Nem mesmo os binários Debian aprovados na Fase3 são tratados como compatíveis automaticamente.

O perfil propõe ext4 sem `orphan_file`, `metadata_csum_seed`, `fast_commit` ou64bit, evitando habilitar features novas sem conferir o BSP. Nenhum filesystem foi criado; esses flags precisarão ser inspecionados na imagem efetivamente gerada. A partição FAT/layout/bootloader ainda não foram montados em uma imagem.

Para integrar init, ainda é necessário ligar PID1/rcS/rcK a `/opt/muos/script/init/sysinit` e `shutdown`, fornecer `/opt/muos` e `/run/muos` e evitar inicializações duplicadas de eudev/D-Bus entre Buildroot e muOS. O muOS exige `/sbin/udevd`; áudio exige os plugins/rotas de PipeWire apropriados ao RK817. A configuração preliminar não implementa esses contratos nem executou os scripts upstream no Debian. O caminho musplash/mmap permanece excluído até resolver o problema de kernel registrado.

## Reexecução e próximos marcos

Os comandos já exercitados, executados no host a partir do repositório, são:

```sh
bash port/scripts/build-phase4-bsp-probe.sh
bash port/scripts/configure-phase4-rootfs.sh
python3 port/scripts/verify-phase4-dtb.py \
  dist/phase4/bsp-probe/rk3326-muos-r35s-panel0.dtb \
  build/phase4/panel-reference/rk3326-r36s-linux.dtb
```

A última referência é o DTB coletado por leitura, com hash fixado; não pode ser substituído por um preset de mesmo nome. Os scripts não gravam mídias nem executam instalação no console.

O marco de sysroot/rootfs headless e sua auditoria foi concluído na [continuação](phase4-rootfs.md). O incremento [core/áudio](phase4-core-audio.md) recompilou utilitários e exercitou cache e start/stop nativos com o rootfs próprio. Os bipes foram ouvidos, ainda baixos; não fecha a validação de áudio. O [input novo](phase4-native-input.md) também passou posteriormente com criação uinput real e controles físicos. Próximos marcos: sons reais e mapping SDL, integrar init/storage completos; fechar GPU/SDL/licenças e proveniência de U-Boot/DDR/BL31; gerar um conjunto completo. Só depois haverá candidato a boot em mídia identificada na Fase 5. A fase atual permanece aberta até atender esses critérios; o primeiro build não equivale a aprovação de firmware.

Evidências em `build/phase4/`: `device-inventory.json`, `hidden-boot-inventory.json`, `installed-hidden.config`, `config-comparison.json`, `installed-Image`, `kernel-source-comparison.txt`, `gpu-package-origin.txt`, `gpu-abi.txt`, `installed-git-blob-ids.json`, fontes públicos em `provenance/`, `kernel-build.log`, `module-verification.json`, `panel-verification.json`, `dtb-negative-checks.txt`, decompilações/diffs em `panel-reference/` e `rootfs-config-run.txt`. Configuração resolvida em `rootfs-output/.config`. Os logs das tentativas de ambiente também foram preservados. Os artefatos são experimentais locais; nenhum upload/release foi realizado.

**Investigação posterior:** a [cadeia de boot instalada](phase4-boot-chain.md) foi lida sem escrita de setores: trust corresponde ao ref, idbloader/U-Boot divergem e o DTS de U-Boot de mesmo nome não corresponde ao Panel 0. O [incremento gráfico](phase4-graphics.md) mantém sua candidata em saída própria, sem substituir o artefato core.

**Userspace próprio, 25/10:** o [menu recompilado](phase4-menu-own-rootfs.md) passou com dependências Buildroot, SDL/KMSDRM, mapping gerado do controle e áudio PipeWire no overlay privado r13p0. Uma divergência do mixer após restaurar serviços foi detectada e reparada, com regressão automática. Isso avança o userspace, sem validar boot/kernel candidato ou fechar o provider/licença para firmware.

**Incremento posterior, 25/10:** o [provider privado integrado](phase4-private-foundation.md) substitui o overlay por uma receita SDK/target coerente com r13p0. Imagem de 281 ELF, QEMU/GBM/UI e fsck passaram. O adaptador de armazenamento de uma única mídia e sua guarda de inicialização passaram em namespace/tmpfs nativo após corrigir a dependência `stat`; não houve exposição dos cartões nem autostart do frontend ampliado. O usuário adiou consultas de licenças para um Markdown único ao fim do projeto: o [registro](../../port/packaging/pending-licenses.json) mantém essas pendências, sem bloquear os ensaios privados. Publicação, módulos/firmware no rootfs final, init/shutdown completo, cadeia própria de boot e o boot da candidata continuam pendentes.

**Frontend ampliado e controles:** a [continuação](phase4-full-frontend.md)
passou em submenus, áudio, volume e brilho reais, usando scripts/manifesto
nativos adicionados ao staging. A correção do volume físico+virtual fica no
patch0006; precisa integrar a próxima imagem junto com esses recursos e o
mapper. Mixer/brilho/serviços foram restaurados e a saúde do aparelho passou
na coleta. O kernel candidato e sua cadeia de boot permanecem sem execução.

**Serviços integrados:** a [continuação de init](phase4-init-services.md)
validou espera do controle/mapping, novo first_paint e supervisão/parada da
UI, incluindo helpers destacados. A candidata de283 ELF foi reconstruída
com autostart configurado após aprovação nativa dos serviços. Isso não é
boot do BSP: módulos/firmware na raiz e cadeia de boot seguem como próximo
marco, com energia e dispatcher de conteúdo ainda incompletos.

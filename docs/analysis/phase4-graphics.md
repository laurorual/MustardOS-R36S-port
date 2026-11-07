# Fase 4 — candidata EGL/GLES/GBM e SDL para o sysroot próprio

Continuação local de 24/10/2026, após o [incremento core/áudio](phase4-core-audio.md).
O console permanece no dArkOSen. **Checkpoint atual:** build, auditoria
ELF/ext4/QEMU e coleta de fontes/licenças passaram. O ensaio nativo chegou à
enumeração SDL/KMSDRM e à leitura do modo DRM, mas **falhou antes do primeiro
frame**: a biblioteca Mali exige UK 10.6 e o kernel responde UK 11.7.
O launcher foi restaurado e o usuário confirmou que está normal e funcional.
Não repetir esta candidata sem trocar e auditar o provider.

**Retomada posterior:** o [overlay local Hardkernel r13p0](phase4-r13-runtime.md) passou em EGL/readback e SDL na tela com as bibliotecas do port. Esta página preserva a rejeição do pacote original; o overlay não reconstrói a imagem nem resolve a licença de redistribuição.

## Escolha e evidência

| Componente candidato | Origem fixada | O que está comprovado |
| --- | --- | --- |
| EGL/GLES/GBM | Buildroot `4f924fd52841608d68ac3dcb83fccee8b8c90316`, pacote rockchip-mali; mirrors `721653b5b3b525a4f80d15aa7e2f9df7b7e60427` | Um provider fornece os três contratos, sem combinar GBM Mesa com EGL Mali |
| Biblioteca escolhida | `lib/aarch64-linux-gnu/libmali-bifrost-g31-rxp0-gbm.so` do arquivo da receita | 38.901.128 bytes, blob Git `4078f62898b4db11b1915f0cdb01a7f59958def7`; diferente do instalado, de 40.867.064 bytes |
| libdrm | 2.4.124 do mesmo Buildroot | Fonte obtido com hash da receita, sem aprovação de cada ioctl no BSP |
| SDL2 | 2.30.12 do mesmo Buildroot, Zlib | KMSDRM + OpenGLES selecionados, sem X11/Wayland; não é a SDL 2.32.10 customizada do dArkOSen |

O [fragmento](../../port/device/rk-r35s-p0/phase4-graphics.fragment) acrescenta
providers e SDL à base core, com a mesma família de toolchain/headers. O
[configurador](../../port/scripts/configure-phase4-graphics.sh) usa saída
separada e verifica que a configuração core permanece idêntica. O Kconfig
resolveu os providers LIBEGL/LIBGLES/LIBGBM para `rockchip-mali` e não selecionou
outro kernel nem `mali-driver`: o BSP continua sendo produzido separadamente.
Os símbolos de disponibilidade para Qt/Kodi/glmark aparecem no diff como
derivações Kconfig; isso não significa que esses aplicativos foram habilitados.

Essa escolha permite investigar um provider com fonte de empacotamento e
licença associados a um arquivo específico. **Hipótese de compatibilidade:**
esse blob funcionará com a interface Bifrost do BSP. Nome parecido, arquitetura
correta, dependências ELF resolvidas e o teste anterior de outra libmali não
demonstram essa hipótese. A revisão posterior da cadeia de includes confirmou
UK **11.7** também na candidata de kernel; o valor 10.6 anotado anteriormente
vinha de um header legado não utilizado por esse caminho de ioctl.

## Licença específica e identidade

O [EULA da revisão escolhida](https://github.com/JeffyCN/mirrors/blob/721653b5b3b525a4f80d15aa7e2f9df7b7e60427/END_USER_LICENCE_AGREEMENT.txt)
foi consultado e comparado com o arquivo do **mesmo tarball** que contém o blob.
SHA256: `a78acc73de9909efb879800d4daa4640c4aaa55cd751238a133954aba15e4285`,
igual ao esperado pela receita. O texto trata de uso/desenvolvimento para
produtos Mali e redistribuição sujeita às condições das cláusulas 1.1/1.2,
incluindo avisos e cópia da licença. A biblioteca permanece proprietária;
não foi classificada como MIT ou software livre.

Isso associa uma licença concreta ao **provider candidato**, sem estendê-la
ao blob diferente em `rk3326_core_builds`. Antes de publicar firmware com
frontend GPLv3 e bibliotecas proprietárias, ainda será necessário fechar o
enquadramento da distribuição e os avisos dos componentes efetivamente
incluídos. Não houve publicação nem incorporação de Mali ao artefato core.

O arquivo de fonte da receita tem SHA256
`1a291bbd75f317ee9205eb356aed617ac269db166ad6528a1734361cc08f8f7c`.
O export de análise local em `provider-source/source-files.json` registra
hashes de blob/EULA/pkg-config. O recipe aplica patchelf para ajustar SONAME
na instalação; o arquivo instalado precisa ter seu próprio hash, distinto
da identidade original quando houver modificação. Strings internas incluem
uma referência Bifrost r6p0, sem provar a versão efetivamente negociada em runtime.

## Build e auditoria executados

```sh
bash port/scripts/build-phase4-graphics.sh status
# Configure somente sem job ativo; não sobrescreve a saída core.
bash port/scripts/configure-phase4-graphics.sh
bash port/scripts/build-phase4-graphics.sh fetch
# Esperar fetch.exit=0 e container parado.
bash port/scripts/build-phase4-graphics.sh build
# Esperar build.exit=0 e container parado.
bash port/scripts/audit-phase4-graphics.sh
bash port/scripts/collect-phase4-graphics-legal-info.sh
```

O build usou container fixado `ccef62bd…6787`, 8 jobs, limite 12 GiB, cache de
downloads compartilhado e rede desabilitada durante compilação. A saída é
independente do rootfs core aprovado parcialmente. Uma tentativa de
reconfigurar durante o build foi rejeitada; hashes dos dois configs e do
manifesto de fontes core ficaram inalterados (`concurrency-check.json`).

O [probe de contrato](../../port/probes/phase4-graphics-contract.c) solicita
somente versão/listagem de drivers SDL e resolução de símbolos EGL/GLES/GBM/DRM.
Não inicializa vídeo; o container de auditoria não expõe GPU/DRM, inclusive a
construtores de bibliotecas. O teste QEMU Cortex-A35 avaliou loader/dependências
e símbolos, **não** negociação com o driver do handheld ou geração de frames.

O [auditor](../../port/scripts/audit-phase4-graphics.sh) também recompila os
probes existentes SDL e DRM para este sysroot, registra ELF e inspeciona o
rootfs/ext4/fsck. Compilação desses probes não autoriza reutilizar o runner
antigo que monta bibliotecas Debian.

O primeiro build terminou com status 0, mas a auditoria encontrou somente
`dummy/evdev`: Kconfig não garantiu a inclusão de KMSDRM. O configure SDL
exigia `gbm >= 11.1.0`; o provider declara 10.4.0. Três alterações locais
Zlib, restritas ao patch-dir desta candidata, permitiram auditar o caminho:

- [0001](../../port/patches/phase4-graphics/sdl2/0001-checked-gbm-10.4.patch): aceita o contrato GBM 10.4 após compile/link dos 18 símbolos obrigatórios; não altera o número declarado em gbm.pc.
- [0002](../../port/patches/phase4-graphics/sdl2/0002-gbm-unversioned-dynamic-loader.patch): detecta o symlink real `libgbm.so`, ausente na busca original por `libgbm.so.*`. Assim usa a resolução dinâmica existente e mantém NULL para as cinco funções opcionais de planos/modificadores ausentes; SDL tem fallback de framebuffer DRM.
- [0003](../../port/patches/phase4-graphics/sdl2/0003-legacy-gbm-cursor-flags.patch): usa CURSOR|WRITE, contrato documentado pelo header do provider, sem inventar GBM_BO_USE_LINEAR ausente. Cursor real permanece não testado. Há fallback semelhante no patch ROCKNIX `projects/ROCKNIX/packages/graphics/SDL2/patches/0007-Support-building-without-hacky-libmali-headers.patch`; não foi copiado.

Após reconstruir SDL, os contratos QEMU passaram com `LD_BIND_NOW=1`, driver
KMSDRM e renderer opengles2 presentes. Foram verificados 251 ELF AArch64,
loader próprio, nota ABI Linux 4.4.0 e ext4 de 512 MiB com fsck sem erro.
SHA256 da imagem: `40b24bb18803f6c086f72321ec75c2cb8326b21298a1f4cfe2ccfe959e33a167`.
Isso comprova compilação/carregamento, sem aprovar o protocolo do driver.

## Ensaio nativo e rejeição do provider

O [preparador](../../port/scripts/prepare-phase4-graphics-session.sh) extraiu
a imagem ext4 real com debugfs/fakeroot, acrescentou probes recompilados
para esse SDK e registrou hashes. O [executor](../../port/scripts/run-phase4-graphics-session.sh)
usou staging em `/tmp` tmpfs, namespaces privados e supervisor de 110 s,
com restauração independente a 150 s. Foram expostos somente nós básicos,
`/dev/dri/card0`, `renderD128` e `/dev/mali0`; sem framebuffer, input, ALSA
ou bibliotecas Debian ligadas ao chroot. Áudio e muinput ficaram desligados.

Evidência em `build/phase4/graphics-config/native-run.log`:

```text
GRAPHICS_LINK_LOAD_CONTRACT=OK; video/GPU runtime untested
GBM_REQUIRED_API=18 present
crtc=60 mode=640x480 ... calculated_hz=59.935683
file /dev/mali0 is not of a compatible version (user 10.6, kernel 11.7)
SDL_CreateWindow: Can't load EGL/GL library on window creation.
PHASE4_CORE_WORKER_EXIT_STATUS=1
MIXER_AND_SERVICES_RESTORED
```

Nenhum contexto EGL, renderer efetivo, readback ou frame foi validado.
O nome opengles2 no contrato é enumeração de capacidade compilada.
Snapshots ALSA inicial/final foram idênticos; os três serviços retornaram,
taint ficou 0, cinco contadores Btrfs ficaram zerados, dmesg não mostrou
novos marcadores de falha e o hash do Image instalado permaneceu inalterado.

**Correção de evidência do kernel:** no Linux `d8402159…`,
`drivers/gpu/arm/Kbuild` seleciona `bifrost_for_linux/`. Seu
`mali_kbase_core_linux.c:51` inclui `mali_kbase_ioctl.h`, cujo contrato em
linhas 55–56 é 11.7. O `.mali_kbase_core_linux.o.cmd` do build registra essa
dependência. O 10.6 de `mali_kbase_uku.h` não descreve o handshake compilado.
Fonte/header/dependências foram preservados em `kernel-abi-evidence/`.
Não há evidência de que um boot da candidata resolveria esta incompatibilidade.

## Artefatos e próxima decisão

`dist/phase4/graphics-candidate/` contém imagem, config, fontes/licenças,
probes, prova nativa rejeitada e checksums. O manifesto distingue
`native_graphics_tested=true` de `native_graphics_passed=false`. A coleta
legal inclui as alterações SDL e o fonte Buildroot; warnings de hashes de
licenças do pacote local são acompanhados pelos arquivos e fontes fixados.
Esse pacote é registro experimental local, sem publicação ou uso para boot.

A inspeção do histórico [ROCKNIX/libmali](https://github.com/ROCKNIX/libmali/tree/e74864b9bc23a6e0f6612c61f9c78afa60bd1832)
encontrou outro rxp0 de 39.674.032 bytes, blob `242e710fc78898ed55d6ceff4d9c43d318928c59`,
SHA256 `b63cd6039affb8a14e428fa581999307745a548a8589cbf453f983da4235ed78`,
com o mesmo blob de EULA nessa árvore. Foi baixado somente para inspeção:
também contém strings r6p0, exige libstdc++/libgcc_s e **não teve UK negociada,
não foi incorporado à imagem nem executado no console**. Não o declarar
substituto compatível. O libmali instalado apresenta strings r13p0; o nome
rxp0 oculta diferenças relevantes. O ROCKNIX atual combina outro provider
g29p1 com seu próprio driver; não é um substituto direto para este BSP.

O menor próximo passo é identificar um provider G31/UK 11.7 com proveniência
e licença associadas, auditar dependências transitivas no SDK próprio e
repetir primeiro a criação de contexto EGL. Só depois repetir quadrantes,
readback e movimento com o usuário. O executor rejeita repetir o mesmo hash
marcado como falho. Não executar musplash, trocar o kernel instalado ou
alterar números de versão para contornar o handshake. Input novo, frontend,
RGA, init completo e boot próprio continuam pendentes.
